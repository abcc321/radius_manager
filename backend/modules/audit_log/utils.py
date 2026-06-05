"""
审计日志工具函数
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from common.models import AuditLog


def log_audit(
    db: Session,
    operator_id: int = None,
    operator_name: str = None,
    module: str = None,
    action: str = None,
    target_type: str = None,
    target_id: int = None,
    target_name: str = None,
    description: str = None,
    old_data: dict = None,
    new_data: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success",
    error_message: str = None
):
    """
    记录审计日志

    Args:
        db: 数据库会话
        operator_id: 操作员ID
        operator_name: 操作员用户名
        module: 操作模块（如：套餐管理、网络用户管理等）
        action: 操作类型（CREATE、UPDATE、DELETE）
        target_type: 操作对象类型（如：Plan、NetworkUser等）
        target_id: 操作对象ID
        target_name: 操作对象名称
        description: 操作描述
        old_data: 操作前的数据
        new_data: 操作后的数据
        ip_address: IP地址
        user_agent: 用户代理
        status: 状态（success、failed）
        error_message: 错误信息
    """
    try:
        audit_log = AuditLog(
            operator_id=operator_id,
            operator_name=operator_name,
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            description=description,
            old_data=json.dumps(old_data, ensure_ascii=False) if old_data else None,
            new_data=json.dumps(new_data, ensure_ascii=False) if new_data else None,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        db.add(audit_log)
        db.commit()
        return audit_log.id
    except Exception as e:
        # 如果记录日志失败，不应该影响主业务，所以只是打印错误
        print(f"记录审计日志失败: {str(e)}")
        db.rollback()
        return None
