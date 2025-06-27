-- 媒体文件表结构更新迁移脚本
-- 用于将现有的media_files表结构更新为新版本

USE cms_db;

-- 添加新字段
ALTER TABLE media_files 
ADD COLUMN file_hash VARCHAR(32) COMMENT 'MD5哈希值，用于去重' AFTER mime_type,
ADD COLUMN url VARCHAR(500) COMMENT '文件访问URL' AFTER file_hash,
ADD COLUMN thumbnail_url VARCHAR(500) COMMENT '缩略图URL' AFTER url,
ADD COLUMN width INT COMMENT '图片宽度' AFTER thumbnail_url,
ADD COLUMN height INT COMMENT '图片高度' AFTER width;

-- 添加新索引
ALTER TABLE media_files ADD INDEX idx_file_hash (file_hash);

-- 更新file_type字段的可能值
-- 将 'image' 更新为 'images'
UPDATE media_files SET file_type = 'images' WHERE file_type = 'image';

-- 将 'video' 更新为 'videos'
UPDATE media_files SET file_type = 'videos' WHERE file_type = 'video';

-- 将 'document' 更新为 'documents'
UPDATE media_files SET file_type = 'documents' WHERE file_type = 'document';

-- 为现有记录生成URL（基于文件路径）
UPDATE media_files SET url = CONCAT('/static/uploads/', file_path) WHERE url IS NULL;

COMMIT; 