-- 添加内容媒体关联表
-- 执行时间：2024年

-- 创建内容媒体关联表
CREATE TABLE IF NOT EXISTS content_media (
    content_id INT NOT NULL,
    media_file_id INT NOT NULL,
    sort_order INT DEFAULT 0 COMMENT '媒体文件在内容中的排序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '关联创建时间',
    PRIMARY KEY (content_id, media_file_id),
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE,
    INDEX idx_content_media_content_id (content_id),
    INDEX idx_content_media_media_file_id (media_file_id),
    INDEX idx_content_media_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容媒体关联表';

-- 添加说明注释
ALTER TABLE content_media COMMENT = '内容与媒体文件的多对多关联表，支持一个内容关联多个媒体文件（最多9个）'; 