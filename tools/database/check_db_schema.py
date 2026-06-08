#!/usr/bin/env python3
"""
检查数据库中各表的实际结构
"""
import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': '192.168.9.210',
    'port': 3306,
    'user': 'root',
    'password': 'Aa321321+',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

# 表名列表
TABLES = [
    'apartments',
    'operators',
    'apartment_admins',
    'nas_devices',
    'nas_status',
    'system_config',
    'radius_servers',
    'radius_communication_logs',
    'plans',
    'network_users',
    'online_users',
    'audit_logs',
    'fault_reports'
]

def check_table_structure(db_name='radius_manager'):
    """检查表的结构"""
    conn = pymysql.connect(**DB_CONFIG, database=db_name)
    cursor = conn.cursor()

    print("=" * 80)
    print(f"数据库: {db_name}")
    print("=" * 80)

    for table_name in TABLES:
        print(f"\n{'-' * 60}")
        print(f"表名: {table_name}")
        print(f"{'-' * 60}")

        # 获取表结构
        cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
        columns = cursor.fetchall()

        if not columns:
            print("  (表不存在或没有字段)")
            continue

        print(f"  {'字段名':<25} {'类型':<25} {'空值':<6} {'键':<6} {'额外':<15} 注释")
        print(f"  {'-'*25} {'-'*25} {'-'*6} {'-'*6} {'-'*15} {'-'*40}")

        for col in columns:
            field = col.get('Field', '')
            col_type = col.get('Type', '')
            null = 'YES' if col.get('Null') == 'YES' else 'NO'
            key = col.get('Key', '')
            extra = col.get('Extra', '')
            comment = col.get('Comment', '')

            print(f"  {field:<25} {col_type:<25} {null:<6} {key:<6} {extra:<15} {comment}")

        # 获取表的注释
        cursor.execute(f"SELECT TABLE_COMMENT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{db_name}' AND TABLE_NAME = '{table_name}'")
        result = cursor.fetchone()
        if result:
            print(f"\n  表注释: {result['TABLE_COMMENT']}")

    cursor.close()
    conn.close()

def check_table_data_count():
    """检查各表的数据量"""
    conn = pymysql.connect(**DB_CONFIG, database='radius_manager')
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("各表数据量统计")
    print("=" * 80)

    for table_name in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM `{table_name}`")
            result = cursor.fetchone()
            count = result['cnt'] if result else 0
            print(f"  {table_name:<30}: {count} 条记录")
        except Exception as e:
            print(f"  {table_name:<30}: 错误 - {e}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    print("开始检查数据库结构...\n")
    check_table_structure()
    check_table_data_count()
    print("\n检查完成!")
