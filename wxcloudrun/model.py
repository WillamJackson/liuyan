from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# 用户表
class Users(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nickname = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(255))
    openid = db.Column(db.String(100), unique=True)
    unionid = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)


# 内容分类表
class Categories(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#667eea')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)


# 话题标签表
class Topics(db.Model):
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#667eea')
    use_count = db.Column(db.Integer, default=0)
    is_hot = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)


# 分享消息表
class Posts(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    # 链接相关字段
    link_url = db.Column(db.String(500))
    link_title = db.Column(db.String(200))
    link_description = db.Column(db.Text)
    link_favicon = db.Column(db.String(255))
    
    # 统计字段
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    
    # 状态字段
    status = db.Column(db.Enum('draft', 'published', 'hidden'), default='published')
    is_featured = db.Column(db.Boolean, default=False)
    is_top = db.Column(db.Boolean, default=False)
    
    # 时间字段
    published_at = db.Column(db.TIMESTAMP, default=datetime.now)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    category = db.relationship('Categories', backref='posts')
    media_files = db.relationship('MediaFiles', backref='post', cascade='all, delete-orphan')
    topics = db.relationship('Topics', secondary='post_topics', backref='posts')


# 媒体文件表
class MediaFiles(db.Model):
    __tablename__ = 'media_files'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.BigInteger, db.ForeignKey('posts.id'), nullable=False)
    media_type = db.Column(db.Enum('image', 'video', 'audio', 'document'), nullable=False)
    cloud_id = db.Column(db.String(500), nullable=False)  # 云存储ID
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.BigInteger, default=0)
    mime_type = db.Column(db.String(100))
    
    # 图片/视频特有字段（可选，系统自动获取）
    width = db.Column(db.Integer, default=0)
    height = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer, default=0)
    
    # 排序和状态
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('uploading', 'success', 'failed'), default='success')
    
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)


# 消息话题关联表
class PostTopics(db.Model):
    __tablename__ = 'post_topics'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.BigInteger, db.ForeignKey('posts.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    
    __table_args__ = (db.UniqueConstraint('post_id', 'topic_id'),)


# 评论表
class Comments(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.BigInteger, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'))
    parent_id = db.Column(db.BigInteger, db.ForeignKey('comments.id'))
    
    # 评论内容
    content = db.Column(db.Text, nullable=False)
    emoji = db.Column(db.String(10))
    
    # 用户信息(冗余存储)
    user_nickname = db.Column(db.String(50), nullable=False)
    user_avatar = db.Column(db.String(255))
    
    # 统计字段
    like_count = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)
    
    # 状态字段
    status = db.Column(db.Enum('normal', 'hidden', 'deleted'), default='normal')
    ip_address = db.Column(db.String(45))
    
    # 时间字段
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    post = db.relationship('Posts', backref='comments')
    user = db.relationship('Users', backref='comments')
    parent = db.relationship('Comments', remote_side=[id], backref='replies')


# 系统配置表
class SystemConfigs(db.Model):
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), nullable=False, unique=True)
    config_value = db.Column(db.Text)
    config_type = db.Column(db.Enum('string', 'number', 'boolean', 'json'), default='string')
    description = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.now)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now)
