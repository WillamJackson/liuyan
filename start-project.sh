#!/bin/bash

# 留言板CMS项目启动脚本
# 项目路径: /usr/local/liuyan
# Conda环境: liuyan

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="/usr/local/liuyan"
CONDA_ENV="liuyan"
GUNICORN_PORT="8000"
NGINX_SITE="liuyan"

echo -e "${BLUE}🚀 启动留言板CMS项目...${NC}"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ 此脚本需要root权限运行${NC}"
   echo "请使用: sudo ./start-project.sh"
   exit 1
fi

# 1. 检查项目目录
echo -e "${YELLOW}📁 检查项目目录...${NC}"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 项目目录不存在: $PROJECT_DIR${NC}"
    exit 1
fi

cd $PROJECT_DIR
echo -e "${GREEN}✅ 项目目录: $PROJECT_DIR${NC}"

# 2. 检查conda环境
echo -e "${YELLOW}🐍 检查Conda环境...${NC}"
if ! conda info --envs | grep -q "$CONDA_ENV"; then
    echo -e "${RED}❌ Conda环境不存在: $CONDA_ENV${NC}"
    echo "请先创建环境: conda create -n $CONDA_ENV python=3.9"
    exit 1
fi

# 获取conda环境的实际路径
CONDA_BASE=$(conda info --base)
CONDA_ENV_PATH="$CONDA_BASE/envs/$CONDA_ENV"

# 检查conda环境路径是否存在
if [ ! -d "$CONDA_ENV_PATH" ]; then
    echo -e "${RED}❌ Conda环境路径不存在: $CONDA_ENV_PATH${NC}"
    exit 1
fi

# 检查gunicorn是否安装
GUNICORN_PATH="$CONDA_ENV_PATH/bin/gunicorn"
if [ ! -f "$GUNICORN_PATH" ]; then
    echo -e "${RED}❌ Gunicorn未安装在环境中: $GUNICORN_PATH${NC}"
    echo "请安装gunicorn: conda activate $CONDA_ENV && pip install gunicorn"
    exit 1
fi

echo -e "${GREEN}✅ Conda环境存在: $CONDA_ENV${NC}"
echo -e "${GREEN}✅ Conda环境路径: $CONDA_ENV_PATH${NC}"
echo -e "${GREEN}✅ Gunicorn路径: $GUNICORN_PATH${NC}"

# 3. 创建必要目录
echo -e "${YELLOW}📂 创建必要目录...${NC}"
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/static/uploads
mkdir -p /var/log/nginx

# 设置权限
chown -R www-data:www-data $PROJECT_DIR/static/uploads
chown -R www-data:www-data $PROJECT_DIR/logs
chmod -R 755 $PROJECT_DIR/static
chmod -R 755 $PROJECT_DIR/logs

echo -e "${GREEN}✅ 目录权限设置完成${NC}"

# 4. 配置Nginx
echo -e "${YELLOW}⚙️  配置Nginx...${NC}"

# 创建Nginx配置文件
cat > /etc/nginx/sites-available/$NGINX_SITE << 'EOF'
server {
    listen 80 default_server;
    server_name _;
    
    # 日志文件
    access_log /var/log/nginx/liuyan_access.log;
    error_log /var/log/nginx/liuyan_error.log;
    
    # 客户端最大上传大小
    client_max_body_size 16M;
    
    # 静态文件处理
    location /static/ {
        alias /usr/local/liuyan/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        
        # 启用gzip压缩
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    # 上传文件处理
    location /static/uploads/ {
        alias /usr/local/liuyan/static/uploads/;
        expires 7d;
        add_header Cache-Control "public";
        
        # 防止执行脚本
        location ~* \.(php|py|sh|exe)$ {
            deny all;
        }
    }
    
    # 代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 16 8k;
    }
    
    # 安全头设置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 隐藏Nginx版本
    server_tokens off;
}
EOF

# 启用站点
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/$NGINX_SITE
ln -s /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/

# 测试Nginx配置
if nginx -t; then
    echo -e "${GREEN}✅ Nginx配置语法正确${NC}"
else
    echo -e "${RED}❌ Nginx配置语法错误${NC}"
    exit 1
fi

# 5. 创建systemd服务文件
echo -e "${YELLOW}🔧 创建systemd服务...${NC}"

cat > /etc/systemd/system/liuyan.service << EOF
[Unit]
Description=Liuyan CMS Gunicorn Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$CONDA_ENV_PATH/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$GUNICORN_PATH -c $PROJECT_DIR/gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload

# 6. 停止可能运行的服务
echo -e "${YELLOW}🛑 停止可能运行的服务...${NC}"
systemctl stop liuyan 2>/dev/null || true
pkill -f gunicorn 2>/dev/null || true

# 7. 启动服务
echo -e "${YELLOW}🚀 启动服务...${NC}"

# 启动并启用liuyan服务
systemctl enable liuyan
systemctl start liuyan

# 启动Nginx
systemctl enable nginx
systemctl restart nginx

# 8. 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 3

# 9. 检查服务状态
echo -e "${YELLOW}📊 检查服务状态...${NC}"

echo "=== Liuyan CMS 服务状态 ==="
if systemctl is-active --quiet liuyan; then
    echo -e "${GREEN}✅ Liuyan CMS 服务运行正常${NC}"
    systemctl status liuyan --no-pager -l | head -10
else
    echo -e "${RED}❌ Liuyan CMS 服务启动失败${NC}"
    systemctl status liuyan --no-pager -l | head -10
fi

echo ""
echo "=== Nginx 服务状态 ==="
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx 服务运行正常${NC}"
    systemctl status nginx --no-pager -l | head -10
else
    echo -e "${RED}❌ Nginx 服务启动失败${NC}"
    systemctl status nginx --no-pager -l | head -10
fi

# 10. 检查端口监听
echo ""
echo "=== 端口监听状态 ==="
if netstat -tlnp | grep -q ":80 "; then
    echo -e "${GREEN}✅ Nginx (端口80) 监听正常${NC}"
else
    echo -e "${RED}❌ Nginx (端口80) 未监听${NC}"
fi

if netstat -tlnp | grep -q ":$GUNICORN_PORT "; then
    echo -e "${GREEN}✅ Gunicorn (端口$GUNICORN_PORT) 监听正常${NC}"
else
    echo -e "${RED}❌ Gunicorn (端口$GUNICORN_PORT) 未监听${NC}"
fi

# 11. 显示部署信息
echo -e "\n${GREEN}🎉 项目启动完成！${NC}"
echo -e "${YELLOW}📋 项目信息:${NC}"
echo "  项目目录: $PROJECT_DIR"
echo "  Conda环境: $CONDA_ENV"
echo "  Nginx配置: /etc/nginx/sites-available/$NGINX_SITE"
echo "  访问日志: /var/log/nginx/liuyan_access.log"
echo "  错误日志: /var/log/nginx/liuyan_error.log"
echo "  系统服务: liuyan.service"
echo ""
echo -e "${YELLOW}🔧 常用命令:${NC}"
echo "  查看应用日志: sudo journalctl -u liuyan -f"
echo "  查看Nginx日志: sudo tail -f /var/log/nginx/liuyan_access.log"
echo "  重启项目: sudo ./restart-project.sh"
echo "  停止项目: sudo ./stop-project.sh"
echo ""

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo -e "${GREEN}✅ 访问地址: http://$SERVER_IP${NC}"
echo -e "${GREEN}✅ 本地访问: http://localhost${NC}"

echo -e "\n${GREEN}🎊 项目启动脚本执行完成！${NC}" 