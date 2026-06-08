"""
操作员认证依赖项
用于从请求中获取当前操作员信息，并记录到审计日志
"""
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from typing import Optional
from common import get_db, Operator


class OperatorInfo:
    """操作员信息类"""
    def __init__(self, operator_id: int, username: str, name: str, role: str, phone: str = None):
        self.operator_id = operator_id
        self.username = username
        self.name = name
        self.role = role
        self.phone = phone


async def get_current_operator(request: Request) -> OperatorInfo:
    """
    获取当前操作员信息

    操作员信息可以从以下几个地方获取（按优先级）：
    1. 请求参数 operator_id, operator_name（从localStorage传递）
    2. request.state 中的操作员信息（由中间件设置）
    3. 请求头 X-Operator-Id 等

    Returns:
        OperatorInfo: 操作员信息对象
    """
    operator_id = None
    username = None
    name = None
    role = None

    # 1. 优先从请求参数获取（从localStorage传递）
    operator_id = request.query_params.get("operator_id")
    if operator_id:
        try:
            operator_id = int(operator_id)
        except (ValueError, TypeError):
            operator_id = None

    name = request.query_params.get("operator_name")
    username = name

    # 2. 尝试从 request.state 获取
    if not operator_id:
        operator_id = getattr(request.state, 'operator_id', None)
    if not name:
        name = getattr(request.state, 'operator_name', None)
    if not username:
        username = getattr(request.state, 'operator_username', None)
    if not role:
        role = getattr(request.state, 'role', None)

    # 3. 尝试从请求头获取（备用方案）
    if not operator_id:
        operator_id = request.headers.get("X-Operator-Id")
        if operator_id:
            try:
                operator_id = int(operator_id)
            except (ValueError, TypeError):
                operator_id = None

    if not name:
        name = request.headers.get("X-Operator-Name")
    if not username:
        username = request.headers.get("X-Operator-Username")
    if not role:
        role = request.headers.get("X-Operator-Role")

    # 如果仍然无法获取操作员ID，返回默认的匿名操作员
    if not operator_id:
        return OperatorInfo(
            operator_id=0,
            username="system",
            name="系统",
            role="system"
        )

    return OperatorInfo(
        operator_id=operator_id,
        username=username or "unknown",
        name=name or username or "未知用户",
        role=role or "operator"
    )


async def get_current_operator_with_db(
    request: Request,
    db: Session = Depends(get_db)
) -> OperatorInfo:
    """
    获取当前操作员信息（带数据库验证）

    如果提供了 operator_id，会从数据库验证操作员是否存在

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        OperatorInfo: 操作员信息对象
    """
    operator_info = await get_current_operator(request)

    # 如果 operator_id 有效，尝试从数据库获取最新信息
    if operator_info.operator_id > 0:
        operator = db.query(Operator).filter(Operator.id == operator_info.operator_id).first()
        if operator:
            operator_info.username = operator.username
            operator_info.name = operator.name or operator.username
            operator_info.role = operator.role
            operator_info.phone = operator.phone

    return operator_info


def set_request_operator(request: Request, operator_info: OperatorInfo):
    """
    将操作员信息设置到 request.state 中

    这个函数可以在中间件中调用，以便在后续的请求处理中直接使用 request.state.operator_id

    Args:
        request: FastAPI 请求对象
        operator_info: 操作员信息对象
    """
    request.state.operator_id = operator_info.operator_id
    request.state.operator_name = operator_info.name
    request.state.operator_username = operator_info.username
    request.state.role = operator_info.role
