import os
import signal
import subprocess
import sys
import time

def check_port(port):
    """检查端口是否被占用"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        pids = []
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if parts:
                    pids.append(parts[-1])
        return list(set(pids))
    except:
        return []

def kill_process(pid):
    """杀掉指定进程"""
    try:
        os.system(f'taskkill /F /PID {pid}')
        print(f"已终止进程 {pid}")
        return True
    except:
        return False

def start_backend(port=8000):
    """启动后端服务"""
    print(f"\n检查端口 {port} 占用情况...")
    
    pids = check_port(port)
    
    if pids:
        print(f"端口 {port} 被以下进程占用: {', '.join(pids)}")
        print("正在终止占用进程...")
        for pid in pids:
            kill_process(pid)
        time.sleep(1)
    
    print(f"\n启动后端服务 (端口 {port})...")
    
    cmd = f'cd /d "D:\\trae_project\\radius_manager\\backend" && python -m uvicorn app:app --reload --host 0.0.0.0 --port {port}'
    
    subprocess.Popen(cmd, shell=True)
    print(f"后端服务已在后台启动 (端口 {port})")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_backend(port)
