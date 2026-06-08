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
print("查看 network_users 表结构")
print("=" * 80)

cursor.execute("DESCRIBE network_users")
columns = cursor.fetchall()
for col in columns:
    print(f"字段: {col['Field']}, 类型: {col['Type']}, 可空: {col['Null']}, 键: {col['Key']}, 默认: {col['Default']}")

print("\n" + "=" * 80)
print("查看 network_users 表的索引")
print("=" * 80)

cursor.execute("SHOW INDEX FROM network_users")
indexes = cursor.fetchall()
for idx in indexes:
    print(f"索引名: {idx['Key_name']}, 字段: {idx['Column_name']}, 唯一: {idx['Non_unique']}")

cursor.close()
conn.close()
