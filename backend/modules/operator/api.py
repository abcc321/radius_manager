from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional
from common import get_db, Operator, ApartmentAdmin, hash_password, verify_password, model_to_dict, models_to_list, get_current_operator_with_db, OperatorInfo

router = APIRouter(prefix="/operators", tags=["操作员管理"])


class OperatorCreate(BaseModel):
    username: str
    password: str
    name: str
    phone: Optional[str] = None
    role: str = "operator"
    apartment_ids: list[int] = []


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class OperatorAssign(BaseModel):
    apartment_ids: list[int]


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.get("/")
async def get_operators(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取操作员列表"""
    query = db.query(Operator)

    if keyword:
        query = query.filter(
            or_(
                Operator.username.contains(keyword),
                Operator.name.contains(keyword)
            )
        )

    if role:
        query = query.filter(Operator.role == role)

    if status:
        query = query.filter(Operator.status == status)

    total = query.count()
    operators = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for op in operators:
        op_dict = model_to_dict(op, exclude=["password_hash"])
        apartments = db.query(ApartmentAdmin).filter(
            ApartmentAdmin.operator_id == op.id
        ).all()
        op_dict["apartment_ids"] = [a.apartment_id for a in apartments]
        result.append(op_dict)

    return {
        "code": 200,
        "data": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/me")
async def get_current_operator_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取当前登录的操作员信息
    用于前端自动填充报障人等信息
    """
    operator_info = await get_current_operator_with_db(request, db)

    if operator_info.operator_id == 0:
        raise HTTPException(status_code=401, detail="未登录")

    # 获取完整的操作员信息
    operator = db.query(Operator).filter(Operator.id == operator_info.operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    op_dict = model_to_dict(operator, exclude=["password_hash"])
    apartments = db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator.id
    ).all()
    op_dict["apartment_ids"] = [a.apartment_id for a in apartments]

    return {"code": 200, "data": op_dict}


@router.get("/{operator_id}")
async def get_operator(operator_id: int, db: Session = Depends(get_db)):
    """获取操作员详情"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    op_dict = model_to_dict(operator, exclude=["password_hash"])
    apartments = db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator.id
    ).all()
    op_dict["apartment_ids"] = [a.apartment_id for a in apartments]

    return {"code": 200, "data": op_dict}


@router.post("/")
async def create_operator(operator_data: OperatorCreate, db: Session = Depends(get_db)):
    """创建操作员"""
    existing = db.query(Operator).filter(
        Operator.username == operator_data.username
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    operator = Operator(
        username=operator_data.username,
        password_hash=hash_password(operator_data.password),
        name=operator_data.name,
        phone=operator_data.phone,
        role=operator_data.role,
        status="active"
    )
    db.add(operator)
    db.flush()

    for apt_id in operator_data.apartment_ids:
        admin = ApartmentAdmin(
            operator_id=operator.id,
            apartment_id=apt_id,
            role="operator"
        )
        db.add(admin)

    db.commit()

    return {
        "code": 200,
        "message": "创建成功",
        "data": model_to_dict(operator, exclude=["password_hash"])
    }


@router.put("/{operator_id}")
async def update_operator(
    operator_id: int,
    operator_data: OperatorUpdate,
    db: Session = Depends(get_db)
):
    """更新操作员"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    if operator_data.name is not None:
        operator.name = operator_data.name
    if operator_data.phone is not None:
        operator.phone = operator_data.phone
    if operator_data.role is not None:
        operator.role = operator_data.role
    if operator_data.status is not None:
        operator.status = operator_data.status

    db.commit()

    return {
        "code": 200,
        "message": "更新成功",
        "data": model_to_dict(operator, exclude=["password_hash"])
    }


@router.delete("/{operator_id}")
async def delete_operator(operator_id: int, db: Session = Depends(get_db)):
    """删除操作员"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    if operator.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员")

    db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator_id
    ).delete()
    db.delete(operator)
    db.commit()

    return {"code": 200, "message": "删除成功"}


@router.put("/{operator_id}/password")
async def change_password(
    operator_id: int,
    password_data: PasswordChange,
    db: Session = Depends(get_db)
):
    """修改密码"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    if not verify_password(password_data.old_password, operator.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    operator.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"code": 200, "message": "密码修改成功"}


@router.put("/{operator_id}/apartments")
async def assign_apartments(
    operator_id: int,
    assign_data: OperatorAssign,
    db: Session = Depends(get_db)
):
    """分配操作员管理的公寓"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="操作员不存在")

    db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator_id
    ).delete()

    for apt_id in assign_data.apartment_ids:
        admin = ApartmentAdmin(
            operator_id=operator_id,
            apartment_id=apt_id,
            role="operator"
        )
        db.add(admin)

    db.commit()

    return {"code": 200, "message": "分配成功"}
