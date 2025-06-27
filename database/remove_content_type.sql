-- 删除content_type字段的迁移脚本
-- 执行前请先备份数据库
-- 兼容MySQL 5.7及以上版本

USE cms_db;

-- 检查并删除content_type字段的索引
SET @exist_index = (SELECT COUNT(*) FROM information_schema.statistics 
    WHERE table_schema = 'cms_db' AND table_name = 'contents' AND index_name = 'idx_content_type');

SET @sql_index = IF(@exist_index > 0, 
    'DROP INDEX idx_content_type ON contents', 
    'SELECT "idx_content_type索引不存在" AS message');

PREPARE stmt_index FROM @sql_index;
EXECUTE stmt_index;
DEALLOCATE PREPARE stmt_index;

-- 检查并删除content_type字段
SET @exist_column = (SELECT COUNT(*) FROM information_schema.columns 
    WHERE table_schema = 'cms_db' AND table_name = 'contents' AND column_name = 'content_type');

SET @sql_column = IF(@exist_column > 0, 
    'ALTER TABLE contents DROP COLUMN content_type', 
    'SELECT "content_type字段不存在" AS message');

PREPARE stmt_column FROM @sql_column;
EXECUTE stmt_column;
DEALLOCATE PREPARE stmt_column;

-- 完成迁移
SELECT '内容类型字段迁移完成，现在只使用分类系统' AS status; 