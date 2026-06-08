"""
审计日志工具函数
"""
from sqlalchemy.orm import Session
from common.models import AuditLog


def log_audit(
    db: Session,
    operator_id: int = None,
    operator_name: str = None,
    module: str = None,
    action: str = None,
    target_id: int = None,
    description: str = None,
    ip_address: str = None,
    status: str = "success",
    error_message: str = None
):
    """
    记录审计日志

    Args:
        db: 数据库会话
        operator_id: 操作员ID
        operator_name: 操作员用户名
        module: 操作模块（如：套餐管理、网络用户管理）
        action: 操作类型（CREATE、UPDATE、DELETE）
        target_id: 操作对象ID
        description: 操作描述（格式：【操作类型】模块 - 操作员: 数据内容）
        ip_address: IP地址
        status: 状态（success、failed）
        error_message: 错误信息
    """
    try:
        audit_log = AuditLog(
            operator_id=operator_id,
            operator_name=operator_name,
            module=module,
            action=action,
            target_id=target_id,
            description=description,
            ip_address=ip_address,
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
