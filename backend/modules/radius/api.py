from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import socket
import threading
import time

from common import get_db, RadiusServer, RadiusCommunicationLog, NasDevice, model_to_dict

router = APIRouter(prefix="/radius", tags=["RADIUS服务器管理"])


class PortStatus(BaseModel):
    port: int
    port_name: str
    is_listening: bool
    check_time: str


class LocalPortStatus(BaseModel):
    auth_port: PortStatus
    acct_port: PortStatus


class RadiusServerCreate(BaseModel):
    server_name: str
    server_ip: str
    auth_port: int = 1812
    acct_port: int = 1813
    secret: str
    status: str = "active"
    description: Optional[str] = None


class RadiusServerUpdate(BaseModel):
    server_name: Optional[str] = None
    server_ip: Optional[str] = None
    auth_port: Optional[int] = None
    acct_port: Optional[int] = None
    secret: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class RadiusLogCreate(BaseModel):
    nas_device_id: Optional[int] = None
    nas_ip: str
    server_ip: str
    port: int
    direction: str
    packet_type: str
    username: Optional[str] = None
    request_code: Optional[str] = None
    raw_data: Optional[str] = None
    is_success: bool = True
    error_message: Optional[str] = None
    response_time: Optional[int] = None


class RadiusLogQuery(BaseModel):
    nas_ip: Optional[str] = None
    direction: Optional[str] = None
    username: Optional[str] = None
    packet_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20


def check_local_port_listening(port: int, timeout: int = 2) -> bool:
    """检查本地端口是否在监听"""
    try:
        addresses = ['127.0.0.1', 'localhost']
        for addr in addresses:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((addr, port))
                sock.close()
                if result == 0:
                    return True
            except:
                continue
        return False
    except Exception as e:
        print(f"检查本地端口失败 {port} - {e}")
        return False


@router.get("/local-port-status", response_model=LocalPortStatus)
async def get_local_port_status():
    """
    获取本地RADIUS服务器端口状态
    检测本机(0.0.0.0/127.0.0.1)的1812(认证)和1813(计费)端口是否在监听
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    auth_listening = check_local_port_listening(1812)
    acct_listening = check_local_port_listening(1813)

    return {
        "auth_port": {
            "port": 1812,
            "port_name": "RADIUS认证端口",
            "is_listening": auth_listening,
            "check_time": now
        },
        "acct_port": {
            "port": 1813,
            "port_name": "RADIUS计费端口",
            "is_listening": acct_listening,
            "check_time": now
        }
    }


@router.post("/check-local-ports")
async def check_local_ports():
    """
    手动检测本地RADIUS服务器端口状态
    检测本机(0.0.0.0/127.0.0.1)的1812和1813端口
    """
    auth_listening = check_local_port_listening(1812)
    acct_listening = check_local_port_listening(1813)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "code": 200,
        "data": {
            "auth_port": {
                "port": 1812,
                "port_name": "RADIUS认证端口",
                "is_listening": auth_listening,
                "check_time": now
            },
            "acct_port": {
                "port": 1813,
                "port_name": "RADIUS计费端口",
                "is_listening": acct_listening,
                "check_time": now
            }
        }
    }


@router.get("/server-status")
async def get_server_status():
    """
    获取RADIUS服务器运行状态
    """
    from radius_server import get_radius_server

    radius_server = get_radius_server()
    is_running = radius_server and radius_server.is_running()

    return {
        "code": 200,
        "data": {
            "is_running": is_running,
            "host": radius_server.host if radius_server else "0.0.0.0",
            "auth_port": radius_server.auth_port if radius_server else 1812,
            "acct_port": radius_server.acct_port if radius_server else 1813
        }
    }


@router.get("/queue-status")
async def get_queue_status():
    """
    获取RADIUS服务器队列状态
    查看日志队列的大小和丢失统计
    """
    from radius_server import get_radius_server

    radius_server = get_radius_server()

    if not radius_server:
        return {
            "code": 404,
            "message": "RADIUS服务器未运行"
        }

    try:
        stats = radius_server.get_queue_stats()
        return {
            "code": 200,
            "data": stats
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取队列状态失败: {str(e)}"
        }


@router.get("/servers")
async def get_servers(db: Session = Depends(get_db)):
    """获取所有RADIUS服务器配置"""
    servers = db.query(RadiusServer).all()
    return {
        "code": 200,
        "data": [model_to_dict(server) for server in servers]
    }


@router.post("/servers")
async def create_server(server_data: RadiusServerCreate, db: Session = Depends(get_db)):
    """创建RADIUS服务器配置"""
    existing = db.query(RadiusServer).filter(
        RadiusServer.server_ip == server_data.server_ip
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该IP地址的服务器已存在")

    server = RadiusServer(**server_data.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)

    return {
        "code": 200,
        "message": "服务器创建成功",
        "data": model_to_dict(server)
    }


@router.put("/servers/{server_id}")
async def update_server(server_id: int, server_data: RadiusServerUpdate, db: Session = Depends(get_db)):
    """更新RADIUS服务器配置"""
    server = db.query(RadiusServer).filter(RadiusServer.id == server_id).first()

    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")

    for key, value in server_data.model_dump(exclude_unset=True).items():
        setattr(server, key, value)

    db.commit()
    db.refresh(server)

    return {
        "code": 200,
        "message": "服务器更新成功",
        "data": model_to_dict(server)
    }


@router.delete("/servers/{server_id}")
async def delete_server(server_id: int, db: Session = Depends(get_db)):
    """删除RADIUS服务器配置"""
    server = db.query(RadiusServer).filter(RadiusServer.id == server_id).first()

    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")

    db.delete(server)
    db.commit()

    return {
        "code": 200,
        "message": "服务器删除成功"
    }


@router.post("/logs")
async def create_log(log_data: RadiusLogCreate, db: Session = Depends(get_db)):
    """
    记录RADIUS通信日志
    记录NAS设备与RADIUS服务器之间的通信内容
    """
    try:
        log = RadiusCommunicationLog(
            nas_device_id=log_data.nas_device_id,
            nas_ip=log_data.nas_ip,
            server_ip=log_data.server_ip,
            port=log_data.port,
            direction=log_data.direction,
            packet_type=log_data.packet_type,
            username=log_data.username,
            request_code=log_data.request_code,
            raw_data=log_data.raw_data,
            is_success=log_data.is_success,
            error_message=log_data.error_message,
            response_time=log_data.response_time
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        return {
            "code": 200,
            "message": "日志记录成功",
            "data": model_to_dict(log)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"日志记录失败: {str(e)}")


@router.get("/logs")
async def get_logs(
    nas_ip: Optional[str] = None,
    direction: Optional[str] = None,
    username: Optional[str] = None,
    packet_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取RADIUS通信日志
    查询NAS设备与RADIUS服务器之间的通信记录
    """
    from common import NasDevice, Apartment

    query = db.query(RadiusCommunicationLog)

    if nas_ip:
        query = query.filter(RadiusCommunicationLog.nas_ip == nas_ip)
    if direction:
        query = query.filter(RadiusCommunicationLog.direction == direction)
    if username:
        query = query.filter(RadiusCommunicationLog.username.contains(username))
    if packet_type:
        # 根据行为类型筛选
        if packet_type == 'user_online':
            # 用户上线 - Access-Request
            query = query.filter(RadiusCommunicationLog.packet_type == 'Access-Request')
        elif packet_type == 'user_offline':
            # 用户下线 - Accounting-Request Stop
            query = query.filter(RadiusCommunicationLog.packet_type == 'Accounting-Request (Stop)')
    if start_date:
        query = query.filter(RadiusCommunicationLog.created_at >= start_date)
    if end_date:
        query = query.filter(RadiusCommunicationLog.created_at <= end_date)

    total = query.count()
    logs = query.order_by(RadiusCommunicationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    logs_with_apartment = []
    for log in logs:
        log_dict = model_to_dict(log)

        nas_device = None
        apartment_name = '未知设备'

        # 优先通过nas_identifier查找
        if log.nas_identifier:
            nas_device = db.query(NasDevice).filter(NasDevice.nas_identifier == log.nas_identifier).first()

        # 如果通过nas_identifier没找到，通过nas_ip查找
        if not nas_device and log.nas_ip:
            nas_device = db.query(NasDevice).filter(NasDevice.ip_address == log.nas_ip).first()

        if nas_device:
            if nas_device.apartment_id:
                apartment = db.query(Apartment).filter(Apartment.id == nas_device.apartment_id).first()
                if apartment:
                    apartment_name = apartment.name
                else:
                    apartment_name = '未分配公寓'
            else:
                apartment_name = '未分配公寓'
            log_dict['nas_name'] = nas_device.name
        else:
            log_dict['nas_name'] = log.nas_ip if log.nas_ip else '未知设备'
            apartment_name = '未注册设备'

        log_dict['apartment_name'] = apartment_name

        logs_with_apartment.append(log_dict)

    return {
        "code": 200,
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "logs": logs_with_apartment
        }
    }


@router.get("/logs/stats")
async def get_logs_stats(
    nas_ip: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取通信日志统计"""
    query = db.query(RadiusCommunicationLog)

    if nas_ip:
        query = query.filter(RadiusCommunicationLog.nas_ip == nas_ip)
    if start_date:
        query = query.filter(RadiusCommunicationLog.created_at >= start_date)
    if end_date:
        query = query.filter(RadiusCommunicationLog.created_at <= end_date)

    total = query.count()
    success_count = query.filter(RadiusCommunicationLog.is_success == True).count()
    fail_count = query.filter(RadiusCommunicationLog.is_success == False).count()
    request_count = query.filter(RadiusCommunicationLog.direction == "request").count()
    response_count = query.filter(RadiusCommunicationLog.direction == "response").count()

    return {
        "code": 200,
        "data": {
            "total": total,
            "success_count": success_count,
            "fail_count": fail_count,
            "request_count": request_count,
            "response_count": response_count
        }
    }


@router.get("/logs/export")
async def export_logs(
    nas_ip: Optional[str] = None,
    direction: Optional[str] = None,
    username: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """导出通信日志"""
    query = db.query(RadiusCommunicationLog)

    if nas_ip:
        query = query.filter(RadiusCommunicationLog.nas_ip == nas_ip)
    if direction:
        query = query.filter(RadiusCommunicationLog.direction == direction)
    if username:
        query = query.filter(RadiusCommunicationLog.username.contains(username))
    if start_date:
        query = query.filter(RadiusCommunicationLog.created_at >= start_date)
    if end_date:
        query = query.filter(RadiusCommunicationLog.created_at <= end_date)

    logs = query.order_by(RadiusCommunicationLog.created_at.desc()).all()

    export_data = []
    for log in logs:
        export_data.append({
            "时间": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            "NAS_IP": log.nas_ip or "",
            "服务器IP": log.server_ip or "",
            "端口": log.port or "",
            "方向": "请求" if log.direction == "request" else "响应",
            "数据包类型": log.packet_type or "",
            "用户名": log.username or "",
            "请求码": log.request_code or "",
            "状态": "成功" if log.is_success else "失败",
            "响应时间(ms)": log.response_time or "",
            "错误信息": log.error_message or "",
            "原始数据": log.raw_data or ""
        })

    return {
        "code": 200,
        "data": export_data
    }


@router.delete("/logs/{log_id}")
async def delete_log(log_id: int, db: Session = Depends(get_db)):
    """删除单条日志"""
    log = db.query(RadiusCommunicationLog).filter(RadiusCommunicationLog.id == log_id).first()

    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    db.delete(log)
    db.commit()

    return {
        "code": 200,
        "message": "日志删除成功"
    }


@router.delete("/logs")
async def clear_logs(
    nas_ip: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """清空通信日志"""
    query = db.query(RadiusCommunicationLog)

    if nas_ip:
        query = query.filter(RadiusCommunicationLog.nas_ip == nas_ip)
    if start_date:
        query = query.filter(RadiusCommunicationLog.created_at >= start_date)
    if end_date:
        query = query.filter(RadiusCommunicationLog.created_at <= end_date)

    count = query.delete()
    db.commit()

    return {
        "code": 200,
        "message": f"成功删除 {count} 条日志"
    }


@router.get("/logs/auth")
async def get_auth_logs(
    username: Optional[str] = None,
    nas_ip: Optional[str] = None,
    result: Optional[str] = None,
    error_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取认证日志"""
    import pymysql

    connection = pymysql.connect(
        host='192.168.9.210',
        user='root',
        password='Aa321321+',
        database='radius_manager',
        charset='utf8mb4'
    )

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            where_clauses = []
            params = []

            if username:
                where_clauses.append("username LIKE %s")
                params.append(f"%{username}%")
            if nas_ip:
                where_clauses.append("nas_ip = %s")
                params.append(nas_ip)
            if result:
                where_clauses.append("result = %s")
                params.append(result)
            if error_code:
                where_clauses.append("error_code = %s")
                params.append(error_code)
            if start_date:
                where_clauses.append("created_at >= %s")
                params.append(start_date)
            if end_date:
                where_clauses.append("created_at <= %s")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            cursor.execute(f"SELECT COUNT(*) as count FROM radius_auth_logs WHERE {where_sql}", params)
            total = cursor.fetchone()['count']

            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT * FROM radius_auth_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])

            logs = cursor.fetchall()

            for log in logs:
                if log['created_at']:
                    log['created_at'] = log['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            return {
                "code": 200,
                "data": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "logs": logs
                }
            }
    finally:
        connection.close()


@router.get("/logs/auth/stats")
async def get_auth_logs_stats(
    username: Optional[str] = None,
    nas_ip: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取认证日志统计"""
    import pymysql

    connection = pymysql.connect(
        host='192.168.9.210',
        user='root',
        password='Aa321321+',
        database='radius_manager',
        charset='utf8mb4'
    )

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            where_clauses = []
            params = []

            if username:
                where_clauses.append("username LIKE %s")
                params.append(f"%{username}%")
            if nas_ip:
                where_clauses.append("nas_ip = %s")
                params.append(nas_ip)
            if start_date:
                where_clauses.append("created_at >= %s")
                params.append(start_date)
            if end_date:
                where_clauses.append("created_at <= %s")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            cursor.execute(f"SELECT COUNT(*) as count FROM radius_auth_logs WHERE {where_sql}", params)
            total = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM radius_auth_logs WHERE {where_sql} AND result = 'success'", params)
            success_count = cursor.fetchone()['count']

            cursor.execute(f"SELECT COUNT(*) as count FROM radius_auth_logs WHERE {where_sql} AND result = 'rejected'", params)
            reject_count = cursor.fetchone()['count']

            return {
                "code": 200,
                "data": {
                    "total": total,
                    "success_count": success_count,
                    "reject_count": reject_count
                }
            }
    finally:
        connection.close()


@router.get("/logs/acct")
async def get_acct_logs(
    username: Optional[str] = None,
    nas_ip: Optional[str] = None,
    behavior_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取用户行为日志（只记录Start和Stop）"""
    import pymysql

    connection = pymysql.connect(
        host='192.168.9.210',
        user='root',
        password='Aa321321+',
        database='radius_manager',
        charset='utf8mb4'
    )

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            where_clauses = []
            params = []

            # 只查询Start和Stop报文
            where_clauses.append("packet_type IN ('Accounting-Request (Start)', 'Accounting-Request (Stop)')")

            if username:
                where_clauses.append("username LIKE %s")
                params.append(f"%{username}%")
            if nas_ip:
                where_clauses.append("nas_ip = %s")
                params.append(nas_ip)

            # 行为类型筛选
            if behavior_type == 'user_online':
                where_clauses.append("packet_type = 'Accounting-Request (Start)'")
            elif behavior_type == 'user_offline':
                where_clauses.append("packet_type = 'Accounting-Request (Stop)'")

            if start_date:
                where_clauses.append("created_at >= %s")
                params.append(start_date)
            if end_date:
                where_clauses.append("created_at <= %s")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses)

            cursor.execute(f"SELECT COUNT(*) as count FROM radius_communication_logs WHERE {where_sql}", params)
            total = cursor.fetchone()['count']

            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT 
                    id, created_at, nas_ip, username, packet_type, 
                    session_time, input_octets, output_octets, error_message
                FROM radius_communication_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])

            logs = cursor.fetchall()

            # 处理日志数据
            for log in logs:
                if log['created_at']:
                    log['created_at'] = log['created_at'].strftime("%Y-%m-%d %H:%M:%S")

            return {
                "code": 200,
                "data": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "logs": logs
                }
            }
    finally:
        connection.close()


@router.get("/logs/acct/stats")
async def get_acct_logs_stats(
    username: Optional[str] = None,
    nas_ip: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取计费日志统计"""
    import pymysql

    connection = pymysql.connect(
        host='192.168.9.210',
        user='root',
        password='Aa321321+',
        database='radius_manager',
        charset='utf8mb4'
    )

    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            where_clauses = []
            params = []

            if username:
                where_clauses.append("username LIKE %s")
                params.append(f"%{username}%")
            if nas_ip:
                where_clauses.append("nas_ip = %s")
                params.append(nas_ip)
            if start_date:
                where_clauses.append("created_at >= %s")
                params.append(start_date)
            if end_date:
                where_clauses.append("created_at <= %s")
                params.append(end_date)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 用户上线（Start报文）
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM radius_communication_logs
                WHERE {where_sql}
                AND packet_type = 'Accounting-Request (Start)'
            """, params)
            start_count = cursor.fetchone()['count']

            # 用户下线（Stop报文）
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM radius_communication_logs
                WHERE {where_sql}
                AND packet_type = 'Accounting-Request (Stop)'
            """, params)
            user_offline_count = cursor.fetchone()['count']

            return {
                "code": 200,
                "data": {
                    "start_count": start_count,
                    "user_offline_count": user_offline_count
                }
            }
    finally:
        connection.close()
