from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from common import get_db, Plan, Apartment, model_to_dict
from modules.audit_log.utils import log_audit

router = APIRouter(prefix="/plans", tags=["套餐管理"])


def check_admin_permission(request: Request):
    """检查是否为管理员"""
    role = getattr(request.state, 'role', None)
    if role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="权限不足，只有管理员才能执行此操作"
        )


class PlanCreate(BaseModel):
    name: str
    price: str
    upload_speed: int
    download_speed: int
    apartment_id: Optional[int] = None
    description: Optional[str] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None
    upload_speed: Optional[int] = None
    download_speed: Optional[int] = None
    apartment_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def get_plans(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    apartment_id: Optional[int] = Query(None, description="公寓ID筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_deleted: bool = Query(False, description="包含已删除的套餐"),
    db: Session = Depends(get_db)
):
    """获取套餐列表"""
    query = db.query(Plan)

    if not include_deleted:
        query = query.filter(Plan.status != "deleted")

    if keyword:
        query = query.filter(
            or_(
                Plan.name.contains(keyword),
                Plan.description.contains(keyword)
            )
        )

    if status:
        query = query.filter(Plan.status == status)

    if apartment_id:
        query = query.filter(Plan.apartment_id == apartment_id)

    total = query.count()
    plans = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for p in plans:
        plan_dict = model_to_dict(p)

        if p.apartment_id:
            apt = db.query(Apartment).filter(Apartment.id == p.apartment_id).first()
            if apt:
                plan_dict["apartment"] = model_to_dict(apt)
            else:
                plan_dict["apartment"] = None
        else:
            plan_dict["apartment"] = None

        result.append(plan_dict)

    return {
        "code": 200,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/all")
async def get_all_plans(
    status: Optional[str] = Query("active", description="状态筛选"),
    apartment_id: Optional[int] = Query(None, description="公寓ID筛选"),
    db: Session = Depends(get_db)
):
    """获取所有套餐（下拉框用）"""
    query = db.query(Plan)

    if status:
        query = query.filter(Plan.status == status)

    if apartment_id:
        query = query.filter(
            (Plan.apartment_id == apartment_id) | (Plan.apartment_id.is_(None))
        )

    plans = query.all()

    result = []
    for p in plans:
        plan_dict = model_to_dict(p)

        if p.apartment_id:
            apt = db.query(Apartment).filter(Apartment.id == p.apartment_id).first()
            if apt:
                plan_dict["apartment_name"] = apt.name
            else:
                plan_dict["apartment_name"] = None
        else:
            plan_dict["apartment_name"] = "通用套餐"

        result.append(plan_dict)

    return {
        "code": 200,
        "data": result
    }


@router.get("/{plan_id}")
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """获取套餐详情"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    plan_dict = model_to_dict(plan)

    if plan.apartment_id:
        apt = db.query(Apartment).filter(Apartment.id == plan.apartment_id).first()
        if apt:
            plan_dict["apartment"] = model_to_dict(apt)
        else:
            plan_dict["apartment"] = None
    else:
        plan_dict["apartment"] = None

    return {"code": 200, "data": plan_dict}


@router.post("/")
async def create_plan(plan_data: PlanCreate, request: Request, db: Session = Depends(get_db), _: None = Depends(check_admin_permission)):
    """创建套餐"""
    if plan_data.apartment_id:
        apt = db.query(Apartment).filter(Apartment.id == plan_data.apartment_id).first()
        if not apt:
            raise HTTPException(status_code=400, detail="公寓不存在")

    plan = Plan(
        name=plan_data.name,
        price=plan_data.price,
        upload_speed=plan_data.upload_speed,
        download_speed=plan_data.download_speed,
        apartment_id=plan_data.apartment_id,
        status="active",
        description=plan_data.description
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # 记录审计日志
    apartment_name = None
    if plan_data.apartment_id:
        apt = db.query(Apartment).filter(Apartment.id == plan_data.apartment_id).first()
        if apt:
            apartment_name = apt.name

    log_audit(
        db=db,
        operator_id=getattr(request.state, 'operator_id', None),
        operator_name=getattr(request.state, 'operator_name', None),
        module="套餐管理",
        action="CREATE",
        target_type="Plan",
        target_id=plan.id,
        target_name=plan.name,
        description=f"创建套餐：{plan.name}，价格：{plan.price}元/月，公寓：{apartment_name or '通用'}",
        new_data=model_to_dict(plan),
        ip_address=request.client.host if request.client else None,
        status="success"
    )

    return {
        "code": 200,
        "message": "创建成功",
        "data": model_to_dict(plan)
    }


@router.put("/{plan_id}")
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin_permission)
):
    """更新套餐"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    # 记录修改前的数据
    old_data = model_to_dict(plan)

    if plan_data.name is not None:
        plan.name = plan_data.name
    if plan_data.price is not None:
        plan.price = plan_data.price
    if plan_data.upload_speed is not None:
        plan.upload_speed = plan_data.upload_speed
    if plan_data.download_speed is not None:
        plan.download_speed = plan_data.download_speed
    if plan_data.apartment_id is not None:
        if plan_data.apartment_id > 0:
            apt = db.query(Apartment).filter(Apartment.id == plan_data.apartment_id).first()
            if not apt:
                raise HTTPException(status_code=400, detail="公寓不存在")
        plan.apartment_id = plan_data.apartment_id if plan_data.apartment_id > 0 else None
    if plan_data.status is not None:
        plan.status = plan_data.status
    if plan_data.description is not None:
        plan.description = plan_data.description

    db.commit()
    db.refresh(plan)

    # 记录审计日志
    log_audit(
        db=db,
        operator_id=getattr(request.state, 'operator_id', None),
        operator_name=getattr(request.state, 'operator_name', None),
        module="套餐管理",
        action="UPDATE",
        target_type="Plan",
        target_id=plan.id,
        target_name=plan.name,
        description=f"更新套餐：{plan.name}",
        old_data=old_data,
        new_data=model_to_dict(plan),
        ip_address=request.client.host if request.client else None,
        status="success"
    )

    return {
        "code": 200,
        "message": "更新成功",
        "data": model_to_dict(plan)
    }


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(check_admin_permission)):
    """删除套餐"""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")

    # 记录删除前的数据
    old_data = model_to_dict(plan)
    plan_name = plan.name

    db.delete(plan)
    db.commit()

    # 记录审计日志
    log_audit(
        db=db,
        operator_id=getattr(request.state, 'operator_id', None),
        operator_name=getattr(request.state, 'operator_name', None),
        module="套餐管理",
        action="DELETE",
        target_type="Plan",
        target_id=plan_id,
        target_name=plan_name,
        description=f"删除套餐：{plan_name}",
        old_data=old_data,
        ip_address=request.client.host if request.client else None,
        status="success"
    )

    return {"code": 200, "message": "删除成功"}
