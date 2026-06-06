# RADIUS 网络计费管理系统

基于 RADIUS 协议的网络用户计费管理系统，支持多公寓管理、在线用户监控、套餐配置、账单生成等功能。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vue 3 前端 (5173)                     │
├─────────────────────────────────────────────────────────┤
│                   FastAPI 后端 (8000)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ RADIUS   │ │ 在线用户  │ │  NAS监控  │ │  WebSocket │  │
│  │ 服务器   │ │  管理    │ │          │ │          │  │
│  │ :1812/1813 │ │          │ │          │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│                    MySQL 数据库                         │
│              (192.168.9.210:3306)                       │
└─────────────────────────────────────────────────────────┘
```

## 功能模块

| 模块 | 功能说明 |
|------|----------|
| **运营商管理** | 操作员账号创建、密码修改、权限分配、公寓关联 |
| **公寓管理** | 公寓增删改查、启用/禁用、在线用户统计 |
| **NAS设备** | NAS设备配置、RADIUS参数设置、连接状态检测 |
| **套餐管理** | 宽带套餐配置、速率限制、计费规则 |
| **用户管理** | 网络用户CRUD、批量导入导出、激活/停用 |
| **在线用户** | 实时在线用户、用户详情、强制下线 |
| **RADIUS日志** | 通信日志记录、用户上线/下线行为分析 |
| **预警分析** | 开通未在线用户、频繁拨号用户分析 |
| **账单管理** | 月度账单生成、Excel导出 |
| **审计日志** | 操作记录追踪、模块/操作类型筛选 |
| **故障处理** | 用户报障、工单处理、故障统计、工作流程（待处理→处理中→已解决→已关闭） |

## 快速启动

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 5.7+

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 数据库配置

编辑 `backend/config.py`：

```python
DB_HOST = "192.168.9.210"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "Aa321321+"
DB_NAME = "radius_manager"
```

### 3. 启动服务

**后端：**
```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5173 |
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |

## 默认账号

- **用户名：** admin
- **密码：** admin123

> 首次登录后请修改密码

## 项目结构

```
radius_manager/
├── backend/                     # 后端服务
│   ├── app.py                   # 应用入口
│   ├── radius_server.py         # RADIUS服务器
│   ├── nas_monitor.py           # NAS监控服务
│   ├── websocket_manager.py      # WebSocket管理
│   ├── startup_check.py         # 启动自检
│   ├── config.py                # 配置文件
│   ├── requirements.txt         # Python依赖
│   │
│   ├── modules/                 # 功能模块
│   │   ├── auth/               # 认证
│   │   ├── operator/           # 运营商/操作员
│   │   ├── apartment/          # 公寓管理
│   │   ├── nas/                # NAS设备
│   │   ├── plan/               # 套餐管理
│   │   ├── network_user/       # 网络用户
│   │   ├── online_user/        # 在线用户
│   │   ├── billing/            # 账单管理
│   │   ├── radius/             # RADIUS日志
│   │   ├── warning/            # 预警分析
│   │   ├── audit_log/          # 审计日志
│   │   └── fault/              # 故障处理
│   │
│   ├── common/                  # 公共模块
│   │   ├── database.py         # 数据库连接
│   │   ├── models.py           # 数据模型
│   │   └── response.py          # 响应封装
│   │
│   └── downloads/              # 下载文件目录
│       └── bills/              # 账单文件
│
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── main.js             # 入口文件
│   │   ├── App.vue             # 根组件
│   │   │
│   │   ├── common/             # 公共模块
│   │   │   ├── request.js      # HTTP请求
│   │   │   └── router.js       # 路由配置
│   │   │
│   │   ├── layouts/            # 布局组件
│   │   │   └── MainLayout.vue  # 主布局
│   │   │
│   │   ├── modules/            # 功能模块
│   │   │   ├── operator/       # 运营商
│   │   │   ├── apartment/      # 公寓
│   │   │   ├── nas/            # NAS设备
│   │   │   ├── plan/           # 套餐
│   │   │   ├── network_user/   # 用户
│   │   │   ├── online_user/    # 在线用户
│   │   │   ├── billing/        # 账单
│   │   │   ├── radius/         # RADIUS日志
│   │   │   ├── warning/        # 预警
│   │   │   └── fault/          # 故障处理
│   │   │
│   │   └── views/              # 页面
│   │       ├── Login.vue
│   │       └── Home.vue
│   │
│   └── package.json
│
└── scripts/                     # 脚本
    └── init_db.sql             # 数据库初始化
```

## 技术栈

### 后端
- **框架：** FastAPI
- **ORM：** SQLAlchemy
- **数据库：** MySQL
- **RADIUS：** py-radius

### 前端
- **框架：** Vue 3
- **UI库：** Element Plus
- **构建：** Vite
- **HTTP：** Axios

## RADIUS 服务端口

| 端口 | 用途 |
|------|------|
| 1812 | RADIUS 认证 |
| 1813 | RADIUS 计费 |
| 3799 | CoA (强制下线) |

## 相关文档

- [操作使用指南](./USAGE_GUIDE.md) - 详细功能操作说明
- [Windows 部署指南](./DEPLOY_WINDOWS.md) - Windows 系统部署说明
- [Ubuntu 部署指南](./DEPLOY_UBUNTU.md) - Ubuntu 系统部署说明

## 许可证

私有项目
