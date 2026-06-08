import pymysql

conn = pymysql.connect(host='192.168.9.210', port=3306, user='root', password='Aa321321+', database='radius_manager')
cursor = conn.cursor(pymysql.cursors.DictCursor)

# 查询 network_users 表中松子岭公寓(status=active)的用户数
cursor.execute("SELECT COUNT(*) as cnt FROM network_users WHERE apartment_id=13 AND status='active'")
print("network_users表中松子岭(status=active)用户数:", cursor.fetchone()['cnt'])

# 查询 network_users 表中松子岭公寓的所有用户数
cursor.execute("SELECT COUNT(*) as cnt FROM network_users WHERE apartment_id=13")
print("network_users表中松子岭所有用户数:", cursor.fetchone()['cnt'])

# 查询 online_users 表中松子岭的用户数
cursor.execute("SELECT COUNT(*) as cnt FROM online_users WHERE apartment_id=13")
print("online_users表中松子岭用户数:", cursor.fetchone()['cnt'])

# 查看network_users表中松子岭的所有用户
cursor.execute("SELECT id, username, status, apartment_id FROM network_users WHERE apartment_id=13 LIMIT 10")
print("\nnetwork_users表中松子岭的用户:")
for row in cursor.fetchall():
    print(f"  id:{row['id']} username:{row['username']} status:{row['status']} apartment_id:{row['apartment_id']}")

# 查看online_users表中松子岭的用户
cursor.execute("SELECT id, username, apartment_id FROM online_users WHERE apartment_id=13 LIMIT 10")
print("\nonline_users表中松子岭的用户:")
for row in cursor.fetchall():
    print(f"  id:{row['id']} username:{row['username']} apartment_id:{row['apartment_id']}")

cursor.close()
conn.close()
