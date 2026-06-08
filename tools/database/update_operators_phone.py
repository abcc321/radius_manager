#!/usr/bin/env python3
"""
更新数据库：为 operators 表添加 phone 字段
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '192.168.9.210',
    'port': 3306,
    'user': 'root',
    'password': 'Aa321321+',
    'charset': 'utf8mb4',
    'database': 'radius_manager'
}

def check_column_exists(cursor, db_name, table_name, column_name):
    """检查字段是否存在"""
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{db_name}'
        AND TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{column_name}'
    """)
    result = cursor.fetchone()
    return result[0] > 0

def add_phone_column(cursor):
    """添加 phone 字段"""
    try:
        cursor.execute("""
            ALTER TABLE `operators`
            ADD COLUMN `phone` VARCHAR(20) COMMENT '手机号' AFTER `name`
        """)
        print("✓ 成功为 operators 表添加 phone 字段")
        return True
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ phone 字段已存在，无需添加")
            return False
        else:
            print(f"✗ 添加字段失败: {e}")
            raise

def main():
    db_name = 'radius_manager'

    print("=" * 60)
    print("开始更新数据库...")
    print("=" * 60)

    # 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 检查字段是否存在
        if check_column_exists(cursor, db_name, 'operators', 'phone'):
            print("ℹ phone 字段已存在于 operators 表")
        else:
            # 添加字段
            add_phone_column(cursor)
            conn.commit()

        # 显示更新后的表结构
        print("\n更新后的 operators 表结构：")
        cursor.execute(f"SHOW FULL COLUMNS FROM `{db_name}`.`operators`")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<20} {col[1]:<25} {col[3]:<15} {col[8] if len(col) > 8 else ''}")

        print("\n" + "=" * 60)
        print("数据库更新完成！")
        print("=" * 60)

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
