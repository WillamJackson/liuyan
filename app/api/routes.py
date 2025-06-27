import os
import uuid
from datetime import datetime
from flask import request, jsonify, current_app, send_from_directory, abort
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import desc, or_
from app.api import bp
from app.models import Content, Category, Tag, MediaFile, SystemSettings, User
from app.utils import FileUploadManager, ImageProcessor, MediaFileValidator
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

# 内容管理API
@bp.route('/contents', methods=['GET'])
def get_contents():
    """获取内容列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', '')

    
    query = Content.query
    
    if search:
        query = query.filter(or_(
            Content.title.contains(search),
            Content.content.contains(search)
        ))
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if status:
        query = query.filter_by(status=status)
    

    
    contents = query.order_by(desc(Content.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': {
            'items': [{
                'id': content.id,
                'title': content.title,
                'content': content.content[:200] + '...' if len(content.content) > 200 else content.content,

                'status': content.status,
                'view_count': content.view_count,
                'category': content.category.name if content.category else None,
                'tags': [tag.name for tag in content.tags],
                'created_at': content.created_at.isoformat(),
                'updated_at': content.updated_at.isoformat()
            } for content in contents.items],
            'pagination': {
                'page': contents.page,
                'pages': contents.pages,
                'per_page': contents.per_page,
                'total': contents.total,
                'has_next': contents.has_next,
                'has_prev': contents.has_prev
            }
        }
    })

@bp.route('/contents/<int:id>', methods=['GET'])
def get_content(id):
    """获取单个内容详情"""
    content = Content.query.get_or_404(id)
    
    # 获取关联的媒体文件（按排序顺序）
    media_files_query = db.session.execute(
        db.text("""
            SELECT mf.*, cm.sort_order 
            FROM media_files mf
            JOIN content_media cm ON mf.id = cm.media_file_id
            WHERE cm.content_id = :content_id
            ORDER BY cm.sort_order
        """),
        {"content_id": content.id}
    )
    
    media_files = []
    for row in media_files_query:
        media_files.append({
            'id': row.id,
            'filename': row.filename,
            'original_name': row.original_name,
            'file_type': row.file_type,
            'mime_type': row.mime_type,
            'file_size': row.file_size,
            'url': row.url,
            'thumbnail_url': row.thumbnail_url,
            'width': row.width,
            'height': row.height,
            'alt_text': row.alt_text,
            'description': row.description,
            'sort_order': row.sort_order
        })
    
    return jsonify({
        'success': True,
        'data': {
            'id': content.id,
            'title': content.title,
            'content': content.content,

            'status': content.status,
            'view_count': content.view_count,
            'is_featured': content.is_featured,

            'category_id': content.category_id,
            'category': content.category.name if content.category else None,
            'tags': [{'id': tag.id, 'name': tag.name} for tag in content.tags],
            'media_files': media_files,
            'created_at': content.created_at.isoformat(),
            'updated_at': content.updated_at.isoformat(),
            'published_at': content.published_at.isoformat() if content.published_at else None
        }
    })

@bp.route('/contents', methods=['POST'])
def create_content():
    """创建新内容"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
    
    # 验证媒体文件数量限制
    media_file_ids = data.get('media_file_ids', [])
    if len(media_file_ids) > 9:
        return jsonify({'success': False, 'message': '媒体文件数量不能超过9个'}), 400
    
    try:
        # 处理标签
        tag_names = data.get('tags', [])
        tags = []
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags.append(tag)
        
        # 获取默认用户
        default_user = get_default_user()
        
        content = Content(
            title=data['title'],
            content=data['content'],

            status=data.get('status', 'draft'),
            is_featured=data.get('is_featured', False),

            category_id=data.get('category_id'),
            user_id=default_user.id,
            tags=tags
        )
        
        if content.status == 'published':
            content.published_at = datetime.utcnow()
        
        db.session.add(content)
        db.session.flush()  # 获取content.id
        
        # 处理媒体文件关联
        if media_file_ids:
            # 验证媒体文件是否存在
            media_files = MediaFile.query.filter(MediaFile.id.in_(media_file_ids)).all()
            if len(media_files) != len(media_file_ids):
                return jsonify({'success': False, 'message': '部分媒体文件不存在'}), 400
            
            # 验证媒体文件类型（只允许图片和视频）
            for media_file in media_files:
                if media_file.file_type not in ['images', 'videos']:
                    return jsonify({'success': False, 'message': f'媒体文件 {media_file.original_name} 类型不支持，只允许图片和视频'}), 400
            
            # 建立关联关系
            for index, media_file_id in enumerate(media_file_ids):
                # 使用原生SQL插入关联数据，因为content_media表包含额外字段
                db.session.execute(
                    db.text("INSERT INTO content_media (content_id, media_file_id, sort_order) VALUES (:content_id, :media_file_id, :sort_order)"),
                    {"content_id": content.id, "media_file_id": media_file_id, "sort_order": index}
                )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '内容创建成功',
            'data': {'id': content.id}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建内容失败: {str(e)}")
        return jsonify({'success': False, 'message': '创建内容失败'}), 500

@bp.route('/contents/<int:id>', methods=['PUT'])
def update_content(id):
    """更新内容"""
    content = Content.query.get_or_404(id)
    
    data = request.get_json()
    
    # 验证媒体文件数量限制
    if 'media_file_ids' in data:
        media_file_ids = data.get('media_file_ids', [])
        if len(media_file_ids) > 9:
            return jsonify({'success': False, 'message': '媒体文件数量不能超过9个'}), 400
    
    try:
        if data.get('title'):
            content.title = data['title']
        if data.get('content'):
            content.content = data['content']

        if data.get('status'):
            old_status = content.status
            content.status = data['status']
            # 如果从非发布状态改为发布状态，设置发布时间
            if old_status != 'published' and content.status == 'published':
                content.published_at = datetime.utcnow()
        
        if 'is_featured' in data:
            content.is_featured = data['is_featured']

        if 'category_id' in data:
            content.category_id = data['category_id']
        
        # 处理标签
        if 'tags' in data:
            content.tags.clear()
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                content.tags.append(tag)
        
        # 处理媒体文件关联
        if 'media_file_ids' in data:
            media_file_ids = data.get('media_file_ids', [])
            
            # 删除现有关联
            db.session.execute(
                db.text("DELETE FROM content_media WHERE content_id = :content_id"),
                {"content_id": content.id}
            )
            
            # 添加新关联
            if media_file_ids:
                # 验证媒体文件是否存在
                media_files = MediaFile.query.filter(MediaFile.id.in_(media_file_ids)).all()
                if len(media_files) != len(media_file_ids):
                    return jsonify({'success': False, 'message': '部分媒体文件不存在'}), 400
                
                # 验证媒体文件类型（只允许图片和视频）
                for media_file in media_files:
                    if media_file.file_type not in ['images', 'videos']:
                        return jsonify({'success': False, 'message': f'媒体文件 {media_file.original_name} 类型不支持，只允许图片和视频'}), 400
                
                # 建立新的关联关系
                for index, media_file_id in enumerate(media_file_ids):
                    db.session.execute(
                        db.text("INSERT INTO content_media (content_id, media_file_id, sort_order) VALUES (:content_id, :media_file_id, :sort_order)"),
                        {"content_id": content.id, "media_file_id": media_file_id, "sort_order": index}
                    )
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '内容更新成功'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新内容失败: {str(e)}")
        return jsonify({'success': False, 'message': '更新内容失败'}), 500

@bp.route('/contents/<int:id>', methods=['DELETE'])
def delete_content(id):
    """删除内容"""
    content = Content.query.get_or_404(id)
    
    db.session.delete(content)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '内容删除成功'})

# 分类管理API
@bp.route('/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    categories = Category.query.filter_by(is_active=True)\
        .order_by(Category.sort_order, Category.name).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'parent_id': cat.parent_id,
            'sort_order': cat.sort_order,
            'content_count': cat.contents.count()
        } for cat in categories]
    })

@bp.route('/categories', methods=['POST'])
def create_category():
    """创建分类"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'success': False, 'message': '分类名称不能为空'}), 400
    
    category = Category(
        name=data['name'],
        description=data.get('description', ''),
        parent_id=data.get('parent_id'),
        sort_order=data.get('sort_order', 0)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '分类创建成功',
        'data': {'id': category.id}
    }), 201

# 标签管理API
@bp.route('/tags', methods=['GET'])
def get_tags():
    """获取标签列表"""
    tags = Tag.query.order_by(Tag.name).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': tag.id,
            'name': tag.name,
            'content_count': len(tag.contents)
        } for tag in tags]
    })

# 内容发布专用媒体上传API
@bp.route('/content/media/upload', methods=['POST'])
def upload_content_media():
    """内容发布时上传媒体文件（支持批量，最多9个）"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if len(files) > 9:
        return jsonify({'success': False, 'message': '一次最多只能上传9个文件'}), 400
    
    uploaded_files = []
    failed_files = []
    
    try:
        for file in files:
            if file.filename == '':
                continue
            
            # 验证文件类型（只允许图片和视频）
            if not FileUploadManager.allowed_file(file.filename):
                failed_files.append({
                    'filename': file.filename,
                    'error': '不支持的文件类型'
                })
                continue
            
            # 检查是否为图片或视频
            file_type = FileUploadManager.get_file_type(file.filename)
            if file_type not in ['images', 'videos']:
                failed_files.append({
                    'filename': file.filename,
                    'error': '只支持图片和视频文件'
                })
                continue
            
            # 验证文件大小
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if not MediaFileValidator.validate_file_size(file_size):
                max_size_mb = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) // (1024 * 1024)
                failed_files.append({
                    'filename': file.filename,
                    'error': f'文件大小超过限制（最大{max_size_mb}MB）'
                })
                continue
            
            try:
                # 获取文件信息
                original_filename = secure_filename(file.filename)
                unique_filename = FileUploadManager.generate_filename(original_filename)
                
                # 获取完整上传路径
                file_path = FileUploadManager.get_upload_path(file_type, unique_filename)
                
                # 保存文件
                file.save(file_path)
                
                # 恶意软件扫描
                if not MediaFileValidator.scan_for_malware(file_path):
                    os.remove(file_path)
                    failed_files.append({
                        'filename': file.filename,
                        'error': '文件安全检查失败'
                    })
                    continue
                
                # 计算文件哈希
                file_hash = FileUploadManager.calculate_file_hash(file_path)
                
                # 检查重复文件
                existing_file = MediaFile.query.filter_by(file_hash=file_hash).first()
                if existing_file:
                    os.remove(file_path)
                    uploaded_files.append({
                        'id': existing_file.id,
                        'filename': existing_file.filename,
                        'original_name': existing_file.original_name,
                        'url': existing_file.url,
                        'thumbnail_url': existing_file.thumbnail_url,
                        'file_type': existing_file.file_type,
                        'is_duplicate': True
                    })
                    continue
                
                # 处理图片
                thumbnail_url = None
                image_info = None
                
                if ImageProcessor.is_image(original_filename):
                    ImageProcessor.compress_image(file_path)
                    thumbnail_path = ImageProcessor.create_thumbnail(file_path)
                    if thumbnail_path:
                        thumbnail_url = FileUploadManager.get_file_url(thumbnail_path)
                    image_info = ImageProcessor.get_image_info(file_path)
                
                # 保存到数据库
                file_url = FileUploadManager.get_file_url(file_path)
                media_file = MediaFile(
                    filename=unique_filename,
                    original_name=original_filename,
                    file_path=os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER']).replace('\\', '/'),
                    file_size=file_size,
                    file_type=file_type,
                    mime_type=file.mimetype,
                    file_hash=file_hash,
                    url=file_url,
                    thumbnail_url=thumbnail_url,
                    width=image_info['width'] if image_info else None,
                    height=image_info['height'] if image_info else None,
                    alt_text=request.form.get('alt_text', ''),
                    description=request.form.get('description', ''),
                    user_id=get_default_user().id
                )
                
                db.session.add(media_file)
                db.session.flush()
                
                uploaded_files.append({
                    'id': media_file.id,
                    'filename': media_file.filename,
                    'original_name': media_file.original_name,
                    'url': media_file.url,
                    'thumbnail_url': media_file.thumbnail_url,
                    'file_type': media_file.file_type,
                    'file_size': media_file.file_size,
                    'width': media_file.width,
                    'height': media_file.height,
                    'is_duplicate': False
                })
                
            except Exception as e:
                current_app.logger.error(f"上传文件失败 {file.filename}: {str(e)}")
                failed_files.append({
                    'filename': file.filename,
                    'error': '文件上传失败'
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功上传 {len(uploaded_files)} 个文件',
            'data': {
                'uploaded_files': uploaded_files,
                'failed_files': failed_files,
                'media_file_ids': [f['id'] for f in uploaded_files]  # 方便前端使用
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量上传失败: {str(e)}")
        return jsonify({'success': False, 'message': '批量上传失败'}), 500

# 媒体文件API
@bp.route('/media/upload', methods=['POST'])
def upload_media():
    """上传媒体文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    # 验证文件类型
    if not FileUploadManager.allowed_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的文件类型'}), 400
    
    # 验证文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if not MediaFileValidator.validate_file_size(file_size):
        max_size_mb = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024) // (1024 * 1024)
        return jsonify({'success': False, 'message': f'文件大小超过限制（最大{max_size_mb}MB）'}), 400
    
    try:
        # 获取文件信息
        original_filename = secure_filename(file.filename)
        file_type = FileUploadManager.get_file_type(original_filename)
        unique_filename = FileUploadManager.generate_filename(original_filename)
        
        # 获取完整上传路径
        file_path = FileUploadManager.get_upload_path(file_type, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 恶意软件扫描
        if not MediaFileValidator.scan_for_malware(file_path):
            os.remove(file_path)
            return jsonify({'success': False, 'message': '文件安全检查失败'}), 400
        
        # 计算文件哈希
        file_hash = FileUploadManager.calculate_file_hash(file_path)
        
        # 检查是否已存在相同文件
        existing_file = MediaFile.query.filter_by(file_hash=file_hash).first()
        if existing_file:
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': '文件已存在',
                'data': {
                    'id': existing_file.id,
                    'filename': existing_file.filename,
                    'original_name': existing_file.original_name,
                    'file_path': existing_file.file_path,
                    'file_type': existing_file.file_type,
                    'file_size': existing_file.file_size,
                    'url': existing_file.url,
                    'thumbnail_url': existing_file.thumbnail_url
                }
            })
        
        # 处理图片
        thumbnail_url = None
        image_info = None
        
        if ImageProcessor.is_image(original_filename):
            # 压缩图片
            ImageProcessor.compress_image(file_path)
            
            # 创建缩略图
            thumbnail_path = ImageProcessor.create_thumbnail(file_path)
            if thumbnail_path:
                thumbnail_url = FileUploadManager.get_file_url(thumbnail_path)
            
            # 获取图片信息
            image_info = ImageProcessor.get_image_info(file_path)
        
        # 获取文件URL
        file_url = FileUploadManager.get_file_url(file_path)
        
        # 保存到数据库
        media_file = MediaFile(
            filename=unique_filename,
            original_name=original_filename,
            file_path=os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER']).replace('\\', '/'),
            file_size=file_size,
            file_type=file_type,
            mime_type=file.mimetype,
            file_hash=file_hash,
            url=file_url,
            thumbnail_url=thumbnail_url,
            width=image_info['width'] if image_info else None,
            height=image_info['height'] if image_info else None,
            alt_text=request.form.get('alt_text', ''),
            description=request.form.get('description', ''),
            user_id=get_default_user().id
        )
        
        db.session.add(media_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'id': media_file.id,
                'filename': media_file.filename,
                'original_name': media_file.original_name,
                'file_path': media_file.file_path,
                'file_type': media_file.file_type,
                'file_size': media_file.file_size,
                'url': media_file.url,
                'thumbnail_url': media_file.thumbnail_url,
                'width': media_file.width,
                'height': media_file.height
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'success': False, 'message': '文件上传失败'}), 500

@bp.route('/media/files/<path:filename>')
def serve_media_file(filename):
    """提供媒体文件访问"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/media', methods=['GET'])
def get_media_files():
    """获取媒体文件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    file_type = request.args.get('file_type', '')
    search = request.args.get('search', '')
    
    query = MediaFile.query
    
    if file_type:
        query = query.filter_by(file_type=file_type)
    
    if search:
        query = query.filter(or_(
            MediaFile.original_name.contains(search),
            MediaFile.alt_text.contains(search),
            MediaFile.description.contains(search)
        ))
    
    media_files = query.order_by(desc(MediaFile.created_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': {
            'items': [{
                'id': media.id,
                'filename': media.filename,
                'original_name': media.original_name,
                'file_path': media.file_path,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'mime_type': media.mime_type,
                'alt_text': media.alt_text,
                'description': media.description,
                'url': media.url,
                'thumbnail_url': media.thumbnail_url,
                'width': media.width,
                'height': media.height,
                'created_at': media.created_at.isoformat()
            } for media in media_files.items],
            'pagination': {
                'page': media_files.page,
                'pages': media_files.pages,
                'per_page': media_files.per_page,
                'total': media_files.total
            }
        }
    })

@bp.route('/media/<int:id>', methods=['GET'])
def get_media_file(id):
    """获取单个媒体文件详情"""
    media_file = MediaFile.query.get_or_404(id)
    
    return jsonify({
        'success': True,
        'data': {
            'id': media_file.id,
            'filename': media_file.filename,
            'original_name': media_file.original_name,
            'file_path': media_file.file_path,
            'file_type': media_file.file_type,
            'file_size': media_file.file_size,
            'mime_type': media_file.mime_type,
            'file_hash': media_file.file_hash,
            'url': media_file.url,
            'thumbnail_url': media_file.thumbnail_url,
            'width': media_file.width,
            'height': media_file.height,
            'alt_text': media_file.alt_text,
            'description': media_file.description,
            'created_at': media_file.created_at.isoformat(),
            'updated_at': media_file.updated_at.isoformat()
        }
    })

@bp.route('/media/<int:id>', methods=['PUT'])
def update_media_file(id):
    """更新媒体文件信息"""
    media_file = MediaFile.query.get_or_404(id)
    
    data = request.get_json()
    
    if 'alt_text' in data:
        media_file.alt_text = data['alt_text']
    if 'description' in data:
        media_file.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '媒体文件信息更新成功'
    })

@bp.route('/media/<int:id>', methods=['DELETE'])
def delete_media_file(id):
    """删除媒体文件"""
    media_file = MediaFile.query.get_or_404(id)
    
    try:
        # 删除物理文件
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_file.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 删除缩略图
        if media_file.thumbnail_url:
            thumbnail_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                media_file.file_path.replace(media_file.filename, f"{os.path.splitext(media_file.filename)[0]}_thumb{os.path.splitext(media_file.filename)[1]}")
            )
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        
        # 从数据库删除记录
        db.session.delete(media_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '媒体文件删除成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"删除媒体文件失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除文件失败'}), 500

@bp.route('/media/batch-upload', methods=['POST'])
def batch_upload_media():
    """批量上传媒体文件"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    results = []
    success_count = 0
    
    for file in files:
        if file.filename == '':
            continue
            
        try:
            # 验证文件类型
            if not FileUploadManager.allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'message': '不支持的文件类型'
                })
                continue
            
            # 验证文件大小
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if not MediaFileValidator.validate_file_size(file_size):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'message': '文件大小超过限制'
                })
                continue
            
            # 处理文件上传
            original_filename = secure_filename(file.filename)
            file_type = FileUploadManager.get_file_type(original_filename)
            unique_filename = FileUploadManager.generate_filename(original_filename)
            file_path = FileUploadManager.get_upload_path(file_type, unique_filename)
            
            file.save(file_path)
            
            # 安全检查
            if not MediaFileValidator.scan_for_malware(file_path):
                os.remove(file_path)
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'message': '文件安全检查失败'
                })
                continue
            
            # 计算文件哈希
            file_hash = FileUploadManager.calculate_file_hash(file_path)
            
            # 检查重复文件
            existing_file = MediaFile.query.filter_by(file_hash=file_hash).first()
            if existing_file:
                os.remove(file_path)
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'message': '文件已存在',
                    'data': {
                        'id': existing_file.id,
                        'url': existing_file.url
                    }
                })
                continue
            
            # 处理图片
            thumbnail_url = None
            image_info = None
            
            if ImageProcessor.is_image(original_filename):
                ImageProcessor.compress_image(file_path)
                thumbnail_path = ImageProcessor.create_thumbnail(file_path)
                if thumbnail_path:
                    thumbnail_url = FileUploadManager.get_file_url(thumbnail_path)
                image_info = ImageProcessor.get_image_info(file_path)
            
            # 保存到数据库
            file_url = FileUploadManager.get_file_url(file_path)
            media_file = MediaFile(
                filename=unique_filename,
                original_name=original_filename,
                file_path=os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER']).replace('\\', '/'),
                file_size=file_size,
                file_type=file_type,
                mime_type=file.mimetype,
                file_hash=file_hash,
                url=file_url,
                thumbnail_url=thumbnail_url,
                width=image_info['width'] if image_info else None,
                height=image_info['height'] if image_info else None,
                user_id=get_default_user().id
            )
            
            db.session.add(media_file)
            db.session.commit()
            
            results.append({
                'filename': file.filename,
                'success': True,
                'message': '上传成功',
                'data': {
                    'id': media_file.id,
                    'url': media_file.url,
                    'thumbnail_url': media_file.thumbnail_url
                }
            })
            success_count += 1
            
        except Exception as e:
            current_app.logger.error(f"批量上传文件失败 {file.filename}: {str(e)}")
            results.append({
                'filename': file.filename,
                'success': False,
                'message': '上传失败'
            })
    
    return jsonify({
        'success': True,
        'message': f'批量上传完成，成功上传 {success_count} 个文件',
        'data': {
            'results': results,
            'success_count': success_count,
            'total_count': len(files)
        }
    })

# 统计API
@bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    total_contents = Content.query.count()
    total_media = MediaFile.query.count()
    total_categories = Category.query.count()
    total_views = db.session.query(db.func.sum(Content.view_count)).scalar() or 0
    
    # 按状态统计
    status_stats = db.session.query(
        Content.status,
        db.func.count(Content.id)
    ).group_by(Content.status).all()
    
    return jsonify({
        'success': True,
        'data': {
            'total_contents': total_contents,
            'total_media': total_media,
            'total_categories': total_categories,
            'total_views': total_views,

            'status_stats': dict(status_stats)
        }
    })

# 系统设置API
@bp.route('/settings', methods=['GET'])
def get_settings():
    """获取系统设置"""
    settings = SystemSettings.query.all()
    settings_dict = {setting.key: {
        'value': setting.value,
        'description': setting.description
    } for setting in settings}
    
    return jsonify({
        'success': True,
        'data': settings_dict
    })

@bp.route('/settings', methods=['POST'])
def update_settings():
    """批量更新系统设置"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': '请提供设置数据'}), 400
    
    try:
        updated_count = 0
        for key, value in data.items():
            setting = SystemSettings.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                updated_count += 1
            else:
                # 创建新设置
                new_setting = SystemSettings(
                    key=key,
                    value=str(value),
                    description=f'用户自定义设置: {key}'
                )
                db.session.add(new_setting)
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 个设置项'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新设置失败: {str(e)}'}), 500

@bp.route('/settings/<key>', methods=['PUT'])
def update_single_setting(key):
    """更新单个系统设置"""
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'success': False, 'message': '请提供设置值'}), 400
    
    try:
        setting = SystemSettings.query.filter_by(key=key).first()
        if not setting:
            # 创建新设置
            setting = SystemSettings(
                key=key,
                value=str(data['value']),
                description=data.get('description', f'用户自定义设置: {key}')
            )
            db.session.add(setting)
        else:
            setting.value = str(data['value'])
            if 'description' in data:
                setting.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '设置更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新设置失败: {str(e)}'}), 500

@bp.route('/settings/<key>', methods=['DELETE'])
def delete_setting(key):
    """删除系统设置"""
    setting = SystemSettings.query.filter_by(key=key).first()
    
    if not setting:
        return jsonify({'success': False, 'message': '设置项不存在'}), 404
    
    try:
        db.session.delete(setting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '设置删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除设置失败: {str(e)}'}), 500 