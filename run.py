#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用启动脚本
"""

import os
from app import create_app
from app.models import db, User, Category, Tag, SystemSettings
from werkzeug.security import generate_password_hash

def create_default_data():
    """创建默认数据"""
    # 创建默认管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        print("✅ 创建默认管理员用户: admin / admin123")
    
    # 创建默认分类
    default_categories = [
        {'name': '技术文章', 'description': '技术相关文章和教程', 'sort_order': 1},
        {'name': '生活分享', 'description': '生活感悟和日常分享', 'sort_order': 2},
        {'name': '资源收藏', 'description': '有用的工具和资源链接', 'sort_order': 3},
        {'name': '项目展示', 'description': '个人项目和作品展示', 'sort_order': 4}
    ]
    
    for cat_data in default_categories:
        if not Category.query.filter_by(name=cat_data['name']).first():
            category = Category(**cat_data)
            db.session.add(category)
            print(f"✅ 创建默认分类: {cat_data['name']}")
    
    # 创建默认标签
    default_tags = ['技术', '生活', '工作', '学习', '分享', '工具', '资源', '教程']
    for tag_name in default_tags:
        if not Tag.query.filter_by(name=tag_name).first():
            tag = Tag(name=tag_name)
            db.session.add(tag)
            print(f"✅ 创建默认标签: {tag_name}")
    
    # 创建默认系统设置
    default_settings = [
        {'key': 'site_title', 'value': '内容管理系统', 'description': '网站标题'},
        {'key': 'site_description', 'value': '微信小程序内容管理后台', 'description': '网站描述'},
        {'key': 'posts_per_page', 'value': '20', 'description': '每页显示文章数'},
        {'key': 'upload_max_size', 'value': '16777216', 'description': '上传文件最大大小(字节)'},
        {'key': 'allowed_file_types', 'value': 'jpg,jpeg,png,gif,mp4,avi,mov,pdf,doc,docx', 'description': '允许上传的文件类型'}
    ]
    
    for setting_data in default_settings:
        if not SystemSettings.query.filter_by(key=setting_data['key']).first():
            setting = SystemSettings(**setting_data)
            db.session.add(setting)
            print(f"✅ 创建默认设置: {setting_data['key']}")
    
    db.session.commit()

if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('FLASK_CONFIG', 'development')
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        print("✅ 数据库表创建完成")
        
        # 创建默认数据
        create_default_data()
        
        print("\n" + "="*50)
        print("🚀 Flask应用启动成功！")
        print("📍 访问地址: http://localhost:5000")
        print("👤 管理员账户: admin / admin123")
        print("="*50 + "\n")
    
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=80,
        debug=True,
        use_reloader=True
    ) 