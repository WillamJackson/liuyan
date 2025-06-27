-- 删除SEO相关字段的迁移脚本
-- 执行前请先备份数据库
-- 兼容MySQL 5.7及以上版本

USE cms_db;

-- 检查并删除meta_description字段
SET @exist_meta_description = (SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = 'cms_db' AND table_name = 'contents' AND column_name = 'meta_description');

SET @sql_meta_description = IF(@exist_meta_description > 0, 
    'ALTER TABLE contents DROP COLUMN meta_description', 
    'SELECT "meta_description字段不存在" AS message');

PREPARE stmt_meta_description FROM @sql_meta_description;
EXECUTE stmt_meta_description;
DEALLOCATE PREPARE stmt_meta_description;

-- 检查并删除meta_keywords字段
SET @exist_meta_keywords = (SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = 'cms_db' AND table_name = 'contents' AND column_name = 'meta_keywords');

SET @sql_meta_keywords = IF(@exist_meta_keywords > 0, 
    'ALTER TABLE contents DROP COLUMN meta_keywords', 
    'SELECT "meta_keywords字段不存在" AS message');

PREPARE stmt_meta_keywords FROM @sql_meta_keywords;
EXECUTE stmt_meta_keywords;
DEALLOCATE PREPARE stmt_meta_keywords;

-- 完成迁移
SELECT 'SEO字段迁移完成' AS status; 