-- =====================================================
-- RADIUS 网络计费管理系统 - 数据库初始化脚本
-- =====================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS radius_manager DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE radius_manager;

-- =====================================================
-- 1. 公寓表
-- =====================================================
CREATE TABLE IF NOT EXISTS `apartments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `code` VARCHAR(50) NOT NULL COMMENT '公寓编号',
    `name` VARCHAR(100) NOT NULL COMMENT '公寓名称',
    `contact` VARCHAR(50) COMMENT '联系人',
    `phone` VARCHAR(20) COMMENT '联系电话',
    `address` VARCHAR(255) COMMENT '地址',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-正常，inactive-禁用',
    `nas_device_id` INT COMMENT '关联的NAS设备ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公寓表';

-- =====================================================
-- 2. 操作员表
-- =====================================================
CREATE TABLE IF NOT EXISTS `operators` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `name` VARCHAR(50) COMMENT '姓名',
    `role` VARCHAR(20) DEFAULT 'operator' COMMENT '角色：admin-系统管理员，operator-普通操作员',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-正常，inactive-禁用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作员表';

-- =====================================================
-- 3. 公寓管理员关联表（多对多关系）
-- =====================================================
CREATE TABLE IF NOT EXISTS `apartment_admins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `operator_id` INT NOT NULL COMMENT '操作员ID',
    `apartment_id` INT NOT NULL COMMENT '公寓ID',
    `role` VARCHAR(20) DEFAULT 'admin' COMMENT '角色：admin-公寓管理员，operator-操作员',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY `uk_operator_apartment` (`operator_id`, `apartment_id`),
    KEY `idx_operator_id` (`operator_id`),
    KEY `idx_apartment_id` (`apartment_id`),
    FOREIGN KEY (`operator_id`) REFERENCES `operators`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`apartment_id`) REFERENCES `apartments`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公寓管理员关联表';

-- =====================================================
-- 4. NAS设备表
-- =====================================================
CREATE TABLE IF NOT EXISTS `nas_devices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `name` VARCHAR(100) NOT NULL COMMENT '设备名称',
    `ip_address` VARCHAR(50) NOT NULL COMMENT 'IP地址',
    `mac_address` VARCHAR(17) COMMENT 'MAC地址',
    `nas_identifier` VARCHAR(100) COMMENT 'NAS标识符',
    `device_type` VARCHAR(50) COMMENT '设备类型（如：RouterOS, MikroTik, Cisco, H3C等）',
    `community` VARCHAR(100) COMMENT 'SNMP团体名',
    `secret` VARCHAR(255) NOT NULL COMMENT '共享密钥（与NAS设备配置的RADIUS密钥一致）',
    `check_interval` INT DEFAULT 1 COMMENT '检测间隔（分钟）',
    `session_timeout` INT DEFAULT 15682168 COMMENT '会话超时时间（秒）',
    `acct_interim_interval` INT DEFAULT 60 COMMENT '计费更新间隔（秒）',
    `description` TEXT COMMENT '设备描述',
    `apartment_id` INT COMMENT '所属公寓ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_ip_address` (`ip_address`),
    UNIQUE KEY `uk_nas_identifier` (`nas_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='NAS设备表';

-- =====================================================
-- 5. NAS设备状态记录表
-- =====================================================
CREATE TABLE IF NOT EXISTS `nas_status` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `nas_device_id` INT NOT NULL COMMENT 'NAS设备ID',
    `status` VARCHAR(20) NOT NULL COMMENT '状态：online-在线，offline-离线',
    `response_time` INT COMMENT '响应时间（毫秒）',
    `error_message` TEXT COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY `idx_nas_device_id` (`nas_device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='NAS设备状态记录表';

-- =====================================================
-- 6. 系统配置表
-- =====================================================
CREATE TABLE IF NOT EXISTS `system_config` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `config_key` VARCHAR(100) NOT NULL COMMENT '配置键',
    `config_value` VARCHAR(255) NOT NULL COMMENT '配置值',
    `description` VARCHAR(255) COMMENT '配置描述',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- =====================================================
-- 7. RADIUS服务器配置表
-- =====================================================
CREATE TABLE IF NOT EXISTS `radius_servers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `server_name` VARCHAR(100) NOT NULL COMMENT '服务器名称',
    `server_ip` VARCHAR(50) NOT NULL COMMENT '服务器IP地址',
    `auth_port` INT DEFAULT 1812 COMMENT '认证端口（默认1812）',
    `acct_port` INT DEFAULT 1813 COMMENT '计费端口（默认1813）',
    `secret` VARCHAR(255) NOT NULL COMMENT '共享密钥',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-正常，inactive-禁用',
    `description` TEXT COMMENT '描述',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS服务器配置表';

-- =====================================================
-- 8. RADIUS通信日志表
-- =====================================================
CREATE TABLE IF NOT EXISTS `radius_communication_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `nas_device_id` INT COMMENT 'NAS设备ID（可选）',
    `nas_ip` VARCHAR(50) COMMENT 'NAS IP地址',
    `nas_identifier` VARCHAR(100) COMMENT 'NAS标识符',
    `server_ip` VARCHAR(50) NOT NULL COMMENT 'RADIUS服务器IP',
    `port` INT NOT NULL COMMENT '端口号',
    `direction` VARCHAR(10) NOT NULL COMMENT '方向：request-请求，response-响应',
    `packet_type` VARCHAR(50) COMMENT '数据包类型：Access-Request, Access-Accept, Accounting-Request (Start), Accounting-Request (Stop)等',
    `username` VARCHAR(100) COMMENT '用户名',
    `session_id` VARCHAR(100) COMMENT '会话ID',
    `request_code` VARCHAR(20) COMMENT '请求码/响应码',
    `raw_data` TEXT COMMENT '原始数据包（十六进制）',
    `is_success` TINYINT(1) DEFAULT 1 COMMENT '是否成功',
    `error_message` TEXT COMMENT '错误信息（如有）',
    `response_time` INT COMMENT '响应时间（毫秒）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY `idx_nas_ip` (`nas_ip`),
    KEY `idx_username` (`username`),
    KEY `idx_packet_type` (`packet_type`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RADIUS通信日志表';

-- =====================================================
-- 9. 套餐表
-- =====================================================
CREATE TABLE IF NOT EXISTS `plans` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `price` VARCHAR(50) NOT NULL COMMENT '套餐费用',
    `upload_speed` INT NOT NULL COMMENT '上行速率（M）',
    `download_speed` INT NOT NULL COMMENT '下行速率（M）',
    `apartment_id` INT COMMENT '关联的公寓ID',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-正常，inactive-禁用',
    `description` TEXT COMMENT '套餐描述',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='套餐表';

-- =====================================================
-- 10. 网络用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS `network_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `apartment_id` INT NOT NULL COMMENT '所属公寓ID',
    `username` VARCHAR(100) NOT NULL COMMENT '上网账号',
    `password` VARCHAR(255) NOT NULL COMMENT '密码',
    `name` VARCHAR(100) COMMENT '姓名',
    `phone` VARCHAR(20) COMMENT '手机号',
    `room` VARCHAR(50) COMMENT '房间号',
    `plan_id` INT COMMENT '套餐ID',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-开通，inactive-停用',
    `activate_date` VARCHAR(10) COMMENT '开通日期',
    `expire_date` VARCHAR(10) COMMENT '到期日期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY `idx_apartment_id` (`apartment_id`),
    KEY `idx_username` (`username`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='网络用户表';

-- =====================================================
-- 11. 在线用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS `online_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `nas_device_id` INT COMMENT 'NAS设备ID',
    `nas_ip` VARCHAR(50) NOT NULL COMMENT 'NAS IP地址',
    `nas_identifier` VARCHAR(100) COMMENT 'NAS标识符',
    `server_ip` VARCHAR(50) NOT NULL COMMENT 'RADIUS服务器IP',
    `session_id` VARCHAR(100) NOT NULL COMMENT '会话ID（Acct-Session-Id）',
    `username` VARCHAR(100) NOT NULL COMMENT '用户名',
    `apartment_id` INT COMMENT '公寓ID',
    `room` VARCHAR(50) COMMENT '房间号',
    `framed_ip` VARCHAR(50) COMMENT '分配的IP地址',
    `calling_station_id` VARCHAR(50) COMMENT '用户MAC地址',
    `called_station_id` VARCHAR(100) COMMENT 'NAS端口标识',
    `start_time` DATETIME NOT NULL COMMENT '上线时间',
    `update_time` DATETIME NOT NULL COMMENT '最后更新时间',
    `input_octets` INT DEFAULT 0 COMMENT '上行流量（字节）',
    `output_octets` INT DEFAULT 0 COMMENT '下行流量（字节）',
    `input_packets` INT DEFAULT 0 COMMENT '上行包数',
    `output_packets` INT DEFAULT 0 COMMENT '下行包数',
    `session_time` INT DEFAULT 0 COMMENT '会话时长（秒）',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active-在线，stopped-已下线',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_session_id` (`session_id`),
    KEY `idx_username` (`username`),
    KEY `idx_nas_ip` (`nas_ip`),
    KEY `idx_apartment_id` (`apartment_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='在线用户表';

-- =====================================================
-- 12. 审计日志表
-- =====================================================
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `operator_id` INT COMMENT '操作员ID',
    `operator_name` VARCHAR(50) COMMENT '操作员用户名',
    `module` VARCHAR(50) NOT NULL COMMENT '操作模块',
    `action` VARCHAR(20) NOT NULL COMMENT '操作类型：CREATE-创建，UPDATE-更新，DELETE-删除',
    `target_type` VARCHAR(50) COMMENT '操作对象类型',
    `target_id` INT COMMENT '操作对象ID',
    `target_name` VARCHAR(255) COMMENT '操作对象名称',
    `description` TEXT COMMENT '操作描述',
    `old_data` TEXT COMMENT '操作前数据（JSON）',
    `new_data` TEXT COMMENT '操作后数据（JSON）',
    `ip_address` VARCHAR(50) COMMENT 'IP地址',
    `user_agent` VARCHAR(255) COMMENT '用户代理',
    `status` VARCHAR(20) DEFAULT 'success' COMMENT '状态：success-成功，failed-失败',
    `error_message` TEXT COMMENT '错误信息（如有）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY `idx_operator_id` (`operator_id`),
    KEY `idx_module` (`module`),
    KEY `idx_action` (`action`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志表';

-- =====================================================
-- 13. 故障报告表
-- =====================================================
CREATE TABLE IF NOT EXISTS `fault_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `username` VARCHAR(100) NOT NULL COMMENT '上网账号',
    `apartment_id` INT NOT NULL COMMENT '公寓ID',
    `apartment_name` VARCHAR(100) COMMENT '公寓名称',
    `room` VARCHAR(50) COMMENT '房间号',
    `fault_type` VARCHAR(50) NOT NULL COMMENT '故障类型：cannot_connect-不能上网，slow_network-网络卡顿，frequent_disconnect-频繁掉线',
    `description` TEXT COMMENT '故障描述',
    `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending-待处理，processing-处理中，resolved-已解决，closed-已关闭',
    `reporter_name` VARCHAR(100) COMMENT '报障人姓名',
    `reporter_phone` VARCHAR(20) COMMENT '报障人电话',
    `fault_time` DATETIME NOT NULL COMMENT '故障时间',
    `resolve_time` DATETIME COMMENT '解决时间',
    `resolve_description` TEXT COMMENT '处理说明',
    `operator_id` INT COMMENT '处理操作员ID',
    `operator_name` VARCHAR(50) COMMENT '处理操作员姓名',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    KEY `idx_user_id` (`user_id`),
    KEY `idx_apartment_id` (`apartment_id`),
    KEY `idx_fault_type` (`fault_type`),
    KEY `idx_status` (`status`),
    KEY `idx_fault_time` (`fault_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='故障报告表';

-- =====================================================
-- 初始化默认数据
-- =====================================================

-- 插入默认公寓
INSERT INTO `apartments` (`code`, `name`, `contact`, `phone`, `address`) VALUES
('APT001', '阳光公寓', '张三', '13800138000', '北京市朝阳区xxx');

-- 插入系统管理员 (密码: admin123)
-- bcrypt hash for 'admin123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfH4eMJ7y
INSERT INTO `operators` (`username`, `password_hash`, `name`, `role`) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfH4eMJ7y', '系统管理员', 'admin');

-- 将管理员关联到公寓
INSERT INTO `apartment_admins` (`operator_id`, `apartment_id`, `role`) VALUES
(1, 1, 'admin');

-- =====================================================
-- 完成
-- =====================================================
