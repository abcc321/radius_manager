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

# 1. 查找松子岭公寓
cursor.execute("SELECT id, name FROM apartments WHERE name LIKE '%松子岭%'")
apartments = cursor.fetchall()
print("=== 公寓信息 ===")
for apt in apartments:
    print(f"  ID: {apt['id']}, Name: {apt['name']}")

apt_id = apartments[0]['id'] if apartments else 13

# 2. 查询 network_users 表中该公寓的所有用户
cursor.execute(f"SELECT id, username, status, apartment_id FROM network_users WHERE apartment_id={apt_id}")
nw_users = cursor.fetchall()
print(f"\n=== network_users 表中该公寓用户 (共 {len(nw_users)} 个) ===")
for u in nw_users:
    print(f"  username: {u['username']}, status: {u['status']}, apartment_id: {u['apartment_id']}")

# 3. 查询 online_users 表中该公寓的所有用户
cursor.execute(f"SELECT id, username, status, apartment_id FROM online_users WHERE apartment_id={apt_id}")
ou_users = cursor.fetchall()
print(f"\n=== online_users 表中该公寓用户 (共 {len(ou_users)} 个) ===")
for u in ou_users:
    print(f"  username: {u['username']}, status: {u.get('status', 'N/A')}, apartment_id: {u['apartment_id']}")

# 4. 测试当前的查询逻辑：network_users.status='active' 且不在 online_users 中
cursor.execute(f"""
    SELECT n.id, n.username, n.status, n.apartment_id
    FROM network_users n
    WHERE n.status = 'active'
    AND n.apartment_id = {apt_id}
    AND NOT EXISTS (
        SELECT 1 FROM online_users o
        WHERE o.username = n.username
        AND o.apartment_id = n.apartment_id
        AND o.status = 'active'
    )
""")
inactive_users = cursor.fetchall()
print(f"\n=== 未在线用户 (network_users.status='active' 且 online_users.status='active' 不存在) ===")
print(f"共 {len(inactive_users)} 个:")
for u in inactive_users:
    print(f"  username: {u['username']}, status: {u['status']}")

# 5. 查看所有公寓
cursor.execute("SELECT id, name FROM apartments")
all_apt = cursor.fetchall()
print(f"\n=== 所有公寓 ({len(all_apt)} 个) ===")
for apt in all_apt:
    print(f"  ID: {apt['id']}, Name: {apt['name']}")

cursor.close()
conn.close()
