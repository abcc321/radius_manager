# Windows 部署指南

本文档介绍如何在 Windows 系统上部署 RADIUS 网络计费管理系统。

## 环境要求

- Windows Server 2016+ 或 Windows 10/11
- Python 3.10+
- MySQL 5.7+ 或 MariaDB 10.3+
- Node.js 18+

## 一、安装 Python

1. 下载 Python 3.10+ 安装包
   - 地址：https://www.python.org/downloads/windows/

2. 安装时勾选：
   - ☑ Add Python to PATH
   - ☑ Install pip

3. 验证安装：
   ```cmd
   python --version
   pip --version
   ```

## 二、安装 Node.js

1. 下载 Node.js 18+ 安装包
   - 地址：https://nodejs.org/

2. 验证安装：
   ```cmd
   node --version
   npm --version
   ```

## 三、安装 MySQL

### 方法1：使用 XAMPP（推荐用于测试）

1. 下载 XAMPP：https://www.apachefriends.org/

2. 安装后启动 Apache 和 MySQL 服务

### 方法2：独立安装 MySQL

1. 下载 MySQL Installer：https://dev.mysql.com/downloads/installer/

2. 选择 "Server only" 安装类型

3. 配置 root 密码

## 四、创建数据库

1. 打开 MySQL 命令行或 phpMyAdmin

2. 执行以下命令创建数据库和用户：

```sql
CREATE DATABASE radius_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'radius'@'localhost' IDENTIFIED BY 'YourPassword123';
GRANT ALL PRIVILEGES ON radius_manager.* TO 'radius'@'localhost';
FLUSH PRIVILEGES;
```

3. 初始化数据表：
```cmd
cd d:\trae_project\radius_manager\scripts
mysql -u root -p radius_manager < init_db.sql
```

## 五、部署后端服务

### 1. 下载项目代码

```cmd
cd d:\
git clone <项目地址> radius_manager
# 或解压项目压缩包到 d:\trae_project\radius_manager
```

### 2. 安装 Python 依赖

```cmd
cd d:\trae_project\radius_manager\backend
pip install -r requirements.txt
```

### 3. 配置数据库连接

编辑 `backend/config.py`：

```python
DB_HOST = "localhost"          # 或 127.0.0.1
DB_PORT = 3306
DB_USER = "radius"            # 或 root
DB_PASSWORD = "YourPassword123"
DB_NAME = "radius_manager"
```

### 4. 测试后端服务

```cmd
cd d:\trae_project\radius_manager\backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

## 六、部署前端

### 1. 安装前端依赖

```cmd
cd d:\trae_project\radius_manager\frontend
npm install
```

### 2. 配置 API 地址

编辑 `frontend/src/common/request.js`，确保 API 地址正确：

```javascript
const baseURL = process.env.NODE_ENV === 'production'
  ? 'http://your-domain.com/api'
  : 'http://localhost:8000'
```

### 3. 构建生产版本

```cmd
cd d:\trae_project\radius_manager\frontend
npm run build
```

构建完成后，静态文件在 `dist` 目录

## 七、配置 Nginx（可选）

### 1. 下载 Nginx for Windows
- 地址：http://nginx.org/en/download.html

### 2. 配置 Nginx

编辑 `nginx.conf`：

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    upstream backend {
        server 127.0.0.1:8000;
    }

    server {
        listen       80;
        server_name  localhost;

        # 前端静态文件
        location / {
            root   d:/trae_project/radius_manager/frontend/dist;
            index  index.html index.htm;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket 支持
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 3. 启动 Nginx

```cmd
cd d:\nginx
start nginx
```

## 八、配置 Windows 服务（使用 NSSM）

### 1. 下载 NSSM
- 地址：https://nssm.cc/download

### 2. 配置后端服务

```cmd
nssm install radius_backend
# Path: d:\trae_project\radius_manager\backend\Scripts\python.exe
# Arguments: -m uvicorn app:app --host 0.0.0.0 --port 8000
# Startup directory: d:\trae_project\radius_manager\backend
```

### 3. 启动服务

```cmd
nssm start radius_backend
```

## 九、防火墙配置

### 开放端口

```cmd
netsh advfirewall firewall add rule name="RADIUS Backend" dir=in action=allow protocol=tcp localport=8000
netsh advfirewall firewall add rule name="RADIUS Frontend" dir=in action=allow protocol=tcp localport=80
netsh advfirewall firewall add rule name="RADIUS Auth" dir=in action=allow protocol=udp localport=1812
netsh advfirewall firewall add rule name="RADIUS Acct" dir=in action=allow protocol=udp localport=1813
```

## 十、验证部署

1. 访问前端页面：http://localhost
2. 访问 API 文档：http://localhost/docs
3. 使用默认账号登录：
   - 用户名：admin
   - 密码：admin123

## 常见问题

### Q: pip install 报错？

```cmd
# 更新 pip
python -m pip install --upgrade pip

# 如果网络慢，使用镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: MySQL 连接失败？

1. 检查 MySQL 服务是否启动
2. 检查用户名密码是否正确
3. 检查防火墙是否开放 3306 端口

### Q: 前端无法访问后端 API？

1. 检查后端服务是否运行
2. 检查 CORS 配置
3. 检查浏览器控制台错误信息

## 更新部署

```cmd
cd d:\trae_project\radius_manager

# 拉取最新代码
git pull

# 更新后端
cd backend
pip install -r requirements.txt
restart nginx  # 或重启后端服务

# 更新前端
cd ..\frontend
npm install
npm run build
```
