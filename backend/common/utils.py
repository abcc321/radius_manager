from datetime import datetime, date
from typing import Optional, List, Any
from passlib.context import CryptContext
from sqlalchemy.orm import Query

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码加密"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证"""
    return pwd_context.verify(plain_password, hashed_password)


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """格式化日期时间"""
    if dt is None:
        return None
    return dt.strftime(fmt)


def format_date(d: Optional[date], fmt: str = "%Y-%m-%d") -> Optional[str]:
    """格式化日期"""
    if d is None:
        return None
    return d.strftime(fmt)


def parse_datetime(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """解析日期时间字符串"""
    try:
        return datetime.strptime(date_str, fmt)
    except:
        return None


def paginate_query(query: Query, page: int = 1, page_size: int = 20) -> tuple:
    """分页查询

    Args:
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        page_size: 每页大小

    Returns:
        (分页结果, 总数)
    """
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def model_to_dict(model: Any, exclude: List[str] = None) -> dict:
    """模型转字典

    Args:
        model: SQLAlchemy模型对象
        exclude: 排除的字段列表

    Returns:
        字典
    """
    if model is None:
        return {}

    if exclude is None:
        exclude = []

    result = {}
    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                result[column.name] = format_datetime(value)
            elif isinstance(value, date):
                result[column.name] = format_date(value)
            else:
                result[column.name] = value

    return result


def models_to_list(models: List[Any], exclude: List[str] = None) -> List[dict]:
    """模型列表转字典列表"""
    return [model_to_dict(model, exclude) for model in models]
