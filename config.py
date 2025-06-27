import os
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:Xx562137890@sh-cynosdbmysql-grp-fm40bmoo.sql.tencentcdb.com:29569/cms_db?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'},
        'videos': {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'},
        'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'},
        'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
    }
    
    # 图片处理配置
    THUMBNAIL_SIZE = (300, 300)  # 缩略图尺寸
    COMPRESS_QUALITY = 85  # 压缩质量 (1-100)
    
    # 媒体文件URL前缀
    MEDIA_URL_PREFIX = '/media'
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # 在生产环境中设置为True
    SESSION_COOKIE_HTTPONLY = True
    
    # 分页配置
    POSTS_PER_PAGE = 20
    
    # 邮件配置（可选）
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:Xx562137890@sh-cynosdbmysql-grp-fm40bmoo.sql.tencentcdb.com:29569/cms_db?charset=utf8mb4'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:Xx562137890@sh-cynosdbmysql-grp-fm40bmoo.sql.tencentcdb.com:29569/cms_db?charset=utf8mb4'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 