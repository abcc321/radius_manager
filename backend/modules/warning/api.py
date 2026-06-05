from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from common.database import get_db
from common.models import NetworkUser, OnlineUser, Apartment, Operator, ApartmentAdmin
from common.response import success, error
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/warnings", tags=["预警管理"])

executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="warning_")


async def run_in_thread(func, *args, **kwargs):
    """在独立线程中运行同步函数，避免阻塞事件循环"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(func, *args, **kwargs))


class ThresholdConfig(BaseModel):
    frequent_dial_threshold: int = 20


def get_operator_apartments(db: Session, operator_id: int):
    """获取操作员管理的公寓ID列表"""
    apartment_admins = db.query(ApartmentAdmin).filter(
        ApartmentAdmin.operator_id == operator_id
    ).all()
    return [admin.apartment_id for admin in apartment_admins]


def is_admin_or_operator(db: Session, operator_id: int):
    """检查是否为管理员或普通操作员"""
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        return False
    return operator.role == "admin"


def get_apartment_name(db: Session, apartment_id: int) -> str:
    """获取公寓名称"""
    if not apartment_id:
        return "未知公寓"
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    return apartment.name if apartment else "未知公寓"


@router.get("/inactive-users")
async def get_inactive_users(
    apartment_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取开通但未在线的用户列表
    这些用户状态是 active，但不在 online_users 表中
    """

    def _query_inactive_users():
        from sqlalchemy import cast, String

        # 处理字符集不一致问题：将两边的 username 和 apartment_id 都转为相同字符集
        # 关键：必须同时匹配 username 和 apartment_id，因为不同公寓可以有相同的用户名
        query = db.query(NetworkUser).filter(
            NetworkUser.status == 'active'
        ).outerjoin(
            OnlineUser,
            and_(
                cast(OnlineUser.username, String(255)) == cast(NetworkUser.username, String(255)),
                OnlineUser.apartment_id == NetworkUser.apartment_id,
                OnlineUser.status == 'active'
            )
        ).filter(
            OnlineUser.id.is_(None)
        )

        if operator_id:
            if not is_admin_or_operator(db, operator_id):
                operator_apartments = get_operator_apartments(db, operator_id)
                if not operator_apartments:
                    return 0, []
                query = query.filter(NetworkUser.apartment_id.in_(operator_apartments))

        if apartment_id:
            query = query.filter(NetworkUser.apartment_id == apartment_id)

        total = query.count()
        offset = (page - 1) * page_size
        users = query.order_by(NetworkUser.updated_at.desc()).offset(offset).limit(page_size).all()

        items = []
        for user in users:
            apartment_name = get_apartment_name(db, user.apartment_id)

            items.append({
                "id": user.id,
                "username": user.username,
                "name": user.name or "-",
                "phone": user.phone or "-",
                "room": user.room or "-",
                "apartment_id": user.apartment_id,
                "apartment_name": apartment_name,
                "plan_id": user.plan_id,
                "activate_date": user.activate_date or "-",
                "expire_date": user.expire_date or "-",
                "status": user.status,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else "-",
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else "-"
            })

        return total, items

    total, items = await run_in_thread(_query_inactive_users)

    return success({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    })


@router.get("/frequent-dialing")
async def get_frequent_dialing_users(
    threshold: int = 10,
    days: int = 1,
    apartment_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取频繁拨号的用户列表
    一天内拨号请求超过指定次数的用户
    默认阈值: 10次/天
    """

    def _query_frequent_dialing():
        from common.database import SessionLocal
        import pymysql

        db_config = {
            'host': '192.168.9.210',
            'port': 3306,
            'user': 'root',
            'password': 'Aa321321+',
            'database': 'radius_manager',
            'charset': 'utf8mb4'
        }

        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            try:
                time_threshold = datetime.now() - timedelta(days=days)

                sql = """
                    SELECT
                        username,
                        COUNT(*) as dial_count,
                        MAX(created_at) as last_dial_time,
                        MIN(created_at) as first_dial_time
                    FROM radius_communication_logs
                    WHERE packet_type = 'Access-Request'
                    AND created_at >= %s
                """

                params = [time_threshold]

                # 按公寓筛选用户
                if apartment_id:
                    users_query = db.query(NetworkUser.username).filter(
                        NetworkUser.apartment_id == apartment_id
                    ).all()
                    user_list = [u[0] for u in users_query]
                    if user_list:
                        placeholders = ','.join(['%s'] * len(user_list))
                        sql += f" AND username IN ({placeholders})"
                        params.extend(user_list)
                    else:
                        return 0, []

                if operator_id:
                    operator = db.query(Operator).filter(Operator.id == operator_id).first()
                    if operator and operator.role != "admin":
                        operator_apartments = get_operator_apartments(db, operator_id)
                        if operator_apartments:
                            users_query = db.query(NetworkUser.username).filter(
                                NetworkUser.apartment_id.in_(operator_apartments)
                            ).all()
                            user_list = [u[0] for u in users_query]
                            if user_list:
                                placeholders = ','.join(['%s'] * len(user_list))
                                sql += f" AND username IN ({placeholders})"
                                params.extend(user_list)
                            else:
                                return 0, []

                sql += """
                    GROUP BY username
                    HAVING COUNT(*) >= %s
                    ORDER BY dial_count DESC
                """

                params.append(threshold)

                sql += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"

                cursor.execute(sql, params)
                results = cursor.fetchall()

                count_sql = """
                    SELECT COUNT(DISTINCT username) as total
                    FROM radius_communication_logs
                    WHERE packet_type = 'Access-Request'
                    AND created_at >= %s
                """
                count_params = [time_threshold]

                # 按公寓筛选用户
                if apartment_id:
                    users_query = db.query(NetworkUser.username).filter(
                        NetworkUser.apartment_id == apartment_id
                    ).all()
                    user_list = [u[0] for u in users_query]
                    if user_list:
                        placeholders = ','.join(['%s'] * len(user_list))
                        count_sql += f" AND username IN ({placeholders})"
                        count_params.extend(user_list)
                    else:
                        return 0, []

                if operator_id:
                    operator = db.query(Operator).filter(Operator.id == operator_id).first()
                    if operator and operator.role != "admin":
                        operator_apartments = get_operator_apartments(db, operator_id)
                        if operator_apartments:
                            users_query = db.query(NetworkUser.username).filter(
                                NetworkUser.apartment_id.in_(operator_apartments)
                            ).all()
                            user_list = [u[0] for u in users_query]
                            if user_list:
                                placeholders = ','.join(['%s'] * len(user_list))
                                count_sql += f" AND username IN ({placeholders})"
                                count_params.extend(user_list)
                            else:
                                return 0, []

                count_sql += " GROUP BY username HAVING COUNT(*) >= %s"

                cursor.execute(count_sql, count_params + [threshold])
                total = len(cursor.fetchall())

                items = []
                for row in results:
                    user_info = db.query(NetworkUser).filter(
                        NetworkUser.username == row['username']
                    ).first()

                    apartment_name = "未知公寓"
                    if user_info and user_info.apartment_id:
                        apartment = db.query(Apartment).filter(
                            Apartment.id == user_info.apartment_id
                        ).first()
                        if apartment:
                            apartment_name = apartment.name

                    items.append({
                        "username": row['username'],
                        "dial_count": row['dial_count'],
                        "threshold": threshold,
                        "period_days": days,
                        "first_dial_time": row['first_dial_time'].strftime("%Y-%m-%d %H:%M:%S") if row['first_dial_time'] else "-",
                        "last_dial_time": row['last_dial_time'].strftime("%Y-%m-%d %H:%M:%S") if row['last_dial_time'] else "-",
                        "user_info": {
                            "name": user_info.name if user_info else "-",
                            "phone": user_info.phone if user_info else "-",
                            "room": user_info.room if user_info else "-",
                            "apartment_name": apartment_name,
                            "status": user_info.status if user_info else "unknown"
                        }
                    })

                return total, items

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"[WARNING API] Error querying frequent dialing users: {e}")
            return 0, []

    total, items = await run_in_thread(_query_frequent_dialing)

    return success({
        "total": total,
        "page": page,
        "page_size": page_size,
        "threshold": threshold,
        "days": days,
        "items": items
    })


@router.get("/statistics")
async def get_warning_statistics(
    apartment_id: Optional[int] = None,
    operator_id: Optional[int] = None,
    threshold: int = 10,
    days: int = 1,
    db: Session = Depends(get_db)
):
    """获取预警统计信息"""

    def _get_statistics():
        from sqlalchemy import cast, String

        inactive_count = 0
        frequent_dialing_count = 0

        # 关键：必须同时匹配 username 和 apartment_id，因为不同公寓可以有相同的用户名
        inactive_query = db.query(NetworkUser).filter(
            NetworkUser.status == 'active'
        ).outerjoin(
            OnlineUser,
            and_(
                cast(OnlineUser.username, String(255)) == cast(NetworkUser.username, String(255)),
                OnlineUser.apartment_id == NetworkUser.apartment_id,
                OnlineUser.status == 'active'
            )
        ).filter(
            OnlineUser.id.is_(None)
        )

        # 按公寓筛选
        if apartment_id:
            inactive_query = inactive_query.filter(NetworkUser.apartment_id == apartment_id)
        elif operator_id:
            if not is_admin_or_operator(db, operator_id):
                operator_apartments = get_operator_apartments(db, operator_id)
                if not operator_apartments:
                    return {
                        "inactive_users": 0,
                        "frequent_dialing_users": 0
                    }
                inactive_query = inactive_query.filter(NetworkUser.apartment_id.in_(operator_apartments))

        inactive_count = inactive_query.count()

        try:
            from common.database import SessionLocal
            import pymysql

            db_config = {
                'host': '192.168.9.210',
                'port': 3306,
                'user': 'root',
                'password': 'Aa321321+',
                'database': 'radius_manager',
                'charset': 'utf8mb4'
            }

            conn = pymysql.connect(**db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            try:
                time_threshold = datetime.now() - timedelta(days=days)

                sql = """
                    SELECT COUNT(DISTINCT username) as total
                    FROM radius_communication_logs
                    WHERE packet_type = 'Access-Request'
                    AND created_at >= %s
                """

                params = [time_threshold]

                if operator_id:
                    operator = db.query(Operator).filter(Operator.id == operator_id).first()
                    if operator and operator.role != "admin":
                        operator_apartments = get_operator_apartments(db, operator_id)
                        if operator_apartments:
                            users_query = db.query(NetworkUser.username).filter(
                                NetworkUser.apartment_id.in_(operator_apartments)
                            ).all()
                            user_list = [u[0] for u in users_query]
                            if user_list:
                                placeholders = ','.join(['%s'] * len(user_list))
                                sql += f" AND username IN ({placeholders})"
                                params.extend(user_list)
                            else:
                                frequent_dialing_count = 0
                                raise Exception("Skip")

                sql += " GROUP BY username HAVING COUNT(*) >= %s"

                cursor.execute(sql, params + [threshold])
                results = cursor.fetchall()
                frequent_dialing_count = len(results)

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            if "Skip" not in str(e):
                print(f"[WARNING API] Error getting frequent dialing count: {e}")

        return {
            "inactive_users": inactive_count,
            "frequent_dialing_users": frequent_dialing_count
        }

    stats = await run_in_thread(_get_statistics)

    return success(stats)
