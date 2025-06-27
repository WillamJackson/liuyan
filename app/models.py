from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# 创建数据库实例
db = SQLAlchemy()

# 内容标签关联表
content_tags = db.Table('content_tags',
    db.Column('content_id', db.Integer, db.ForeignKey('contents.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# 内容媒体关联表
content_media = db.Table('content_media',
    db.Column('content_id', db.Integer, db.ForeignKey('contents.id'), primary_key=True),
    db.Column('media_file_id', db.Integer, db.ForeignKey('media_files.id'), primary_key=True),
    db.Column('sort_order', db.Integer, default=0),  # 排序字段
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    contents = db.relationship('Content', backref='author', lazy='dynamic')
    media_files = db.relationship('MediaFile', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    contents = db.relationship('Content', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Content(db.Model):
    """内容模型"""
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default='draft', index=True)  # draft, published, pending
    view_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)

    
    # 外键
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)
    
    # 关系
    tags = db.relationship('Tag', secondary=content_tags, lazy='subquery',
                          backref=db.backref('contents', lazy=True))
    media_files = db.relationship('MediaFile', secondary=content_media, lazy='subquery',
                                 backref=db.backref('contents', lazy=True))
    
    def publish(self):
        """发布内容"""
        self.status = 'published'
        self.published_at = datetime.utcnow()
    
    def unpublish(self):
        """取消发布"""
        self.status = 'draft'
        self.published_at = None
    
    @property
    def is_published(self):
        """是否已发布"""
        return self.status == 'published'
    
    def __repr__(self):
        return f'<Content {self.title}>'

class MediaFile(db.Model):
    """媒体文件模型"""
    __tablename__ = 'media_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # images, videos, documents, archives
    mime_type = db.Column(db.String(100), nullable=False)
    file_hash = db.Column(db.String(32), index=True)  # MD5哈希值，用于去重
    url = db.Column(db.String(500))  # 文件访问URL
    thumbnail_url = db.Column(db.String(500))  # 缩略图URL
    width = db.Column(db.Integer)  # 图片宽度
    height = db.Column(db.Integer)  # 图片高度
    alt_text = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_image(self):
        """是否为图片文件"""
        return self.file_type == 'images'
    
    @property
    def is_video(self):
        """是否为视频文件"""
        return self.file_type == 'videos'
    
    @property
    def is_document(self):
        """是否为文档文件"""
        return self.file_type == 'documents'
    
    @property
    def is_archive(self):
        """是否为压缩文件"""
        return self.file_type == 'archives'
    
    @property
    def size_human_readable(self):
        """人类可读的文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def __repr__(self):
        return f'<MediaFile {self.filename}>'

class SystemSettings(db.Model):
    """系统设置模型"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.key}>' 