import pymysql

conn = pymysql.connect(
    host='192.168.9.210',
    port=3306,
    user='root',
    password='Aa321321+',
    database='radius_manager',
    charset='utf8mb4'
)
cursor = conn.cursor(pymysql.cursors.DictCursor)

print("=" * 80)
print("【查询】青年公寓(status='active')的用户在 online_users 表中的情况")
print("=" * 80)

cursor.execute("""
    SELECT n.id, n.username, n.status, n.apartment_id
    FROM network_users n
    WHERE n.apartment_id = 12 AND n.status = 'active'
    ORDER BY n.username
""")
active_users = cursor.fetchall()

print(f"\n青年公寓开通用户数: {len(active_users)}")

for u in active_users:
    cursor.execute("""
        SELECT COUNT(*) as cnt, GROUP_CONCAT(status) as statuses
        FROM online_users
        WHERE username = %s AND apartment_id = %s AND status = 'active'
    """, (u['username'], u['apartment_id']))
    result = cursor.fetchone()
    if result['cnt'] > 0:
        online_status = f"在线 (有 {result['cnt']} 条 active 记录)"
    else:
        # 再查所有状态
        cursor.execute("""
            SELECT COUNT(*) as cnt, GROUP_CONCAT(status) as statuses
            FROM online_users
            WHERE username = %s AND apartment_id = %s
        """, (u['username'], u['apartment_id']))
        all_result = cursor.fetchone()
        if all_result['cnt'] > 0:
            online_status = f"不在线 (有 {all_result['cnt']} 条记录, 状态: {all_result['statuses']})"
        else:
            online_status = "不在线 (无记录)"
    print(f"  {u['username']}: {online_status}")

cursor.close()
conn.close()
