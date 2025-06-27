#!/bin/bash

# 留言板CMS项目重启脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 重启留言板CMS项目...${NC}"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ 此脚本需要root权限运行${NC}"
   echo "请使用: sudo ./restart-project.sh"
   exit 1
fi

# 1. 重启Liuyan CMS服务
echo -e "${YELLOW}🔄 重启Liuyan CMS服务...${NC}"
if systemctl is-active --quiet liuyan; then
    systemctl restart liuyan
    echo -e "${GREEN}✅ Liuyan CMS服务重启完成${NC}"
else
    echo -e "${YELLOW}⚠️  Liuyan CMS服务未运行，正在启动...${NC}"
    systemctl start liuyan
    echo -e "${GREEN}✅ Liuyan CMS服务启动完成${NC}"
fi

# 2. 重启Nginx服务
echo -e "${YELLOW}🔄 重启Nginx服务...${NC}"
if systemctl is-active --quiet nginx; then
    systemctl restart nginx
    echo -e "${GREEN}✅ Nginx服务重启完成${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx服务未运行，正在启动...${NC}"
    systemctl start nginx
    echo -e "${GREEN}✅ Nginx服务启动完成${NC}"
fi

# 3. 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 3

# 4. 检查服务状态
echo -e "${YELLOW}📊 检查服务状态...${NC}"

echo "=== Liuyan CMS 服务状态 ==="
if systemctl is-active --quiet liuyan; then
    echo -e "${GREEN}✅ Liuyan CMS 服务运行正常${NC}"
else
    echo -e "${RED}❌ Liuyan CMS 服务异常${NC}"
    systemctl status liuyan --no-pager -l | head -5
fi

echo ""
echo "=== Nginx 服务状态 ==="
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx 服务运行正常${NC}"
else
    echo -e "${RED}❌ Nginx 服务异常${NC}"
    systemctl status nginx --no-pager -l | head -5
fi

# 5. 检查端口监听
echo ""
echo "=== 端口监听状态 ==="
if netstat -tlnp | grep -q ":80 "; then
    echo -e "${GREEN}✅ Nginx (端口80) 监听正常${NC}"
else
    echo -e "${RED}❌ Nginx (端口80) 未监听${NC}"
fi

if netstat -tlnp | grep -q ":8000 "; then
    echo -e "${GREEN}✅ Gunicorn (端口8000) 监听正常${NC}"
else
    echo -e "${RED}❌ Gunicorn (端口8000) 未监听${NC}"
fi

# 6. 显示重启完成信息
echo -e "\n${GREEN}🎉 项目重启完成！${NC}"

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo -e "${GREEN}✅ 访问地址: http://$SERVER_IP${NC}"

echo -e "\n${YELLOW}🔧 如需查看日志:${NC}"
echo "  应用日志: sudo journalctl -u liuyan -f"
echo "  Nginx日志: sudo tail -f /var/log/nginx/liuyan_access.log"

echo -e "\n${GREEN}🎊 重启脚本执行完成！${NC}" 