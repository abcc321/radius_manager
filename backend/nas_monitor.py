"""
NAS设备定时检测服务
使用异步并发方式同时检测所有设备
"""
import subprocess
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.database import SessionLocal
from common.models import NasDevice


class NasMonitor:
    """NAS设备监控管理器"""

    def __init__(self, max_workers=10):
        self.device_monitors = {}
        self.running = False
        self.max_workers = max_workers  # 最大并发数
        self.lock = threading.Lock()

    def ping_host(self, ip_address, timeout=3):
        """Ping主机检测是否在线"""
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(timeout * 1000), ip_address],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )

            if result.returncode == 0:
                output = result.stdout.decode('gbk', errors='ignore')

                time_ms = None
                for line in output.split('\n'):
                    if '时间' in line or 'time' in line.lower():
                        try:
                            if '时间' in line:
                                time_str = line.split('时间=')[1].split('ms')[0]
                            else:
                                time_str = line.split('time=')[1].split('ms')[0]
                            time_ms = int(time_str)
                            break
                        except:
                            pass

                if time_ms is None:
                    for line in output.split('\n'):
                        if 'TTL' in line or 'ttl' in line:
                            time_ms = 0
                            break

                return True, time_ms, None
            else:
                return False, None, "Ping failed"

        except subprocess.TimeoutExpired:
            return False, None, "Timeout"
        except Exception as e:
            return False, None, str(e)

    def check_device(self, device_info):
        """检测单个设备"""
        device_id, device_name, ip_address = device_info

        print(f"  [{device_name}] Checking...", end=" ", flush=True)

        is_online, response_time, error = self.ping_host(ip_address)
        new_status = "online" if is_online else "offline"

        # 更新设备状态到数据库（仅当状态变化时）
        db = SessionLocal()
        try:
            device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
            if device:
                current_status = device.status or "offline"
                # 只有状态发生变化时才更新数据库
                if current_status != new_status:
                    device.status = new_status
                    db.commit()
                    status_change = f"状态变化: {current_status} → {new_status}"
                    if is_online:
                        print(f"✓ online ({status_change}", end="")
                        if response_time is not None:
                            print(f", {response_time}ms)")
                        else:
                            print(")")
                    else:
                        print(f"✗ offline ({status_change}", end="")
                        if error:
                            print(f", {error})")
                        else:
                            print(")")
                else:
                    # 状态无变化，仅打印检测结果
                    if is_online:
                        print(f"✓ online", end="")
                        if response_time is not None:
                            print(f" ({response_time}ms)")
                        else:
                            print()
                    else:
                        print(f"✗ offline", end="")
                        if error:
                            print(f" - {error}")
                        else:
                            print()
        except Exception as e:
            print(f"  [{device_name}] Database update error: {e}")
            db.rollback()
        finally:
            db.close()

    def check_all_devices(self):
        """并发检测所有设备"""
        db = SessionLocal()
        try:
            devices = db.query(NasDevice).all()

            if not devices:
                print("  No devices to check.")
                return

            # 准备设备信息列表
            device_list = [(d.id, d.name, d.ip_address) for d in devices]

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking {len(device_list)} device(s)...")

            # 使用线程池并发检测所有设备
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.check_device, device): device for device in device_list}
                for future in as_completed(futures):
                    # 等待所有任务完成
                    pass

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Check completed.")

        finally:
            db.close()

    def get_next_check_times(self):
        """获取所有设备的下次检测时间"""
        db = SessionLocal()
        try:
            devices = db.query(NasDevice).all()
            result = []
            for device in devices:
                interval = device.check_interval or 1
                result.append({
                    'name': device.name,
                    'interval': interval,
                    'next_check_seconds': interval * 60
                })
            return result
        finally:
            db.close()

    def start(self):
        """启动监控服务"""
        if self.running:
            return

        self.running = True
        print("\n" + "=" * 70)
        print("[OK] NAS Device Monitor Service Started (Async Mode)")
        print("=" * 70)
        print(f"Max concurrent checks: {self.max_workers}")

        # 立即执行一次全量检测
        print("\nExecuting initial check for all devices...")
        self.check_all_devices()

        # 获取设备列表
        db = SessionLocal()
        try:
            devices = db.query(NasDevice).all()
            print(f"\n[OK] Loaded {len(devices)} device(s) for monitoring")
        finally:
            db.close()

        # 启动定时检测线程
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()

        print("\nMonitoring will run continuously...")
        print("=" * 70)

    def _check_loop(self):
        """定时检测循环"""
        db = SessionLocal()
        try:
            # 获取所有设备的间隔（转换为秒）
            devices = db.query(NasDevice).all()
            device_intervals = {d.id: max(1, d.check_interval or 1) * 60 for d in devices}

            # 记录每个设备上次检测时间
            last_check = {d.id: time.time() for d in devices}

            while self.running:
                current_time = time.time()

                # 检查哪些设备需要检测
                devices_to_check = []
                for device_id, interval_seconds in device_intervals.items():
                    if current_time - last_check[device_id] >= interval_seconds:
                        devices_to_check.append(device_id)

                # 如果有设备需要检测
                if devices_to_check:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking {len(devices_to_check)} device(s)...")

                    # 获取设备信息
                    devices_to_check_info = []
                    for device_id in devices_to_check:
                        device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
                        if device:
                            devices_to_check_info.append((device.id, device.name, device.ip_address))
                            last_check[device_id] = current_time

                    # 并发检测
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = {executor.submit(self.check_device, device): device for device in devices_to_check_info}
                        for future in as_completed(futures):
                            pass

                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Check completed.")

                # 检查是否有新设备或设备间隔改变
                all_devices = db.query(NasDevice).all()
                for device in all_devices:
                    interval_seconds = max(1, device.check_interval or 1) * 60
                    if device.id not in device_intervals:
                        # 新设备
                        device_intervals[device.id] = interval_seconds
                        last_check[device.id] = current_time
                        print(f"  [+ New device detected] {device.name}")
                    elif device_intervals[device.id] != interval_seconds:
                        # 间隔改变
                        device_intervals[device.id] = interval_seconds
                        print(f"  [~ Interval changed] {device.name}: {interval_seconds // 60} min")

                # 每分钟刷新设备列表
                time.sleep(60)

        finally:
            db.close()

    def stop(self):
        """停止监控服务"""
        self.running = False
        if hasattr(self, 'check_thread'):
            self.check_thread.join(timeout=5)
        print("[OK] NAS Monitor Service Stopped")


monitor_instance = None


def start_monitor():
    """启动监控服务"""
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = NasMonitor()
        monitor_instance.start()


def stop_monitor():
    """停止监控服务"""
    global monitor_instance
    if monitor_instance:
        monitor_instance.stop()
        monitor_instance = None


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("NAS Device Monitor Service (Async Mode)")
    print("=" * 70)
    print("\nThis service will automatically monitor all NAS devices concurrently.")
    print("Each device will be checked according to its own interval.")
    print("\nPress Ctrl+C to stop...\n")

    monitor = NasMonitor()
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[STOP] Shutting down monitor...")
        monitor.stop()
