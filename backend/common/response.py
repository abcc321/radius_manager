from typing import Any, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = 200
    message: str = "操作成功"
    data: Optional[Any] = None
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


def success(data: Any = None, message: str = "操作成功") -> dict:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data).dict(exclude_none=True)


def success_with_page(data: list, total: int, page: int, page_size: int, message: str = "获取成功") -> dict:
    """分页成功响应"""
    return ResponseModel(
        code=200,
        message=message,
        data=data,
        total=total,
        page=page,
        page_size=page_size
    ).dict(exclude_none=True)


def error(code: int = 400, message: str = "操作失败", data: Any = None) -> dict:
    """错误响应"""
    return ResponseModel(code=code, message=message, data=data).dict(exclude_none=True)


def not_found(message: str = "资源不存在") -> dict:
    """404响应"""
    return error(code=404, message=message)


def unauthorized(message: str = "未登录") -> dict:
    """401响应"""
    return error(code=401, message=message)


def forbidden(message: str = "权限不足") -> dict:
    """403响应"""
    return error(code=403, message=message)


def server_error(message: str = "服务器错误") -> dict:
    """500响应"""
    return error(code=500, message=message)
