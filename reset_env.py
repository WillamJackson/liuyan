#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
重置环境变量并启动应用
"""

import os
import sys

# 强制设置正确的环境变量
os.environ['MYSQL_USERNAME'] = 'root'
os.environ['MYSQL_PASSWORD'] = 'Xx562137890'
os.environ['MYSQL_ADDRESS'] = '10.35.103.199:3306'

print("🔧 强制重置环境变量:")
print(f"  MYSQL_USERNAME: {os.environ['MYSQL_USERNAME']}")
print(f"  MYSQL_PASSWORD: {os.environ['MYSQL_PASSWORD']}")
print(f"  MYSQL_ADDRESS: {os.environ['MYSQL_ADDRESS']}")
print("=" * 50)

# 导入并启动应用
if __name__ == "__main__":
    from wxcloudrun import app
    
    # 启动应用
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    
    print(f"🚀 启动应用: {host}:{port}")
    app.run(host=host, port=port, debug=True) 