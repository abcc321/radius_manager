from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from common.database import get_db
from common.models import OnlineUser, NasDevice, Apartment, Operator, ApartmentAdmin, NetworkUser
from common.response import success, error
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/online-users", tags=["在线用户管理"])

executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="online_user_")


async def run_in_thread(func, *args, **kwargs):
    """在独立线程中运行同步函数，避免阻塞事件循环"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(func, *args, **kwargs))


def get_apartment_name_sync(db: Session, apartment_id: int) -> str:
    """同步获取公寓名称"""
    if not apartment_id:
        return "未知公寓"
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    return apartment.name if apartment else "未知公寓"


def get_nas_name_sync(db: Session, nas_identifier: Optional[str], nas_ip: Optional[str]) -> str:
    """同步获取NAS名称"""
    if nas_identifier:
        nas_device = db.query(NasDevice).filter(
            NasDevice.nas_identifier == nas_identifier
        ).first()
        if nas_device:
            return nas_device.name
        if nas_ip:
            nas_device = db.query(NasDevice).filter(
                NasDevice.ip_address == nas_ip
            ).first()
            if nas_device:
                return nas_device.name
            return nas_ip
        return "未知NAS"
    elif nas_ip:
        nas_device = db.query(NasDevice).filter(
            NasDevice.ip_address == nas_ip
        ).first()
        if nas_device:
            return nas_device.name
        return nas_ip
    return "未知NAS"


def batch_get_apartment_names_sync(db: Session, apartment_ids: list) -> dict:
    """批量获取公寓名称"""
    if not apartment_ids:
        return {}
    apartments = db.query(Apartment.id, Apartment.name).filter(
        Apartment.id.in_(apartment_ids)
    ).all()
    return {apt.id: apt.name for apt in apartments}


def batch_get_nas_names_sync(db: Session, nas_data: list) -> dict:
    """批量获取NAS名称，nas_data是包含nas_identifier和nas_ip的字典列表"""
    result = {}
    identifiers = set()
    ips = set()

    for item in nas_data:
        if item.get('nas_identifier'):
            identifiers.add(item['nas_identifier'])
        if item.get('nas_ip'):
            ips.add(item['nas_ip'])

    nas_devices = db.query(NasDevice.nas_identifier, NasDevice.ip_address, NasDevice.name).all()
    nas_map = {}
    for dev in nas_devices:
        if dev.nas_identifier:
            nas_map[('identifier', dev.nas_identifier)] = dev.name
        if dev.ip_address:
            nas_map[('ip', dev.ip_address)] = dev.name

    for item in nas_data:
        key = ('identifier', item['nas_identifier']) if item.get('nas_identifier') else ('ip', item['nas_ip'])
        if key in nas_map:
            result[f"{item['nas_identifier']}:{item['nas_ip']}"] = nas_map[key]
        elif item.get('nas_ip'):
            result[f"{item['nas_identifier']}:{item['nas_ip']}"] = item['nas_ip']
        else:
            result[f"{item['nas_identifier']}:{item['nas_ip']}"] = "未知NAS"

    return result


def format_bytes(bytes_value):
    """格式化字节为可读单位"""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"


def format_seconds(seconds):
    """格式化秒为可读时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}小时{minutes}分{secs}秒"


class KickUserRequest(BaseModel):
    session_id: str
    reason: Optional[str] = "Admin kick"


def get_operator_apartments(db: Session, operator_id: int):
    """获取操作员管理的公寓ID列表"""
    apartment_admins = db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator_id
    ).all()
    return [admin.apartment_id for admin in apartment_admins]


def is_admin_or_operator(db: Session, operator_id: int):
    """检查是否为管理员（admin角色可以直接查看所有数据）"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        return False
    return operator.role == "admin"


@router.get("/list")
async def get_online_users(
    username: Optional[str] = None,
    apartment_id: Optional[int] = None,
    nas_ip: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    operator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    def _query_online_users():
        query = db.query(OnlineUser).filter(OnlineUser.status == "active")

        if operator_id:
            if not is_admin_or_operator(db, operator_id):
                operator_apartments = get_operator_apartments(db, operator_id)
                if not operator_apartments:
                    return 0, []
                query = query.filter(OnlineUser.apartment_id.in_(operator_apartments))

        if username:
            query = query.filter(OnlineUser.username.like(f"%{username}%"))
        if apartment_id:
            query = query.filter(OnlineUser.apartment_id == apartment_id)
        if nas_ip:
            query = query.filter(OnlineUser.nas_ip == nas_ip)

        total = query.count()
        offset = (page - 1) * page_size
        users = query.order_by(OnlineUser.start_time.desc()).offset(offset).limit(page_size).all()

        apartment_ids = list(set([u.apartment_id for u in users if u.apartment_id]))
        nas_data = [{'nas_identifier': u.nas_identifier, 'nas_ip': u.nas_ip} for u in users]

        apartment_names = batch_get_apartment_names_sync(db, apartment_ids)
        nas_names = batch_get_nas_names_sync(db, nas_data)

        items = []
        for user in users:
            apartment_name = apartment_names.get(user.apartment_id, "未知公寓") if user.apartment_id else "未知公寓"
            nas_key = f"{user.nas_identifier}:{user.nas_ip}"
            nas_name = nas_names.get(nas_key, user.nas_ip if user.nas_ip else "未知NAS")

            items.append({
                "id": user.id,
                "username": user.username,
                "nas_ip": user.nas_ip,
                "nas_identifier": user.nas_identifier,
                "nas_name": nas_name,
                "session_id": user.session_id,
                "apartment_id": user.apartment_id,
                "apartment_name": apartment_name,
                "room": user.room or "-",
                "framed_ip": user.framed_ip or "-",
                "calling_station_id": user.calling_station_id or "-",
                "start_time": user.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "online_duration": format_seconds(int((datetime.now() - user.start_time).total_seconds())),
                "online_duration_seconds": int((datetime.now() - user.start_time).total_seconds()),
                "input_octets": user.input_octets,
                "output_octets": user.output_octets,
                "input_formatted": format_bytes(user.input_octets),
                "output_formatted": format_bytes(user.output_octets),
                "total_traffic": format_bytes(user.input_octets + user.output_octets),
                "session_time": user.session_time,
                "session_time_formatted": format_seconds(user.session_time),
                "status": user.status
            })

        return total, items

    total, items = await run_in_thread(_query_online_users)

    return success({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })


@router.get("/statistics")
async def get_online_statistics(
    operator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    def _get_statistics():
        query = db.query(OnlineUser).filter(OnlineUser.status == "active")

        if operator_id:
            if not is_admin_or_operator(db, operator_id):
                operator_apartments = get_operator_apartments(db, operator_id)
                if not operator_apartments:
                    return {
                        "total_online": 0,
                        "total_apartments": 0,
                        "total_traffic": {
                            "input": 0,
                            "output": 0,
                            "input_formatted": "0 B",
                            "output_formatted": "0 B",
                            "total_formatted": "0 B"
                        }
                    }
                query = query.filter(OnlineUser.apartment_id.in_(operator_apartments))

        total_online = query.count()

        stats = db.query(
            func.sum(OnlineUser.input_octets).label('total_input'),
            func.sum(OnlineUser.output_octets).label('total_output')
        ).filter(OnlineUser.status == "active").first()

        total_input = stats.total_input or 0 if stats else 0
        total_output = stats.total_output or 0 if stats else 0

        if operator_id and not is_admin_or_operator(db, operator_id):
            operator_apartments = get_operator_apartments(db, operator_id)
            apartments_with_users = query.filter(
                OnlineUser.apartment_id.in_(operator_apartments)
            ).distinct().count()
        else:
            apartments_with_users = db.query(OnlineUser.apartment_id).filter(
                OnlineUser.status == "active"
            ).distinct().count()

        return {
            "total_online": total_online,
            "total_apartments": apartments_with_users,
            "total_traffic": {
                "input": total_input,
                "output": total_output,
                "input_formatted": format_bytes(total_input),
                "output_formatted": format_bytes(total_output),
                "total_formatted": format_bytes(total_input + total_output)
            }
        }

    stats = await run_in_thread(_get_statistics)
    return success(stats)


@router.get("/{session_id}")
async def get_user_detail(
    session_id: str,
    db: Session = Depends(get_db)
):
    def _get_user_detail_sync():
        user = db.query(OnlineUser).filter(OnlineUser.session_id == session_id).first()
        if not user:
            return None, "用户不存在或已下线"

        apartment_name = "未知公寓"
        if user.apartment_id:
            apartment = db.query(Apartment).filter(Apartment.id == user.apartment_id).first()
            if apartment:
                apartment_name = apartment.name

        nas_name = "未知NAS"
        nas_device = None
        if user.nas_identifier:
            nas_device = db.query(NasDevice).filter(
                NasDevice.nas_identifier == user.nas_identifier
            ).first()
        elif user.nas_ip:
            nas_device = db.query(NasDevice).filter(
                NasDevice.ip_address == user.nas_ip
            ).first()

        if nas_device:
            nas_name = nas_device.name
        elif user.nas_ip:
            nas_name = user.nas_ip

        network_user = db.query(NetworkUser).filter(
            NetworkUser.username == user.username
        ).first()

        return {
            "id": user.id,
            "username": user.username,
            "nas_ip": user.nas_ip,
            "nas_identifier": user.nas_identifier,
            "nas_name": nas_name,
            "session_id": user.session_id,
            "apartment_id": user.apartment_id,
            "apartment_name": apartment_name,
            "room": user.room or "-",
            "framed_ip": user.framed_ip or "-",
            "calling_station_id": user.calling_station_id or "-",
            "called_station_id": user.called_station_id or "-",
            "start_time": user.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": user.update_time.strftime("%Y-%m-%d %H:%M:%S"),
            "online_duration": format_seconds(int((datetime.now() - user.start_time).total_seconds())),
            "input_octets": user.input_octets,
            "output_octets": user.output_octets,
            "input_formatted": format_bytes(user.input_octets),
            "output_formatted": format_bytes(user.output_octets),
            "total_traffic": format_bytes(user.input_octets + user.output_octets),
            "session_time": user.session_time,
            "session_time_formatted": format_seconds(user.session_time),
            "status": user.status,
            "user_info": {
                "name": network_user.name if network_user else "-",
                "phone": network_user.phone if network_user else "-",
                "room": network_user.room if network_user else "-",
                "plan_id": network_user.plan_id if network_user else None
            } if network_user else None
        }, None

    result, error_msg = await run_in_thread(_get_user_detail_sync)

    if error_msg:
        return error(error_msg)

    return success(result)


@router.post("/kick")
async def kick_user(
    request: KickUserRequest,
    db: Session = Depends(get_db)
):
    def _kick_user_sync():
        user = db.query(OnlineUser).filter(
            OnlineUser.session_id == request.session_id,
            OnlineUser.status == "active"
        ).first()

        if not user:
            return {
                "success": False,
                "error": "用户不存在或已下线",
                "username": None,
                "session_id": None,
                "coa_success": False,
                "coa_message": ""
            }

        username = user.username
        nas_ip = user.nas_ip
        nas_identifier = user.nas_identifier
        session_id = user.session_id
        framed_ip = user.framed_ip

        coa_success = False
        coa_message = ""

        try:
            from radius_server import get_radius_server
            radius_server = get_radius_server()

            if radius_server and radius_server.is_running():
                secret = radius_server.secret

                if nas_identifier:
                    nas_device = radius_server.get_nas_device_by_identifier(nas_identifier)
                    if nas_device:
                        secret = nas_device['secret'].encode()
                elif nas_ip:
                    nas_device = radius_server.get_nas_device_by_ip(nas_ip)
                    if nas_device:
                        secret = nas_device['secret'].encode()

                coa_success = radius_server.create_disconnect_request(
                    username=username,
                    session_id=session_id,
                    secret=secret,
                    nas_ip=nas_ip,
                    framed_ip=framed_ip
                )

                if coa_success:
                    coa_message = " (CoA请求已发送)"
        except Exception as e:
            print(f"[KICK] CoA请求失败: {e}")
            coa_success = False

        if coa_success:
            user.status = "stopped"
            user.update_time = datetime.now()
            db.commit()
            print(f"[KICK] ✅ 用户 {username} 已踢出并更新状态")
        else:
            print(f"[KICK] ⚠️  CoA请求失败，不更新数据库状态")

        return {
            "success": True,
            "error": None,
            "username": username,
            "session_id": session_id,
            "coa_success": coa_success,
            "coa_message": coa_message if coa_success else " (CoA失败，用户可能未下线)"
        }

    result = await run_in_thread(_kick_user_sync)

    if not result["success"]:
        return error(result["error"])

    return success({
        "message": f"用户 {result['username']} 已踢出{result['coa_message']}",
        "session_id": result["session_id"],
        "username": result["username"],
        "coa_success": result["coa_success"]
    })
