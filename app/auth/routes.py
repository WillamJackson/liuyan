from flask import redirect, url_for
from app.auth import bp

@bp.route('/login')
def login():
    """重定向到仪表盘（无需登录）"""
    return redirect(url_for('main.dashboard'))

@bp.route('/logout')
def logout():
    """重定向到仪表盘（无需登出）"""
    return redirect(url_for('main.dashboard')) 