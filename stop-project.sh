#!/bin/bash

# 留言板CMS项目停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 停止留言板CMS项目...${NC}"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ 此脚本需要root权限运行${NC}"
   echo "请使用: sudo ./stop-project.sh"
   exit 1
fi

# 1. 停止Liuyan CMS服务
echo -e "${YELLOW}🛑 停止Liuyan CMS服务...${NC}"
if systemctl is-active --quiet liuyan; then
    systemctl stop liuyan
    echo -e "${GREEN}✅ Liuyan CMS服务已停止${NC}"
else
    echo -e "${YELLOW}⚠️  Liuyan CMS服务未运行${NC}"
fi

# 2. 停止相关进程
echo -e "${YELLOW}🛑 停止相关进程...${NC}"
if pgrep -f "gunicorn.*wsgi:app" > /dev/null; then
    pkill -f "gunicorn.*wsgi:app"
    echo -e "${GREEN}✅ Gunicorn进程已停止${NC}"
else
    echo -e "${YELLOW}⚠️  未发现Gunicorn进程${NC}"
fi

# 3. 选择是否停止Nginx
echo -e "${YELLOW}❓ 是否停止Nginx服务? (y/N)${NC}"
read -t 10 -r response || response="n"
case $response in
    [yY]|[yY][eE][sS])
        echo -e "${YELLOW}🛑 停止Nginx服务...${NC}"
        if systemctl is-active --quiet nginx; then
            systemctl stop nginx
            echo -e "${GREEN}✅ Nginx服务已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  Nginx服务未运行${NC}"
        fi
        ;;
    *)
        echo -e "${YELLOW}⚠️  保持Nginx服务运行${NC}"
        ;;
esac

# 4. 等待进程完全停止
echo -e "${YELLOW}⏳ 等待进程完全停止...${NC}"
sleep 2

# 5. 检查停止状态
echo -e "${YELLOW}📊 检查停止状态...${NC}"

echo "=== Liuyan CMS 服务状态 ==="
if systemctl is-active --quiet liuyan; then
    echo -e "${RED}❌ Liuyan CMS 服务仍在运行${NC}"
    systemctl status liuyan --no-pager -l | head -5
else
    echo -e "${GREEN}✅ Liuyan CMS 服务已停止${NC}"
fi

echo ""
echo "=== Gunicorn 进程状态 ==="
if pgrep -f "gunicorn.*wsgi:app" > /dev/null; then
    echo -e "${RED}❌ 仍有Gunicorn进程运行${NC}"
    pgrep -f "gunicorn.*wsgi:app" | xargs ps -p
else
    echo -e "${GREEN}✅ 所有Gunicorn进程已停止${NC}"
fi

echo ""
echo "=== Nginx 服务状态 ==="
if systemctl is-active --quiet nginx; then
    echo -e "${YELLOW}⚠️  Nginx 服务仍在运行${NC}"
else
    echo -e "${GREEN}✅ Nginx 服务已停止${NC}"
fi

# 6. 检查端口占用
echo ""
echo "=== 端口占用状态 ==="
if netstat -tlnp | grep -q ":8000 "; then
    echo -e "${RED}❌ 端口8000仍被占用${NC}"
    netstat -tlnp | grep ":8000 "
else
    echo -e "${GREEN}✅ 端口8000已释放${NC}"
fi

if netstat -tlnp | grep -q ":80 "; then
    echo -e "${YELLOW}⚠️  端口80仍被占用 (可能是Nginx)${NC}"
else
    echo -e "${GREEN}✅ 端口80已释放${NC}"
fi

# 7. 显示停止完成信息
echo -e "\n${GREEN}🎉 项目停止完成！${NC}"

echo -e "\n${YELLOW}🔧 常用命令:${NC}"
echo "  启动项目: sudo ./start-project.sh"
echo "  重启项目: sudo ./restart-project.sh"
echo "  查看服务状态: sudo systemctl status liuyan"
echo "  查看进程: ps aux | grep gunicorn"

# 8. 清理选项
echo -e "\n${YELLOW}❓ 是否清理日志文件? (y/N)${NC}"
read -t 10 -r response || response="n"
case $response in
    [yY]|[yY][eE][sS])
        echo -e "${YELLOW}🧹 清理日志文件...${NC}"
        truncate -s 0 /var/log/nginx/liuyan_access.log 2>/dev/null || true
        truncate -s 0 /var/log/nginx/liuyan_error.log 2>/dev/null || true
        journalctl --vacuum-time=1d --quiet || true
        echo -e "${GREEN}✅ 日志文件已清理${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠️  保留日志文件${NC}"
        ;;
esac

echo -e "\n${GREEN}🎊 停止脚本执行完成！${NC}" 