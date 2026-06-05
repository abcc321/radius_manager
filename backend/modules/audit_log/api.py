"""
审计日志 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from common import get_db, AuditLog, model_to_dict

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


class AuditLogResponse(BaseModel):
    id: int
    operator_id: Optional[int]
    operator_name: Optional[str]
    module: str
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    target_name: Optional[str]
    description: Optional[str]
    old_data: Optional[str]
    new_data: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/")
async def get_audit_logs(
    module: Optional[str] = Query(None, description="模块筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    operator_name: Optional[str] = Query(None, description="操作员名称筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（目标名称/描述）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取审计日志列表"""
    query = db.query(AuditLog)

    # 模块筛选
    if module:
        query = query.filter(AuditLog.module == module)

    # 操作类型筛选
    if action:
        query = query.filter(AuditLog.action == action)

    # 操作员名称筛选
    if operator_name:
        query = query.filter(AuditLog.operator_name.contains(operator_name))

    # 关键词搜索
    if keyword:
        query = query.filter(
            (AuditLog.target_name.contains(keyword)) |
            (AuditLog.description.contains(keyword))
        )

    # 状态筛选
    if status:
        query = query.filter(AuditLog.status == status)

    # 日期范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end + timedelta(days=1)  # 包含结束日期
            query = query.filter(AuditLog.created_at < end)
        except ValueError:
            pass

    # 按时间倒序
    query = query.order_by(desc(AuditLog.created_at))

    # 获取总数
    total = query.count()

    # 分页
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "data": {
            "items": [model_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/modules")
async def get_modules(db: Session = Depends(get_db)):
    """获取所有模块列表"""
    modules = db.query(AuditLog.module).distinct().all()
    return {
        "code": 200,
        "data": [m[0] for m in modules if m[0]]
    }


@router.get("/actions")
async def get_actions():
    """获取所有操作类型"""
    return {
        "code": 200,
        "data": ["CREATE", "UPDATE", "DELETE"]
    }


@router.get("/statistics")
async def get_statistics(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取审计日志统计"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 按模块统计
    by_module = db.query(
        AuditLog.module,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.module).all()

    # 按操作类型统计
    by_action = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()

    # 按状态统计
    by_status = db.query(
        AuditLog.status,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.status).all()

    # 总数
    total = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= start_date
    ).scalar()

    return {
        "code": 200,
        "data": {
            "total": total,
            "by_module": {item[0]: item[1] for item in by_module},
            "by_action": {item[0]: item[1] for item in by_action},
            "by_status": {item[0]: item[1] for item in by_status}
        }
    }


@router.get("/{log_id}")
async def get_audit_log(log_id: int, db: Session = Depends(get_db)):
    """获取审计日志详情"""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

    if not log:
        return {
            "code": 404,
            "message": "日志记录不存在"
        }

    log_dict = model_to_dict(log)

    # 解析 JSON 数据
    if log_dict.get('old_data'):
        try:
            log_dict['old_data'] = json.loads(log_dict['old_data'])
        except:
            pass

    if log_dict.get('new_data'):
        try:
            log_dict['new_data'] = json.loads(log_dict['new_data'])
        except:
            pass

    return {
        "code": 200,
        "data": log_dict
    }


import json
