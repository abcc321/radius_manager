from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from common import get_db, NasDevice, NasStatus, model_to_dict

router = APIRouter(prefix="/nas", tags=["NAS设备管理"])


class NasDeviceCreate(BaseModel):
    name: str
    ip_address: str
    mac_address: Optional[str] = None
    nas_identifier: Optional[str] = None
    device_type: Optional[str] = None
    community: Optional[str] = None
    secret: str
    check_interval: int = 1
    session_timeout: Optional[int] = None
    acct_interim_interval: Optional[int] = None
    description: Optional[str] = None
    apartment_id: Optional[int] = None


class NasDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    nas_identifier: Optional[str] = None
    device_type: Optional[str] = None
    community: Optional[str] = None
    secret: Optional[str] = None
    check_interval: Optional[int] = None
    session_timeout: Optional[int] = None
    acct_interim_interval: Optional[int] = None
    description: Optional[str] = None
    apartment_id: Optional[int] = None


@router.get("/")
async def get_nas_devices(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    apartment_id: Optional[int] = Query(None, description="公寓ID筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取NAS设备列表"""
    from common import Apartment
    query = db.query(NasDevice)

    if keyword:
        query = query.filter(
            or_(
                NasDevice.name.contains(keyword),
                NasDevice.ip_address.contains(keyword),
                NasDevice.device_type.contains(keyword)
            )
        )

    if apartment_id:
        query = query.filter(NasDevice.apartment_id == apartment_id)

    if status:
        from sqlalchemy import func
        latest_status_ids = db.query(
            func.max(NasStatus.id).label('id')
        ).group_by(NasStatus.nas_device_id).subquery()

        status_subquery = db.query(NasStatus).filter(
            NasStatus.id == latest_status_ids.c.id,
            NasStatus.status == status
        ).subquery()

        query = query.join(
            status_subquery,
            NasDevice.id == status_subquery.c.nas_device_id
        )

    total = query.count()
    devices = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for device in devices:
        device_dict = model_to_dict(device)

        last_status = db.query(NasStatus).filter(
            NasStatus.nas_device_id == device.id
        ).order_by(NasStatus.created_at.desc()).first()

        if last_status:
            device_dict["status"] = last_status.status
            device_dict["last_check"] = last_status.created_at.isoformat()
            device_dict["response_time"] = last_status.response_time
            device_dict["last_error"] = last_status.error_message
        else:
            device_dict["status"] = "unknown"
            device_dict["last_check"] = None
            device_dict["response_time"] = None
            device_dict["last_error"] = None

        if device.apartment_id:
            apartment = db.query(Apartment).filter(Apartment.id == device.apartment_id).first()
            if apartment:
                device_dict["apartment_name"] = apartment.name
                device_dict["apartment_code"] = apartment.code
            else:
                device_dict["apartment_name"] = None
                device_dict["apartment_code"] = None
        else:
            device_dict["apartment_name"] = None
            device_dict["apartment_code"] = None

        result.append(device_dict)

    return {
        "code": 200,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{device_id}")
async def get_nas_device(device_id: int, db: Session = Depends(get_db)):
    """获取NAS设备详情"""
    from common import Apartment
    device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="NAS设备不存在")

    device_dict = model_to_dict(device)

    last_status = db.query(NasStatus).filter(
        NasStatus.nas_device_id == device_id
    ).order_by(NasStatus.created_at.desc()).first()

    if last_status:
        device_dict["status"] = last_status.status
        device_dict["last_check"] = last_status.created_at.isoformat()
        device_dict["response_time"] = last_status.response_time
        device_dict["last_error"] = last_status.error_message
    else:
        device_dict["status"] = "unknown"
        device_dict["last_check"] = None
        device_dict["response_time"] = None
        device_dict["last_error"] = None

    if device.apartment_id:
        apartment = db.query(Apartment).filter(Apartment.id == device.apartment_id).first()
        if apartment:
            device_dict["apartment_name"] = apartment.name
            device_dict["apartment_code"] = apartment.code
        else:
            device_dict["apartment_name"] = None
            device_dict["apartment_code"] = None
    else:
        device_dict["apartment_name"] = None
        device_dict["apartment_code"] = None

    status_history = db.query(NasStatus).filter(
        NasStatus.nas_device_id == device_id
    ).order_by(NasStatus.created_at.desc()).limit(10).all()
    device_dict["status_history"] = [model_to_dict(s) for s in status_history]

    return {"code": 200, "data": device_dict}


@router.post("/")
async def create_nas_device(device_data: NasDeviceCreate, db: Session = Depends(get_db)):
    """创建NAS设备"""
    existing = db.query(NasDevice).filter(NasDevice.ip_address == device_data.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="IP地址已存在")

    if device_data.nas_identifier:
        existing_identifier = db.query(NasDevice).filter(
            NasDevice.nas_identifier == device_data.nas_identifier
        ).first()
        if existing_identifier:
            raise HTTPException(status_code=400, detail="NAS标识符已存在")

    device = NasDevice(
        name=device_data.name,
        ip_address=device_data.ip_address,
        mac_address=device_data.mac_address,
        nas_identifier=device_data.nas_identifier,
        device_type=device_data.device_type,
        community=device_data.community,
        secret=device_data.secret,
        check_interval=device_data.check_interval or 1,
        description=device_data.description,
        apartment_id=device_data.apartment_id
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "code": 200,
        "message": "创建成功",
        "data": model_to_dict(device)
    }


@router.put("/{device_id}")
async def update_nas_device(
    device_id: int,
    device_data: NasDeviceUpdate,
    db: Session = Depends(get_db)
):
    """更新NAS设备"""
    device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="NAS设备不存在")

    if device_data.nas_identifier is not None:
        if device_data.nas_identifier:
            existing_identifier = db.query(NasDevice).filter(
                NasDevice.nas_identifier == device_data.nas_identifier,
                NasDevice.id != device_id
            ).first()
            if existing_identifier:
                raise HTTPException(status_code=400, detail="NAS标识符已被其他设备使用")
        device.nas_identifier = device_data.nas_identifier

    if device_data.name is not None:
        device.name = device_data.name
    if device_data.ip_address is not None:
        device.ip_address = device_data.ip_address
    if device_data.mac_address is not None:
        device.mac_address = device_data.mac_address
    if device_data.device_type is not None:
        device.device_type = device_data.device_type
    if device_data.community is not None:
        device.community = device_data.community
    if device_data.secret is not None:
        device.secret = device_data.secret
    if device_data.check_interval is not None:
        device.check_interval = max(1, device_data.check_interval)
    if device_data.description is not None:
        device.description = device_data.description
    if device_data.apartment_id is not None:
        device.apartment_id = device_data.apartment_id

    db.commit()
    db.refresh(device)

    return {
        "code": 200,
        "message": "更新成功",
        "data": model_to_dict(device)
    }


@router.delete("/{device_id}")
async def delete_nas_device(device_id: int, db: Session = Depends(get_db)):
    """删除NAS设备"""
    device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="NAS设备不存在")

    db.delete(device)
    db.commit()

    return {"code": 200, "message": "删除成功"}


@router.post("/{device_id}/test")
async def test_nas_device(device_id: int, db: Session = Depends(get_db)):
    """测试NAS设备是否在线（通过Ping）"""
    import subprocess

    device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="NAS设备不存在")

    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '3000', device.ip_address],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )

        if result.returncode == 0:
            output = result.stdout.decode('gbk', errors='ignore')

            response_time = None
            for line in output.split('\n'):
                if '时间' in line or 'time' in line.lower():
                    try:
                        if '时间' in line:
                            time_str = line.split('时间=')[1].split('ms')[0]
                        else:
                            time_str = line.split('time=')[1].split('ms')[0]
                        response_time = int(time_str)
                        break
                    except:
                        pass

            if response_time is None:
                for line in output.split('\n'):
                    if 'TTL' in line or 'ttl' in line:
                        response_time = 0
                        break

            status = "online"
            error_message = None
        else:
            status = "offline"
            response_time = None
            error_message = "Ping failed"

    except subprocess.TimeoutExpired:
        status = "offline"
        response_time = None
        error_message = "Timeout"
    except Exception as e:
        status = "offline"
        response_time = None
        error_message = str(e)

    status_record = NasStatus(
        nas_device_id=device_id,
        status=status,
        response_time=response_time,
        error_message=error_message
    )
    db.add(status_record)
    db.commit()

    return {
        "code": 200,
        "message": "测试完成",
        "data": {
            "device_id": device_id,
            "ip_address": device.ip_address,
            "status": status,
            "response_time": response_time,
            "error_message": error_message
        }
    }


@router.get("/{device_id}/status")
async def get_nas_device_status(device_id: int, db: Session = Depends(get_db)):
    """获取NAS设备状态历史"""
    device = db.query(NasDevice).filter(NasDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="NAS设备不存在")

    status_records = db.query(NasStatus).filter(
        NasStatus.nas_device_id == device_id
    ).order_by(NasStatus.created_at.desc()).limit(100).all()

    return {
        "code": 200,
        "data": [model_to_dict(s) for s in status_records],
        "total": len(status_records)
    }
