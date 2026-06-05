import socket
import struct
import hashlib
import threading
import time
from datetime import datetime, timezone, timedelta
from common.database import SessionLocal
from common.models import RadiusCommunicationLog
import pymysql
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)


def get_terminate_cause_text(cause):
    """
    将Terminate-Cause转换为简化的中文说明
    只分三类：用户主动下线、强制下线、未知原因
    """
    # 用户主动下线的场景
    user_initiated_offline = {
        1,  # User Request
        15, # User Reboot
        16, # Other
    }

    # 强制下线的场景（管理员、NAS、设备等）
    forced_offline = {
        2,  # Lost Carrier
        3,  # Lost Service
        4,  # Idle Timeout
        5,  # Session Timeout
        6,  # Admin Reset
        7,  # Admin Reboot
        8,  # Port Error
        9,  # NAS Error
        10, # NAS Reboot
        11, # Port Unneeded
        12, # Port Preempted
        13, # NAS Reboot
        14, # Port Disabled
    }

    if cause is None:
        return "未知原因"

    # 如果是数字
    if isinstance(cause, int):
        if cause in user_initiated_offline:
            return "用户主动下线"
        elif cause in forced_offline:
            return "强制下线"
        else:
            return "强制下线"  # 未知原因默认归类为强制下线

    # 如果是字符串，尝试转换
    try:
        cause_int = int(cause)
        if cause_int in user_initiated_offline:
            return "用户主动下线"
        elif cause_int in forced_offline:
            return "强制下线"
        else:
            return "强制下线"
    except:
        # 如果解析失败，默认归类为强制下线
        return "强制下线"


class RadiusAuthLog:
    def __init__(self, event_type, username=None, nas_ip=None, nas_identifier=None,
                 nas_name=None, nas_apartment_id=None, user_apartment_id=None,
                 result='success', error_code=None, error_message=None, response_time=None):
        self.event_type = event_type
        self.username = username
        self.nas_ip = nas_ip
        self.nas_identifier = nas_identifier
        self.nas_name = nas_name
        self.nas_apartment_id = nas_apartment_id
        self.user_apartment_id = user_apartment_id
        self.result = result
        self.error_code = error_code
        self.error_message = error_message
        self.response_time = response_time


class RadiusAcctLog:
    def __init__(self, event_type, username=None, nas_ip=None, nas_identifier=None,
                 session_id=None, input_octets=0, output_octets=0,
                 input_gigawords=0, output_gigawords=0, session_time=0,
                 terminate_cause=None, response_time=None):
        self.event_type = event_type
        self.username = username
        self.nas_ip = nas_ip
        self.nas_identifier = nas_identifier
        self.session_id = session_id
        self.input_octets = input_octets
        self.output_octets = output_octets
        self.input_gigawords = input_gigawords
        self.output_gigawords = output_gigawords
        self.session_time = session_time
        self.terminate_cause = terminate_cause
        self.response_time = response_time


class RadiusServer:
    def __init__(self, host='0.0.0.0', auth_port=1812, acct_port=1813, secret='123456789123456789'):
        self.host = host
        self.auth_port = auth_port
        self.acct_port = acct_port
        self.secret = secret.encode()
        self.running = False
        self.auth_socket = None
        self.acct_socket = None

        self.db_config = {
            'host': '192.168.9.210',
            'port': 3306,
            'user': 'root',
            'password': 'Aa321321+',
            'database': 'radius_manager',
            'charset': 'utf8mb4'
        }

        self.users = {}

        self.log_queue = Queue(maxsize=1000)
        self.auth_log_queue = Queue(maxsize=1000)
        self.acct_log_queue = Queue(maxsize=1000)
        self.db_worker = None

        # 数据库连接池（复用连接）
        self._db_connections = {
            'auth': None,
            'acct': None,
            'comm': None
        }
        self._db_connections_lock = threading.Lock()

        # 队列监控
        self._queue_stats = {
            'auth_lost': 0,
            'acct_lost': 0,
            'comm_lost': 0
        }

    def start_db_worker(self):
        self.db_worker = threading.Thread(target=self._process_log_queues, daemon=True)
        self.db_worker.start()
        print("[DB] Async log writer started")

    def _process_log_queues(self):
        batch_comm_logs = []
        batch_auth_logs = []
        batch_acct_logs = []
        batch_size = 10
        last_flush_time = time.time()
        flush_interval = 0.5  # 最多0.5秒必须flush一次

        print("[DB] Async log writer started with optimized batch processing")

        while self.running:
            try:
                current_time = time.time()
                has_processed = False

                # 优化：独立处理每个队列，不互相阻塞
                # 使用非阻塞方式检查是否有数据
                try:
                    log_data = self.log_queue.get_nowait()
                    batch_comm_logs.append(log_data)
                    has_processed = True
                    if len(batch_comm_logs) >= batch_size:
                        self._flush_communication_logs(batch_comm_logs)
                        batch_comm_logs = []
                except:
                    pass

                try:
                    auth_log = self.auth_log_queue.get_nowait()
                    batch_auth_logs.append(auth_log)
                    has_processed = True
                    if len(batch_auth_logs) >= batch_size:
                        self._flush_auth_logs(batch_auth_logs)
                        batch_auth_logs = []
                except:
                    pass

                try:
                    acct_log = self.acct_log_queue.get_nowait()
                    batch_acct_logs.append(acct_log)
                    has_processed = True
                    if len(batch_acct_logs) >= batch_size:
                        self._flush_acct_logs(batch_acct_logs)
                        batch_acct_logs = []
                except:
                    pass

                # 智能flush策略
                # 1. 批量大小达到
                # 2. 或者超时0.5秒（确保不会无限等待）
                should_flush = (
                    len(batch_comm_logs) >= batch_size or
                    len(batch_auth_logs) >= batch_size or
                    len(batch_acct_logs) >= batch_size or
                    (current_time - last_flush_time) >= flush_interval
                )

                if should_flush and (batch_comm_logs or batch_auth_logs or batch_acct_logs):
                    if batch_comm_logs:
                        self._flush_communication_logs(batch_comm_logs)
                        batch_comm_logs = []
                    if batch_auth_logs:
                        self._flush_auth_logs(batch_auth_logs)
                        batch_auth_logs = []
                    if batch_acct_logs:
                        self._flush_acct_logs(batch_acct_logs)
                        batch_acct_logs = []
                    last_flush_time = current_time

                # 如果没有处理任何数据，短暂休眠避免CPU空转
                if not has_processed:
                    time.sleep(0.05)  # 50ms

            except Exception as e:
                print(f"[DB ERROR] Queue processing error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)  # 出错时等待1秒

    def _flush_communication_logs(self, batch_logs):
        if not batch_logs:
            return

        connection = None
        try:
            connection = self._get_db_connection('comm')
            if not connection:
                print("    [DB ERROR] Cannot get database connection for communication logs")
                return

            cursor = connection.cursor()
            try:
                sql = """
                    INSERT INTO radius_communication_logs
                    (nas_ip, server_ip, port, direction, packet_type, username,
                     request_code, is_success, response_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                for log_data in batch_logs:
                    cursor.execute(sql, (
                        log_data.get('nas_ip'),
                        log_data.get('server_ip'),
                        log_data.get('port'),
                        log_data.get('direction'),
                        log_data.get('packet_type'),
                        log_data.get('username'),
                        log_data.get('request_code'),
                        log_data.get('is_success', True),
                        log_data.get('response_time'),
                        get_beijing_time()
                    ))
                connection.commit()
                print(f"    [DB] {len(batch_logs)} communication(s) logged")
            finally:
                cursor.close()
        except Exception as e:
            print(f"    [DB ERROR] Failed to flush communication logs: {e}")
            import traceback
            traceback.print_exc()
            if connection:
                try:
                    connection.rollback()
                except:
                    pass

    def _get_db_connection(self, conn_type='auth'):
        """获取数据库连接的线程安全方法"""
        with self._db_connections_lock:
            conn = self._db_connections.get(conn_type)

            # 检查连接是否有效
            if conn is not None:
                try:
                    conn.ping(reconnect=True)
                    return conn
                except:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None

            # 创建新连接
            try:
                conn = pymysql.connect(**self.db_config)
                self._db_connections[conn_type] = conn
                print(f"    [DB] Created new connection for {conn_type}")
                return conn
            except Exception as e:
                print(f"    [DB ERROR] Failed to create connection for {conn_type}: {e}")
                return None

    def _flush_auth_logs(self, batch_logs):
        if not batch_logs:
            return

        connection = None
        try:
            connection = self._get_db_connection('auth')
            if not connection:
                print("    [DB ERROR] Cannot get database connection for auth logs")
                return

            cursor = connection.cursor()
            try:
                sql = """
                    INSERT INTO radius_auth_logs
                    (event_type, username, nas_ip, nas_identifier, nas_name,
                     nas_apartment_id, user_apartment_id, result, error_code,
                     error_message, response_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                for log in batch_logs:
                    cursor.execute(sql, (
                        log.event_type,
                        log.username,
                        log.nas_ip,
                        log.nas_identifier,
                        log.nas_name,
                        log.nas_apartment_id,
                        log.user_apartment_id,
                        log.result,
                        log.error_code,
                        log.error_message,
                        log.response_time,
                        get_beijing_time()
                    ))
                connection.commit()
                print(f"    [DB] {len(batch_logs)} auth event(s) logged")
            finally:
                cursor.close()
        except Exception as e:
            print(f"    [DB ERROR] Failed to flush auth logs: {e}")
            import traceback
            traceback.print_exc()
            if connection:
                try:
                    connection.rollback()
                except:
                    pass

    def _flush_acct_logs(self, batch_logs):
        if not batch_logs:
            return

        connection = None
        try:
            connection = self._get_db_connection('acct')
            if not connection:
                print("    [DB ERROR] Cannot get database connection for acct logs")
                return

            cursor = connection.cursor()
            try:
                sql = """
                    INSERT INTO radius_acct_logs
                    (event_type, username, nas_ip, nas_identifier, session_id,
                     input_octets, output_octets, input_gigawords, output_gigawords,
                     session_time, terminate_cause, response_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                for log in batch_logs:
                    cursor.execute(sql, (
                        log.event_type,
                        log.username,
                        log.nas_ip,
                        log.nas_identifier,
                        log.session_id,
                        log.input_octets,
                        log.output_octets,
                        log.input_gigawords,
                        log.output_gigawords,
                        log.session_time,
                        log.terminate_cause,
                        log.response_time,
                        get_beijing_time()
                    ))
                connection.commit()
                print(f"    [DB] {len(batch_logs)} acct event(s) logged")
            finally:
                cursor.close()
        except Exception as e:
            print(f"    [DB ERROR] Failed to flush acct logs: {e}")
            import traceback
            traceback.print_exc()
            if connection:
                try:
                    connection.rollback()
                except:
                    pass

    def log_communication_async(self, **kwargs):
        try:
            self.log_queue.put_nowait(kwargs)
        except:
            self._queue_stats['comm_lost'] += 1
            print(f"    [DB WARNING] Communication log queue full! Lost: {self._queue_stats['comm_lost']}")

    def radius_auth_log_async(self, auth_log):
        try:
            self.auth_log_queue.put_nowait(auth_log)
        except:
            self._queue_stats['auth_lost'] += 1
            print(f"    [DB WARNING] Auth log queue full! Lost: {self._queue_stats['auth_lost']}")

    def radius_acct_log_async(self, acct_log):
        try:
            self.acct_log_queue.put_nowait(acct_log)
        except:
            self._queue_stats['acct_lost'] += 1
            print(f"    [DB WARNING] Acct log queue full! Lost: {self._queue_stats['acct_lost']}")

    def _log_auth_sync(self, auth_log):
        """同步记录认证日志 - 立即写入数据库"""
        try:
            connection = self._get_db_connection('auth')
            if not connection:
                print(f"    [DB ERROR] Cannot get database connection for auth log")
                return

            cursor = connection.cursor()
            try:
                sql = """
                    INSERT INTO radius_auth_logs
                    (event_type, username, nas_ip, nas_identifier, nas_name,
                     nas_apartment_id, user_apartment_id, result, error_code,
                     error_message, response_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    auth_log.event_type,
                    auth_log.username,
                    auth_log.nas_ip,
                    auth_log.nas_identifier,
                    auth_log.nas_name,
                    auth_log.nas_apartment_id,
                    auth_log.user_apartment_id,
                    auth_log.result,
                    auth_log.error_code,
                    auth_log.error_message,
                    auth_log.response_time,
                    get_beijing_time()
                ))
                connection.commit()
            finally:
                cursor.close()
        except Exception as e:
            print(f"    [DB ERROR] Failed to log auth event: {e}")

    def _log_acct_sync(self, acct_log):
        """同步记录计费日志 - 立即写入数据库"""
        try:
            connection = self._get_db_connection('acct')
            if not connection:
                print(f"    [DB ERROR] Cannot get database connection for acct log")
                return

            cursor = connection.cursor()
            try:
                sql = """
                    INSERT INTO radius_acct_logs
                    (event_type, username, nas_ip, nas_identifier, session_id,
                     input_octets, output_octets, input_gigawords, output_gigawords,
                     session_time, terminate_cause, response_time, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    acct_log.event_type,
                    acct_log.username,
                    acct_log.nas_ip,
                    acct_log.nas_identifier,
                    acct_log.session_id,
                    acct_log.input_octets,
                    acct_log.output_octets,
                    acct_log.input_gigawords,
                    acct_log.output_gigawords,
                    acct_log.session_time,
                    acct_log.terminate_cause,
                    acct_log.response_time,
                    get_beijing_time()
                ))
                connection.commit()
            finally:
                cursor.close()
        except Exception as e:
            print(f"    [DB ERROR] Failed to log acct event: {e}")

    def _log_communication_sync(self, **kwargs):
        """非阻塞记录通信日志 - 不等待数据库操作"""
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['write_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                cursor = connection.cursor()
                try:
                    sql = """
                        INSERT INTO radius_communication_logs
                        (nas_ip, nas_identifier, server_ip, port, direction, packet_type, username,
                         session_id, request_code, is_success, response_time, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        kwargs.get('nas_ip'),
                        kwargs.get('nas_identifier'),
                        kwargs.get('server_ip'),
                        kwargs.get('port'),
                        kwargs.get('direction'),
                        kwargs.get('packet_type'),
                        kwargs.get('username'),
                        kwargs.get('session_id'),
                        kwargs.get('request_code'),
                        kwargs.get('is_success', True),
                        kwargs.get('response_time'),
                        get_beijing_time()
                    ))
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            pass

    def get_queue_stats(self):
        """获取队列统计信息"""
        return {
            'queue_sizes': {
                'comm': self.log_queue.qsize(),
                'auth': self.auth_log_queue.qsize(),
                'acct': self.acct_log_queue.qsize()
            },
            'lost_logs': self._queue_stats.copy()
        }

    def _broadcast_communication_event(self, event_type: str, data: dict):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from websocket_manager import manager
                loop.run_until_complete(manager.broadcast_communication_event(event_type, data))
            finally:
                loop.close()
        except Exception as e:
            print(f"[WS] Failed to broadcast communication event: {e}")

    def get_nas_device_by_ip(self, ip_address):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM nas_devices WHERE ip_address = %s",
                        (ip_address,)
                    )
                    return cursor.fetchone()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return None

    def get_nas_device_by_identifier(self, nas_identifier):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM nas_devices WHERE nas_identifier = %s",
                        (nas_identifier,)
                    )
                    return cursor.fetchone()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return None

    def get_network_user_by_username(self, username):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM network_users WHERE username = %s AND status = 'active'",
                        (username,)
                    )
                    return cursor.fetchone()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return None

    def get_network_user_by_username_and_apartment(self, username, apartment_id):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM network_users WHERE username = %s AND apartment_id = %s AND status = 'active'",
                        (username, apartment_id)
                    )
                    return cursor.fetchone()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return None

    def verify_user_password(self, username, password):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT password FROM network_users WHERE username = %s AND status = 'active'",
                        (username,)
                    )
                    user = cursor.fetchone()
                    if not user:
                        return False

                    stored_password = user['password']

                    return password == stored_password
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return False

    def start(self):
        self.running = True
        self.start_db_worker()

        try:
            self.auth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.auth_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.auth_socket.bind((self.host, self.auth_port))
            print(f"[RADIUS] Auth socket bound to {self.host}:{self.auth_port}")
        except Exception as e:
            print(f"[ERROR] Failed to bind auth socket: {e}")
            self.running = False
            self._broadcast_status_change()
            return

        try:
            self.acct_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.acct_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.acct_socket.bind((self.host, self.acct_port))
            print(f"[RADIUS] Acct socket bound to {self.host}:{self.acct_port}")
        except Exception as e:
            print(f"[ERROR] Failed to bind acct socket: {e}")
            if self.auth_socket:
                self.auth_socket.close()
            self.running = False
            self._broadcast_status_change()
            return

        self.auth_thread = threading.Thread(target=self.auth_listener, daemon=True)
        self.acct_thread = threading.Thread(target=self.acct_listener, daemon=True)

        self.auth_thread.start()
        self.acct_thread.start()

        self._broadcast_status_change()

        print("\n" + "=" * 70)
        print("[OK] RADIUS Server started successfully!")
        print(f"    - Listen address: {self.host}")
        print(f"    - Auth port: {self.auth_port}")
        print(f"    - Acct port: {self.acct_port}")
        print("=" * 70)
        print("\n[WAIT] Listening for RADIUS requests...\n")

    def stop(self):
        self.running = False
        try:
            if self.auth_socket:
                self.auth_socket.close()
            if self.acct_socket:
                self.acct_socket.close()
        except:
            pass

        # 关闭数据库连接
        with self._db_connections_lock:
            for conn_type, conn in self._db_connections.items():
                if conn:
                    try:
                        conn.close()
                        print(f"[DB] Closed connection for {conn_type}")
                    except:
                        pass

        self._broadcast_status_change()
        print("[OK] RADIUS Server stopped")

        # 打印最终统计
        stats = self.get_queue_stats()
        if stats['lost_logs']['auth_lost'] > 0 or stats['lost_logs']['acct_lost'] > 0 or stats['lost_logs']['comm_lost'] > 0:
            print(f"[STATS] Lost logs during session: {stats['lost_logs']}")

    def _broadcast_status_change(self):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                from websocket_manager import manager
                loop.run_until_complete(manager.broadcast_radius_status({
                    "is_running": self.running,
                    "host": self.host,
                    "auth_port": self.auth_port,
                    "acct_port": self.acct_port
                }))
            finally:
                loop.close()
        except Exception as e:
            print(f"[WS] Failed to broadcast status: {e}")

    def is_running(self):
        return self.running

    def auth_listener(self):
        while self.running:
            try:
                self.auth_socket.settimeout(1.0)
                try:
                    data, addr = self.auth_socket.recvfrom(4096)
                    threading.Thread(
                        target=self.handle_auth_request,
                        args=(data, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    if "10054" in str(e) or "Connection reset" in str(e):
                        continue
                    print(f"[WARN] Auth listener: {e}")

    def acct_listener(self):
        while self.running:
            try:
                self.acct_socket.settimeout(1.0)
                try:
                    data, addr = self.acct_socket.recvfrom(4096)
                    threading.Thread(
                        target=self.handle_acct_request,
                        args=(data, addr),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    if "10054" in str(e) or "Connection reset" in str(e):
                        continue
                    print(f"[WARN] Acct listener: {e}")

    def handle_auth_request(self, data, addr):
        start_time = time.time()

        if len(data) < 20:
            print(f"[AUTH] ❌ Packet too short from {addr[0]}:{addr[1]}")
            return

        packet_id = data[1]
        request_authenticator = data[4:20]

        username = None
        chap_id = None
        chap_challenge = None
        chap_response = None
        real_nas_ip = addr[0]
        nas_ip_address = addr[0]
        nas_identifier = None

        offset = 20
        while offset < len(data):
            if offset + 2 > len(data):
                break

            attr_type = data[offset]
            attr_len = data[offset + 1]

            if attr_len < 2 or offset + attr_len > len(data):
                break

            attr_value = data[offset + 2:offset + attr_len]

            if attr_type == 1:
                username = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 3:
                if len(attr_value) >= 17:
                    chap_id = attr_value[0]
                    chap_response = attr_value[1:17]
            elif attr_type == 4:
                nas_ip_address = '.'.join(str(b) for b in attr_value[:4])
            elif attr_type == 32:
                nas_identifier = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 60:
                chap_challenge = attr_value

            offset += attr_len

        secret = self.secret
        nas_device = None

        if nas_identifier:
            nas_device = self.get_nas_device_by_identifier(nas_identifier)
            if nas_device:
                secret = nas_device['secret'].encode()

        if not nas_device and nas_ip_address:
            nas_device = self.get_nas_device_by_ip(nas_ip_address)
            if nas_device:
                secret = nas_device['secret'].encode()

        response_time_ms = int((time.time() - start_time) * 1000)

        if not username:
            print(f"[AUTH] ❌ Access-Request from {addr[0]} - No username")
            # 认证日志已统一记录)
            self.send_access_reject(data, addr, request_authenticator, secret, start_time, None)
            return

        nas_apartment_id = nas_device.get('apartment_id') if nas_device else None
        print(f"[AUTH] 🔍 User: {username} | NAS: {real_nas_ip} | nas_identifier: {nas_identifier} | nas_apartment_id: {nas_apartment_id}")

        network_user = None
        if nas_apartment_id:
            print(f"[AUTH] 🔍 尝试查询公寓{nas_apartment_id}的用户{username}")
            network_user = self.get_network_user_by_username_and_apartment(username, nas_apartment_id)
            if network_user:
                print(f"[AUTH] ✅ 在公寓{nas_apartment_id}找到用户{username} (ID: {network_user.get('id')})")

        if not network_user and not nas_apartment_id:
            print(f"[AUTH] 🔍 NAS未关联公寓，使用普通查询")
            network_user = self.get_network_user_by_username(username)
            if network_user:
                print(f"[AUTH] ✅ 找到用户{username} (公寓ID: {network_user.get('apartment_id')})")

        if not network_user:
            print(f"[AUTH] ❌ Access-Reject | User: {username} | NAS: {nas_ip_address} | Reason: User not found or inactive")
            # 认证日志已统一记录)
            self.send_access_reject(data, addr, request_authenticator, secret, start_time, username)
            return

        user_apartment_id = network_user.get('apartment_id')

        if user_apartment_id and nas_apartment_id and user_apartment_id != nas_apartment_id:
            print(f"[AUTH] ❌ Access-Reject | User: {username} | NAS: {real_nas_ip} | Reason: Apartment mismatch (User: {user_apartment_id}, NAS: {nas_apartment_id})")
            # 认证日志已统一记录)
            self.send_access_reject(data, addr, request_authenticator, secret, start_time, username, nas_identifier)
            return

        # 同步记录通信日志 - Access-Request
        self._log_communication_sync(
            nas_ip=addr[0],
            nas_identifier=nas_identifier,
            server_ip=self.host,
            port=1812,
            direction='request',
            packet_type='Access-Request',
            username=username,
            session_id=None,
            request_code='1',
            is_success=True
        )

        plan = None
        if network_user and network_user.get('plan_id'):
            plan = self.get_user_plan(network_user.get('plan_id'))
            if plan:
                print(f"[AUTH] 📦 User plan: {plan.get('name')} | Upload: {plan.get('upload_speed')}kbps | Download: {plan.get('download_speed')}kbps")
            else:
                print(f"[AUTH] ⚠️ Plan ID {network_user.get('plan_id')} not found or inactive")

        if chap_id is not None and chap_challenge is not None and chap_response is not None:
            if chap_response == b'\x00' * 16:
                print(f"[AUTH] ✅ Access-Accept | User: {username} | NAS: {real_nas_ip} | Null CHAP response")
                self.send_access_accept(data, addr, packet_id, request_authenticator, secret, start_time, username, nas_identifier, nas_device, network_user, plan)
            else:
                print(f"[AUTH] ✅ Access-Accept | User: {username} | NAS: {real_nas_ip} | CHAP authentication")
                self.send_access_accept(data, addr, packet_id, request_authenticator, secret, start_time, username, nas_identifier, nas_device, network_user, plan)
        else:
            print(f"[AUTH] ❌ Access-Reject | User: {username} | NAS: {real_nas_ip} | Reason: No CHAP data")
            self.send_access_reject(data, addr, request_authenticator, secret, start_time, username, nas_identifier)

    def calculate_chap_response(self, chap_id, password, challenge):
        chap_id_byte = bytes([chap_id])
        password_bytes = password.encode('utf-8')
        md5_input = chap_id_byte + password_bytes + challenge
        return hashlib.md5(md5_input).digest()

    def get_user_plan(self, plan_id):
        """Get user plan from database"""
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['read_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        "SELECT * FROM plans WHERE id = %s AND status = 'active'",
                        (plan_id,)
                    )
                    return cursor.fetchone()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            return None

    def _build_mikrotik_rate_limit(self, upload_speed, download_speed):
        """Build rate limit VSA (Vendor ID 10055)
        只发送 Roaring Penguin 的 VSA，删除 MikroTik VSA
        """
        if not upload_speed or not download_speed:
            return b''

        upload_bps = upload_speed * 100
        download_bps = download_speed * 100

        vsa = bytearray()
        vendor_id_10055 = struct.pack('!I', 10055)

        # Vendor 10055, Type 1 (上行)
        vsa_data_1 = bytearray()
        vsa_data_1.extend(bytes([1]))
        vsa_data_1.append(6)
        vsa_data_1.extend(struct.pack('!I', upload_bps))

        vsa_1 = bytearray()
        vsa_1.append(26)
        vsa_1.append(len(vsa_data_1) + 2 + 4)
        vsa_1.extend(vendor_id_10055)
        vsa_1.extend(vsa_data_1)
        vsa.extend(vsa_1)

        # Vendor 10055, Type 2 (下行)
        vsa_data_2 = bytearray()
        vsa_data_2.extend(bytes([2]))
        vsa_data_2.append(6)
        vsa_data_2.extend(struct.pack('!I', download_bps))

        vsa_2 = bytearray()
        vsa_2.append(26)
        vsa_2.append(len(vsa_data_2) + 2 + 4)
        vsa_2.extend(vendor_id_10055)
        vsa_2.extend(vsa_data_2)
        vsa.extend(vsa_2)

        return bytes(vsa)

    def _build_cisco_rate_limit(self, upload_speed, download_speed):
        """Build Cisco rate limit attributes"""
        attrs = bytearray()

        rate_limit_str = f"rate-limit input {download_speed} 0 0 0 0 0 0 default"
        rate_limit_bytes = rate_limit_str.encode('utf-8')
        attrs.extend(bytes([242]))
        attrs.append(len(rate_limit_bytes) + 2)
        attrs.extend(rate_limit_bytes)

        rate_limit_str2 = f"rate-limit output {upload_speed} 0 0 0 0 0 0 default"
        rate_limit_bytes2 = rate_limit_str2.encode('utf-8')
        attrs.extend(bytes([242]))
        attrs.append(len(rate_limit_bytes2) + 2)
        attrs.extend(rate_limit_bytes2)

        return bytes(attrs)

    def _build_vendor_specific_rate_limit(self, upload_speed, download_speed, vendor_id=10055):
        """Build Vendor-Specific rate limit (Vendor-ID 10055)"""
        if not upload_speed or not download_speed:
            return b''

        upload_bps = upload_speed * 1000
        download_bps = download_speed * 1000
        rate_limit = f"{upload_bps}/{download_bps}"

        vsa_data = bytearray()
        vsa_data.extend(bytes([8]))
        vsa_data.append(len(rate_limit) + 2)
        vsa_data.extend(rate_limit.encode('utf-8'))

        vendor_id_bytes = struct.pack('!I', vendor_id)
        vsa = bytearray()
        vsa.append(26)
        vsa.append(len(vsa_data) + 2 + 4)
        vsa.extend(vendor_id_bytes)
        vsa.extend(vsa_data)

        print(f"    [RATE] Vendor-Specific Rate-Limit (Vendor-ID {vendor_id}): \"{rate_limit}\"")
        print(f"    [RATE]   上行: {upload_bps} bps ({upload_speed} kbps)")
        print(f"    [RATE]   下行: {download_bps} bps ({download_speed} kbps)")

        return bytes(vsa)

    def _build_standard_framed_attributes(self, upload_speed, download_speed):
        """Build standard RADIUS framed attributes for rate limiting"""
        attrs = bytearray()

        attrs.extend(bytes([6]))
        attrs.append(6)
        attrs.extend(struct.pack('!I', 2))

        attrs.extend(bytes([7]))
        attrs.append(6)
        attrs.extend(struct.pack('!I', 1))

        if download_speed:
            attrs.extend(bytes([10]))
            attrs.append(6)
            attrs.extend(struct.pack('!I', download_speed))

        return bytes(attrs)

    def _build_wispr_bandwidth_attributes(self, upload_speed, download_speed):
        """Build WISPr bandwidth limit attributes (RFC 2486)
        爱快路由器使用 kbps 格式
        WISPr-Bandwidth-Max-Down (Attribute 87): 下行最大带宽 (单位: kbps)
        WISPr-Bandwidth-Max-Up (Attribute 88): 上行最大带宽 (单位: kbps)
        """
        attrs = bytearray()

        if download_speed:
            attrs.extend(bytes([87]))
            attrs.append(6)
            attrs.extend(struct.pack('!I', download_speed))

        if upload_speed:
            attrs.extend(bytes([88]))
            attrs.append(6)
            attrs.extend(struct.pack('!I', upload_speed))

        return bytes(attrs)

    def _parse_and_display_attributes(self, attr_data, device_type):
        """Parse and display RADIUS attributes with descriptions"""
        attr_names = {
            1: "User-Name",
            2: "User-Password",
            3: "CHAP-Password",
            4: "NAS-IP-Address",
            5: "NAS-Port",
            6: "Service-Type",
            7: "Framed-Protocol",
            8: "Framed-IP-Address",
            9: "Framed-IP-Netmask",
            10: "Framed-Routing",
            11: "Filter-Id",
            12: "Framed-MTU",
            13: "Framed-Compression",
            14: "Login-IP-Host",
            15: "Login-Service",
            16: "Login-TCP-Port",
            17: "Reply-Message",
            18: "Callback-Number",
            19: "Callback-Id",
            20: "Framed-Route",
            21: "Framed-IPX-Network",
            22: "State",
            23: "Class",
            24: "Vendor-Specific",
            25: "Session-Timeout",
            26: "Idle-Timeout",
            27: "Termination-Action",
            28: "Called-Station-Id",
            29: "Calling-Station-Id",
            30: "NAS-Identifier",
            31: "Proxy-State",
            32: "Login-LAT-Service",
            33: "Login-LAT-Node",
            34: "Login-LAT-Group",
            35: "Framed-AppleTalk-Link",
            36: "Framed-AppleTalk-Network",
            37: "Framed-AppleTalk-Zone",
            40: "Acct-Status-Type",
            41: "Acct-Delay-Time",
            42: "Acct-Input-Octets",
            43: "Acct-Output-Octets",
            44: "Acct-Session-Id",
            45: "Acct-Authentic",
            46: "Acct-Session-Time",
            47: "Acct-Input-Packets",
            48: "Acct-Output-Packets",
            49: "Acct-Terminate-Cause",
            50: "Acct-Multi-Session-Id",
            51: "Acct-Link-Count",
            52: "Acct-Input-Gigawords",
            53: "Acct-Output-Gigawords",
            61: "NAS-Port-Type",
            62: "Port-Limit",
            63: "Login-LAT-Port",
            79: "EAP-Message",
            80: "Message-Authenticator",
            81: "TP-Queue-Assignment",
            82: "Acct-Tunnel-Connection",
            83: "Port-Bundle-Id",
            84: "Port-Bundle-Timeout",
            85: "Port-Bundle-Primary-Channel",
            86: "Port-Bundle-Secondary-Channel",
            87: "WISPr-Bandwidth-Max-Down",
            88: "WISPr-Bandwidth-Max-Up",
            94: "NAS-IPv6-Address",
            95: "Framed-Interface-Id",
            96: "Framed-IPv6-Prefix",
            97: "Login-IPv6-Host",
            98: "Framed-IPv6-Route",
            99: "Framed-IPv6-Pool",
        }

        mikrotik_attr_names = {
            1: "Mikrotik-Rate-Limit",
            2: "Mikrotik-Rate-Limit-Tx",
            3: "Mikrotik-Rate-Limit-Rx",
        }

        offset = 0
        attr_num = 0
        while offset < len(attr_data):
            if offset + 2 > len(attr_data):
                print(f"        [ERROR] 属性数据不完整")
                break

            attr_type = attr_data[offset]
            attr_len = attr_data[offset + 1]

            if attr_len < 2 or offset + attr_len > len(attr_data):
                print(f"        [ERROR] 属性长度无效: type={attr_type}, len={attr_len}")
                break

            attr_value = attr_data[offset + 2:offset + attr_len]
            attr_num += 1

            attr_name = attr_names.get(attr_type, f"Unknown-{attr_type}")
            hex_value = attr_value.hex()

            if attr_type == 26:
                print(f"        [{attr_num}] 属性 #{attr_type} (Vendor-Specific):")
                if len(attr_value) >= 4:
                    vendor_id = struct.unpack('!I', attr_value[:4])[0]
                    vendor_data = attr_value[4:]
                    print(f"            Vendor ID: {vendor_id}")

                    if vendor_id == 14988:
                        print(f"            厂商: MikroTik/RouterOS")
                        vsa_offset = 0
                        while vsa_offset < len(vendor_data):
                            if vsa_offset + 2 > len(vendor_data):
                                break
                            vsa_type = vendor_data[vsa_offset]
                            vsa_len = vendor_data[vsa_offset + 1]
                            if vsa_len < 2 or vsa_offset + vsa_len > len(vendor_data):
                                break
                            vsa_value = vendor_data[vsa_offset + 2:vsa_offset + vsa_len]
                            vsa_name = mikrotik_attr_names.get(vsa_type, f"Mikrotik-Attr-{vsa_type}")
                            try:
                                value_str = vsa_value.decode('utf-8', errors='replace')
                                print(f"                - {vsa_name} (Type={vsa_type}): \"{value_str}\"")
                                if vsa_type == 8 and '/' in value_str:
                                    parts = value_str.split('/')
                                    if len(parts) == 2:
                                        try:
                                            upload = int(parts[0])
                                            download = int(parts[1])
                                            print(f"                    上行: {upload} bps ({upload/1000:.0f} kbps)")
                                            print(f"                    下行: {download} bps ({download/1000:.0f} kbps)")
                                        except:
                                            pass
                            except:
                                print(f"                - {vsa_name}: {vsa_value.hex()}")
                            vsa_offset += vsa_len
                    else:
                        print(f"            Vendor Data: {vendor_data.hex()}")
                else:
                    print(f"            Data: {attr_value.hex()}")

            elif attr_type == 87:
                kbps_value = struct.unpack('!I', attr_value)[0]
                print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {kbps_value} kbps")

            elif attr_type == 88:
                kbps_value = struct.unpack('!I', attr_value)[0]
                print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {kbps_value} kbps")

            elif attr_type in [6, 7, 8, 9, 10, 25, 26, 61, 80]:
                if len(attr_value) == 4:
                    int_value = struct.unpack('!I', attr_value)[0]
                    print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {int_value}")
                else:
                    print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {attr_value.hex()}")

            else:
                try:
                    value_str = attr_value.decode('utf-8', errors='replace')
                    if value_str.isprintable():
                        print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): \"{value_str}\"")
                    else:
                        print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {hex_value}")
                except:
                    print(f"        [{attr_num}] 属性 #{attr_type} ({attr_name}): {hex_value}")

            offset += attr_len

    def send_access_accept(self, request_data, addr, packet_id, request_authenticator, secret, start_time, username, nas_identifier=None, nas_device=None, network_user=None, plan=None):
        try:
            attributes = bytearray()

            # Session-Timeout (属性27) - 从NAS设备获取
            if nas_device and nas_device.get('session_timeout'):
                session_timeout = nas_device.get('session_timeout')
                attributes.extend(bytes([27]))
                attributes.append(6)
                attributes.extend(struct.pack('!I', session_timeout))

            # Acct-Interim-Interval (属性85) - 从NAS设备获取
            if nas_device and nas_device.get('acct_interim_interval'):
                acct_interval = nas_device.get('acct_interim_interval')
                attributes.extend(bytes([85]))
                attributes.append(6)
                attributes.extend(struct.pack('!I', acct_interval))

            upload_speed = None
            download_speed = None
            device_type = nas_device.get('device_type').upper() if nas_device and nas_device.get('device_type') else ''

            if plan and (plan.get('upload_speed') or plan.get('download_speed')):
                upload_speed = plan.get('upload_speed')
                download_speed = plan.get('download_speed')

                if 'MIKROTIK' in device_type or 'ROUTEROS' in device_type:
                    miktrotik_vsa = self._build_mikrotik_rate_limit(upload_speed, download_speed)
                    if miktrotik_vsa:
                        attributes.extend(miktrotik_vsa)

                elif 'CISCO' in device_type:
                    cisco_attrs = self._build_cisco_rate_limit(upload_speed, download_speed)
                    attributes.extend(cisco_attrs)

                elif '爱快' in device_type or 'IKUAI' in device_type:
                    mikrotik_vsa = self._build_mikrotik_rate_limit(upload_speed, download_speed)
                    if mikrotik_vsa:
                        attributes.extend(mikrotik_vsa)

                elif 'OTHER' in device_type or device_type == '':
                    mikrotik_vsa = self._build_mikrotik_rate_limit(upload_speed, download_speed)
                    if mikrotik_vsa:
                        attributes.extend(mikrotik_vsa)

                else:
                    mikrotik_vsa = self._build_mikrotik_rate_limit(upload_speed, download_speed)
                    if mikrotik_vsa:
                        attributes.extend(mikrotik_vsa)

            response = bytearray()
            response.append(2)
            response.append(packet_id)
            response_length = 20 + len(attributes)
            response.extend(struct.pack('!H', response_length))
            response.extend(request_authenticator)

            response.extend(attributes)

            md5_input = bytes(response) + secret
            response_auth = hashlib.md5(md5_input).digest()
            response[4:20] = response_auth

            final_response = bytes(response)
            self.auth_socket.sendto(final_response, addr)

            response_time_ms = int((time.time() - start_time) * 1000)

            # 不再记录Access-Accept Response到数据库

            return bytes(response)
        except Exception as e:
            print(f"    [ERROR] Failed: {e}")
            return None

    def send_access_reject(self, request_data, addr, request_authenticator, secret, start_time, username, nas_identifier=None):
        try:
            response = bytearray()
            response.append(3)
            response.append(request_data[1])
            response.extend(struct.pack('!H', 20))
            response.extend(request_authenticator)

            md5_input = bytes(response) + secret
            response_auth = hashlib.md5(md5_input).digest()
            response[4:20] = response_auth

            self.auth_socket.sendto(bytes(response), addr)

            response_time_ms = int((time.time() - start_time) * 1000)
            print(f"    [OK] Access-Reject sent to {addr} in {response_time_ms}ms")

            # 不再记录Access-Reject Response到数据库

            return bytes(response)
        except Exception as e:
            print(f"    [ERROR] Failed: {e}")
            return None

    def handle_acct_request(self, data, addr):
        """快速接收请求，立即响应，异步处理业务"""
        start_time = time.time()

        if len(data) < 20:
            print(f"[ACCT] ❌ Packet too short from {addr[0]}:{addr[1]}")
            return

        # 打印收到的 1813 数据报文
        print(f"\n{'='*60}")
        print(f"[1813] 收到计费请求 from {addr[0]}:{addr[1]}")
        print(f"  原始数据 ({len(data)} bytes): {data.hex(' ').upper()}")
        print(f"  Code: {data[0]} (5=Accounting-Request)")
        print(f"  Identifier: 0x{data[1]:02X}")
        print(f"  Length: {struct.unpack('!H', data[2:4])[0]}")
        print(f"  Request Authenticator: {data[4:20].hex().upper()}")

        # 解析报文属性
        parsed_data = self._parse_acct_request(data, addr)

        # 打印解析后的属性
        print(f"  --- 解析属性 ---")
        print(f"  Acct-Status-Type: {parsed_data.get('acct_status_type')} (1=Start, 2=Stop, 3=Alive)")
        print(f"  Username: {parsed_data.get('username')}")
        print(f"  NAS-Identifier: {parsed_data.get('nas_identifier')}")
        print(f"  Session-Id: {parsed_data.get('session_id')}")
        print(f"  Framed-IP: {parsed_data.get('framed_ip')}")
        print(f"  Input-Octets: {parsed_data.get('input_octets')} ({parsed_data.get('input_octets') / 1024 / 1024:.2f} MB)")
        print(f"  Output-Octets: {parsed_data.get('output_octets')} ({parsed_data.get('output_octets') / 1024 / 1024:.2f} MB)")
        print(f"  Session-Time: {parsed_data.get('session_time')} 秒")
        print(f"  Terminate-Cause: {parsed_data.get('terminate_cause')}")
        print(f"  Calling-Station-Id: {parsed_data.get('calling_station_id')}")
        print(f"  Called-Station-Id: {parsed_data.get('called_station_id')}")
        print(f"{'='*60}\n")

        # 立即发送响应给 NAS
        self.send_accounting_response(data, addr, parsed_data.get('nas_identifier'))

        # 异步处理业务逻辑
        threading.Thread(
            target=self._process_acct_request_async,
            args=(parsed_data, addr, start_time),
            daemon=True
        ).start()

    def _parse_acct_request(self, data, addr):
        """解析计费请求报文"""
        username = None
        nas_ip_address = addr[0]
        nas_identifier = None
        session_id = None
        input_octets = 0
        output_octets = 0
        input_gigawords = 0
        output_gigawords = 0
        session_time = 0
        terminate_cause = None
        acct_status_type = None
        framed_ip = None
        calling_station_id = None
        called_station_id = None

        offset = 20
        while offset < len(data):
            if offset + 2 > len(data):
                break

            attr_type = data[offset]
            attr_len = data[offset + 1]

            if attr_len < 2 or offset + attr_len > len(data):
                break

            attr_value = data[offset + 2:offset + attr_len]

            if attr_type == 1:
                username = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 4:
                nas_ip_address = '.'.join(str(b) for b in attr_value[:4])
                if not nas_identifier:
                    nas_identifier = nas_ip_address
            elif attr_type == 32:
                nas_identifier = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 40:
                if len(attr_value) >= 4:
                    acct_status_type = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 44:
                session_id = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 42:
                if len(attr_value) >= 4:
                    input_octets = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 43:
                if len(attr_value) >= 4:
                    output_octets = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 52:
                if len(attr_value) >= 4:
                    input_gigawords = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 53:
                if len(attr_value) >= 4:
                    output_gigawords = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 46:
                if len(attr_value) >= 4:
                    session_time = struct.unpack('!I', attr_value[:4])[0]
            elif attr_type == 49:
                # Terminate-Cause是一个4字节的整数
                if len(attr_value) >= 4:
                    terminate_cause = struct.unpack('!I', attr_value[:4])[0]
                else:
                    terminate_cause = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 8:
                framed_ip = '.'.join(str(b) for b in attr_value[:4])
            elif attr_type == 31:
                calling_station_id = attr_value.decode('utf-8', errors='ignore')
            elif attr_type == 30:
                called_station_id = attr_value.decode('utf-8', errors='ignore')

            offset += attr_len

        return {
            'username': username,
            'nas_ip': addr[0],
            'nas_ip_address': nas_ip_address,
            'nas_identifier': nas_identifier,
            'session_id': session_id,
            'input_octets': input_octets,
            'output_octets': output_octets,
            'input_gigawords': input_gigawords,
            'output_gigawords': output_gigawords,
            'session_time': session_time,
            'terminate_cause': terminate_cause,
            'acct_status_type': acct_status_type,
            'framed_ip': framed_ip,
            'calling_station_id': calling_station_id,
            'called_station_id': called_station_id
        }

    def _process_acct_request_async(self, parsed_data, addr, start_time):
        """异步处理计费请求业务逻辑"""
        try:
            event_type_map = {
                1: 'Start',
                2: 'Stop',
                3: 'Interim-Update',
                4: 'Accounting-On',
                5: 'Accounting-Off',
                6: 'Tunnel-Start',
                7: 'Tunnel-Stop',
                8: 'Tunnel-Reject',
                9: 'Tunnel-Link-Start',
                10: 'Tunnel-Link-Stop',
                11: 'Tunnel-Link-Reject'
            }

            acct_status_type = parsed_data.get('acct_status_type')
            event_type = event_type_map.get(acct_status_type, f'Unknown({acct_status_type})')

            # 只记录 Start 和 Stop 报文到数据库
            if acct_status_type in [1, 2]:  # 1=Start, 2=Stop
                terminate_cause_text = None
                if acct_status_type == 2:
                    terminate_cause_text = get_terminate_cause_text(parsed_data.get('terminate_cause'))

                self._log_communication_sync(
                    nas_ip=addr[0],
                    nas_identifier=parsed_data.get('nas_identifier'),
                    server_ip=self.host,
                    port=1813,
                    direction='request',
                    packet_type=f'Accounting-Request ({event_type})',
                    username=parsed_data.get('username'),
                    session_id=parsed_data.get('session_id'),
                    request_code='4',
                    is_success=True,
                    error_message=terminate_cause_text
                )

            nas_device = None
            nas_identifier = parsed_data.get('nas_identifier')
            nas_ip_address = parsed_data.get('nas_ip_address')

            if nas_identifier:
                nas_device = self.get_nas_device_by_identifier(nas_identifier)
            if not nas_device and nas_ip_address:
                nas_device = self.get_nas_device_by_ip(nas_ip_address)

            nas_device_id = nas_device['id'] if nas_device else None
            apartment_id = nas_device['apartment_id'] if nas_device else None

            input_octets = parsed_data.get('input_octets', 0)
            output_octets = parsed_data.get('output_octets', 0)
            input_gigawords = parsed_data.get('input_gigawords', 0)
            output_gigawords = parsed_data.get('output_gigawords', 0)
            session_time = parsed_data.get('session_time', 0)

            if acct_status_type == 1:
                self._add_online_user(
                    nas_device_id=nas_device_id,
                    nas_ip=parsed_data.get('nas_ip'),
                    nas_identifier=nas_identifier,
                    server_ip=self.host,
                    session_id=parsed_data.get('session_id'),
                    username=parsed_data.get('username'),
                    apartment_id=apartment_id,
                    framed_ip=parsed_data.get('framed_ip'),
                    calling_station_id=parsed_data.get('calling_station_id'),
                    called_station_id=parsed_data.get('called_station_id')
                )
                print(f"[ACCT] ✅ {event_type} | User: {parsed_data.get('username')} | NAS: {parsed_data.get('nas_ip')} | Session: {parsed_data.get('session_id')} | Online")

            elif acct_status_type == 2:
                self._remove_online_user(
                    parsed_data.get('session_id'),
                    parsed_data.get('terminate_cause'),
                    session_time,
                    input_octets,
                    output_octets,
                    input_gigawords,
                    output_gigawords
                )
                terminate_cause = parsed_data.get('terminate_cause')
                cause_text = get_terminate_cause_text(terminate_cause)
                print(f"[ACCT] ⏹️  {event_type} | User: {parsed_data.get('username')} | NAS: {parsed_data.get('nas_ip')} | Session: {parsed_data.get('session_id')} | Offline | Duration: {session_time}s | Upload: {input_octets + input_gigawords * 4294967296} bytes | Download: {output_octets + output_gigawords * 4294967296} bytes | Cause: {cause_text}")

            elif acct_status_type == 3:
                self._update_online_user_traffic(
                    parsed_data.get('session_id'),
                    input_octets,
                    output_octets,
                    session_time,
                    input_gigawords,
                    output_gigawords
                )
                print(f"[ACCT] 📊 {event_type} | User: {parsed_data.get('username')} | NAS: {parsed_data.get('nas_ip')} | Session: {parsed_data.get('session_id')} | Upload: {input_octets + input_gigawords * 4294967296} bytes | Download: {output_octets + output_gigawords * 4294967296} bytes")

            else:
                print(f"[ACCT] ℹ️  {event_type} | User: {parsed_data.get('username')} | NAS: {parsed_data.get('nas_ip')}")

        except Exception as e:
            print(f"[ACCT ERROR] Async processing error: {e}")

    def _add_online_user(self, **kwargs):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['write_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO online_users
                        (nas_device_id, nas_ip, nas_identifier, server_ip, session_id, username,
                         apartment_id, framed_ip, calling_station_id, called_station_id,
                         start_time, update_time, input_octets, output_octets, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 'active', %s)
                    """, (
                        kwargs.get('nas_device_id'),
                        kwargs.get('nas_ip'),
                        kwargs.get('nas_identifier'),
                        kwargs.get('server_ip'),
                        kwargs.get('session_id'),
                        kwargs.get('username'),
                        kwargs.get('apartment_id'),
                        kwargs.get('framed_ip'),
                        kwargs.get('calling_station_id'),
                        kwargs.get('called_station_id'),
                        get_beijing_time(),
                        get_beijing_time(),
                        get_beijing_time()
                    ))
                    connection.commit()
                    print(f"    [DB] User {kwargs.get('username')} is now online")
                finally:
                    cursor.close()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            pass

    def _remove_online_user(self, session_id, terminate_cause, session_time, input_octets, output_octets, input_gigawords=0, output_gigawords=0):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['write_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                cursor = connection.cursor()
                try:
                    total_input = input_octets + (input_gigawords * (1024**3) * 4)
                    total_output = output_octets + (output_gigawords * (1024**3) * 4)

                    cursor.execute("""
                        UPDATE online_users
                        SET status = 'stopped',
                            session_time = %s,
                            input_octets = %s,
                            output_octets = %s,
                            update_time = %s
                        WHERE session_id = %s
                    """, (session_time, total_input, total_output, get_beijing_time(), session_id))
                    connection.commit()
                    print(f"    [DB] User session {session_id} is now offline with {total_input} bytes upload and {total_output} bytes download")
                finally:
                    cursor.close()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            pass

    def _update_online_user_traffic(self, session_id, input_octets, output_octets, session_time, input_gigawords=0, output_gigawords=0):
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['write_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                cursor = connection.cursor()
                try:
                    total_input = input_octets + (input_gigawords * (1024**3) * 4)
                    total_output = output_octets + (output_gigawords * (1024**3) * 4)

                    cursor.execute("""
                        UPDATE online_users
                        SET input_octets = %s,
                            output_octets = %s,
                            session_time = %s,
                            update_time = %s
                        WHERE session_id = %s AND status = 'active'
                    """, (total_input, total_output, session_time, get_beijing_time(), session_id))
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            pass

    def send_accounting_response(self, request_data, addr, nas_identifier=None):
        try:
            # 根据NAS设备获取对应的密钥
            nas_secret = self.secret  # 默认密钥

            # 尝试通过NAS Identifier查找密钥
            if nas_identifier:
                nas_device = self.get_nas_device_by_identifier(nas_identifier)
                if nas_device and nas_device.get('secret'):
                    nas_secret = nas_device['secret'].encode()

            # 如果通过IP查找密钥
            if nas_secret == self.secret:
                nas_device = self.get_nas_device_by_ip(addr[0])
                if nas_device and nas_device.get('secret'):
                    nas_secret = nas_device['secret'].encode()

            print(f"    [INFO] NAS {addr[0]} 使用密钥: {nas_secret.decode()[:10]}...")

            # 构建20字节响应头
            # 公式: MD5(Code + ID + Length + Request-Authenticator + Secret)
            response = bytearray(20)
            response[0] = 5                                          # Code: Accounting-Response
            response[1] = request_data[1]                           # Identifier: 与请求相同
            response[2] = 0
            response[3] = 20                                        # Length: 20字节
            response[4:20] = request_data[4:20]                      # Request-Authenticator: 来自请求

            # 计算 Response Authenticator（使用对应NAS的密钥）
            md5_input = bytes(response) + nas_secret
            response[4:20] = hashlib.md5(md5_input).digest()

            self.acct_socket.sendto(bytes(response), addr)

            print(f"    [OK] Accounting-Response sent to {addr}")

            # 不再记录Response报文到数据库，只记录Start和Stop

            return bytes(response)
        except Exception as e:
            print(f"    [ERROR] Failed: {e}")
            return None

    def create_disconnect_request(self, username, session_id, secret, nas_ip, framed_ip=None, nas_port=3799):
        try:
            packet = bytearray()

            packet.append(40)  # Code: 40 = Disconnect-Request
            packet_id = int(time.time() * 1000) % 256
            packet.append(packet_id)
            packet.extend(b'\x00\x00')  # Length placeholder

            packet.extend(b'\x00' * 16)  # Request Authenticator (placeholder)

            attributes = bytearray()

            username_bytes = username.encode('utf-8')
            attributes.append(1)  # User-Name
            attributes.append(len(username_bytes) + 2)
            attributes.extend(username_bytes)

            nas_ip_bytes = socket.inet_aton(nas_ip)
            attributes.append(4)  # NAS-IP-Address
            attributes.append(6)
            attributes.extend(nas_ip_bytes)

            attributes.append(6)  # Service-Type
            attributes.append(6)
            attributes.extend(b'\x00\x00\x00\x13')  # 19 = Disconnect-Request (0x13)

            if framed_ip:
                try:
                    framed_ip_bytes = socket.inet_aton(framed_ip)
                    attributes.append(8)  # Framed-IP-Address
                    attributes.append(6)
                    attributes.extend(framed_ip_bytes)
                except:
                    pass

            session_id_bytes = session_id.encode('utf-8')
            attributes.append(44)  # Acct-Session-Id
            attributes.append(len(session_id_bytes) + 2)
            attributes.extend(session_id_bytes)

            packet.extend(attributes)

            packet[2:4] = struct.pack('!H', len(packet))

            secret_bytes = secret if isinstance(secret, bytes) else secret.encode('utf-8')
            authenticator_data = bytes(packet) + secret_bytes
            authenticator_hash = hashlib.md5(authenticator_data).digest()
            packet[4:20] = authenticator_hash

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            try:
                print(f"    [COA DEBUG] Sending Disconnect-Request:")
                print(f"      - NAS IP: {nas_ip}:{nas_port}")
                print(f"      - Username: {username}")
                print(f"      - Session ID: {session_id}")
                print(f"      - Framed IP: {framed_ip or 'N/A'}")
                print(f"      - Packet Size: {len(packet)} bytes")

                sock.sendto(bytes(packet), (nas_ip, nas_port))
                print(f"    [COA] Disconnect-Request sent to {nas_ip}:{nas_port}")

                # 不记录 Disconnect-Request 到数据库，只打印日志
                print(f"    [COA] Disconnect-Request sent to {nas_ip}:{nas_port}")

                try:
                    data, addr = sock.recvfrom(1024)
                    if len(data) > 0:
                        response_code = data[0]
                        response_id = data[1]

                        if response_id != packet_id:
                            error_msg = "Identifier mismatch"
                            print(f"    [COA] ⚠️  {error_msg}! Sent: {packet_id}, Received: {response_id}")
                            # 不记录 Identifier mismatch 到数据库
                            return False

                        if response_code == 41:
                            print(f"    [COA] Disconnect-ACK received from {addr}")
                            # 不记录 Disconnect-ACK 到数据库
                            return True
                        elif response_code == 42:
                            error_code = data[4] if len(data) > 4 else 0
                            error_msg = self.get_nak_error_message(error_code)
                            print(f"    [COA] Disconnect-NAK received from {addr} - {error_msg}")
                            # 不记录 Disconnect-NAK 到数据库
                            return False
                except socket.timeout:
                    print(f"    [COA] No response from NAS (timeout)")
                    # 不记录 Disconnect-Timeout 到数据库
                    return False

                return False
            except Exception as e:
                print(f"    [COA ERROR] Failed to send Disconnect-Request: {e}")
                return False
            finally:
                sock.close()
        except Exception as e:
            print(f"    [COA ERROR] Failed to create Disconnect-Request: {e}")
            return False

    def get_nak_error_message(self, error_code):
        error_messages = {
            0: "Session-Context-Not-Found",
            1: "Unsupported-Service",
            2: "Unsupported-Extension",
            3: "Invalid-EAP-Packet",
            4: "Session-Not-Ready",
            5: "Session-Context-Removed",
            6: "Proxy-Request-Not-Routable",
            401: "Authorization-Reject",
            402: "Invalid-Request",
            403: "Processing-Error"
        }
        return error_messages.get(error_code, f"Unknown error ({error_code})")

    def _log_coa_request_sync(self, **kwargs):
        """记录CoA请求日志"""
        try:
            db_config_with_timeout = self.db_config.copy()
            db_config_with_timeout['connect_timeout'] = 1
            db_config_with_timeout['write_timeout'] = 1
            connection = pymysql.connect(**db_config_with_timeout)
            try:
                cursor = connection.cursor()
                try:
                    sql = """
                        INSERT INTO radius_communication_logs
                        (nas_ip, nas_identifier, server_ip, port, direction, packet_type, username,
                         session_id, request_code, is_success, error_message, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        kwargs.get('nas_ip'),
                        kwargs.get('nas_identifier'),
                        kwargs.get('server_ip'),
                        kwargs.get('port'),
                        kwargs.get('direction'),
                        kwargs.get('packet_type'),
                        kwargs.get('username'),
                        kwargs.get('session_id'),
                        kwargs.get('request_code'),
                        kwargs.get('is_success', True),
                        kwargs.get('error_message'),
                        get_beijing_time()
                    ))
                    connection.commit()
                finally:
                    cursor.close()
            finally:
                try:
                    connection.close()
                except:
                    pass
        except:
            pass


radius_server_instance = None

def get_radius_server():
    global radius_server_instance
    return radius_server_instance

def start_radius_server(host='0.0.0.0', auth_port=1812, acct_port=1813, secret='123456789123456789'):
    global radius_server_instance

    if radius_server_instance and radius_server_instance.is_running():
        print("[RADIUS] Server already running")
        return radius_server_instance

    radius_server_instance = RadiusServer(
        host=host,
        auth_port=auth_port,
        acct_port=acct_port,
        secret=secret
    )

    radius_server_instance.start()
    return radius_server_instance

def stop_radius_server():
    global radius_server_instance

    if radius_server_instance:
        radius_server_instance.stop()
        radius_server_instance = None
        print("[RADIUS] Server stopped")
