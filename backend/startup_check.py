"""
启动自检模块
所有环境检查功能都集中在这里，方便后续扩展
"""

import os
import sys
import time
import socket
import subprocess
from typing import List, Tuple

class Colors:
    """颜色定义"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def p_success(text):
    """成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def p_error(text):
    """错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def p_warn(text):
    """警告信息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def p_info(text):
    """普通信息"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def check_port_pids(port: int) -> List[str]:
    """获取端口占用的进程ID列表"""
    try:
        cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -State Listen | Select-Object OwningProcess -ExpandProperty OwningProcess"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        pids = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line.isdigit():
                pids.append(line)
        return list(set(pids))
    except Exception as e:
        p_error(f"获取进程ID失败: {e}")
        return []

def kill_process(pid: str) -> bool:
    """终止指定进程"""
    try:
        cmd = f'taskkill /F /PID {pid}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            p_success(f"已终止进程 {pid}")
            return True
        else:
            p_error(f"终止进程 {pid} 失败")
            return False
    except Exception as e:
        p_error(f"终止进程异常: {e}")
        return False

def is_port_free(port: int) -> bool:
    """检查端口是否空闲"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

class StartupCheck:
    """自检管理器"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.check_results = []
    
    def print_header(self):
        """打印自检头部"""
        print(f"\n{Colors.BLUE}{'='*50}")
        print("RADIUS网络计费管理系统 - 启动自检")
        print(f"{'='*50}{Colors.RESET}\n")
    
    def check_python_dependencies(self) -> bool:
        """检查Python依赖"""
        p_info("检查Python依赖...")
        
        required = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pymysql',
            'pydantic', 'passlib', 'cryptography'
        ]
        
        missing = []
        for module in required:
            try:
                __import__(module.replace('-', '_'))
            except ImportError:
                missing.append(module)
        
        if missing:
            p_error(f"缺少依赖: {', '.join(missing)}")
            p_info("请运行: pip install -r requirements.txt")
            self.check_results.append(("Python依赖", False))
            return False
        
        p_success("Python依赖检查通过")
        self.check_results.append(("Python依赖", True))
        return True
    
    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        p_info("检查数据库连接...")
        
        try:
            from config import settings
            
            db_url = settings.DATABASE_URL
            parts = db_url.replace('mysql+pymysql://', '').split('@')[1].split('/')
            host_port = parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 3306
            db_name = parts[1].split('?')[0]
            
            pymysql = __import__('pymysql')
            conn = pymysql.connect(
                host=host,
                port=port,
                user='root',
                password='Aa321321+',
                database=db_name,
                charset='utf8mb4',
                connect_timeout=5
            )
            conn.close()
            
            p_success("数据库连接正常")
            self.check_results.append(("数据库连接", True))
            return True
            
        except Exception as e:
            p_error(f"数据库连接失败: {e}")
            self.check_results.append(("数据库连接", False))
            return False
    
    def check_disk_space(self) -> bool:
        """检查磁盘空间"""
        p_info("检查磁盘空间...")
        
        try:
            result = subprocess.run(
                'wmic logicaldisk where "DriveType=3" get Size,FreeSpace /format:list',
                shell=True, capture_output=True, text=True
            )
            
            free_space_gb = 0
            for line in result.stdout.split('\n'):
                if 'FreeSpace' in line:
                    value = line.split('=')[1].strip()
                    if value:
                        free_space_gb = max(free_space_gb, int(value) / (1024**3))
            
            if free_space_gb < 1:
                p_warn(f"磁盘空间不足: {free_space_gb:.2f} GB")
                self.check_results.append(("磁盘空间", False))
                return False
            
            p_success(f"磁盘空间充足: {free_space_gb:.2f} GB")
            self.check_results.append(("磁盘空间", True))
            return True
            
        except Exception as e:
            p_warn(f"磁盘空间检查失败: {e}")
            self.check_results.append(("磁盘空间", True))
            return True
    
    def check_network_connectivity(self) -> bool:
        """检查网络连接"""
        p_info("检查网络连接...")
        
        test_hosts = ['8.8.8.8', '114.114.114.114']
        
        for host in test_hosts:
            try:
                result = subprocess.run(
                    f'ping -n 1 -w 1000 {host}',
                    shell=True, capture_output=True, timeout=2
                )
                if result.returncode == 0:
                    p_success("网络连接正常")
                    self.check_results.append(("网络连接", True))
                    return True
            except:
                continue
        
        p_warn("网络连接异常（可能无法访问外网）")
        self.check_results.append(("网络连接", True))
        return True
    
    def check_port_available(self) -> bool:
        """检查端口可用性"""
        p_info(f"检查端口 {self.port} 可用性...")
        
        if is_port_free(self.port):
            p_success(f"端口 {self.port} 空闲")
            self.check_results.append(("端口检查", True))
            return True
        
        p_warn(f"端口 {self.port} 被占用，开始清理...")
        
        for _ in range(3):
            pids = check_port_pids(self.port)
            if not pids:
                break
            
            p_info(f"发现进程: {', '.join(pids)}")
            for pid in pids:
                kill_process(pid)
            time.sleep(1)
        
        if is_port_free(self.port):
            p_success("端口已释放")
            self.check_results.append(("端口检查", True))
            return True
        else:
            p_warn("端口仍被占用，服务可能无法正常启动")
            self.check_results.append(("端口检查", False))
            return False
    
    def run_all_checks(self) -> bool:
        """运行所有自检"""
        self.print_header()
        
        checks = [
            self.check_python_dependencies,
            self.check_database_connection,
            self.check_disk_space,
            self.check_network_connectivity,
            self.check_port_available,
        ]
        
        all_passed = True
        for check in checks:
            print("-" * 50)
            result = check()
            if not result:
                all_passed = False
            print()
        
        self.print_summary(all_passed)
        return all_passed
    
    def print_summary(self, all_passed: bool):
        """打印自检总结"""
        print(f"\n{Colors.BLUE}{'='*50}")
        print("自检结果汇总")
        print(f"{'='*50}{Colors.RESET}\n")
        
        for name, passed in self.check_results:
            status = "通过" if passed else "失败"
            if passed:
                p_success(f"{name}: {status}")
            else:
                p_error(f"{name}: {status}")
        
        print()
        if all_passed:
            p_success("所有检查通过，服务即将启动...")
        else:
            p_warn("部分检查未通过，但将继续尝试启动...")
        
        print()

def run_startup_checks(port: int = 8000) -> bool:
    """运行启动自检的便捷函数"""
    checker = StartupCheck(port)
    return checker.run_all_checks()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    success = run_startup_checks(port)
    sys.exit(0 if success else 1)
