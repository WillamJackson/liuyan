#!/bin/bash

# 留言板CMS项目状态检查脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 留言板CMS项目状态检查...${NC}"

# 配置变量
PROJECT_DIR="/usr/local/liuyan"
CONDA_ENV="liuyan"

echo -e "${CYAN}===========================================${NC}"
echo -e "${CYAN}         留言板CMS系统状态报告${NC}"
echo -e "${CYAN}===========================================${NC}"

# 1. 系统信息
echo -e "\n${YELLOW}🖥️  系统信息${NC}"
echo "  操作系统: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
echo "  内核版本: $(uname -r)"
echo "  系统时间: $(date)"
echo "  运行时间: $(uptime -p 2>/dev/null || uptime)"

# 2. 项目目录状态
echo -e "\n${YELLOW}📁 项目目录状态${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo -e "  项目目录: ${GREEN}✅ 存在${NC} ($PROJECT_DIR)"
    echo "  目录大小: $(du -sh $PROJECT_DIR 2>/dev/null | cut -f1)"
    echo "  文件权限: $(ls -ld $PROJECT_DIR | cut -d' ' -f1,3,4)"
    
    # 检查重要文件
    if [ -f "$PROJECT_DIR/wsgi.py" ]; then
        echo -e "  wsgi.py: ${GREEN}✅ 存在${NC}"
    else
        echo -e "  wsgi.py: ${RED}❌ 不存在${NC}"
    fi
    
    if [ -f "$PROJECT_DIR/gunicorn.conf.py" ]; then
        echo -e "  gunicorn.conf.py: ${GREEN}✅ 存在${NC}"
    else
        echo -e "  gunicorn.conf.py: ${RED}❌ 不存在${NC}"
    fi
    
    if [ -d "$PROJECT_DIR/static/uploads" ]; then
        echo -e "  上传目录: ${GREEN}✅ 存在${NC}"
        echo "  上传文件数: $(find $PROJECT_DIR/static/uploads -type f 2>/dev/null | wc -l)"
    else
        echo -e "  上传目录: ${RED}❌ 不存在${NC}"
    fi
else
    echo -e "  项目目录: ${RED}❌ 不存在${NC} ($PROJECT_DIR)"
fi

# 3. Conda环境状态
echo -e "\n${YELLOW}🐍 Conda环境状态${NC}"
if command -v conda >/dev/null 2>&1; then
    echo -e "  Conda: ${GREEN}✅ 已安装${NC}"
    echo "  Conda版本: $(conda --version)"
    
    if conda env list | grep -q "^$CONDA_ENV "; then
        echo -e "  环境 '$CONDA_ENV': ${GREEN}✅ 存在${NC}"
        # 检查Python版本
        PYTHON_VERSION=$(conda run -n $CONDA_ENV python --version 2>/dev/null || echo "无法获取")
        echo "  Python版本: $PYTHON_VERSION"
    else
        echo -e "  环境 '$CONDA_ENV': ${RED}❌ 不存在${NC}"
    fi
else
    echo -e "  Conda: ${RED}❌ 未安装${NC}"
fi

# 4. 服务状态
echo -e "\n${YELLOW}🔧 服务状态${NC}"

# Liuyan CMS服务
if systemctl list-unit-files | grep -q "liuyan.service"; then
    if systemctl is-active --quiet liuyan; then
        echo -e "  Liuyan CMS: ${GREEN}✅ 运行中${NC}"
        echo "  启动时间: $(systemctl show liuyan --property=ActiveEnterTimestamp --value)"
        echo "  PID: $(systemctl show liuyan --property=MainPID --value)"
    else
        echo -e "  Liuyan CMS: ${RED}❌ 已停止${NC}"
        echo "  状态: $(systemctl is-active liuyan)"
    fi
    
    if systemctl is-enabled --quiet liuyan; then
        echo -e "  开机启动: ${GREEN}✅ 已启用${NC}"
    else
        echo -e "  开机启动: ${YELLOW}⚠️  未启用${NC}"
    fi
else
    echo -e "  Liuyan CMS: ${RED}❌ 服务未配置${NC}"
fi

# Nginx服务
if systemctl list-unit-files | grep -q "nginx.service"; then
    if systemctl is-active --quiet nginx; then
        echo -e "  Nginx: ${GREEN}✅ 运行中${NC}"
        echo "  启动时间: $(systemctl show nginx --property=ActiveEnterTimestamp --value)"
    else
        echo -e "  Nginx: ${RED}❌ 已停止${NC}"
        echo "  状态: $(systemctl is-active nginx)"
    fi
    
    if systemctl is-enabled --quiet nginx; then
        echo -e "  开机启动: ${GREEN}✅ 已启用${NC}"
    else
        echo -e "  开机启动: ${YELLOW}⚠️  未启用${NC}"
    fi
else
    echo -e "  Nginx: ${RED}❌ 未安装${NC}"
fi

# 5. 进程状态
echo -e "\n${YELLOW}⚡ 进程状态${NC}"

# Gunicorn进程
GUNICORN_PIDS=$(pgrep -f "gunicorn.*wsgi:app" 2>/dev/null || echo "")
if [ -n "$GUNICORN_PIDS" ]; then
    echo -e "  Gunicorn: ${GREEN}✅ 运行中${NC}"
    echo "  进程数: $(echo $GUNICORN_PIDS | wc -w)"
    echo "  PID: $GUNICORN_PIDS"
    
    # 显示内存使用
    MEMORY_USAGE=$(ps -p $GUNICORN_PIDS -o pid,rss --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum/1024}' || echo "0")
    echo "  内存使用: ${MEMORY_USAGE} MB"
else
    echo -e "  Gunicorn: ${RED}❌ 未运行${NC}"
fi

# Nginx进程
NGINX_PIDS=$(pgrep nginx 2>/dev/null || echo "")
if [ -n "$NGINX_PIDS" ]; then
    echo -e "  Nginx: ${GREEN}✅ 运行中${NC}"
    echo "  进程数: $(echo $NGINX_PIDS | wc -w)"
else
    echo -e "  Nginx: ${RED}❌ 未运行${NC}"
fi

# 6. 端口监听状态
echo -e "\n${YELLOW}🌐 端口监听状态${NC}"

# 检查端口80
if netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "  端口 80 (HTTP): ${GREEN}✅ 监听中${NC}"
    PORT_80_PROCESS=$(netstat -tlnp 2>/dev/null | grep ":80 " | awk '{print $7}' | head -1)
    echo "  进程: $PORT_80_PROCESS"
else
    echo -e "  端口 80 (HTTP): ${RED}❌ 未监听${NC}"
fi

# 检查端口8000
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "  端口 8000 (Gunicorn): ${GREEN}✅ 监听中${NC}"
    PORT_8000_PROCESS=$(netstat -tlnp 2>/dev/null | grep ":8000 " | awk '{print $7}' | head -1)
    echo "  进程: $PORT_8000_PROCESS"
else
    echo -e "  端口 8000 (Gunicorn): ${RED}❌ 未监听${NC}"
fi

# 检查端口443
if netstat -tlnp 2>/dev/null | grep -q ":443 "; then
    echo -e "  端口 443 (HTTPS): ${GREEN}✅ 监听中${NC}"
else
    echo -e "  端口 443 (HTTPS): ${YELLOW}⚠️  未监听${NC}"
fi

# 7. Nginx配置状态
echo -e "\n${YELLOW}⚙️  Nginx配置状态${NC}"

if [ -f "/etc/nginx/sites-available/liuyan" ]; then
    echo -e "  配置文件: ${GREEN}✅ 存在${NC} (/etc/nginx/sites-available/liuyan)"
else
    echo -e "  配置文件: ${RED}❌ 不存在${NC}"
fi

if [ -L "/etc/nginx/sites-enabled/liuyan" ]; then
    echo -e "  配置启用: ${GREEN}✅ 已启用${NC}"
else
    echo -e "  配置启用: ${RED}❌ 未启用${NC}"
fi

# 测试Nginx配置
if command -v nginx >/dev/null 2>&1; then
    if nginx -t >/dev/null 2>&1; then
        echo -e "  配置语法: ${GREEN}✅ 正确${NC}"
    else
        echo -e "  配置语法: ${RED}❌ 错误${NC}"
    fi
fi

# 8. 日志文件状态
echo -e "\n${YELLOW}📝 日志文件状态${NC}"

# Nginx日志
if [ -f "/var/log/nginx/liuyan_access.log" ]; then
    LOG_SIZE=$(du -sh /var/log/nginx/liuyan_access.log 2>/dev/null | cut -f1)
    echo -e "  Nginx访问日志: ${GREEN}✅ 存在${NC} (大小: $LOG_SIZE)"
else
    echo -e "  Nginx访问日志: ${RED}❌ 不存在${NC}"
fi

if [ -f "/var/log/nginx/liuyan_error.log" ]; then
    LOG_SIZE=$(du -sh /var/log/nginx/liuyan_error.log 2>/dev/null | cut -f1)
    echo -e "  Nginx错误日志: ${GREEN}✅ 存在${NC} (大小: $LOG_SIZE)"
else
    echo -e "  Nginx错误日志: ${RED}❌ 不存在${NC}"
fi

# 应用日志
if journalctl -u liuyan --since "1 hour ago" --quiet >/dev/null 2>&1; then
    LOG_LINES=$(journalctl -u liuyan --since "1 hour ago" --no-pager | wc -l)
    echo -e "  应用日志: ${GREEN}✅ 可访问${NC} (最近1小时: $LOG_LINES 行)"
else
    echo -e "  应用日志: ${YELLOW}⚠️  无法访问${NC}"
fi

# 9. 磁盘空间
echo -e "\n${YELLOW}💾 磁盘空间状态${NC}"
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "  根目录使用率: ${GREEN}✅ ${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "  根目录使用率: ${YELLOW}⚠️  ${DISK_USAGE}%${NC}"
else
    echo -e "  根目录使用率: ${RED}❌ ${DISK_USAGE}%${NC}"
fi

# 10. 网络连接测试
echo -e "\n${YELLOW}🌍 网络连接测试${NC}"

# 本地连接测试
if curl -s -o /dev/null -w "%{http_code}" http://localhost >/dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  本地HTTP连接: ${GREEN}✅ 正常 (${HTTP_CODE})${NC}"
    else
        echo -e "  本地HTTP连接: ${YELLOW}⚠️  异常 (${HTTP_CODE})${NC}"
    fi
else
    echo -e "  本地HTTP连接: ${RED}❌ 失败${NC}"
fi

# 获取公网IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取")
echo "  公网IP: $PUBLIC_IP"

# 11. 总结
echo -e "\n${CYAN}===========================================${NC}"
echo -e "${CYAN}              状态检查完成${NC}"
echo -e "${CYAN}===========================================${NC}"

echo -e "\n${YELLOW}🔧 管理命令:${NC}"
echo "  启动项目: sudo ./start-project.sh"
echo "  重启项目: sudo ./restart-project.sh"
echo "  停止项目: sudo ./stop-project.sh"
echo "  查看状态: ./status-project.sh"
echo ""
echo "  查看应用日志: sudo journalctl -u liuyan -f"
echo "  查看Nginx日志: sudo tail -f /var/log/nginx/liuyan_access.log"
echo "  查看错误日志: sudo tail -f /var/log/nginx/liuyan_error.log"

echo -e "\n${GREEN}📊 状态检查报告生成完成！${NC}" 