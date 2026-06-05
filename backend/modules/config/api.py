from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from common import get_db, SystemConfig, model_to_dict

router = APIRouter(prefix="/config", tags=["系统配置"])


class ConfigUpdate(BaseModel):
    config_key: str
    config_value: str


@router.get("/")
async def get_config(config_key: str, db: Session = Depends(get_db)):
    """获取指定配置"""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "code": 200,
        "data": model_to_dict(config)
    }


@router.get("/all")
async def get_all_configs(db: Session = Depends(get_db)):
    """获取所有配置"""
    configs = db.query(SystemConfig).all()

    result = {}
    for config in configs:
        result[config.config_key] = {
            "value": config.config_value,
            "description": config.description
        }

    return {
        "code": 200,
        "data": result
    }


@router.put("/")
async def update_config(config_data: ConfigUpdate, db: Session = Depends(get_db)):
    """更新配置"""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_data.config_key
    ).first()

    if not config:
        config = SystemConfig(
            config_key=config_data.config_key,
            config_value=config_data.config_value
        )
        db.add(config)
    else:
        config.config_value = config_data.config_value

    db.commit()
    db.refresh(config)

    return {
        "code": 200,
        "message": "配置更新成功",
        "data": model_to_dict(config)
    }


def get_check_interval(db: Session = None) -> int:
    """获取检测间隔（分钟）"""
    if db is None:
        from common.database import SessionLocal
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == "check_interval"
        ).first()

        if config:
            try:
                interval = int(config.config_value)
                return max(1, interval)  # 最小1分钟
            except ValueError:
                return 1
        else:
            return 1
    finally:
        if should_close:
            db.close()
