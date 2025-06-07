import logging
from datetime import datetime
from sqlalchemy.exc import OperationalError
from sqlalchemy import desc, and_, or_

from wxcloudrun import db
from wxcloudrun.model import (
    Counters, Posts, Categories, Topics, MediaFiles, 
    PostTopics, Comments, SystemConfigs
)

# 初始化日志
logger = logging.getLogger('log')


# ==================== 原有的计数器相关方法 ====================
def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return Counters.query.filter(Counters.id == id).first()
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        counter = Counters.query.get(id)
        if counter is None:
            return
        db.session.delete(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.session.add(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        counter = query_counterbyid(counter.id)
        if counter is None:
            return
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_counterbyid errorMsg= {} ".format(e))


# ==================== 内容发布系统相关方法 ====================

# 分类相关
def get_all_categories():
    """获取所有启用的分类"""
    try:
        return Categories.query.filter(Categories.is_active == True).order_by(Categories.sort_order).all()
    except OperationalError as e:
        logger.error("get_all_categories errorMsg= {} ".format(e))
        return []


def get_category_by_id(category_id):
    """根据ID获取分类"""
    try:
        return Categories.query.get(category_id)
    except OperationalError as e:
        logger.error("get_category_by_id errorMsg= {} ".format(e))
        return None


# 话题相关
def get_all_topics():
    """获取所有话题"""
    try:
        return Topics.query.order_by(desc(Topics.use_count), Topics.name).all()
    except OperationalError as e:
        logger.error("get_all_topics errorMsg= {} ".format(e))
        return []


def get_hot_topics():
    """获取热门话题"""
    try:
        return Topics.query.filter(Topics.is_hot == True).order_by(desc(Topics.use_count)).all()
    except OperationalError as e:
        logger.error("get_hot_topics errorMsg= {} ".format(e))
        return []


def get_or_create_topic(topic_name):
    """获取或创建话题"""
    try:
        topic = Topics.query.filter(Topics.name == topic_name).first()
        if not topic:
            topic = Topics(name=topic_name)
            db.session.add(topic)
            db.session.commit()
        return topic
    except OperationalError as e:
        logger.error("get_or_create_topic errorMsg= {} ".format(e))
        return None


# 内容相关
def create_post(post_data):
    """创建新的内容"""
    try:
        logger.info(f"Creating post with data: {post_data}")
        
        post = Posts(
            title=post_data.get('title'),
            content=post_data.get('content'),
            category_id=post_data.get('category_id'),
            link_url=post_data.get('link_url'),
            link_title=post_data.get('link_title'),
            link_description=post_data.get('link_description'),
            link_favicon=post_data.get('link_favicon'),
            status=post_data.get('status', 'published'),
            is_featured=post_data.get('is_featured', False),
            is_top=post_data.get('is_top', False)
        )
        
        db.session.add(post)
        db.session.flush()  # 获取post.id
        logger.info(f"Post created with ID: {post.id}")
        
        # 处理话题标签
        topics = post_data.get('topics', [])
        for topic_name in topics:
            if topic_name.strip():
                topic = get_or_create_topic(topic_name.strip())
                if topic:
                    post_topic = PostTopics(post_id=post.id, topic_id=topic.id)
                    db.session.add(post_topic)
        
        # 处理媒体文件
        media_files = post_data.get('media_files', [])
        logger.info(f"Processing {len(media_files)} media files")
        
        for i, media_data in enumerate(media_files):
            logger.info(f"Processing media file {i}: {media_data}")
            
            # 验证必要字段
            if not media_data.get('cloud_id'):
                logger.warning(f"Media file {i} missing cloud_id, skipping")
                continue
                
            media_file = MediaFiles(
                post_id=post.id,
                media_type=media_data.get('media_type', 'document'),
                cloud_id=media_data.get('cloud_id'),
                file_name=media_data.get('file_name', ''),
                file_size=media_data.get('file_size', 0),
                mime_type=media_data.get('mime_type', ''),
                width=media_data.get('width', 0),
                height=media_data.get('height', 0),
                duration=media_data.get('duration', 0),
                sort_order=i
            )
            db.session.add(media_file)
        
        db.session.commit()
        logger.info(f"Post {post.id} created successfully")
        return post
        
    except Exception as e:
        logger.error(f"create_post error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        db.session.rollback()
        return None


def get_posts_list(page=1, per_page=10, category_id=None, status='published'):
    """获取内容列表"""
    try:
        query = Posts.query
        
        if status:
            query = query.filter(Posts.status == status)
        
        if category_id:
            query = query.filter(Posts.category_id == category_id)
        
        # 按置顶和发布时间排序
        query = query.order_by(desc(Posts.is_top), desc(Posts.published_at))
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return pagination
    except OperationalError as e:
        logger.error("get_posts_list errorMsg= {} ".format(e))
        return None


def get_post_by_id(post_id):
    """根据ID获取内容详情"""
    try:
        return Posts.query.get(post_id)
    except OperationalError as e:
        logger.error("get_post_by_id errorMsg= {} ".format(e))
        return None


def update_post(post_id, post_data):
    """更新内容"""
    try:
        post = Posts.query.get(post_id)
        if not post:
            return None
        
        # 更新基本信息
        post.title = post_data.get('title', post.title)
        post.content = post_data.get('content', post.content)
        post.category_id = post_data.get('category_id', post.category_id)
        post.link_url = post_data.get('link_url', post.link_url)
        post.link_title = post_data.get('link_title', post.link_title)
        post.link_description = post_data.get('link_description', post.link_description)
        post.link_favicon = post_data.get('link_favicon', post.link_favicon)
        post.status = post_data.get('status', post.status)
        post.is_featured = post_data.get('is_featured', post.is_featured)
        post.is_top = post_data.get('is_top', post.is_top)
        post.updated_at = datetime.now()
        
        # 更新话题标签
        if 'topics' in post_data:
            # 删除旧的话题关联
            PostTopics.query.filter(PostTopics.post_id == post_id).delete()
            
            # 添加新的话题关联
            topics = post_data.get('topics', [])
            for topic_name in topics:
                if topic_name.strip():
                    topic = get_or_create_topic(topic_name.strip())
                    if topic:
                        post_topic = PostTopics(post_id=post.id, topic_id=topic.id)
                        db.session.add(post_topic)
        
        # 更新媒体文件
        if 'media_files' in post_data:
            # 删除旧的媒体文件
            MediaFiles.query.filter(MediaFiles.post_id == post_id).delete()
            
            # 添加新的媒体文件
            media_files = post_data.get('media_files', [])
            for i, media_data in enumerate(media_files):
                media_file = MediaFiles(
                    post_id=post.id,
                    media_type=media_data.get('media_type'),
                    cloud_id=media_data.get('cloud_id'),
                    file_name=media_data.get('file_name'),
                    file_size=media_data.get('file_size', 0),
                    mime_type=media_data.get('mime_type'),
                    width=media_data.get('width', 0),
                    height=media_data.get('height', 0),
                    duration=media_data.get('duration', 0),
                    sort_order=i
                )
                db.session.add(media_file)
        
        db.session.commit()
        return post
    except OperationalError as e:
        logger.error("update_post errorMsg= {} ".format(e))
        db.session.rollback()
        return None


def delete_post(post_id):
    """删除内容"""
    try:
        post = Posts.query.get(post_id)
        if not post:
            return False
        
        db.session.delete(post)
        db.session.commit()
        return True
    except OperationalError as e:
        logger.error("delete_post errorMsg= {} ".format(e))
        db.session.rollback()
        return False


def search_posts(keyword, page=1, per_page=10):
    """搜索内容"""
    try:
        query = Posts.query.filter(
            and_(
                Posts.status == 'published',
                or_(
                    Posts.title.contains(keyword),
                    Posts.content.contains(keyword)
                )
            )
        ).order_by(desc(Posts.published_at))
        
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return pagination
    except OperationalError as e:
        logger.error("search_posts errorMsg= {} ".format(e))
        return None


def get_post_with_details(post_id):
    """获取内容详情（包含媒体文件和话题）"""
    try:
        post = Posts.query.get(post_id)
        if not post:
            return None
        
        # 获取分类信息
        category = None
        if post.category_id:
            category = Categories.query.get(post.category_id)
        
        # 获取媒体文件
        media_files = MediaFiles.query.filter(
            MediaFiles.post_id == post_id
        ).order_by(MediaFiles.sort_order).all()
        
        # 获取话题标签
        topics = db.session.query(Topics).join(
            PostTopics, Topics.id == PostTopics.topic_id
        ).filter(PostTopics.post_id == post_id).all()
        
        return {
            'post': post,
            'category': category,
            'media_files': media_files,
            'topics': topics
        }
    except OperationalError as e:
        logger.error("get_post_with_details errorMsg= {} ".format(e))
        return None


# 系统配置相关
def get_config(config_key, default_value=None):
    """获取系统配置"""
    try:
        config = SystemConfigs.query.filter(SystemConfigs.config_key == config_key).first()
        if config:
            return config.config_value
        return default_value
    except OperationalError as e:
        logger.error("get_config errorMsg= {} ".format(e))
        return default_value


def set_config(config_key, config_value, config_type='string', description=None):
    """设置系统配置"""
    try:
        config = SystemConfigs.query.filter(SystemConfigs.config_key == config_key).first()
        if config:
            config.config_value = config_value
            config.config_type = config_type
            config.updated_at = datetime.now()
        else:
            config = SystemConfigs(
                config_key=config_key,
                config_value=config_value,
                config_type=config_type,
                description=description
            )
            db.session.add(config)
        
        db.session.commit()
        return True
    except OperationalError as e:
        logger.error("set_config errorMsg= {} ".format(e))
        db.session.rollback()
        return False
