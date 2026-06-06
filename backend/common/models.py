from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from common.database import Base


class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")


class Apartment(BaseModel):
    """公寓表"""
    __tablename__ = "apartments"

    code = Column(String(50), unique=True, nullable=False, comment="公寓编号")
    name = Column(String(100), nullable=False, comment="公寓名称")
    contact = Column(String(50), comment="联系人")
    phone = Column(String(20), comment="联系电话")
    address = Column(String(255), comment="地址")
    status = Column(String(20), default="active", comment="状态：active-正常，inactive-禁用")
    nas_device_id = Column(Integer, nullable=True, comment="关联的NAS设备ID")


class Operator(BaseModel):
    """操作员表"""
    __tablename__ = "operators"

    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    name = Column(String(50), comment="姓名")
    role = Column(String(20), default="operator", comment="角色：admin-系统管理员，operator-普通操作员")
    status = Column(String(20), default="active", comment="状态：active-正常，inactive-禁用")


class ApartmentAdmin(BaseModel):
    """公寓管理员关联表"""
    __tablename__ = "apartment_admins"

    operator_id = Column(Integer, nullable=False, comment="操作员ID")
    apartment_id = Column(Integer, nullable=False, comment="公寓ID")
    role = Column(String(20), default="admin", comment="角色：admin-公寓管理员，operator-操作员")


class NasDevice(BaseModel):
    """NAS设备表"""
    __tablename__ = "nas_devices"

    name = Column(String(100), nullable=False, comment="设备名称")
    ip_address = Column(String(50), nullable=False, unique=True, comment="IP地址")
    mac_address = Column(String(17), comment="MAC地址")
    nas_identifier = Column(String(100), unique=True, comment="NAS标识符")
    device_type = Column(String(50), comment="设备类型（如：RouterOS, Cisco, H3C等）")
    community = Column(String(100), comment="SNMP团体名")
    secret = Column(String(255), nullable=False, comment="共享密钥")
    check_interval = Column(Integer, default=1, comment="检测间隔（分钟）")
    session_timeout = Column(Integer, default=15682168, comment="会话超时时间（秒）")
    acct_interim_interval = Column(Integer, default=60, comment="计费更新间隔（秒）")
    description = Column(Text, comment="设备描述")
    apartment_id = Column(Integer, nullable=True, comment="所属公寓ID")


class NasStatus(BaseModel):
    """NAS设备状态记录表"""
    __tablename__ = "nas_status"

    nas_device_id = Column(Integer, nullable=False, comment="NAS设备ID")
    status = Column(String(20), nullable=False, comment="状态：online-在线，offline-离线")
    response_time = Column(Integer, comment="响应时间（毫秒）")
    error_message = Column(Text, comment="错误信息")


class SystemConfig(BaseModel):
    """系统配置表"""
    __tablename__ = "system_config"

    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_value = Column(String(255), nullable=False, comment="配置值")
    description = Column(String(255), comment="配置描述")


class RadiusServer(BaseModel):
    """RADIUS服务器配置表"""
    __tablename__ = "radius_servers"

    server_name = Column(String(100), nullable=False, comment="服务器名称")
    server_ip = Column(String(50), nullable=False, comment="服务器IP地址")
    auth_port = Column(Integer, default=1812, comment="认证端口（默认1812）")
    acct_port = Column(Integer, default=1813, comment="计费端口（默认1813）")
    secret = Column(String(255), nullable=False, comment="共享密钥")
    status = Column(String(20), default="active", comment="状态：active-正常，inactive-禁用")
    description = Column(Text, comment="描述")


class RadiusCommunicationLog(BaseModel):
    """RADIUS通信日志表"""
    __tablename__ = "radius_communication_logs"

    nas_device_id = Column(Integer, nullable=True, comment="NAS设备ID（可选）")
    nas_ip = Column(String(50), comment="NAS IP地址")
    nas_identifier = Column(String(100), comment="NAS标识符")
    server_ip = Column(String(50), nullable=False, comment="RADIUS服务器IP")
    port = Column(Integer, nullable=False, comment="端口号")
    direction = Column(String(10), nullable=False, comment="方向：request-请求，response-响应")
    packet_type = Column(String(50), comment="数据包类型：Access-Request, Access-Accept, Access-Reject, Accounting-Request, Accounting-Response等")
    username = Column(String(100), comment="用户名")
    session_id = Column(String(100), comment="会话ID")
    request_code = Column(String(20), comment="请求码/响应码")
    raw_data = Column(Text, comment="原始数据包（十六进制）")
    is_success = Column(Boolean, default=True, comment="是否成功")
    error_message = Column(Text, comment="错误信息（如有）")
    response_time = Column(Integer, comment="响应时间（毫秒）")


class Plan(BaseModel):
    """套餐表"""
    __tablename__ = "plans"

    name = Column(String(100), nullable=False, comment="套餐名称")
    price = Column(String(50), nullable=False, comment="套餐费用")
    upload_speed = Column(Integer, nullable=False, comment="上行速率（M）")
    download_speed = Column(Integer, nullable=False, comment="下行速率（M）")
    apartment_id = Column(Integer, nullable=True, comment="关联的公寓ID")
    status = Column(String(20), default="active", comment="状态：active-正常，inactive-禁用")
    description = Column(Text, comment="套餐描述")


class NetworkUser(BaseModel):
    """网络用户表"""
    __tablename__ = "network_users"

    apartment_id = Column(Integer, nullable=False, comment="所属公寓ID")
    username = Column(String(100), nullable=False, comment="上网账号")
    password = Column(String(255), nullable=False, comment="密码")
    name = Column(String(100), comment="姓名")
    phone = Column(String(20), comment="手机号")
    room = Column(String(50), comment="房间号")
    plan_id = Column(Integer, nullable=True, comment="套餐ID")
    status = Column(String(20), default="active", comment="状态：active-开通，inactive-停用")
    activate_date = Column(String(10), comment="开通日期")
    expire_date = Column(String(10), comment="到期日期")


class OnlineUser(BaseModel):
    """在线用户表"""
    __tablename__ = "online_users"

    nas_device_id = Column(Integer, nullable=True, comment="NAS设备ID")
    nas_ip = Column(String(50), nullable=False, comment="NAS IP地址")
    nas_identifier = Column(String(100), comment="NAS标识符")
    server_ip = Column(String(50), nullable=False, comment="RADIUS服务器IP")
    session_id = Column(String(100), unique=True, nullable=False, comment="会话ID（Acct-Session-Id）")
    username = Column(String(100), nullable=False, comment="用户名")
    apartment_id = Column(Integer, nullable=True, comment="公寓ID")
    room = Column(String(50), comment="房间号")
    framed_ip = Column(String(50), comment="分配的IP地址")
    calling_station_id = Column(String(50), comment="用户MAC地址")
    called_station_id = Column(String(100), comment="NAS端口标识")
    start_time = Column(DateTime, nullable=False, comment="上线时间")
    update_time = Column(DateTime, nullable=False, comment="最后更新时间")
    input_octets = Column(Integer, default=0, comment="上行流量（字节）")
    output_octets = Column(Integer, default=0, comment="下行流量（字节）")
    input_packets = Column(Integer, default=0, comment="上行包数")
    output_packets = Column(Integer, default=0, comment="下行包数")
    session_time = Column(Integer, default=0, comment="会话时长（秒）")
    status = Column(String(20), default="active", comment="状态：active-在线，stopped-已下线")


class AuditLog(BaseModel):
    """审计日志表"""
    __tablename__ = "audit_logs"

    operator_id = Column(Integer, nullable=True, comment="操作员ID")
    operator_name = Column(String(50), comment="操作员用户名")
    module = Column(String(50), nullable=False, comment="操作模块")
    action = Column(String(20), nullable=False, comment="操作类型：CREATE-创建，UPDATE-更新，DELETE-删除")
    target_type = Column(String(50), comment="操作对象类型")
    target_id = Column(Integer, comment="操作对象ID")
    target_name = Column(String(255), comment="操作对象名称")
    description = Column(Text, comment="操作描述")
    old_data = Column(Text, comment="操作前数据（JSON）")
    new_data = Column(Text, comment="操作后数据（JSON）")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(255), comment="用户代理")
    status = Column(String(20), default="success", comment="状态：success-成功，failed-失败")
    error_message = Column(Text, comment="错误信息（如有）")


class FaultReport(BaseModel):
    """故障报告表"""
    __tablename__ = "fault_reports"

    user_id = Column(Integer, nullable=False, comment="用户ID")
    username = Column(String(100), nullable=False, comment="上网账号")
    apartment_id = Column(Integer, nullable=False, comment="公寓ID")
    apartment_name = Column(String(100), comment="公寓名称")
    room = Column(String(50), comment="房间号")
    fault_type = Column(String(50), nullable=False, comment="故障类型：cannot_connect-不能上网，slow_network-网络卡顿，frequent_disconnect-频繁掉线")
    description = Column(Text, comment="故障描述")
    status = Column(String(20), default="pending", comment="状态：pending-待处理，processing-处理中，resolved-已解决，closed-已关闭")
    reporter_name = Column(String(100), comment="报障人姓名")
    reporter_phone = Column(String(20), comment="报障人电话")
    fault_time = Column(DateTime, nullable=False, comment="故障时间")
    resolve_time = Column(DateTime, comment="解决时间")
    resolve_description = Column(Text, comment="处理说明")
    operator_id = Column(Integer, comment="处理操作员ID")
    operator_name = Column(String(50), comment="处理操作员姓名")
