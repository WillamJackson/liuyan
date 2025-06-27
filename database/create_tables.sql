-- 微信小程序内容管理系统数据库建表脚本
-- 数据库版本: MySQL 8.0+
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci

-- 创建数据库
CREATE DATABASE IF NOT EXISTS cms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cms_db;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(80) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(120) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 2. 分类表
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    description TEXT COMMENT '分类描述',
    parent_id INT DEFAULT NULL COMMENT '父分类ID',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_name (name),
    INDEX idx_parent_id (parent_id),
    INDEX idx_sort_order (sort_order),
    
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类表';

-- 3. 标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '标签ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '标签名称',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- 4. 内容表
CREATE TABLE IF NOT EXISTS contents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '内容ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',

    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态: draft, published, pending',
    view_count INT DEFAULT 0 COMMENT '浏览量',
    is_featured BOOLEAN DEFAULT FALSE COMMENT '是否推荐',

    category_id INT COMMENT '分类ID',
    user_id INT NOT NULL COMMENT '用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    published_at TIMESTAMP NULL COMMENT '发布时间',
    
    INDEX idx_title (title),

    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_published_at (published_at),
    INDEX idx_category_id (category_id),
    INDEX idx_user_id (user_id),
    
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容表';

-- 5. 内容标签关联表
CREATE TABLE IF NOT EXISTS content_tags (
    content_id INT NOT NULL COMMENT '内容ID',
    tag_id INT NOT NULL COMMENT '标签ID',
    
    PRIMARY KEY (content_id, tag_id),
    INDEX idx_content_id (content_id),
    INDEX idx_tag_id (tag_id),
    
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容标签关联表';

-- 6. 媒体文件表
CREATE TABLE IF NOT EXISTS media_files (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '媒体文件ID',
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    original_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size INT NOT NULL COMMENT '文件大小(字节)',
    file_type VARCHAR(50) NOT NULL COMMENT '文件类型: images, videos, documents, archives',
    mime_type VARCHAR(100) NOT NULL COMMENT 'MIME类型',
    file_hash VARCHAR(32) COMMENT 'MD5哈希值，用于去重',
    url VARCHAR(500) COMMENT '文件访问URL',
    thumbnail_url VARCHAR(500) COMMENT '缩略图URL',
    width INT COMMENT '图片宽度',
    height INT COMMENT '图片高度',
    alt_text VARCHAR(200) COMMENT '替代文本',
    description TEXT COMMENT '文件描述',
    user_id INT NOT NULL COMMENT '上传用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_filename (filename),
    INDEX idx_file_type (file_type),
    INDEX idx_file_hash (file_hash),
    INDEX idx_created_at (created_at),
    INDEX idx_user_id (user_id),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='媒体文件表';

-- 7. 系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '设置ID',
    `key` VARCHAR(100) NOT NULL UNIQUE COMMENT '设置键',
    `value` TEXT COMMENT '设置值',
    description VARCHAR(300) COMMENT '设置描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统设置表';

-- 插入默认数据

-- 插入默认分类
INSERT INTO categories (name, description, sort_order) VALUES
('技术文章', '技术相关文章和教程', 1),
('生活分享', '生活感悟和日常分享', 2),
('资源收藏', '有用的工具和资源链接', 3),
('项目展示', '个人项目和作品展示', 4);

-- 插入默认标签
INSERT INTO tags (name) VALUES
('技术'),
('生活'),
('工作'),
('学习'),
('分享'),
('工具'),
('资源'),
('教程');

-- 插入默认系统设置
INSERT INTO system_settings (`key`, `value`, description) VALUES
('site_title', '内容管理系统', '网站标题'),
('site_description', '微信小程序内容管理后台', '网站描述'),
('posts_per_page', '20', '每页显示文章数'),
('upload_max_size', '16777216', '上传文件最大大小(字节)'),
('allowed_file_types', 'jpg,jpeg,png,gif,mp4,avi,mov,pdf,doc,docx', '允许上传的文件类型');

-- 创建全文索引（MySQL 5.7+）
-- ALTER TABLE contents ADD FULLTEXT INDEX idx_content_fulltext (title, content);

COMMIT; 