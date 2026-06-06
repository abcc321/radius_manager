from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from common.database import get_db
from common.response import success, error
from common.models import FaultReport, NetworkUser, Apartment

router = APIRouter(prefix="/fault", tags=["故障管理"])


# Pydantic 模型
class FaultReportCreate(BaseModel):
    user_id: int
    fault_type: str
    description: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    fault_time: Optional[datetime] = None


class FaultReportUpdate(BaseModel):
    status: Optional[str] = None
    resolve_description: Optional[str] = None
    resolve_time: Optional[datetime] = None


class FaultReportResponse(BaseModel):
    id: int
    user_id: int
    username: str
    apartment_id: int
    apartment_name: Optional[str]
    room: Optional[str]
    fault_type: str
    fault_type_text: str
    description: Optional[str]
    status: str
    status_text: str
    reporter_name: Optional[str]
    reporter_phone: Optional[str]
    fault_time: datetime
    resolve_time: Optional[datetime]
    resolve_description: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 辅助函数
def get_fault_type_text(fault_type: str) -> str:
    type_map = {
        "cannot_connect": "不能上网",
        "slow_network": "网络卡顿",
        "frequent_disconnect": "频繁掉线"
    }
    return type_map.get(fault_type, fault_type)


def get_status_text(status: str) -> str:
    status_map = {
        "pending": "待处理",
        "processing": "处理中",
        "resolved": "已解决",
        "closed": "已关闭"
    }
    return status_map.get(status, status)


def format_fault_report(report: FaultReport) -> dict:
    """格式化故障报告数据"""
    return {
        "id": report.id,
        "user_id": report.user_id,
        "username": report.username,
        "apartment_id": report.apartment_id,
        "apartment_name": report.apartment_name,
        "room": report.room,
        "fault_type": report.fault_type,
        "fault_type_text": get_fault_type_text(report.fault_type),
        "description": report.description,
        "status": report.status,
        "status_text": get_status_text(report.status),
        "reporter_name": report.reporter_name,
        "reporter_phone": report.reporter_phone,
        "fault_time": report.fault_time,
        "resolve_time": report.resolve_time,
        "resolve_description": report.resolve_description,
        "operator_id": report.operator_id,
        "operator_name": report.operator_name,
        "created_at": report.created_at,
        "updated_at": report.updated_at
    }


@router.post("/reports")
def create_fault_report(
    data: FaultReportCreate,
    db: Session = Depends(get_db)
):
    """创建故障报告"""
    # 获取用户信息
    user = db.query(NetworkUser).filter(NetworkUser.id == data.user_id).first()
    if not user:
        return error(message="用户不存在")

    # 获取公寓信息
    apartment = db.query(Apartment).filter(Apartment.id == user.apartment_id).first()
    apartment_name = apartment.name if apartment else None

    # 创建故障报告
    fault_report = FaultReport(
        user_id=data.user_id,
        username=user.username,
        apartment_id=user.apartment_id,
        apartment_name=apartment_name,
        room=user.room,
        fault_type=data.fault_type,
        description=data.description,
        status="pending",
        reporter_name=data.reporter_name,
        reporter_phone=data.reporter_phone,
        fault_time=data.fault_time or datetime.now()
    )

    db.add(fault_report)
    db.commit()
    db.refresh(fault_report)

    return success(data=format_fault_report(fault_report), message="故障报告已提交")


@router.get("/reports")
def get_fault_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    fault_type: Optional[str] = None,
    apartment_id: Optional[int] = None,
    keyword: Optional[str] = None,
    exclude_status: Optional[str] = Query(None, description="排除的状态，多个用逗号分隔"),
    db: Session = Depends(get_db)
):
    """获取故障报告列表"""
    query = db.query(FaultReport)

    # 过滤条件
    if status:
        query = query.filter(FaultReport.status == status)

    # 如果指定了排除状态
    if exclude_status:
        exclude_list = [s.strip() for s in exclude_status.split(',')]
        query = query.filter(~FaultReport.status.in_(exclude_list))

    if fault_type:
        query = query.filter(FaultReport.fault_type == fault_type)

    if apartment_id:
        query = query.filter(FaultReport.apartment_id == apartment_id)

    if keyword:
        query = query.filter(
            (FaultReport.username.like(f"%{keyword}%")) |
            (FaultReport.reporter_name.like(f"%{keyword}%")) |
            (FaultReport.description.like(f"%{keyword}%"))
        )

    # 统计总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    reports = query.order_by(FaultReport.created_at.desc()).offset(offset).limit(page_size).all()

    # 格式化数据
    data = [format_fault_report(report) for report in reports]

    return {
        "code": 200,
        "data": data,
        "total": total
    }


@router.get("/reports/{report_id}")
def get_fault_report_detail(
    report_id: int,
    db: Session = Depends(get_db)
):
    """获取故障报告详情"""
    report = db.query(FaultReport).filter(FaultReport.id == report_id).first()

    if not report:
        return error(message="故障报告不存在")

    return success(data=format_fault_report(report))


@router.put("/reports/{report_id}")
def update_fault_report(
    report_id: int,
    data: FaultReportUpdate,
    db: Session = Depends(get_db)
):
    """更新故障报告状态"""
    report = db.query(FaultReport).filter(FaultReport.id == report_id).first()

    if not report:
        return error(message="故障报告不存在")

    # 更新字段
    if data.status is not None:
        report.status = data.status

    if data.resolve_description is not None:
        report.resolve_description = data.resolve_description

    if data.resolve_time is not None:
        report.resolve_time = data.resolve_time
    elif data.status in ["resolved", "closed"]:
        report.resolve_time = datetime.now()

    db.commit()
    db.refresh(report)

    return success(data=format_fault_report(report), message="更新成功")


@router.delete("/reports/{report_id}")
def delete_fault_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """删除故障报告"""
    report = db.query(FaultReport).filter(FaultReport.id == report_id).first()

    if not report:
        return error(message="故障报告不存在")

    db.delete(report)
    db.commit()

    return success(message="删除成功")


@router.get("/statistics")
def get_fault_statistics(
    db: Session = Depends(get_db)
):
    """获取故障统计"""
    query = db.query(FaultReport)

    total = query.count()
    pending = query.filter(FaultReport.status == "pending").count()
    processing = query.filter(FaultReport.status == "processing").count()
    resolved = query.filter(FaultReport.status == "resolved").count()
    closed = query.filter(FaultReport.status == "closed").count()

    # 按故障类型统计
    cannot_connect = query.filter(FaultReport.fault_type == "cannot_connect").count()
    slow_network = query.filter(FaultReport.fault_type == "slow_network").count()
    frequent_disconnect = query.filter(FaultReport.fault_type == "frequent_disconnect").count()

    return success(data={
        "total": total,
        "pending": pending,
        "processing": processing,
        "resolved": resolved,
        "closed": closed,
        "by_type": {
            "cannot_connect": cannot_connect,
            "slow_network": slow_network,
            "frequent_disconnect": frequent_disconnect
        }
    })
