// search.js
const { api } = require('../../utils/api.js')

Page({
  data: {
    statusBarHeight: 0,
    searchKeyword: '',
    isSearching: false,
    searchResults: [],
    searchHistory: [],
    hotTags: ['工作效率', 'GitHub', '产品设计', 'AI工具', '前端开发', '思维导图'],
    reactionTypes: [
      { type: 'like', emoji: '👍', count: 0 },
      { type: 'love', emoji: '❤️', count: 0 },
      { type: 'think', emoji: '🤔', count: 0 },
      { type: 'inspire', emoji: '💡', count: 0 },
      { type: 'learn', emoji: '📚', count: 0 }
    ]
  },

  onLoad() {
    // 获取系统信息
    const systemInfo = wx.getSystemInfoSync()
    this.setData({
      statusBarHeight: systemInfo.statusBarHeight
    })
    
    // 加载搜索历史
    this.loadSearchHistory()
  },

  onShow() {
    // 页面显示时重新加载搜索历史
    this.loadSearchHistory()
  },

  // 加载搜索历史
  loadSearchHistory() {
    try {
      const history = wx.getStorageSync('searchHistory') || []
      this.setData({ searchHistory: history })
    } catch (e) {
      console.error('加载搜索历史失败:', e)
    }
  },

  // 保存搜索历史
  saveSearchHistory(keyword) {
    if (!keyword.trim()) return
    
    try {
      let history = wx.getStorageSync('searchHistory') || []
      
      // 移除重复项
      history = history.filter(item => item !== keyword)
      
      // 添加到开头
      history.unshift(keyword)
      
      // 限制历史记录数量
      if (history.length > 10) {
        history = history.slice(0, 10)
      }
      
      wx.setStorageSync('searchHistory', history)
      this.setData({ searchHistory: history })
    } catch (e) {
      console.error('保存搜索历史失败:', e)
    }
  },



  // 搜索输入
  onSearchInput(e) {
    const keyword = e.detail.value
    this.setData({ searchKeyword: keyword })
    
    // 实时搜索（防抖）
    clearTimeout(this.searchTimer)
    this.searchTimer = setTimeout(() => {
      if (keyword.trim()) {
        this.performSearch(keyword)
      } else {
        this.setData({ searchResults: [] })
      }
    }, 300)
  },

  // 搜索确认
  onSearch(e) {
    const keyword = e.detail.value || this.data.searchKeyword
    if (keyword.trim()) {
      this.performSearch(keyword)
      this.saveSearchHistory(keyword)
    }
  },

  // 执行搜索
  performSearch(keyword) {
    this.setData({ isSearching: true })
    
    api.searchContents(keyword)
      .then(result => {
        // 高亮关键词
        const highlightResults = result.contents.map(item => ({
          ...item,
          highlightTitle: this.highlightKeyword(item.title, keyword),
          highlightContent: this.highlightKeyword(item.content, keyword)
        }))
        
        this.setData({
          searchResults: highlightResults,
          isSearching: false
        })
      })
      .catch(error => {
        console.error('搜索失败:', error)
        this.setData({ isSearching: false })
        
        wx.showToast({
          title: '搜索失败，请检查网络',
          icon: 'none',
          duration: 2000
        })
      })
  },

  // 高亮关键词
  highlightKeyword(text, keyword) {
    if (!keyword) return text
    
    const regex = new RegExp(`(${keyword})`, 'gi')
    return text.replace(regex, '<span style="background: #fff3cd; padding: 2px 4px; border-radius: 4px;">$1</span>')
  },

  // 通过标签搜索
  searchByTag(e) {
    const tag = e.currentTarget.dataset.tag
    this.setData({ searchKeyword: tag })
    this.performSearch(tag)
    this.saveSearchHistory(tag)
  },

  // 清空搜索
  clearSearch() {
    this.setData({
      searchKeyword: '',
      searchResults: []
    })
  },

  // 删除搜索历史
  deleteHistory(e) {
    const index = e.currentTarget.dataset.index
    const history = [...this.data.searchHistory]
    history.splice(index, 1)
    
    try {
      wx.setStorageSync('searchHistory', history)
      this.setData({ searchHistory: history })
    } catch (e) {
      console.error('删除搜索历史失败:', e)
    }
  },

  // 语音搜索
  startVoiceSearch() {
    wx.showToast({
      title: '语音搜索功能开发中',
      icon: 'none'
    })
  },

  // 切换反馈状态
  toggleReaction(e) {
    const { contentId, type } = e.currentTarget.dataset
    console.log('Toggle reaction:', contentId, type)
    
    wx.showToast({
      title: '反馈已记录',
      icon: 'success',
      duration: 1000
    })
  },

  // 分享内容
  shareContent(e) {
    const item = e.currentTarget.dataset.item
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
  },

  // 打开链接
  openLink(e) {
    const url = e.currentTarget.dataset.url
    wx.setClipboardData({
      data: url,
      success: () => {
        wx.showToast({
          title: '链接已复制',
          icon: 'success'
        })
      }
    })
  },

  // 预览图片
  previewImage(e) {
    const { urls, current } = e.currentTarget.dataset
    const imageUrls = urls.map(item => item.url)
    
    wx.previewImage({
      urls: imageUrls,
      current: current
    })
  }
}) 