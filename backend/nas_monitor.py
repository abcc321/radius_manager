"""
NAS设备定时检测服务
每个设备按自己的间隔进行检测
"""
import subprocess
import time
import threading
from datetime import datetime
from common.database import SessionLocal
from common.models import NasDevice, NasStatus


class DeviceMonitor:
    """单个设备监控器"""

    def __init__(self, device_id, device_name, ip_address, check_interval_minutes):
        self.device_id = device_id
        self.device_name = device_name
        self.ip_address = ip_address
        self.check_interval_seconds = check_interval_minutes * 60
        self.running = False
        self.monitor_thread = None

    def ping_host(self, timeout=3):
        """Ping主机检测是否在线"""
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', str(timeout * 1000), self.ip_address],
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

    def check_device(self):
        """检测设备"""
        print(f"  [{self.device_name}] Checking...", end=" ")

        is_online, response_time, error = self.ping_host()

        db = SessionLocal()
        try:
            status_record = NasStatus(
                nas_device_id=self.device_id,
                status="online" if is_online else "offline",
                response_time=response_time,
                error_message=error
            )
            db.add(status_record)
            db.commit()

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

        finally:
            db.close()

    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.check_device()
            except Exception as e:
                print(f"  [{self.device_name}] Error: {e}")

            time.sleep(self.check_interval_seconds)

    def start(self):
        """启动监控"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


class NasMonitor:
    """NAS设备监控管理器"""

    def __init__(self):
        self.device_monitors = {}
        self.running = False

    def load_devices(self):
        """加载所有设备并启动监控"""
        db = SessionLocal()
        try:
            devices = db.query(NasDevice).all()

            for device in devices:
                if device.id not in self.device_monitors:
                    interval = device.check_interval or 1
                    interval = max(1, interval)

                    monitor = DeviceMonitor(
                        device_id=device.id,
                        device_name=device.name,
                        ip_address=device.ip_address,
                        check_interval_minutes=interval
                    )
                    self.device_monitors[device.id] = monitor
                    monitor.start()
                    print(f"  Started monitoring: {device.name} (every {interval} min)")

        finally:
            db.close()

    def check_new_devices(self):
        """检查新设备并启动监控"""
        db = SessionLocal()
        try:
            devices = db.query(NasDevice).all()

            existing_ids = set(self.device_monitors.keys())
            current_ids = set(device.id for device in devices)

            new_ids = current_ids - existing_ids
            for device_id in new_ids:
                device = next((d for d in devices if d.id == device_id), None)
                if device:
                    interval = device.check_interval or 1
                    interval = max(1, interval)

                    monitor = DeviceMonitor(
                        device_id=device.id,
                        device_name=device.name,
                        ip_address=device.ip_address,
                        check_interval_minutes=interval
                    )
                    self.device_monitors[device.id] = monitor
                    monitor.start()
                    print(f"  [+ New] Started monitoring: {device.name} (every {interval} min)")

        finally:
            db.close()

    def start(self):
        """启动监控服务"""
        if self.running:
            return

        self.running = True
        print("\n" + "=" * 70)
        print("[OK] NAS Device Monitor Service Started")
        print("=" * 70)
        print("\nLoading devices and starting monitors...")

        self.load_devices()

        if len(self.device_monitors) == 0:
            print("  No devices found.")
        else:
            print(f"\n[OK] Started monitoring {len(self.device_monitors)} device(s)")

        print("\nMonitoring will run continuously...")
        print("=" * 70)

    def stop(self):
        """停止监控服务"""
        self.running = False

        for monitor in self.device_monitors.values():
            monitor.stop()

        self.device_monitors.clear()
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
    print("NAS Device Monitor Service")
    print("=" * 70)
    print("\nThis service will automatically monitor all NAS devices.")
    print("Each device will be checked according to its own interval.")
    print("\nPress Ctrl+C to stop...\n")

    monitor = NasMonitor()
    monitor.start()

    try:
        while True:
            time.sleep(10)
            monitor.check_new_devices()
    except KeyboardInterrupt:
        print("\n\n[STOP] Shutting down monitor...")
        monitor.stop()
