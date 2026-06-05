"""
自检模块配置
用于自定义自检行为和阈值
"""

class CheckConfig:
    """自检配置类"""
    
    def __init__(self):
        # 端口配置
        self.default_port = 8000
        self.max_port_cleanup_attempts = 3
        self.port_cleanup_interval = 1  # 秒
        
        # 数据库配置
        self.db_connection_timeout = 5  # 秒
        
        # 磁盘空间配置
        self.min_free_disk_gb = 1  # 最小剩余空间（GB）
        
        # 网络连接配置
        self.network_test_timeout = 2  # 秒
        self.network_test_hosts = ['8.8.8.8', '114.114.114.114']
        
        # Python依赖配置
        self.required_modules = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'pymysql',
            'pydantic',
            'passlib',
            'cryptography'
        ]
        
        # 显示配置
        self.show_header = True
        self.show_separator = True
        self.show_summary = True
        
        # 行为配置
        self.fail_on_error = False  # 检查失败时是否停止
        self.cleanup_on_startup = True  # 启动时是否清理端口
        
        # 日志配置
        self.log_to_file = False
        self.log_file_path = 'startup_check.log'

# 全局配置实例
config = CheckConfig()

def get_config():
    """获取配置实例"""
    return config

def update_config(**kwargs):
    """更新配置项
    
    Example:
        update_config(
            default_port=9000,
            min_free_disk_gb=2,
            fail_on_error=True
        )
    """
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"未知的配置项: {key}")

def reset_config():
    """重置为默认配置"""
    global config
    config = CheckConfig()
