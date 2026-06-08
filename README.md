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
| **预警分析** | 开通未在线用户分析、频繁拨号用户分析 |
| **账单管理** | 月度账单生成、Excel导出 |
| **审计日志** | 操作记录追踪、模块/操作类型筛选 |
| **故障处理** | 用户报障、工单处理、故障统计、工作流程（待处理→处理中→已解决→已关闭） |

## 数据库结构

系统使用13张数据表，具体结构如下：

### 1. apartments - 公寓表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| code | VARCHAR(50) | 公寓编号（唯一） |
| name | VARCHAR(100) | 公寓名称 |
| contact | VARCHAR(50) | 联系人 |
| phone | VARCHAR(20) | 联系电话 |
| address | VARCHAR(255) | 地址 |
| status | VARCHAR(20) | 状态：active-正常，inactive-禁用 |
| nas_device_id | INT | 关联的NAS设备ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 2. operators - 操作员表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| username | VARCHAR(50) | 用户名（唯一） |
| password_hash | VARCHAR(255) | 密码哈希 |
| name | VARCHAR(50) | 姓名 |
| phone | VARCHAR(20) | 手机号 |
| role | VARCHAR(20) | 角色：admin-系统管理员，operator-普通操作员 |
| status | VARCHAR(20) | 状态：active-正常，inactive-禁用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3. apartment_admins - 公寓管理员关联表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| operator_id | INT | 操作员ID |
| apartment_id | INT | 公寓ID |
| role | VARCHAR(20) | 角色：admin-公寓管理员，operator-操作员 |
| created_at | DATETIME | 创建时间 |

### 4. nas_devices - NAS设备表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 设备名称 |
| ip_address | VARCHAR(50) | IP地址（唯一） |
| mac_address | VARCHAR(17) | MAC地址 |
| nas_identifier | VARCHAR(100) | NAS标识符（RADIUS Attribute 32） |
| device_type | VARCHAR(50) | 设备类型（如：RouterOS, Cisco, H3C等） |
| community | VARCHAR(100) | SNMP团体名 |
| secret | VARCHAR(255) | 共享密钥 |
| check_interval | INT | 检测间隔（分钟） |
| session_timeout | INT | 会话超时时间（秒） |
| acct_interim_interval | INT | 计费更新间隔（秒） |
| description | TEXT | 设备描述 |
| status | VARCHAR(20) | 设备状态：online-在线，offline-离线 |
| apartment_id | INT | 所属公寓ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 5. nas_status - NAS设备状态记录表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| nas_device_id | INT | NAS设备ID |
| status | VARCHAR(20) | 状态：online-在线，offline-离线 |
| response_time | INT | 响应时间（毫秒） |
| error_message | TEXT | 错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 6. system_config - 系统配置表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| config_key | VARCHAR(100) | 配置键（唯一） |
| config_value | VARCHAR(255) | 配置值 |
| description | VARCHAR(255) | 配置描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 7. radius_servers - RADIUS服务器配置表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| server_name | VARCHAR(100) | 服务器名称 |
| server_ip | VARCHAR(50) | 服务器IP地址（唯一） |
| auth_port | INT | 认证端口（默认1812） |
| acct_port | INT | 计费端口（默认1813） |
| secret | VARCHAR(255) | 共享密钥 |
| status | VARCHAR(20) | 状态：active-正常，inactive-禁用 |
| description | TEXT | 描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 8. radius_communication_logs - RADIUS通信日志表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| nas_device_id | INT | NAS设备ID（可选） |
| nas_ip | VARCHAR(50) | NAS IP地址 |
| nas_identifier | VARCHAR(100) | NAS标识符 |
| server_ip | VARCHAR(50) | RADIUS服务器IP |
| port | INT | 端口号 |
| direction | VARCHAR(10) | 方向：request-请求，response-响应 |
| packet_type | VARCHAR(50) | 数据包类型 |
| username | VARCHAR(100) | 用户名 |
| session_id | VARCHAR(100) | 会话ID |
| request_code | VARCHAR(20) | 请求码/响应码 |
| raw_data | TEXT | 原始数据包（十六进制） |
| is_success | TINYINT(1) | 是否成功 |
| error_message | TEXT | 错误信息（如有） |
| response_time | INT | 响应时间（毫秒） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 9. plans - 套餐表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| name | VARCHAR(100) | 套餐名称 |
| price | VARCHAR(50) | 套餐费用 |
| upload_speed | INT | 上行速率（KB/s） |
| download_speed | INT | 下行速率（KB/s） |
| apartment_id | INT | 关联的公寓ID |
| status | VARCHAR(20) | 状态：active-正常，inactive-禁用 |
| description | TEXT | 套餐描述 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 10. network_users - 网络用户表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| apartment_id | INT | 所属公寓ID |
| username | VARCHAR(100) | 上网账号 |
| password | VARCHAR(255) | 密码 |
| name | VARCHAR(100) | 姓名 |
| phone | VARCHAR(20) | 手机号 |
| room | VARCHAR(50) | 房间号 |
| plan_id | INT | 套餐ID |
| status | VARCHAR(20) | 状态：active-开通，inactive-停用 |
| activate_date | VARCHAR(10) | 开通日期 |
| expire_date | VARCHAR(10) | 到期日期 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 11. online_users - 在线用户表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| nas_device_id | INT | NAS设备ID |
| nas_ip | VARCHAR(50) | NAS IP地址 |
| nas_identifier | VARCHAR(100) | NAS标识符 |
| server_ip | VARCHAR(50) | RADIUS服务器IP |
| session_id | VARCHAR(100) | 会话ID（唯一，Acct-Session-Id） |
| username | VARCHAR(100) | 用户名 |
| apartment_id | INT | 公寓ID |
| room | VARCHAR(50) | 房间号 |
| framed_ip | VARCHAR(50) | 分配的IP地址 |
| calling_station_id | VARCHAR(50) | 用户MAC地址 |
| called_station_id | VARCHAR(100) | NAS端口标识 |
| start_time | DATETIME | 上线时间 |
| update_time | DATETIME | 最后更新时间 |
| input_octets | INT | 上行流量（字节） |
| output_octets | INT | 下行流量（字节） |
| input_packets | INT | 上行包数 |
| output_packets | INT | 下行包数 |
| session_time | INT | 会话时长（秒） |
| status | VARCHAR(20) | 状态：active-在线，stopped-已下线 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 12. audit_logs - 审计日志表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键ID |
| operator_id | INT | 操作员ID |
| operator_name | VARCHAR(50) | 操作员用户名 |
| module | VARCHAR(50) | 操作模块 |
| action | VARCHAR(20) | 操作类型：CREATE-创建，UPDATE-更新，DELETE-删除 |
| target_type | VARCHAR(50) | 操作对象类型 |
| target_id | INT | 操作对象ID |
| target_name | VARCHAR(255) | 操作对象名称 |
| description | TEXT | 操作描述 |
| old_data | TEXT | 操作前数据（JSON） |
| new_data | TEXT | 操作后数据（JSON） |
| ip_address | VARCHAR(50) | IP地址 |
| user_agent | VARCHAR(255) | 用户代理 |
| status | VARCHAR(20) | 状态：success-成功，failed-失败 |
| error_message | TEXT | 错误信息（如有） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 13. fault_reports - 故障报告表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键 |
| user_id | INT | 用户ID |
| username | VARCHAR(100) | 上网账号 |
| apartment_id | INT | 公寓ID |
| apartment_name | VARCHAR(100) | 公寓名称 |
| room | VARCHAR(50) | 房间号 |
| fault_type | VARCHAR(50) | 故障类型：cannot_connect-不能上网，slow_network-网络卡顿，frequent_disconnect-频繁掉线 |
| description | TEXT | 故障描述 |
| status | VARCHAR(20) | 状态：pending-待处理，processing-处理中，resolved-已解决，closed-已关闭 |
| reporter_name | VARCHAR(100) | 报障人姓名 |
| reporter_phone | VARCHAR(20) | 报障人电话 |
| fault_time | DATETIME | 故障时间 |
| resolve_time | DATETIME | 解决时间 |
| resolve_description | TEXT | 处理说明 |
| operator_id | INT | 处理操作员ID |
| operator_name | VARCHAR(50) | 处理操作员姓名 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

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

### 3. 初始化数据库

```bash
# 执行数据库初始化脚本
mysql -h 192.168.9.210 -u root -pAa321321+ < scripts/init_db.sql
```

### 4. 启动服务

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
│   ├── websocket_manager.py     # WebSocket管理
│   ├── startup_check.py         # 启动自检
│   ├── config.py                # 配置文件
│   ├── requirements.txt        # Python依赖
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
│   │   └── response.py         # 响应封装
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
│   │   │   ├── router.js       # 路由配置
│   │   │   └── styles/         # 公共样式
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
├── scripts/                     # 数据库脚本
│   ├── README.md              # 脚本说明
│   ├── init_db.sql            # 数据库初始化
│   └── migration_add_nas_status.sql  # 增量迁移脚本
│
├── tools/                      # 工具脚本
│   ├── README.md              # 工具说明
│   ├── database/              # 数据库工具
│   │   ├── check_db_schema.py       # 检查数据库结构
│   │   ├── check_status.py          # 检查用户状态
│   │   └── update_operators_phone.py # 更新操作员手机号
│   └── debug/                 # 调试脚本（临时使用）
│       ├── check_songziling.py
│       ├── check_active.py
│       ├── check_expire.py
│       ├── check_table.py
│       └── check_db.py
│
└── docs/                      # 文档
    └── mobile-responsive.md    # 移动端响应式设计文档
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

### 服务器端端口（NAS → 服务器）

| 端口 | 类型 | 用途 | 说明 |
|------|------|------|------|
| 1812 | UDP | RADIUS 认证 | NAS 设备向服务器发送用户认证请求 |
| 1813 | UDP | RADIUS 计费 | NAS 设备向服务器发送计费更新 |

### NAS 设备端口（服务器 → NAS）

| 端口 | 类型 | 用途 | 说明 |
|------|------|------|------|
| 3799 | UDP | CoA/Disconnect | 服务器向 NAS 发送强制下线指令 |

> **说明**：1812/1813 是服务器需要监听的端口，由 NAS 设备主动发起请求；3799 是 NAS 设备需要监听的端口，接收来自服务器的强制下线请求。

## 相关文档

- [操作使用指南](./USAGE_GUIDE.md) - 详细功能操作说明
- [Windows 部署指南](./DEPLOY_WINDOWS.md) - Windows 系统部署说明
- [Ubuntu 部署指南](./DEPLOY_UBUNTU.md) - Ubuntu 系统部署说明
- [移动端响应式设计](./docs/mobile-responsive.md) - 移动端适配说明
- [工具脚本说明](./tools/README.md) - 数据库工具和调试脚本说明
- [数据库脚本说明](./scripts/README.md) - SQL脚本使用说明

## 许可证

私有项目
