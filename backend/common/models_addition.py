"""
账单记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timedelta
from common.database import Base


class BillRecord(Base):
    """账单记录表"""
    __tablename__ = "bill_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    bill_month = Column(String(7), nullable=False, comment="账单月份（格式：YYYY-MM）")
    apartment_id = Column(Integer, nullable=False, comment="公寓ID")
    apartment_name = Column(String(100), comment="公寓名称")
    apartment_code = Column(String(50), comment="公寓编号")

    total_accounts = Column(Integer, default=0, comment="总账号数")
    active_accounts = Column(Integer, default=0, comment="开通账号数")
    inactive_accounts = Column(Integer, default=0, comment="未开通账号数")
    total_amount = Column(String(50), default="0.00", comment="总费用")

    file_path = Column(String(500), nullable=False, comment="Excel文件路径")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")

    operator_id = Column(Integer, comment="操作员ID")
    operator_name = Column(String(100), comment="操作员姓名")

    status = Column(String(20), default="completed", comment="状态：generating-生成中，completed-已完成，failed-失败")
    error_message = Column(Text, comment="错误信息")
