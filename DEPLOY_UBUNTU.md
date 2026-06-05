# Ubuntu 部署指南

本文档介绍如何在 Ubuntu 系统上部署 RADIUS 网络计费管理系统。

## 环境要求

- Ubuntu 20.04+ / 22.04+
- Python 3.10+
- MySQL 8.0+ 或 MariaDB 10.6+
- Node.js 18+
- Nginx

## 一、系统更新

```bash
sudo apt update && sudo apt upgrade -y
```

## 二、安装 Python

```bash
# 安装 Python 和相关工具
sudo apt install -y python3 python3-pip python3-venv

# 验证安装
python3 --version
pip3 --version
```

## 三、安装 Node.js

```bash
# 添加 NodeSource 仓库（以 Node.js 18 为例）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# 安装 Node.js
sudo apt install -y nodejs

# 验证安装
node --version
npm --version
```

## 四、安装 MySQL

### 安装 MySQL Server

```bash
sudo apt install -y mysql-server

# 启动服务并设置开机自启
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置（设置 root 密码等）
sudo mysql_secure_installation
```

### 创建数据库和用户

```bash
sudo mysql
```

在 MySQL 命令行中执行：

```sql
CREATE DATABASE radius_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'radius'@'localhost' IDENTIFIED BY 'YourStrongPassword123';
GRANT ALL PRIVILEGES ON radius_manager.* TO 'radius'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 初始化数据表

```bash
cd /opt/radius_manager/scripts
mysql -u radius -p radius_manager < init_db.sql
```

## 五、部署后端服务

### 1. 创建部署目录

```bash
sudo mkdir -p /opt/radius_manager
sudo chown $USER:$USER /opt/radius_manager
cd /opt/radius_manager
```

### 2. 上传项目代码

```bash
# 方法1：使用 git
git clone <项目地址> .

# 方法2：使用 scp 上传压缩包
scp radius_manager.tar.gz user@server:/opt/
tar -xzf radius_manager.tar.gz
```

### 3. 创建虚拟环境

```bash
cd /opt/radius_manager/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
nano /opt/radius_manager/backend/.env
```

添加以下内容：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=radius
DB_PASSWORD=YourStrongPassword123
DB_NAME=radius_manager
SECRET_KEY=your-secret-key-here
```

### 5. 配置数据库连接

编辑 `backend/config.py`：

```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "radius")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "radius_manager")
```

## 六、创建 Systemd 服务

### 创建后端服务文件

```bash
sudo nano /etc/systemd/system/radius-backend.service
```

添加以下内容：

```ini
[Unit]
Description=RADIUS Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/radius_manager/backend
Environment="PATH=/opt/radius_manager/backend/venv/bin"
ExecStart=/opt/radius_manager/backend/venv/bin/gunicorn app:app -w 4 -b 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 安装 Gunicorn（生产服务器）

```bash
source /opt/radius_manager/backend/venv/bin/activate
pip install gunicorn
```

### 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl start radius-backend
sudo systemctl enable radius-backend

# 检查状态
sudo systemctl status radius-backend
```

## 七、部署前端

### 1. 安装依赖并构建

```bash
cd /opt/radius_manager/frontend

npm install
npm run build
```

### 2. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/radius-manager
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 或服务器 IP

    # 前端静态文件
    root /opt/radius_manager/frontend/dist;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # 前端路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. 启用站点

```bash
# 删除默认站点
sudo rm /etc/nginx/sites-enabled/default

# 启用我们的站点
sudo ln -s /etc/nginx/sites-available/radius-manager /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 4. 配置 SSL（可选）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com
```

## 八、配置防火墙

```bash
# 安装 ufw
sudo apt install -y ufw

# 配置规则
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

## 九、RADIUS 服务端口配置

如果需要 RADIUS 服务（UDP 端口）：

```bash
sudo ufw allow 1812/udp  # RADIUS 认证
sudo ufw allow 1813/udp  # RADIUS 计费
sudo ufw allow 3799/udp  # CoA 端口
```

## 十、配置日志轮转

```bash
sudo nano /etc/logrotate.d/radius-manager
```

添加以下内容：

```
/opt/radius_manager/backend/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## 十一、验证部署

1. 访问前端页面：http://your-domain.com
2. 访问 API：http://your-domain.com/docs
3. 使用默认账号登录：
   - 用户名：admin
   - 密码：admin123

## 常见问题

### Q: 权限错误？

```bash
# 设置目录权限
sudo chown -R www-data:www-data /opt/radius_manager
```

### Q: 数据库连接失败？

```bash
# 检查 MySQL 服务状态
sudo systemctl status mysql

# 检查连接
mysql -u radius -p -h localhost
```

### Q: Nginx 502 错误？

```bash
# 检查后端服务
sudo systemctl status radius-backend

# 检查端口占用
sudo netstat -tlnp | grep 8000
```

## 更新部署

```bash
# 进入项目目录
cd /opt/radius_manager

# 拉取最新代码
git pull

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart radius-backend

# 更新前端
cd ../frontend
npm install
npm run build

# 重载 Nginx
sudo systemctl reload nginx
```

## 备份

```bash
# 备份数据库
mysqldump -u radius -p radius_manager > backup_$(date +%Y%m%d).sql

# 备份代码
tar -czf radius_manager_backup_$(date +%Y%m%d).tar.gz /opt/radius_manager
```
