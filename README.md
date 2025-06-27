# 微信小程序内容管理系统

一个基于Flask的现代化内容管理系统，专为微信小程序后端设计。

## 项目特性

- 🚀 **现代化架构**: 基于Flask + SQLAlchemy + MySQL
- 📱 **移动优先**: 响应式设计，适配各种设备
- 🔐 **安全可靠**: 用户认证、权限控制、CSRF保护
- 📝 **内容管理**: 支持博客、软件资源、网站地址、评论等多种内容类型
- 🖼️ **媒体管理**: 文件上传、图片压缩、缩略图生成
- 🏷️ **分类标签**: 灵活的分类和标签系统
- 📊 **数据统计**: 实时统计和数据分析
- 🎨 **美观界面**: 基于Tailwind CSS的现代化UI

## 技术栈

- **后端**: Flask 2.3.3
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy
- **前端**: HTML5 + Tailwind CSS + JavaScript
- **图片处理**: Pillow
- **认证**: Flask-Login

## 项目结构

```
liuyan/
├── app/                    # 应用包
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   ├── main/              # 主要页面路由
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── auth/              # 认证路由
│   │   ├── __init__.py
│   │   └── routes.py
│   └── api/               # API路由
│       ├── __init__.py
│       └── routes.py
├── templates/             # HTML模板
│   ├── auth/
│   └── errors/
├── static/               # 静态文件
│   └── uploads/          # 上传文件目录
├── database/             # 数据库脚本
│   └── create_tables.sql
├── config.py             # 配置文件
├── app.py                # 应用入口
├── run.py                # 启动脚本
├── requirements.txt      # 依赖列表
└── README.md            # 项目说明
```

## 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.7+
- MySQL 8.0+
- pip

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置

1. 创建MySQL数据库：
```sql
CREATE DATABASE cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 修改 `config.py` 中的数据库连接信息：
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://用户名:密码@localhost:3306/cms_db?charset=utf8mb4'
```

3. 或者执行SQL脚本：
```bash
mysql -u root -p < database/create_tables.sql
```

### 4. 启动应用

```bash
python run.py
```

应用将在 http://localhost:5000 启动

### 5. 登录系统

- 用户名: `admin`
- 密码: `admin123`

## API接口

### 认证接口

- `POST /auth/login` - 用户登录
- `GET /auth/logout` - 用户登出
- `POST /auth/change-password` - 修改密码

### 内容管理接口

- `GET /api/contents` - 获取内容列表
- `POST /api/contents` - 创建内容
- `GET /api/contents/<id>` - 获取单个内容
- `PUT /api/contents/<id>` - 更新内容
- `DELETE /api/contents/<id>` - 删除内容

### 媒体文件接口

- `POST /api/media/upload` - 上传文件
- `GET /api/media` - 获取媒体文件列表
- `GET /api/media/files/<path>` - 访问媒体文件

### 分类标签接口

- `GET /api/categories` - 获取分类列表
- `POST /api/categories` - 创建分类
- `GET /api/tags` - 获取标签列表

### 统计接口

- `GET /api/dashboard/stats` - 获取仪表盘统计数据

## 数据库表结构

### 用户表 (users)
- 用户认证和基本信息

### 内容表 (contents)
- 存储所有类型的内容（博客、软件资源、网站地址、评论）

### 分类表 (categories)
- 支持层级分类结构

### 标签表 (tags)
- 内容标签系统

### 媒体文件表 (media_files)
- 上传文件的元数据

### 系统设置表 (system_settings)
- 可配置的系统参数

## 功能特性

### 内容管理
- ✅ 多种内容类型支持
- ✅ 富文本编辑
- ✅ 草稿和发布状态
- ✅ 分类和标签
- ✅ 搜索和筛选
- ✅ 批量操作

### 媒体管理
- ✅ 文件上传
- ✅ 图片压缩
- ✅ 缩略图生成
- ✅ 文件类型验证
- ✅ 存储空间统计

### 用户管理
- ✅ 用户认证
- ✅ 会话管理
- ✅ 权限控制
- ✅ 密码修改

### 系统管理
- ✅ 系统设置
- ✅ 数据统计
- ✅ 错误处理
- ✅ 日志记录

## 开发指南

### 添加新功能

1. 在 `app/models.py` 中定义数据模型
2. 在相应的蓝图中添加路由
3. 创建HTML模板
4. 更新API接口

### 自定义配置

修改 `config.py` 文件中的配置项：

```python
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'your-database-url'
    UPLOAD_FOLDER = 'your-upload-path'
    # 其他配置...
```

### 部署到生产环境

1. 设置环境变量 `FLASK_CONFIG=production`
2. 配置生产数据库
3. 设置安全的SECRET_KEY
4. 配置Web服务器（如Nginx + Gunicorn）

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发者。

---

**注意**: 这是一个开发版本，请在生产环境中修改默认密码和安全配置。 