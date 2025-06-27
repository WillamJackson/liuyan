from flask import render_template, request, redirect, url_for, flash, current_app
from sqlalchemy import desc, or_
from app.main import bp
from app.models import Content, Category, Tag, MediaFile, SystemSettings, User
from app import db

def get_default_user():
    """获取默认用户，如果不存在则创建"""
    user = User.query.first()
    if not user:
        user = User(
            username='admin',
            email='admin@example.com'
        )
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
    return user

@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    # 统计数据
    total_contents = Content.query.count()
    total_media = MediaFile.query.count()
    total_categories = Category.query.count()
    total_views = db.session.query(db.func.sum(Content.view_count)).scalar() or 0
    
    # 最近发布的内容
    recent_contents = Content.query.filter_by(status='published')\
        .order_by(desc(Content.published_at))\
        .limit(5).all()
    
    # 草稿内容
    draft_contents = Content.query.filter_by(status='draft')\
        .order_by(desc(Content.updated_at))\
        .limit(5).all()
    
    return render_template('dashboard.html',
                         total_contents=total_contents,
                         total_media=total_media,
                         total_categories=total_categories,
                         total_views=total_views,
                         recent_contents=recent_contents,
                         draft_contents=draft_contents)

@bp.route('/content-list')
def content_list():
    """内容列表页面"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')

    
    # 构建查询
    query = Content.query
    
    # 搜索条件
    if search:
        query = query.filter(or_(
            Content.title.contains(search),
            Content.content.contains(search)
        ))
    
    # 分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 状态筛选
    if status:
        query = query.filter_by(status=status)
    

    
    # 分页
    contents = query.order_by(desc(Content.created_at))\
        .paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'], 
                 error_out=False)
    
    # 为每个内容获取媒体文件数量
    for content in contents.items:
        media_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM content_media WHERE content_id = :content_id"),
            {"content_id": content.id}
        ).scalar()
        content.media_count = media_count
    
    # 获取分类列表
    categories = Category.query.filter_by(is_active=True).all()
    
    return render_template('content-list.html',
                         contents=contents,
                         categories=categories,
                         search=search,
                         current_category=category_id,
                         current_status=status,
)

@bp.route('/content-editor')
@bp.route('/content-editor/<int:id>')
def content_editor(id=None):
    """内容编辑器页面"""
    content = None
    if id:
        content = Content.query.get_or_404(id)
    
    # 获取分类和标签
    categories = Category.query.filter_by(is_active=True).all()
    tags = Tag.query.all()
    
    return render_template('content-editor.html',
                         content=content,
                         categories=categories,
                         tags=tags)

@bp.route('/media-library')
def media_library():
    """媒体库页面"""
    page = request.args.get('page', 1, type=int)
    file_type = request.args.get('type', '')
    search = request.args.get('search', '')
    
    # 构建查询
    query = MediaFile.query
    
    # 文件类型筛选
    if file_type:
        query = query.filter_by(file_type=file_type)
    
    # 搜索筛选
    if search:
        query = query.filter(or_(
            MediaFile.original_name.contains(search),
            MediaFile.alt_text.contains(search)
        ))
    
    # 分页
    media_files = query.order_by(desc(MediaFile.created_at))\
        .paginate(page=page, per_page=20, error_out=False)
    
    # 计算存储使用情况
    total_size = db.session.query(db.func.sum(MediaFile.file_size)).scalar() or 0
    
    return render_template('media-library.html',
                         media_files=media_files,
                         current_type=file_type,
                         search=search,
                         total_size=total_size)

@bp.route('/category-management')
def category_management():
    """分类管理页面"""
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    tags = Tag.query.order_by(Tag.name).all()
    
    return render_template('category-management.html',
                         categories=categories,
                         tags=tags)

@bp.route('/system-settings')
def system_settings():
    """系统设置页面"""
    settings = SystemSettings.query.all()
    settings_dict = {setting.key: setting.value for setting in settings}
    
    return render_template('system-settings.html',
                         settings=settings_dict)

@bp.route('/editor')
def editor():
    """简单编辑器页面"""
    return render_template('editor.html')

@bp.route('/list')
def list_view():
    """列表视图页面"""
    return render_template('list.html')

@bp.route('/category')
def category():
    """分类页面"""
    return render_template('category.html')

@bp.route('/media')
def media():
    """媒体页面"""
    return render_template('media.html')

@bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html') 