-- =====================================================
-- 迁移脚本：为 nas_devices 表添加 status 字段
-- 执行日期：2026-06-06
-- =====================================================

-- 为 nas_devices 表添加 status 字段
ALTER TABLE `nas_devices`
ADD COLUMN `status` VARCHAR(20) DEFAULT 'offline' COMMENT '设备状态：online-在线，offline-离线' AFTER `description`;

-- 验证字段添加成功
DESCRIBE `nas_devices`;
