from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
    ]
)

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLdb库
pymysql.install_as_MySQLdb()

def ensure_database_exists():
    """确保数据库存在，如果不存在则创建"""
    try:
        # 先连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=config.db_address.split(':')[0],
            port=int(config.db_address.split(':')[1]) if ':' in config.db_address else 3306,
            user=config.username,
            password=config.password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute("CREATE DATABASE IF NOT EXISTS liuyan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ 数据库 liuyan 确保存在")
        
        connection.close()
        return True
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG
app.config['SECRET_KEY'] = 'liuyan-secret-key-2024'  # 添加secret key支持session和flash

# 确保数据库存在
if not ensure_database_exists():
    print("⚠️ 数据库创建失败，但继续启动...")

# 设定数据库链接 - 添加连接参数解决连接问题
database_uri = 'mysql://{}:{}@{}/liuyan?charset=utf8mb4&connect_timeout=60&read_timeout=60&write_timeout=60'.format(
    config.username, config.password, config.db_address
)
print(f"数据库连接URI: {database_uri}")
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 添加连接池配置
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # 连接前检查连接是否有效
    'pool_recycle': 300,    # 连接回收时间（5分钟）
    'pool_timeout': 20,     # 连接池获取连接的超时时间
    'max_overflow': 0,      # 连接池溢出大小
}

# 初始化DB操作对象
db = SQLAlchemy(app)

# 创建表
def create_tables():
    """创建数据库表"""
    try:
        with app.app_context():
            db.create_all()
            print("✅ 数据库表创建完成")
    except Exception as e:
        print(f"❌ 创建表失败: {e}")

# 注册Blueprint
from wxcloudrun.views import main_bp
app.register_blueprint(main_bp)
print("✅ Blueprint 注册完成")

# 注册模板全局函数
@app.template_global()
def get_post_details_for_template(post_id):
    """模板中获取内容详情的辅助函数"""
    from wxcloudrun.dao import get_post_with_details
    return get_post_with_details(post_id)

print("✅ 模板全局函数注册完成")

# 加载配置
app.config.from_object('config')

# 在应用启动时创建表
create_tables()
