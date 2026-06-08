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
print("【查询1】network_users 表中状态不是 'active' 的用户")
print("=" * 80)

cursor.execute("""
    SELECT n.id, n.username, n.status as nw_status, n.apartment_id, a.name as apartment_name
    FROM network_users n
    LEFT JOIN apartments a ON n.apartment_id = a.id
    WHERE n.status != 'active'
    ORDER BY n.apartment_id, n.username
""")
inactive_users = cursor.fetchall()

if inactive_users:
    print(f"\n共找到 {len(inactive_users)} 个状态不是 'active' 的用户:\n")
    for u in inactive_users:
        print(f"  用户ID: {u['id']}, 用户名: {u['username']}, 状态: {u['nw_status']}, "
              f"公寓ID: {u['apartment_id']}, 公寓名: {u['apartment_name']}")
else:
    print("\n没有找到状态不是 'active' 的用户")

print("\n" + "=" * 80)
print("【查询2】每个公寓的开通用户数 (status='active') vs 总用户数")
print("=" * 80)

cursor.execute("""
    SELECT
        a.id as apartment_id,
        a.name as apartment_name,
        COUNT(n.id) as total_users,
        SUM(CASE WHEN n.status = 'active' THEN 1 ELSE 0 END) as active_users,
        SUM(CASE WHEN n.status != 'active' THEN 1 ELSE 0 END) as inactive_users
    FROM apartments a
    LEFT JOIN network_users n ON a.id = n.apartment_id
    GROUP BY a.id, a.name
    ORDER BY a.id
""")
apartments = cursor.fetchall()

print("\n公寓用户统计:")
for apt in apartments:
    print(f"  {apt['apartment_name']} (ID:{apt['apartment_id']}): "
          f"总用户={apt['total_users']}, 开通={apt['active_users']}, 未开通={apt['inactive_users']}")

print("\n" + "=" * 80)
print("【查询3】状态不是 'active' 的用户在 online_users 表中的情况")
print("=" * 80)

for u in inactive_users:
    cursor.execute("""
        SELECT COUNT(*) as cnt, GROUP_CONCAT(status) as statuses
        FROM online_users
        WHERE username = %s AND apartment_id = %s
    """, (u['username'], u['apartment_id']))
    result = cursor.fetchone()
    online_status = f"有 {result['cnt']} 条记录, 状态: {result['statuses']}" if result['cnt'] > 0 else "无记录"
    print(f"  {u['username']} (公寓:{u['apartment_name']}): {online_status}")

cursor.close()
conn.close()
