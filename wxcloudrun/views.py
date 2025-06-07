from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from wxcloudrun.dao import (
    # 原有的计数器方法
    query_counterbyid, update_counterbyid, insert_counter,
    # 新增的内容管理方法
    create_post, get_posts_list, get_post_with_details, update_post, delete_post,
    get_all_categories, get_all_topics, get_hot_topics, search_posts
)
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_response, make_err_response
from werkzeug.utils import secure_filename
import os
import uuid
import mimetypes
import traceback
import logging

# 创建logger
logger = logging.getLogger(__name__)

# 创建蓝图
main_bp = Blueprint('main', __name__)


# ==================== 原有的路由（保持不变） ====================
@main_bp.route('/')
def index():
    """
    :return: 返回index页面
    """
    logger.info("🚨🚨🚨 收到根路径请求")
    logger.info(f"🚨🚨🚨 请求方法: {request.method}")
    logger.info(f"🚨🚨🚨 请求路径: {request.path}")
    logger.info(f"🚨🚨🚨 请求头: {dict(request.headers)}")
    return render_template('index.html')


@main_bp.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@main_bp.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


# ==================== 内容发布系统路由 ====================

# 管理后台首页
@main_bp.route('/admin')
def admin_index():
    """管理后台首页"""
    return redirect(url_for('main.admin_posts'))


# 内容管理页面
@main_bp.route('/admin/posts')
def admin_posts():
    """内容列表页面"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', 'published')
    
    # 获取内容列表
    pagination = get_posts_list(page=page, per_page=10, category_id=category_id, status=status)
    
    # 获取分类列表
    categories = get_all_categories()
    
    return render_template('admin/posts.html', 
                         pagination=pagination, 
                         categories=categories,
                         current_category=category_id,
                         current_status=status)


# 内容编辑页面
@main_bp.route('/admin/posts/create')
def admin_create_post():
    """创建内容页面"""
    categories = get_all_categories()
    hot_topics = get_hot_topics()
    return render_template('admin/edit_post.html', 
                         categories=categories, 
                         hot_topics=hot_topics,
                         post=None)


@main_bp.route('/admin/posts/<int:post_id>/edit')
def admin_edit_post(post_id):
    """编辑内容页面"""
    post_data = get_post_with_details(post_id)
    if not post_data:
        flash('内容不存在', 'error')
        return redirect(url_for('main.admin_posts'))
    
    categories = get_all_categories()
    hot_topics = get_hot_topics()
    
    # 将数据库对象转换为可序列化的字典
    serializable_post_data = {
        'post': {
            'id': post_data['post'].id,
            'title': post_data['post'].title,
            'content': post_data['post'].content,
            'category_id': post_data['post'].category_id,
            'link_url': post_data['post'].link_url,
            'link_title': post_data['post'].link_title,
            'link_description': post_data['post'].link_description,
            'link_favicon': post_data['post'].link_favicon,
            'status': post_data['post'].status,
            'is_featured': post_data['post'].is_featured,
            'is_top': post_data['post'].is_top,
        },
        'category': {
            'id': post_data['category'].id,
            'name': post_data['category'].name
        } if post_data['category'] else None,
        'topics': [{'id': t.id, 'name': t.name} for t in post_data['topics']],
        'media_files': [{
            'id': m.id,
            'media_type': m.media_type,
            'cloud_id': m.cloud_id,
            'file_name': m.file_name,
            'file_size': m.file_size,
            'mime_type': m.mime_type,
            'width': m.width,
            'height': m.height,
            'duration': m.duration,
            'sort_order': m.sort_order
        } for m in post_data['media_files']]
    }
    
    return render_template('admin/edit_post.html', 
                         categories=categories, 
                         hot_topics=hot_topics,
                         post_data=serializable_post_data)


# API接口

@main_bp.route('/api/posts', methods=['POST'])
def api_create_post():
    """创建内容API"""
    try:
        data = request.get_json()
        logger.info(f"Received create post request: {data}")
        
        # 验证必填字段
        if not data.get('title') and not data.get('content') and not data.get('media_files'):
            return make_err_response('标题、内容或媒体文件至少填写一项')
        
        # 处理话题标签
        topics = []
        if data.get('topics'):
            if isinstance(data['topics'], str):
                # 如果是字符串，按逗号分割
                topics = [t.strip() for t in data['topics'].split(',') if t.strip()]
            elif isinstance(data['topics'], list):
                topics = [str(t).strip() for t in data['topics'] if str(t).strip()]
        
        # 构建内容数据
        post_data = {
            'title': data.get('title', '').strip(),
            'content': data.get('content', '').strip(),
            'category_id': data.get('category_id'),
            'link_url': data.get('link_url', '').strip(),
            'link_title': data.get('link_title', '').strip(),
            'link_description': data.get('link_description', '').strip(),
            'link_favicon': data.get('link_favicon', '').strip(),
            'status': data.get('status', 'published'),
            'is_featured': data.get('is_featured', False),
            'is_top': data.get('is_top', False),
            'topics': topics,
            'media_files': data.get('media_files', [])
        }
        
        logger.info(f"Processed post data: {post_data}")
        
        # 创建内容
        post = create_post(post_data)
        if post:
            logger.info(f"Post created successfully with ID: {post.id}")
            return make_succ_response({
                'id': post.id,
                'title': post.title,
                'status': post.status,
                'created_at': post.created_at.isoformat() if post.created_at else None
            })
        else:
            logger.error("create_post returned None")
            return make_err_response('创建失败')
            
    except Exception as e:
        logger.error(f"api_create_post error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return make_err_response(f'创建失败: {str(e)}')


@main_bp.route('/api/posts/<int:post_id>', methods=['PUT'])
def api_update_post(post_id):
    """更新内容API"""
    try:
        data = request.get_json()
        
        # 处理话题标签
        topics = []
        if data.get('topics'):
            if isinstance(data['topics'], str):
                topics = [t.strip() for t in data['topics'].split(',') if t.strip()]
            elif isinstance(data['topics'], list):
                topics = [str(t).strip() for t in data['topics'] if str(t).strip()]
        
        # 构建更新数据
        update_data = {
            'title': data.get('title', '').strip(),
            'content': data.get('content', '').strip(),
            'category_id': data.get('category_id'),
            'link_url': data.get('link_url', '').strip(),
            'link_title': data.get('link_title', '').strip(),
            'link_description': data.get('link_description', '').strip(),
            'link_favicon': data.get('link_favicon', '').strip(),
            'status': data.get('status', 'published'),
            'is_featured': data.get('is_featured', False),
            'is_top': data.get('is_top', False),
            'topics': topics,
            'media_files': data.get('media_files', [])
        }
        
        # 更新内容
        success = update_post(post_id, update_data)
        if success:
            return make_succ_response({'id': post_id, 'message': '更新成功'})
        else:
            return make_err_response('更新失败')
            
    except Exception as e:
        return make_err_response(f'更新失败: {str(e)}')


@main_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    """删除内容API"""
    print(f"🚨🚨🚨 DELETE API CALLED - POST ID: {post_id} 🚨🚨🚨")
    logger.info(f"🗑️ 开始删除内容，ID: {post_id}")
    
    try:
        print(f"🔍 进入try块，准备获取内容详情")
        # 先获取内容详情，包括媒体文件信息
        logger.info(f"📋 获取内容详情: {post_id}")
        post_data = get_post_with_details(post_id)
        print(f"📊 获取到的内容数据: {post_data is not None}")
        
        if not post_data:
            print(f"❌ 内容不存在: {post_id}")
            logger.warning(f"❌ 内容不存在: {post_id}")
            return make_err_response('内容不存在')
        
        # 删除关联的媒体文件
        media_files = post_data.get('media_files', [])
        print(f"📁 发现媒体文件数量: {len(media_files)}")
        logger.info(f"📁 发现 {len(media_files)} 个媒体文件需要删除")
        
        deleted_files = []
        failed_files = []
        
        for i, media_file in enumerate(media_files):
            # 获取文件ID
            cloud_id = getattr(media_file, 'cloud_id', None) or getattr(media_file, 'file_url', None)
            print(f"📄 处理媒体文件 {i+1}/{len(media_files)}: {cloud_id}")
            logger.info(f"📄 处理媒体文件 {i+1}/{len(media_files)}: {cloud_id}")
            
            if cloud_id:
                try:
                    print(f"🔄 调用删除文件函数: {cloud_id}")
                    logger.info(f"🔄 调用删除文件函数: {cloud_id}")
                    delete_result = delete_cloud_file(cloud_id)
                    print(f"📤 删除结果: {delete_result}")
                    logger.info(f"📤 删除结果: {delete_result}")
                    
                    if delete_result['success']:
                        deleted_files.append(cloud_id)
                        print(f"✅ 成功删除云存储文件: {cloud_id}")
                        logger.info(f"✅ 成功删除云存储文件: {cloud_id}")
                    else:
                        failed_files.append(cloud_id)
                        print(f"⚠️ 删除云存储文件失败: {cloud_id}, 错误: {delete_result['error']}")
                        logger.warning(f"⚠️ 删除云存储文件失败: {cloud_id}, 错误: {delete_result['error']}")
                except Exception as e:
                    failed_files.append(cloud_id)
                    print(f"💥 删除云存储文件异常: {cloud_id}, 错误: {str(e)}")
                    logger.error(f"💥 删除云存储文件异常: {cloud_id}, 错误: {str(e)}")
            else:
                print(f"⚠️ 媒体文件 {i+1} 没有有效的文件ID")
                logger.warning(f"⚠️ 媒体文件 {i+1} 没有有效的文件ID")
        
        # 删除数据库记录
        print(f"🗄️ 开始删除数据库记录: {post_id}")
        logger.info(f"🗄️ 开始删除数据库记录: {post_id}")
        success = delete_post(post_id)
        print(f"🗄️ 数据库删除结果: {success}")
        logger.info(f"🗄️ 数据库删除结果: {success}")
        
        if success:
            result = {
                'message': '删除成功',
                'deleted_files': len(deleted_files),
                'failed_files': len(failed_files)
            }
            
            if failed_files:
                result['warning'] = f'有 {len(failed_files)} 个文件删除失败，但内容已删除'
            
            print(f"🎉 删除完成: 成功删除 {len(deleted_files)} 个文件，{len(failed_files)} 个文件失败")
            logger.info(f"🎉 删除完成: 成功删除 {len(deleted_files)} 个文件，{len(failed_files)} 个文件失败")
            return make_succ_response(result)
        else:
            print(f"❌ 数据库删除失败: {post_id}")
            logger.error(f"❌ 数据库删除失败: {post_id}")
            return make_err_response('删除失败')
    except Exception as e:
        print(f"💥💥💥 删除内容异常: {str(e)} 💥💥💥")
        logger.error(f"💥 删除内容异常: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整的异常堆栈
        logger.error(f"📋 异常堆栈: {traceback.format_exc()}")
        return make_err_response(f'删除失败: {str(e)}')


def delete_cloud_file(cloud_id):
    """删除云存储文件"""
    logger.info(f"🔥 开始删除云存储文件: {cloud_id}")
    
    try:
        import requests
        
        # 检查文件ID格式
        if not cloud_id:
            logger.error("❌ 文件ID为空")
            return {'success': False, 'error': '文件ID为空'}
        
        # 如果是HTTP/HTTPS URL，跳过删除（可能是外部链接）
        if cloud_id.startswith(('http://', 'https://')):
            logger.info(f"🌐 跳过HTTP URL格式文件: {cloud_id}")
            return {'success': True, 'message': 'HTTP URL格式，跳过删除'}
        
        # 确保是cloud://格式
        if not cloud_id.startswith('cloud://'):
            logger.warning(f"⚠️ 文件ID格式不正确: {cloud_id}")
            return {'success': False, 'error': f'文件ID格式不正确: {cloud_id}'}
        
        # 获取环境ID
        env_id = os.environ.get('TCB_ENV') or os.environ.get('WX_ENV_ID') or 'prod-7g25n1fzd374434f'
        logger.info(f"🌍 使用环境ID: {env_id}")
        
        # 检查是否在云托管环境中
        is_cloudbase = (os.path.exists('/.cloudbase') or 
                      os.environ.get('CLOUDBASE_RUNTIME') or 
                      os.environ.get('TCB_RUNTIME') or
                      os.environ.get('WX_CLOUDBASE_ENV'))
        
        logger.info(f"☁️ 云托管环境检测: {is_cloudbase}")
        logger.info(f"📁 /.cloudbase 存在: {os.path.exists('/.cloudbase')}")
        logger.info(f"🔧 环境变量检查:")
        logger.info(f"  CLOUDBASE_RUNTIME: {os.environ.get('CLOUDBASE_RUNTIME')}")
        logger.info(f"  TCB_RUNTIME: {os.environ.get('TCB_RUNTIME')}")
        logger.info(f"  WX_CLOUDBASE_ENV: {os.environ.get('WX_CLOUDBASE_ENV')}")
        
        # 构建删除请求
        if is_cloudbase:
            # 云托管环境：使用内网API，不需要access_token
            delete_url = "http://api.weixin.qq.com/tcb/batchdeletefile"
            headers = {
                'Content-Type': 'application/json',
                'X-WX-SOURCE': 'cloudbase'
            }
            logger.info("🏠 使用云托管环境API")
        else:
            # 非云托管环境：需要access_token，但这里我们无法获取
            # 在云托管环境外，文件删除需要通过其他方式处理
            logger.warning("⚠️ 非云托管环境，无法直接删除文件")
            return {'success': False, 'error': '非云托管环境，无法删除文件'}
        
        delete_data = {
            "env": env_id,
            "fileid_list": [cloud_id]
        }
        
        logger.info(f"📡 删除文件API调用:")
        logger.info(f"  URL: {delete_url}")
        logger.info(f"  Headers: {headers}")
        logger.info(f"  Data: {delete_data}")
        
        # 发送删除请求
        logger.info("🚀 发送删除请求...")
        response = requests.post(delete_url, json=delete_data, headers=headers, timeout=30)
        
        logger.info(f"📥 删除文件API响应状态: {response.status_code}")
        logger.info(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"📊 删除文件API响应JSON: {result}")
                
                if result.get('errcode') == 0:
                    delete_list = result.get('delete_list', [])
                    logger.info(f"📋 删除列表: {delete_list}")
                    
                    if delete_list and len(delete_list) > 0:
                        file_result = delete_list[0]
                        logger.info(f"📄 文件删除结果: {file_result}")
                        
                        # 检查单个文件的删除状态
                        if file_result.get('status') == 0:  # 注意这里是status而不是errcode
                            logger.info("✅ 文件删除成功")
                            return {'success': True, 'message': '文件删除成功'}
                        else:
                            error_msg = file_result.get('errmsg', '未知错误')
                            logger.error(f"❌ 文件删除失败: {error_msg}")
                            return {'success': False, 'error': f"文件删除失败: {error_msg}"}
                    else:
                        logger.error("❌ 删除结果为空")
                        return {'success': False, 'error': '删除结果为空'}
                else:
                    error_msg = result.get('errmsg', '未知错误')
                    logger.error(f"❌ API调用失败: {error_msg} (errcode: {result.get('errcode')})")
                    return {'success': False, 'error': f"API调用失败: {error_msg} (errcode: {result.get('errcode')})"}
            except ValueError as e:
                logger.error(f"💥 解析响应JSON失败: {e}, 响应内容: {response.text}")
                return {'success': False, 'error': f'响应格式错误: {str(e)}'}
        else:
            logger.error(f"💥 HTTP请求失败: {response.status_code}, 响应: {response.text}")
            return {'success': False, 'error': f'HTTP请求失败: {response.status_code}'}
            
    except requests.exceptions.RequestException as req_error:
        logger.error(f"💥 删除文件网络请求异常: {str(req_error)}")
        return {'success': False, 'error': f'网络请求失败: {str(req_error)}'}
        
    except Exception as e:
        logger.error(f"💥 删除文件异常: {str(e)}")
        import traceback
        logger.error(f"📋 异常堆栈: {traceback.format_exc()}")
        return {'success': False, 'error': f'删除失败: {str(e)}'}


@main_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def api_get_post(post_id):
    """获取单个内容详情API"""
    try:
        post_data = get_post_with_details(post_id)
        if not post_data:
            return make_err_response('内容不存在')
        
        # 构建返回数据
        result = {
            'id': post_data['post'].id,
            'title': post_data['post'].title,
            'content': post_data['post'].content,
            'category_id': post_data['post'].category_id,
            'category_name': post_data['category'].name if post_data['category'] else None,
            'link_url': post_data['post'].link_url,
            'link_title': post_data['post'].link_title,
            'link_description': post_data['post'].link_description,
            'link_favicon': post_data['post'].link_favicon,
            'status': post_data['post'].status,
            'is_featured': post_data['post'].is_featured,
            'is_top': post_data['post'].is_top,
            'view_count': post_data['post'].view_count,
            'like_count': post_data['post'].like_count,
            'comment_count': post_data['post'].comment_count,
            'created_at': post_data['post'].created_at.isoformat() if post_data['post'].created_at else None,
            'updated_at': post_data['post'].updated_at.isoformat() if post_data['post'].updated_at else None,
            'topics': [{'id': t.id, 'name': t.name} for t in post_data['topics']],
            'media_files': [{
                'id': m.id,
                'file_type': m.file_type,
                'file_url': m.file_url,
                'file_name': m.file_name,
                'file_size': m.file_size,
                'sort_order': m.sort_order
            } for m in post_data['media_files']]
        }
        
        return make_succ_response(result)
        
    except Exception as e:
        return make_err_response(f'获取失败: {str(e)}')


@main_bp.route('/api/posts', methods=['GET'])
def api_get_posts():
    """获取内容列表API"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # 限制最大每页数量
        category_id = request.args.get('category_id', type=int)
        status = request.args.get('status', 'published')
        search = request.args.get('search', '').strip()
        
        # 如果有搜索关键词，使用搜索功能
        if search:
            pagination = search_posts(search, page=page, per_page=per_page, 
                                    category_id=category_id, status=status)
        else:
            pagination = get_posts_list(page=page, per_page=per_page, 
                                      category_id=category_id, status=status)
        
        # 构建返回数据
        posts_data = []
        for post_data in pagination.items:
            post_info = {
                'id': post_data['post'].id,
                'title': post_data['post'].title,
                'content': post_data['post'].content[:200] + '...' if len(post_data['post'].content or '') > 200 else post_data['post'].content,
                'category_id': post_data['post'].category_id,
                'category_name': post_data['category'].name if post_data['category'] else None,
                'status': post_data['post'].status,
                'is_featured': post_data['post'].is_featured,
                'is_top': post_data['post'].is_top,
                'view_count': post_data['post'].view_count,
                'like_count': post_data['post'].like_count,
                'comment_count': post_data['post'].comment_count,
                'created_at': post_data['post'].created_at.isoformat() if post_data['post'].created_at else None,
                'topics': [{'id': t.id, 'name': t.name} for t in post_data['topics']],
                'media_count': len(post_data['media_files']),
                'has_link': bool(post_data['post'].link_url)
            }
            posts_data.append(post_info)
        
        result = {
            'posts': posts_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }
        
        return make_succ_response(result)
        
    except Exception as e:
        return make_err_response(f'获取列表失败: {str(e)}')


@main_bp.route('/api/categories', methods=['GET'])
def api_get_categories():
    """获取分类列表API"""
    logger.info("🚨🚨🚨 收到分类列表请求")
    logger.info(f"🚨🚨🚨 请求方法: {request.method}")
    logger.info(f"🚨🚨🚨 请求路径: {request.path}")
    logger.info(f"🚨🚨🚨 请求头: {dict(request.headers)}")
    
    try:
        categories = get_all_categories()
        categories_data = [{
            'id': cat.id,
            'name': cat.name,
            'description': getattr(cat, 'description', ''),
            'icon': getattr(cat, 'icon', ''),  # 安全获取icon属性
            'sort_order': getattr(cat, 'sort_order', 0),
            'is_active': getattr(cat, 'is_active', True)
        } for cat in categories]
        
        logger.info(f"🚨🚨🚨 返回分类数据: {len(categories_data)} 条")
        return make_succ_response(categories_data)
        
    except Exception as e:
        logger.error(f"🚨🚨🚨 获取分类失败: {str(e)}")
        logger.error(f"🚨🚨🚨 错误详情: {traceback.format_exc()}")
        return make_err_response(f'获取分类失败: {str(e)}')


@main_bp.route('/api/topics', methods=['GET'])
def api_get_topics():
    """获取话题列表API"""
    try:
        # 获取查询参数
        hot_only = request.args.get('hot_only', 'false').lower() == 'true'
        
        if hot_only:
            topics = get_hot_topics()
        else:
            topics = get_all_topics()
        
        topics_data = [{
            'id': topic.id,
            'name': topic.name,
            'description': topic.description,
            'post_count': topic.post_count,
            'is_hot': topic.is_hot,
            'created_at': topic.created_at.isoformat() if topic.created_at else None
        } for topic in topics]
        
        return make_succ_response(topics_data)
        
    except Exception as e:
        return make_err_response(f'获取话题失败: {str(e)}')


@main_bp.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件到微信云托管对象存储"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': -1, 'errorMsg': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': -1, 'errorMsg': '没有选择文件'})
        
        # 生成唯一文件名
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # 根据文件类型确定存储路径和媒体类型
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        if content_type.startswith('image/'):
            folder = 'images'
            media_type = 'image'
        elif content_type.startswith('video/'):
            folder = 'videos'
            media_type = 'video'
        elif content_type.startswith('audio/'):
            folder = 'audios'
            media_type = 'audio'
        else:
            folder = 'documents'
            media_type = 'document'
        
        # 构建云存储路径
        date_path = datetime.now().strftime('%Y/%m/%d')
        storage_path = f"{folder}/{date_path}/{unique_filename}"
        
        # 读取文件内容
        file_content = file.read()
        file_size = len(file_content)
        
        # 获取环境ID
        env_id = os.environ.get('TCB_ENV') or os.environ.get('WX_ENV_ID') or 'prod-7g25n1fzd374434f'
        
        logger.info(f"开始上传文件，env_id: {env_id}, path: {storage_path}, size: {file_size}")
        
        try:
            import requests
            
            # 检查是否在云托管环境中
            is_cloudbase = (os.path.exists('/.cloudbase') or 
                          os.environ.get('CLOUDBASE_RUNTIME') or 
                          os.environ.get('TCB_RUNTIME') or
                          os.environ.get('WX_CLOUDBASE_ENV'))
            
            # 检查是否在本地调试环境中
            is_local_debug = (os.environ.get('LOCAL_DEBUG') == 'true' or 
                            os.environ.get('VSCODE_DEBUG') == 'true' or
                            not is_cloudbase)
            
            logger.info(f"环境检测 - 云托管环境: {is_cloudbase}, 本地调试: {is_local_debug}")
            
            # === 第一步：获取上传授权 ===
            if is_local_debug:
                # 本地调试环境：使用HTTP协议访问本地代理
                auth_url = "http://api.weixin.qq.com/tcb/uploadfile"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; WeChatCloudRun/1.0)'
                }
                logger.info("使用本地调试环境（HTTP协议）")
            elif is_cloudbase:
                # 云托管环境：使用开放接口服务
                auth_url = "http://api.weixin.qq.com/tcb/uploadfile"
                headers = {
                    'Content-Type': 'application/json',
                    'X-WX-SOURCE': 'cloudbase'
                }
                logger.info("使用云托管环境（开放接口服务）")
            else:
                # 生产环境：使用外部API
                auth_url = "https://api.weixin.qq.com/tcb/uploadfile"
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; WeChatCloudRun/1.0)'
                }
                logger.info("使用生产环境（HTTPS协议）")
            
            auth_data = {
                "env": env_id,
                "path": storage_path
            }
            
            logger.info(f"调用上传授权API: {auth_url}")
            
            # 获取上传授权
            auth_response = requests.post(auth_url, json=auth_data, headers=headers, timeout=15)
            
            logger.info(f"授权API响应状态: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                auth_result = auth_response.json()
                logger.info(f"授权API响应: {auth_result}")
                
                if auth_result.get('errcode') == 0:
                    upload_url = auth_result.get('url')
                    authorization = auth_result.get('authorization')
                    token = auth_result.get('token')
                    cos_file_id = auth_result.get('cos_file_id')
                    file_id = auth_result.get('file_id')
                    
                    if upload_url and authorization:
                        logger.info(f"开始上传文件到COS: {upload_url}")
                        
                        # === 第二步：上传文件到COS ===
                        # 使用multipart/form-data格式上传
                        upload_data = {
                            'key': storage_path,
                            'Signature': authorization,
                            'x-cos-security-token': token,
                            'x-cos-meta-fileid': cos_file_id
                        }
                        
                        upload_files = {
                            'file': (unique_filename, file_content, content_type)
                        }
                        
                        upload_response = requests.post(
                            upload_url, 
                            data=upload_data,
                            files=upload_files,
                            timeout=60
                        )
                        
                        logger.info(f"文件上传响应: {upload_response.status_code}")
                        
                        if upload_response.status_code in [200, 204]:
                            # 构建cloud_id
                            cloud_id = file_id or f"cloud://{env_id}.{cos_file_id}"
                            logger.info(f"文件上传成功: {cloud_id}")
                            
                            return jsonify({
                                'code': 0,
                                'data': {
                                    'cloud_id': cloud_id,
                                    'file_name': file.filename,
                                    'file_size': file_size,
                                    'media_type': media_type,
                                    'mime_type': content_type,
                                    'content_type': content_type,
                                    'storage_path': storage_path
                                }
                            })
                        else:
                            logger.error(f"COS上传失败: {upload_response.status_code} - {upload_response.text}")
                            return jsonify({'code': -1, 'errorMsg': f'文件上传到COS失败: {upload_response.status_code}'})
                    else:
                        logger.error("获取上传URL或授权信息失败")
                        return jsonify({'code': -1, 'errorMsg': '获取上传授权信息不完整'})
                else:
                    logger.error(f"获取上传授权失败: {auth_result}")
                    return jsonify({'code': -1, 'errorMsg': f'获取上传授权失败: {auth_result.get("errmsg", "未知错误")}'})
            else:
                logger.error(f"授权请求失败: {auth_response.status_code} - {auth_response.text}")
                return jsonify({'code': -1, 'errorMsg': f'授权请求失败: HTTP {auth_response.status_code}'})
                
        except requests.exceptions.RequestException as req_error:
            logger.error(f"网络请求异常: {str(req_error)}")
            
            # 如果是连接被拒绝的错误，提供更详细的调试指导
            if "Connection refused" in str(req_error):
                error_msg = (
                    "网络连接被拒绝。请检查本地调试环境配置：\n"
                    "1. 确保已安装VSCode weixin-cloudbase插件\n"
                    "2. 在VSCode Docker面板中启动 api.weixin.qq.com 代理服务\n"
                    "3. 确保容器与代理服务在同一网络中"
                )
                return jsonify({'code': -1, 'errorMsg': error_msg})
            
            return jsonify({'code': -1, 'errorMsg': f'网络请求失败: {str(req_error)}'})
            
        except Exception as upload_error:
            logger.error(f"上传处理异常: {str(upload_error)}")
            logger.error(f"异常详情: {traceback.format_exc()}")
            return jsonify({'code': -1, 'errorMsg': f'上传处理失败: {str(upload_error)}'})
        
    except Exception as e:
        logger.error(f"文件上传总体异常: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        return jsonify({'code': -1, 'errorMsg': f'上传失败: {str(e)}'})

@main_bp.route('/api/file/preview/<filename>')
def preview_file(filename):
    """文件预览接口（临时实现）"""
    # 实际部署时，这个接口应该从云存储获取文件
    return jsonify({'code': -1, 'errorMsg': '预览功能需要在云托管环境中实现'})

@main_bp.route('/api/files/delete', methods=['POST'])
def api_delete_files():
    """批量删除云存储文件API"""
    print(f"🚨🚨🚨 BATCH DELETE API CALLED 🚨🚨🚨")
    logger.info(f"🗑️ 批量删除文件API被调用")
    
    try:
        data = request.get_json()
        print(f"📥 接收到的数据: {data}")
        logger.info(f"📥 接收到的数据: {data}")
        
        file_ids = data.get('file_ids', [])
        print(f"📋 要删除的文件ID列表: {file_ids}")
        logger.info(f"📋 要删除的文件ID列表: {file_ids}")
        
        if not file_ids:
            print("❌ 文件ID列表为空")
            return jsonify({'code': -1, 'errorMsg': '请提供要删除的文件ID列表'})
        
        if len(file_ids) > 50:  # 限制批量删除数量
            print(f"❌ 文件数量超限: {len(file_ids)}")
            return jsonify({'code': -1, 'errorMsg': '单次最多删除50个文件'})
        
        deleted_files = []
        failed_files = []
        
        for i, file_id in enumerate(file_ids):
            print(f"🔄 处理文件 {i+1}/{len(file_ids)}: {file_id}")
            logger.info(f"🔄 处理文件 {i+1}/{len(file_ids)}: {file_id}")
            
            try:
                delete_result = delete_cloud_file(file_id)
                print(f"📤 删除结果: {delete_result}")
                logger.info(f"📤 删除结果: {delete_result}")
                
                if delete_result['success']:
                    deleted_files.append(file_id)
                    print(f"✅ 成功删除云存储文件: {file_id}")
                    logger.info(f"✅ 成功删除云存储文件: {file_id}")
                else:
                    failed_files.append({
                        'file_id': file_id,
                        'error': delete_result['error']
                    })
                    print(f"⚠️ 删除云存储文件失败: {file_id}, 错误: {delete_result['error']}")
                    logger.warning(f"⚠️ 删除云存储文件失败: {file_id}, 错误: {delete_result['error']}")
            except Exception as e:
                failed_files.append({
                    'file_id': file_id,
                    'error': str(e)
                })
                print(f"💥 删除云存储文件异常: {file_id}, 错误: {str(e)}")
                logger.error(f"💥 删除云存储文件异常: {file_id}, 错误: {str(e)}")
        
        # 调整返回格式，与前端期望一致
        result = {
            'message': '',
            'deleted_files': len(deleted_files),  # 前端期望的字段名
            'failed_files': len(failed_files),    # 前端期望的字段名
            'deleted_count': len(deleted_files),
            'failed_count': len(failed_files),
            'deleted_list': deleted_files,
            'failed_list': failed_files
        }
        
        if len(deleted_files) > 0:
            result['message'] = f'成功删除 {len(deleted_files)} 个文件'
            if len(failed_files) > 0:
                result['message'] += f'，{len(failed_files)} 个文件删除失败'
        else:
            result['message'] = '所有文件删除失败'
        
        print(f"🎉 批量删除完成: {result}")
        logger.info(f"🎉 批量删除完成: {result}")
        
        return jsonify({'code': 0, 'data': result})
        
    except Exception as e:
        print(f"💥💥💥 批量删除文件异常: {str(e)} 💥💥💥")
        logger.error(f"💥 批量删除文件异常: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整的异常堆栈
        logger.error(f"📋 异常堆栈: {traceback.format_exc()}")
        return jsonify({'code': -1, 'errorMsg': f'批量删除失败: {str(e)}'})

@main_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
