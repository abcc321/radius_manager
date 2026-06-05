from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from common import get_db, Operator, Apartment, ApartmentAdmin, hash_password, verify_password, model_to_dict

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    apartments: list


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    operator = db.query(Operator).filter(Operator.username == request.username).first()

    if not operator:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(request.password, operator.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if operator.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")

    apartments = db.query(Apartment).join(
        ApartmentAdmin, Apartment.id == ApartmentAdmin.apartment_id
    ).filter(
        ApartmentAdmin.operator_id == operator.id
    ).all()

    apartments_data = [model_to_dict(apt, exclude=["created_at", "updated_at"]) for apt in apartments]

    return LoginResponse(
        id=operator.id,
        username=operator.username,
        name=operator.name or operator.username,
        role=operator.role,
        apartments=apartments_data
    )


@router.get("/apartments")
async def get_apartments(
    operator_id: int,
    db: Session = Depends(get_db)
):
    """获取操作员管理的公寓列表"""
    apartments = db.query(Apartment).join(
        ApartmentAdmin, Apartment.id == ApartmentAdmin.apartment_id
    ).filter(
        ApartmentAdmin.operator_id == operator_id
    ).all()

    return [model_to_dict(apt, exclude=["created_at", "updated_at"]) for apt in apartments]
