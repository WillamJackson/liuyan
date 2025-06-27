import os
import uuid
import hashlib
from datetime import datetime
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app

class FileUploadManager:
    """文件上传管理器"""
    
    @staticmethod
    def allowed_file(filename, file_type=None):
        """检查文件是否允许上传"""
        if '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        
        if file_type:
            return ext in allowed_extensions.get(file_type, set())
        else:
            # 检查是否在任何类型中
            all_extensions = set()
            for extensions in allowed_extensions.values():
                all_extensions.update(extensions)
            return ext in all_extensions
    
    @staticmethod
    def get_file_type(filename):
        """获取文件类型"""
        if '.' not in filename:
            return 'other'
        
        ext = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        
        for file_type, extensions in allowed_extensions.items():
            if ext in extensions:
                return file_type
        
        return 'other'
    
    @staticmethod
    def generate_filename(original_filename):
        """生成唯一的文件名"""
        # 获取文件扩展名
        ext = ''
        if '.' in original_filename:
            ext = '.' + original_filename.rsplit('.', 1)[1].lower()
        
        # 生成唯一文件名：时间戳 + UUID + 扩展名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}{ext}"
        
        return filename
    
    @staticmethod
    def get_upload_path(file_type, filename):
        """获取上传文件的完整路径"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # 按类型创建子目录
        type_folder = os.path.join(upload_folder, file_type)
        
        # 按日期创建子目录
        date_folder = datetime.now().strftime('%Y/%m')
        full_folder = os.path.join(type_folder, date_folder)
        
        # 确保目录存在
        os.makedirs(full_folder, exist_ok=True)
        
        return os.path.join(full_folder, filename)
    
    @staticmethod
    def get_file_url(file_path):
        """获取文件的URL路径"""
        # 将绝对路径转换为相对URL路径
        upload_folder = current_app.config['UPLOAD_FOLDER']
        relative_path = os.path.relpath(file_path, upload_folder)
        
        # 转换为URL格式（使用正斜杠）
        url_path = relative_path.replace(os.path.sep, '/')
        
        return f"/static/uploads/{url_path}"
    
    @staticmethod
    def calculate_file_hash(file_path):
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class ImageProcessor:
    """图片处理器"""
    
    @staticmethod
    def is_image(filename):
        """检查是否为图片文件"""
        return FileUploadManager.get_file_type(filename) == 'images'
    
    @staticmethod
    def create_thumbnail(image_path, thumbnail_path=None, size=None):
        """创建缩略图"""
        if not size:
            size = current_app.config.get('THUMBNAIL_SIZE', (300, 300))
        
        if not thumbnail_path:
            # 生成缩略图路径
            dir_path = os.path.dirname(image_path)
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            thumbnail_path = os.path.join(dir_path, f"{name}_thumb{ext}")
        
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 创建缩略图（保持宽高比）
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 保存缩略图
                img.save(thumbnail_path, 'JPEG', quality=current_app.config.get('COMPRESS_QUALITY', 85))
                
            return thumbnail_path
        except Exception as e:
            current_app.logger.error(f"创建缩略图失败: {str(e)}")
            return None
    
    @staticmethod
    def compress_image(image_path, quality=None, max_size=None):
        """压缩图片"""
        if not quality:
            quality = current_app.config.get('COMPRESS_QUALITY', 85)
        
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸（如果指定了最大尺寸）
                if max_size:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 保存压缩后的图片
                img.save(image_path, 'JPEG', quality=quality, optimize=True)
                
            return True
        except Exception as e:
            current_app.logger.error(f"压缩图片失败: {str(e)}")
            return False
    
    @staticmethod
    def get_image_info(image_path):
        """获取图片信息"""
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': os.path.getsize(image_path)
                }
        except Exception as e:
            current_app.logger.error(f"获取图片信息失败: {str(e)}")
            return None

class MediaFileValidator:
    """媒体文件验证器"""
    
    @staticmethod
    def validate_file_size(file_size, max_size=None):
        """验证文件大小"""
        if not max_size:
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        
        return file_size <= max_size
    
    @staticmethod
    def validate_file_type(filename, allowed_types=None):
        """验证文件类型"""
        if not allowed_types:
            return FileUploadManager.allowed_file(filename)
        
        file_type = FileUploadManager.get_file_type(filename)
        return file_type in allowed_types
    
    @staticmethod
    def scan_for_malware(file_path):
        """恶意软件扫描（基础实现）"""
        # 这里可以集成第三方恶意软件扫描API
        # 目前只做基础的文件头检查
        
        dangerous_signatures = [
            b'\x4d\x5a',  # PE executable
            b'\x7f\x45\x4c\x46',  # ELF executable
            b'\xca\xfe\xba\xbe',  # Mach-O executable
        ]
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                for signature in dangerous_signatures:
                    if header.startswith(signature):
                        return False
            return True
        except Exception:
            return False 