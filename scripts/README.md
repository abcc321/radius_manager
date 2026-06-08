# 数据库脚本

本文档包含数据库相关的SQL脚本。

## 目录结构

```
scripts/
├── README.md                        # 本文件
├── init_db.sql                     # 数据库初始化脚本（完整建表）
└── migration_add_nas_status.sql   # 增量迁移脚本（添加nas_devices表status字段）
```

## 脚本说明

### init_db.sql
完整的数据库初始化脚本，包含13张表的创建和初始数据。

**包含的表：**
1. apartments - 公寓表
2. operators - 操作员表
3. apartment_admins - 公寓管理员关联表
4. nas_devices - NAS设备表
5. nas_status - NAS设备状态记录表
6. system_config - 系统配置表
7. radius_servers - RADIUS服务器配置表
8. radius_communication_logs - RADIUS通信日志表
9. plans - 套餐表
10. network_users - 网络用户表
11. online_users - 在线用户表
12. audit_logs - 审计日志表
13. fault_reports - 故障报告表

### migration_add_nas_status.sql
增量迁移脚本，为nas_devices表添加status字段。

## 使用方法

### 初始化数据库
```bash
mysql -h 192.168.9.210 -u root -pAa321321+ < scripts/init_db.sql
```

### 执行迁移
```bash
mysql -h 192.168.9.210 -u root -pAa321321+ radius_manager < scripts/migration_add_nas_status.sql
```

## 注意事项

1. 执行init_db.sql会创建数据库和所有表，如果表已存在会跳过（IF NOT EXISTS）
2. 迁移脚本只用于更新现有数据库，不会影响已有数据
3. 执行前请备份数据库
