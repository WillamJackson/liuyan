import os

# 是否开启debug模式 - 设置为最详细的调试级别
DEBUG = True

# 打印所有环境变量用于调试
print("=== 环境变量调试信息 ===")
for key, value in sorted(os.environ.items()):
    if any(keyword in key.upper() for keyword in ['MYSQL', 'DB', 'DATABASE']):
        print(f"  {key}: {repr(value)}")

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'Xx562137890')
db_address_env = os.environ.get("MYSQL_ADDRESS", '10.35.103.199:3306')

# 强制使用指定的数据库地址（如果环境变量被错误设置）
if 'sh-cynosdbmysql-grp-fm40bmoo' in db_address_env:
    print(f"⚠️  检测到错误的数据库地址: {db_address_env}")
    print("🔧 强制使用正确的数据库地址: 10.35.103.199:3306")
    db_address = '10.35.103.199:3306'
else:
    db_address = db_address_env

print(f"✅ 最终数据库配置:")
print(f"  用户名: {username}")
print(f"  密码: {password}")
print(f"  地址: {db_address}")
print("========================")
