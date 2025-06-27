// API配置和请求工具
const API_BASE_URL = 'https://flask-xp0n-166034-6-1256841508.sh.run.tcloudbase.com/api'

// 请求封装
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          console.error('API请求失败:', res)
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        console.error('网络请求失败:', err)
        reject(err)
      }
    })
  })
}

// 内容类型映射
const CONTENT_TYPE_MAP = {
  'blog': { icon: '📝', name: '博客' },
  'link': { icon: '🔗', name: '网址' },
  'document': { icon: '📄', name: '文档' },
  'software': { icon: '💾', name: '软件' }
}

// 获取内容类型信息
function getContentTypeInfo(contentType) {
  return CONTENT_TYPE_MAP[contentType] || { icon: '📝', name: '内容' }
}

// 格式化时间
function formatTime(dateString) {
  const now = new Date()
  const date = new Date(dateString)
  const diff = now - date
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 处理API返回的内容数据
function processContentData(apiData) {
  return apiData.map(item => {
    const typeInfo = getContentTypeInfo(item.content_type)
    
    // 处理媒体文件
    const mediaList = (item.media_files || [])
      .filter(media => media.file_type === 'image')
      .map(media => ({
        id: media.id,
        url: media.url || media.file_path
      }))
    
    // 检查是否有链接
    const linkUrl = (item.media_files || [])
      .find(media => media.file_type === 'link')?.url || null
    
    return {
      id: item.id,
      typeIcon: typeInfo.icon,
      typeName: typeInfo.name,
      timeText: formatTime(item.created_at || item.updated_at),
      title: item.title,
      content: item.content,
      mediaList: mediaList,
      linkUrl: linkUrl,
      reactions: item.reactions || { like: 0, love: 0, think: 0, inspire: 0, learn: 0 }
    }
  })
}

// 构建查询字符串
function buildQueryString(params) {
  const queryParts = []
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    }
  }
  return queryParts.join('&')
}

// API接口函数
const api = {
  // 获取内容列表
  getContents(params = {}) {
    const queryParams = buildQueryString({
      status: 'published',
      per_page: params.per_page || 20,
      page: params.page || 1,
      ...params
    })
    
    return request(`/contents?${queryParams}`)
      .then(data => {
        return {
          contents: processContentData(data.contents || data.data || []),
          total: data.total || 0,
          hasMore: data.has_more !== false
        }
      })
  },
  
  // 获取单个内容详情
  getContent(id) {
    return request(`/contents/${id}`)
      .then(data => {
        return processContentData([data])[0]
      })
  },
  
  // 搜索内容
  searchContents(keyword, params = {}) {
    const queryParams = buildQueryString({
      search: keyword,
      status: 'published',
      per_page: params.per_page || 50,
      page: params.page || 1,
      ...params
    })
    
    return request(`/contents?${queryParams}`)
      .then(data => {
        return {
          contents: processContentData(data.contents || data.data || []),
          total: data.total || 0
        }
      })
  }
}

module.exports = {
  api,
  formatTime,
  getContentTypeInfo,
  processContentData
} 