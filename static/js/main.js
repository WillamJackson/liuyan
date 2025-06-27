// 主要JavaScript功能

// 全局配置
const config = {
    apiBaseUrl: '/api',
    csrfToken: document.querySelector('meta[name=csrf-token]')?.getAttribute('content')
};

// 工具函数
const utils = {
    // 显示加载状态
    showLoading: (element) => {
        element.disabled = true;
        element.innerHTML = '<span class="loading"></span> 加载中...';
    },

    // 隐藏加载状态
    hideLoading: (element, originalText) => {
        element.disabled = false;
        element.innerHTML = originalText;
    },

    // 显示通知
    showNotification: (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    },

    // 格式化日期
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 格式化文件大小
    formatFileSize: (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// API请求封装
const api = {
    // 通用请求方法
    request: async (url, options = {}) => {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(config.csrfToken && { 'X-CSRFToken': config.csrfToken })
            }
        };

        const response = await fetch(config.apiBaseUrl + url, {
            ...defaultOptions,
            ...options,
            headers: { ...defaultOptions.headers, ...options.headers }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

    // GET请求
    get: (url) => api.request(url),

    // POST请求
    post: (url, data) => api.request(url, {
        method: 'POST',
        body: JSON.stringify(data)
    }),

    // PUT请求
    put: (url, data) => api.request(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),

    // DELETE请求
    delete: (url) => api.request(url, { method: 'DELETE' })
};

// 内容管理功能
const contentManager = {
    // 删除内容
    deleteContent: async (id) => {
        if (!confirm('确定要删除这篇内容吗？此操作不可恢复。')) {
            return;
        }

        try {
            await api.delete(`/contents/${id}`);
            utils.showNotification('内容删除成功', 'success');
            location.reload();
        } catch (error) {
            console.error('删除失败:', error);
            utils.showNotification('删除失败，请重试', 'error');
        }
    },

    // 批量删除内容
    batchDelete: async (ids) => {
        if (!confirm(`确定要删除选中的 ${ids.length} 篇内容吗？此操作不可恢复。`)) {
            return;
        }

        try {
            await Promise.all(ids.map(id => api.delete(`/contents/${id}`)));
            utils.showNotification('批量删除成功', 'success');
            location.reload();
        } catch (error) {
            console.error('批量删除失败:', error);
            utils.showNotification('批量删除失败，请重试', 'error');
        }
    },

    // 发布/取消发布内容
    togglePublish: async (id, currentStatus) => {
        const newStatus = currentStatus === 'published' ? 'draft' : 'published';
        
        try {
            await api.put(`/contents/${id}`, { status: newStatus });
            utils.showNotification(
                newStatus === 'published' ? '内容已发布' : '内容已取消发布', 
                'success'
            );
            location.reload();
        } catch (error) {
            console.error('状态更新失败:', error);
            utils.showNotification('状态更新失败，请重试', 'error');
        }
    }
};

// 文件上传功能
const fileUploader = {
    // 上传文件
    upload: async (file, onProgress) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(config.apiBaseUrl + '/media/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`上传失败: ${response.status}`);
            }

            return response.json();
        } catch (error) {
            console.error('文件上传失败:', error);
            throw error;
        }
    },

    // 验证文件类型
    validateFile: (file, allowedTypes = ['image/*', 'video/*', 'application/pdf']) => {
        const isValidType = allowedTypes.some(type => {
            if (type.endsWith('/*')) {
                return file.type.startsWith(type.slice(0, -1));
            }
            return file.type === type;
        });

        if (!isValidType) {
            throw new Error('不支持的文件类型');
        }

        // 检查文件大小 (16MB)
        if (file.size > 16 * 1024 * 1024) {
            throw new Error('文件大小不能超过16MB');
        }

        return true;
    }
};

// 表单验证
const formValidator = {
    // 验证必填字段
    validateRequired: (value, fieldName) => {
        if (!value || value.trim() === '') {
            throw new Error(`${fieldName}不能为空`);
        }
        return true;
    },

    // 验证邮箱格式
    validateEmail: (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            throw new Error('邮箱格式不正确');
        }
        return true;
    },

    // 验证密码强度
    validatePassword: (password) => {
        if (password.length < 6) {
            throw new Error('密码长度至少6位');
        }
        return true;
    }
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化侧边栏活动状态
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('nav a');
    
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('bg-indigo-50', 'text-indigo-700');
            link.classList.remove('text-gray-700', 'hover:bg-gray-50');
        }
    });

    // 初始化工具提示
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            // 可以在这里添加自定义工具提示逻辑
        });
    });

    // 自动隐藏flash消息
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert, [class*="bg-red-"], [class*="bg-green-"], [class*="bg-blue-"]');
        alerts.forEach(alert => {
            if (alert.parentElement && alert.parentElement.classList.contains('mb-4')) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        });
    }, 5000);
});

// 媒体库管理功能
const MediaLibrary = {
    currentPage: 1,
    perPage: 20,
    currentFilter: '',
    uploadQueue: [],
    isUploading: false,
    
    init() {
        this.loadMediaFiles();
        this.bindEvents();
        this.initDropZone();
    },
    
    bindEvents() {
        // 文件上传
        document.getElementById('fileInput')?.addEventListener('change', this.handleFileUpload.bind(this));
        
        // 批量上传按钮
        document.getElementById('batchUploadBtn')?.addEventListener('click', () => {
            document.getElementById('batchFileInput')?.click();
        });
        
        document.getElementById('batchFileInput')?.addEventListener('change', this.handleBatchUpload.bind(this));
        
        // 文件类型筛选
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.currentFilter = e.target.dataset.filter;
                this.currentPage = 1;
                this.loadMediaFiles();
                
                // 更新按钮状态
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
        
        // 搜索
        document.getElementById('searchInput')?.addEventListener('input', this.debounce((e) => {
            this.currentPage = 1;
            this.loadMediaFiles(e.target.value);
        }, 300));
        
        // 分页
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('page-btn')) {
                this.currentPage = parseInt(e.target.dataset.page);
                this.loadMediaFiles();
            }
        });
        
        // 模态框关闭
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeAllModals();
            }
        });
        
        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    initDropZone() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
        });
        
        dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
    },
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    },
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFileUpload({ target: { files } });
    },
    
    async loadMediaFiles(search = '') {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                search: search
            });
            
            if (this.currentFilter) {
                params.append('file_type', this.currentFilter);
            }
            
            const response = await fetch(`/api/media?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderMediaFiles(data.data.items);
                this.renderPagination(data.data.pagination);
                this.updateStats(data.data.pagination);
            }
        } catch (error) {
            console.error('加载媒体文件失败:', error);
            utils.showNotification('加载媒体文件失败', 'error');
        }
    },
    
    renderMediaFiles(files) {
        const container = document.getElementById('mediaGrid');
        if (!container) return;
        
        if (files.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <i class="fas fa-images text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">暂无媒体文件</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = files.map(file => `
            <div class="media-item bg-white rounded-lg shadow-sm border hover:shadow-md transition-all duration-200 group" data-id="${file.id}">
                <div class="relative">
                    ${this.renderFilePreview(file)}
                    <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <div class="flex space-x-1">
                            <button class="p-1 bg-white rounded shadow-sm hover:bg-gray-50" 
                                    onclick="MediaLibrary.previewFile(${file.id})" 
                                    title="预览">
                                <i class="fas fa-eye text-xs text-gray-600"></i>
                            </button>
                            <button class="p-1 bg-white rounded shadow-sm hover:bg-gray-50" 
                                    onclick="MediaLibrary.editFile(${file.id})" 
                                    title="编辑">
                                <i class="fas fa-edit text-xs text-gray-600"></i>
                            </button>
                            <button class="p-1 bg-white rounded shadow-sm hover:bg-gray-50" 
                                    onclick="MediaLibrary.deleteFile(${file.id})" 
                                    title="删除">
                                <i class="fas fa-trash text-xs text-red-600"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="p-3">
                    <h4 class="text-sm font-medium text-gray-900 truncate mb-1" title="${file.original_name}">
                        ${file.original_name}
                    </h4>
                    <div class="flex justify-between items-center text-xs text-gray-500 mb-2">
                        <span>${utils.formatFileSize(file.file_size)}</span>
                        <span class="px-2 py-1 bg-gray-100 rounded">${this.getFileTypeLabel(file.file_type)}</span>
                    </div>
                    ${file.width && file.height ? `<p class="text-xs text-gray-400 mb-2">${file.width} × ${file.height}</p>` : ''}
                    <div class="flex justify-between items-center">
                        <button class="text-xs text-blue-600 hover:text-blue-800 flex items-center" 
                                onclick="MediaLibrary.copyUrl('${file.url}')">
                            <i class="fas fa-copy mr-1"></i>复制链接
                        </button>
                        <span class="text-xs text-gray-400">${utils.formatDate(file.created_at)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    renderFilePreview(file) {
        if (file.file_type === 'images' && file.thumbnail_url) {
            return `
                <div class="aspect-square bg-gray-100 rounded-t-lg overflow-hidden">
                    <img src="${file.thumbnail_url}" alt="${file.alt_text || file.original_name}" 
                         class="w-full h-full object-cover cursor-pointer"
                         onclick="MediaLibrary.previewFile(${file.id})">
                </div>
            `;
        } else {
            const iconClass = this.getFileIcon(file.file_type);
            const iconColor = this.getFileIconColor(file.file_type);
            return `
                <div class="aspect-square bg-gray-50 rounded-t-lg flex items-center justify-center cursor-pointer"
                     onclick="MediaLibrary.previewFile(${file.id})">
                    <i class="${iconClass} text-4xl ${iconColor}"></i>
                </div>
            `;
        }
    },
    
    getFileIcon(fileType) {
        const icons = {
            'images': 'fas fa-image',
            'videos': 'fas fa-video',
            'documents': 'fas fa-file-alt',
            'archives': 'fas fa-file-archive'
        };
        return icons[fileType] || 'fas fa-file';
    },
    
    getFileIconColor(fileType) {
        const colors = {
            'images': 'text-green-500',
            'videos': 'text-purple-500',
            'documents': 'text-blue-500',
            'archives': 'text-orange-500'
        };
        return colors[fileType] || 'text-gray-400';
    },
    
    getFileTypeLabel(fileType) {
        const labels = {
            'images': '图片',
            'videos': '视频',
            'documents': '文档',
            'archives': '压缩包'
        };
        return labels[fileType] || '其他';
    },
    
    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        if (!container || pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let paginationHTML = '';
        
        // 上一页
        if (pagination.has_prev) {
            paginationHTML += `<button class="page-btn px-3 py-2 text-sm text-gray-500 hover:text-gray-700" data-page="${pagination.page - 1}">上一页</button>`;
        }
        
        // 页码
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === pagination.page;
            paginationHTML += `
                <button class="page-btn px-3 py-2 text-sm ${isActive ? 'bg-blue-500 text-white' : 'text-gray-500 hover:text-gray-700'}" 
                        data-page="${i}">${i}</button>
            `;
        }
        
        // 下一页
        if (pagination.has_next) {
            paginationHTML += `<button class="page-btn px-3 py-2 text-sm text-gray-500 hover:text-gray-700" data-page="${pagination.page + 1}">下一页</button>`;
        }
        
        container.innerHTML = paginationHTML;
    },
    
    updateStats(pagination) {
        const statsElement = document.getElementById('mediaStats');
        if (statsElement) {
            statsElement.textContent = `共 ${pagination.total} 个文件`;
        }
    },
    
    async handleFileUpload(event) {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        this.showUploadProgress();
        
        const uploadPromises = Array.from(files).map((file, index) => 
            this.uploadFileWithProgress(file, index, files.length)
        );
        
        try {
            const results = await Promise.all(uploadPromises);
            const successCount = results.filter(r => r.success).length;
            
            utils.showNotification(`成功上传 ${successCount} 个文件`, 'success');
            this.loadMediaFiles(); // 重新加载文件列表
            event.target.value = ''; // 清空input
        } catch (error) {
            console.error('文件上传失败:', error);
            utils.showNotification('部分文件上传失败', 'error');
        } finally {
            this.hideUploadProgress();
        }
    },
    
    async handleBatchUpload(event) {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        this.showUploadProgress();
        
        try {
            const response = await fetch('/api/media/batch-upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                utils.showNotification(data.message, 'success');
                this.loadMediaFiles();
            } else {
                utils.showNotification(data.message || '批量上传失败', 'error');
            }
            
            event.target.value = '';
        } catch (error) {
            console.error('批量上传失败:', error);
            utils.showNotification('批量上传失败', 'error');
        } finally {
            this.hideUploadProgress();
        }
    },
    
    async uploadFileWithProgress(file, index, total) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/media/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            this.updateUploadProgress(index + 1, total);
            
            return data;
        } catch (error) {
            console.error(`文件 ${file.name} 上传失败:`, error);
            return { success: false, message: '上传失败' };
        }
    },
    
    showUploadProgress() {
        const progressElement = document.getElementById('uploadProgress');
        if (progressElement) {
            progressElement.classList.remove('hidden');
        }
    },
    
    hideUploadProgress() {
        const progressElement = document.getElementById('uploadProgress');
        if (progressElement) {
            progressElement.classList.add('hidden');
        }
    },
    
    updateUploadProgress(current, total) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar && progressText) {
            const percentage = Math.round((current / total) * 100);
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `${current}/${total} 文件已上传`;
        }
    },
    
    copyUrl(url) {
        const fullUrl = window.location.origin + url;
        navigator.clipboard.writeText(fullUrl).then(() => {
            utils.showNotification('链接已复制到剪贴板', 'success');
        }).catch(() => {
            // 兼容旧浏览器
            const textArea = document.createElement('textarea');
            textArea.value = fullUrl;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            utils.showNotification('链接已复制到剪贴板', 'success');
        });
    },
    
    async previewFile(id) {
        try {
            const response = await fetch(`/api/media/${id}`);
            const data = await response.json();
            
            if (data.success) {
                this.showPreviewModal(data.data);
            }
        } catch (error) {
            console.error('获取文件详情失败:', error);
        }
    },
    
    showPreviewModal(file) {
        // 创建模态框HTML
        const modalHTML = `
            <div id="previewModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-overlay">
                <div class="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
                    <div class="flex justify-between items-center p-4 border-b">
                        <h3 class="text-lg font-semibold">${file.original_name}</h3>
                        <button onclick="MediaLibrary.closePreviewModal()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="p-4">
                        ${this.renderPreviewContent(file)}
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },
    
    renderPreviewContent(file) {
        if (file.file_type === 'images') {
            return `
                <img src="${file.url}" alt="${file.alt_text || file.original_name}" 
                     class="max-w-full max-h-96 mx-auto rounded-lg">
                <div class="mt-4 text-sm text-gray-600">
                    <p>尺寸: ${file.width} × ${file.height}</p>
                    <p>大小: ${utils.formatFileSize(file.file_size)}</p>
                    <p>类型: ${file.mime_type}</p>
                </div>
            `;
        } else {
            const iconClass = this.getFileIcon(file.file_type);
            const iconColor = this.getFileIconColor(file.file_type);
            return `
                <div class="text-center py-8">
                    <i class="${iconClass} text-6xl ${iconColor} mb-4"></i>
                    <p class="text-lg font-medium">${file.original_name}</p>
                    <div class="mt-4 text-sm text-gray-600">
                        <p>大小: ${utils.formatFileSize(file.file_size)}</p>
                        <p>类型: ${file.mime_type}</p>
                        <p>上传时间: ${utils.formatDate(file.created_at)}</p>
                    </div>
                    <a href="${file.url}" target="_blank" 
                       class="inline-block mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                        下载文件
                    </a>
                </div>
            `;
        }
    },
    
    closePreviewModal() {
        const modal = document.getElementById('previewModal');
        if (modal) {
            modal.remove();
        }
    },
    
    async editFile(id) {
        try {
            const response = await fetch(`/api/media/${id}`);
            const data = await response.json();
            
            if (data.success) {
                this.showEditModal(data.data);
            }
        } catch (error) {
            console.error('获取文件详情失败:', error);
        }
    },
    
    showEditModal(file) {
        const modalHTML = `
            <div id="editModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 modal-overlay">
                <div class="bg-white rounded-lg max-w-md w-full mx-4">
                    <div class="flex justify-between items-center p-4 border-b">
                        <h3 class="text-lg font-semibold">编辑文件信息</h3>
                        <button onclick="MediaLibrary.closeEditModal()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="p-4">
                        <input type="hidden" id="editFileId" value="${file.id}">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">替代文本</label>
                            <input type="text" id="editAltText" value="${file.alt_text || ''}" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 mb-2">描述</label>
                            <textarea id="editDescription" rows="3" 
                                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">${file.description || ''}</textarea>
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button onclick="MediaLibrary.closeEditModal()" 
                                    class="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50">
                                取消
                            </button>
                            <button onclick="MediaLibrary.saveFileEdit()" 
                                    class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                                保存
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },
    
    closeEditModal() {
        const modal = document.getElementById('editModal');
        if (modal) {
            modal.remove();
        }
    },
    
    async saveFileEdit() {
        const fileId = document.getElementById('editFileId').value;
        const altText = document.getElementById('editAltText').value;
        const description = document.getElementById('editDescription').value;
        
        try {
            const response = await fetch(`/api/media/${fileId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    alt_text: altText,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                utils.showNotification('文件信息更新成功', 'success');
                this.closeEditModal();
                this.loadMediaFiles();
            } else {
                utils.showNotification(data.message || '更新失败', 'error');
            }
        } catch (error) {
            console.error('更新文件信息失败:', error);
            utils.showNotification('更新失败', 'error');
        }
    },
    
    async deleteFile(id) {
        if (!confirm('确定要删除这个文件吗？删除后无法恢复。')) return;
        
        try {
            const response = await fetch(`/api/media/${id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                utils.showNotification('文件删除成功', 'success');
                this.loadMediaFiles();
            } else {
                utils.showNotification(data.message || '文件删除失败', 'error');
            }
        } catch (error) {
            console.error('文件删除失败:', error);
            utils.showNotification('文件删除失败', 'error');
        }
    },
    
    closeAllModals() {
        document.querySelectorAll('[id$="Modal"]').forEach(modal => {
            modal.remove();
        });
    }
};

// 导出全局对象
window.CMS = {
    utils,
    api,
    contentManager,
    fileUploader,
    formValidator,
    MediaLibrary
}; 