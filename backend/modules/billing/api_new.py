"""
生成账单API
"""
from fastapi import APIRouter, Depends, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from common import get_db
from modules.billing.billing_service_new import BillingGenerateService

router = APIRouter(prefix="/billing", tags=["生成帐单"])


def get_operator_info(x_operator_id: Optional[str] = Header(None), x_operator_name: Optional[str] = Header(None)):
    """获取操作员信息"""
    operator_id = int(x_operator_id) if x_operator_id else None
    return {
        "operator_id": operator_id,
        "operator_name": x_operator_name
    }


@router.post("/generate/")
async def generate_bill(
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    apartment_id: int = Query(..., description="公寓ID"),
    db: Session = Depends(get_db),
    operator_info: dict = Depends(get_operator_info)
):
    """生成账单"""
    try:
        service = BillingGenerateService(db)
        result = service.generate_bill(
            apartment_id=apartment_id,
            year=year,
            month=month,
            operator_id=operator_info.get("operator_id"),
            operator_name=operator_info.get("operator_name")
        )

        return {
            "code": 200,
            "message": "账单生成成功",
            "data": result
        }
    except ValueError as e:
        return {
            "code": 400,
            "message": str(e)
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"生成失败: {str(e)}"
        }


@router.get("/records/")
async def get_bill_records(
    apartment_id: Optional[int] = Query(None, description="公寓ID"),
    bill_month: Optional[str] = Query(None, description="账单月份"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取账单记录列表"""
    service = BillingGenerateService(db)
    result = service.get_bill_records(
        apartment_id=apartment_id,
        bill_month=bill_month,
        page=page,
        page_size=page_size
    )

    return {
        "code": 200,
        "data": result["data"],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.get("/records/{record_id}/")
async def get_bill_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取账单记录详情"""
    service = BillingGenerateService(db)
    result = service.get_bill_record(record_id)

    if not result:
        return {
            "code": 404,
            "message": "账单记录不存在"
        }

    return {
        "code": 200,
        "data": result
    }


@router.get("/records/{record_id}/download/")
async def download_bill(
    record_id: int,
    db: Session = Depends(get_db)
):
    """下载账单文件"""
    service = BillingGenerateService(db)
    file_data = service.get_bill_file(record_id)

    if not file_data:
        return {
            "code": 404,
            "message": "文件不存在"
        }

    record = service.get_bill_record(record_id)
    filename = record["file_name"] if record else "bill.xlsx"

    return StreamingResponse(
        BytesIO(file_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
        }
    )


@router.get("/records/{record_id}/details/")
async def get_bill_details(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取账单明细"""
    service = BillingGenerateService(db)
    result = service.get_bill_details(record_id)

    if not result:
        return {
            "code": 404,
            "message": "账单记录不存在"
        }

    return {
        "code": 200,
        "data": result
    }


@router.delete("/records/{record_id}/")
async def delete_bill(
    record_id: int,
    db: Session = Depends(get_db)
):
    """删除账单"""
    service = BillingGenerateService(db)
    success = service.delete_bill(record_id)

    if not success:
        return {
            "code": 404,
            "message": "账单记录不存在"
        }

    return {
        "code": 200,
        "message": "账单删除成功"
    }


@router.get("/apartments/")
async def get_apartments(db: Session = Depends(get_db)):
    """获取公寓列表"""
    service = BillingGenerateService(db)
    apartments = service.get_all_apartments()

    return {
        "code": 200,
        "data": apartments
    }
