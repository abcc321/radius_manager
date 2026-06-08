# 数据库工具脚本

本文档包含用于数据库调试、检查和维护的Python脚本。

## 目录结构

```
tools/
├── README.md                    # 本文件
├── database/
│   ├── check_db_schema.py      # 检查数据库表结构
│   ├── check_status.py         # 检查用户状态
│   └── update_operators_phone.py # 更新操作员手机号
└── debug/
    ├── check_songziling.py     # 调试：检查松子岭数据
    ├── check_active.py          # 调试：检查开通用户
    ├── check_expire.py          # 调试：检查到期用户
    ├── check_table.py           # 调试：检查表结构
    └── check_db.py             # 调试：检查数据库数据
```

## 脚本说明

### database/ - 数据库工具（长期使用）

#### check_db_schema.py
检查数据库中所有表的实际结构，包括字段、类型、注释等。
```bash
python tools/database/check_db_schema.py
```

#### check_status.py
检查network_users表中非active状态的用户，统计各公寓的用户情况。
```bash
python tools/database/check_status.py
```

#### update_operators_phone.py
为operators表添加phone字段（增量更新脚本）。
```bash
python tools/database/update_operators_phone.py
```

### debug/ - 调试脚本（临时使用）

这些脚本用于临时调试特定问题，使用完毕后可删除。

#### check_songziling.py
检查松子岭公寓的用户数据和在线状态。

#### check_active.py
检查青年公寓开通用户在在线表中的状态。

#### check_expire.py
检查特定用户的到期日期和状态。

#### check_table.py
检查数据库表结构和索引。

#### check_db.py
综合检查数据库中的用户数据。

## 注意事项

1. 所有脚本使用相同的数据库配置：
   - Host: 192.168.9.210
   - Port: 3306
   - User: root
   - Password: Aa321321+
   - Database: radius_manager

2. 调试脚本使用完毕后建议删除，避免混淆。

3. 如需修改数据库配置，直接编辑脚本中的配置部分。
