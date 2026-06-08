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
print("查询松子岭222用户的详细数据")
print("=" * 80)

cursor.execute("""
    SELECT id, username, name, phone, room, apartment_id, 
           status, expire_date, activate_date, created_at, updated_at
    FROM network_users
    WHERE username = '222' AND apartment_id = 13
""")
user = cursor.fetchone()

if user:
    print(f"\n用户ID: {user['id']}")
    print(f"用户名: {user['username']}")
    print(f"姓名: {user['name']}")
    print(f"电话: {user['phone']}")
    print(f"房间: {user['room']}")
    print(f"公寓ID: {user['apartment_id']}")
    print(f"数据库status字段: {user['status']}")
    print(f"开通日期(activate_date): {user['activate_date']}")
    print(f"到期日期(expire_date): {user['expire_date']}")
    print(f"创建时间: {user['created_at']}")
    print(f"更新时间: {user['updated_at']}")
    
    # 前端判断逻辑
    print("\n--- 前端判断逻辑 ---")
    if not user['expire_date']:
        print("前端显示: 未开通（因为没有expire_date）")
    else:
        from datetime import datetime
        now = datetime.now()
        expire = user['expire_date']
        if expire <= now:
            print(f"前端显示: 已过期（到期日期: {expire}）")
        else:
            print(f"前端显示: 已开通（到期日期: {expire}）")
else:
    print("未找到该用户")

cursor.close()
conn.close()
