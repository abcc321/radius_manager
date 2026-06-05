from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from common import get_db, Apartment, NasDevice, NasStatus, model_to_dict

router = APIRouter(prefix="/apartments", tags=["公寓管理"])


class ApartmentCreate(BaseModel):
    code: str
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    nas_device_id: Optional[int] = None


class ApartmentUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    nas_device_id: Optional[int] = None


@router.get("/")
async def get_apartments(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_deleted: bool = Query(False, description="包含已删除的公寓"),
    db: Session = Depends(get_db)
):
    """获取公寓列表"""
    query = db.query(Apartment)

    # 默认过滤掉已删除的公寓
    if not include_deleted:
        query = query.filter(Apartment.status != "deleted")

    if keyword:
        query = query.filter(
            or_(
                Apartment.code.contains(keyword),
                Apartment.name.contains(keyword),
                Apartment.address.contains(keyword)
            )
        )

    if status:
        query = query.filter(Apartment.status == status)

    total = query.count()
    apartments = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for apt in apartments:
        apt_dict = model_to_dict(apt)
        
        if apt.nas_device_id:
            nas = db.query(NasDevice).filter(NasDevice.id == apt.nas_device_id).first()
            if nas:
                apt_dict["nas_device"] = model_to_dict(nas, exclude=["secret"])
                last_status = db.query(NasStatus).filter(
                    NasStatus.nas_device_id == apt.nas_device_id
                ).order_by(NasStatus.created_at.desc()).first()
                apt_dict["nas_status"] = last_status.status if last_status else "unknown"
            else:
                apt_dict["nas_device"] = None
                apt_dict["nas_status"] = None
        else:
            apt_dict["nas_device"] = None
            apt_dict["nas_status"] = None
        
        result.append(apt_dict)

    return {
        "code": 200,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{apartment_id}")
async def get_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """获取公寓详情"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    apt_dict = model_to_dict(apartment)
    
    if apartment.nas_device_id:
        nas = db.query(NasDevice).filter(NasDevice.id == apartment.nas_device_id).first()
        if nas:
            apt_dict["nas_device"] = model_to_dict(nas, exclude=["secret"])
            last_status = db.query(NasStatus).filter(
                NasStatus.nas_device_id == apartment.nas_device_id
            ).order_by(NasStatus.created_at.desc()).first()
            apt_dict["nas_status"] = last_status.status if last_status else "unknown"
        else:
            apt_dict["nas_device"] = None
            apt_dict["nas_status"] = None
    else:
        apt_dict["nas_device"] = None
        apt_dict["nas_status"] = None

    return {"code": 200, "data": apt_dict}


@router.post("/")
async def create_apartment(apartment_data: ApartmentCreate, db: Session = Depends(get_db)):
    """创建公寓"""
    existing = db.query(Apartment).filter(Apartment.code == apartment_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="公寓编号已存在")

    if apartment_data.nas_device_id:
        nas = db.query(NasDevice).filter(NasDevice.id == apartment_data.nas_device_id).first()
        if not nas:
            raise HTTPException(status_code=400, detail="NAS设备不存在")

    apartment = Apartment(
        code=apartment_data.code,
        name=apartment_data.name,
        contact=apartment_data.contact,
        phone=apartment_data.phone,
        address=apartment_data.address,
        status="active",
        nas_device_id=apartment_data.nas_device_id
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)

    return {
        "code": 200,
        "message": "创建成功",
        "data": model_to_dict(apartment)
    }


@router.put("/{apartment_id}")
async def update_apartment(
    apartment_id: int,
    apartment_data: ApartmentUpdate,
    db: Session = Depends(get_db)
):
    """更新公寓"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    if apartment_data.name is not None:
        apartment.name = apartment_data.name
    if apartment_data.contact is not None:
        apartment.contact = apartment_data.contact
    if apartment_data.phone is not None:
        apartment.phone = apartment_data.phone
    if apartment_data.address is not None:
        apartment.address = apartment_data.address
    if apartment_data.status is not None:
        apartment.status = apartment_data.status
    if apartment_data.nas_device_id is not None:
        if apartment_data.nas_device_id > 0:
            nas = db.query(NasDevice).filter(NasDevice.id == apartment_data.nas_device_id).first()
            if not nas:
                raise HTTPException(status_code=400, detail="NAS设备不存在")
        apartment.nas_device_id = apartment_data.nas_device_id if apartment_data.nas_device_id > 0 else None

    db.commit()
    db.refresh(apartment)

    return {
        "code": 200,
        "message": "更新成功",
        "data": model_to_dict(apartment)
    }


@router.post("/{apartment_id}/disable")
async def disable_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """停用公寓"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    apartment.status = "inactive"
    db.commit()
    db.refresh(apartment)

    return {
        "code": 200,
        "message": "停用成功",
        "data": model_to_dict(apartment)
    }


@router.post("/{apartment_id}/enable")
async def enable_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """启用公寓"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    apartment.status = "active"
    db.commit()
    db.refresh(apartment)

    return {
        "code": 200,
        "message": "启用成功",
        "data": model_to_dict(apartment)
    }


@router.delete("/{apartment_id}")
async def delete_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """删除公寓"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    apartment.status = "deleted"
    db.commit()

    return {"code": 200, "message": "删除成功"}


@router.get("/{apartment_id}/stats")
async def get_apartment_stats(apartment_id: int, db: Session = Depends(get_db)):
    """获取公寓统计信息"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    stats = {
        "apartment_id": apartment_id,
        "apartment_code": apartment.code,
        "apartment_name": apartment.name
    }

    if apartment.nas_device_id:
        nas = db.query(NasDevice).filter(NasDevice.id == apartment.nas_device_id).first()
        if nas:
            stats["nas_status"] = nas.status
            stats["nas_last_heartbeat"] = model_to_dict(nas).get("last_heartbeat")
            
            online_count = db.query(OnlineUser).filter(
                OnlineUser.nas_device_id == apartment.nas_device_id,
                OnlineUser.status == "online"
            ).count()
            stats["online_user_count"] = online_count
            
            total_bytes = db.query(OnlineUser).filter(
                OnlineUser.nas_device_id == apartment.nas_device_id
            ).with_entities(
                db.query(OnlineUser.input_bytes).label("input"),
                db.query(OnlineUser.output_bytes).label("output")
            ).all()
            
            stats["total_input_bytes"] = sum([u.input_bytes or 0 for u in db.query(OnlineUser).filter(
                OnlineUser.nas_device_id == apartment.nas_device_id
            ).all()])
            stats["total_output_bytes"] = sum([u.output_bytes or 0 for u in db.query(OnlineUser).filter(
                OnlineUser.nas_device_id == apartment.nas_device_id
            ).all()])
        else:
            stats["nas_status"] = None
            stats["online_user_count"] = 0
            stats["total_input_bytes"] = 0
            stats["total_output_bytes"] = 0
    else:
        stats["nas_status"] = None
        stats["online_user_count"] = 0
        stats["total_input_bytes"] = 0
        stats["total_output_bytes"] = 0

    return {"code": 200, "data": stats}


@router.get("/{apartment_id}/online-users")
async def get_apartment_online_users(
    apartment_id: int,
    db: Session = Depends(get_db)
):
    """获取公寓在线用户列表"""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="公寓不存在")

    if not apartment.nas_device_id:
        return {"code": 200, "data": [], "total": 0}

    online_users = db.query(OnlineUser).filter(
        OnlineUser.nas_device_id == apartment.nas_device_id,
        OnlineUser.status == "online"
    ).all()

    result = []
    for user in online_users:
        user_dict = model_to_dict(user)
        user_dict["duration"] = (datetime.utcnow() - user.start_time).total_seconds()
        result.append(user_dict)

    return {"code": 200, "data": result, "total": len(result)}
