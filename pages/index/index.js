// index.js
const { api } = require('../../utils/api.js')

Page({
  data: {
    statusBarHeight: 0,
    refreshing: false,
    hasMore: true,
    page: 1,
    contentList: [],
    loading: false,
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
    
    // 加载内容数据
    this.loadContent()
  },

  onShow() {
    // 页面显示时刷新数据
    this.refreshContent()
  },

  onReachBottom() {
    // 触底加载更多
    this.loadMoreContent()
  },

  onRefresh() {
    // 下拉刷新
    this.setData({ refreshing: true })
    this.refreshContent()
  },

  // 加载内容数据
  loadContent() {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    
    api.getContents({ page: this.data.page, per_page: 20 })
      .then(result => {
        const newContentList = this.data.page === 1 
          ? result.contents 
          : [...this.data.contentList, ...result.contents]
        
        this.setData({
          contentList: newContentList,
          hasMore: result.hasMore,
          refreshing: false,
          loading: false
        })
      })
      .catch(error => {
        console.error('加载内容失败:', error)
        this.setData({ 
          refreshing: false,
          loading: false 
        })
        
        // 如果API调用失败，显示提示
        wx.showToast({
          title: '加载失败，请检查网络',
          icon: 'none',
          duration: 2000
        })
      })
  },

  // 刷新内容
  refreshContent() {
    this.setData({ page: 1 })
    this.loadContent()
  },

  // 加载更多内容
  loadMoreContent() {
    if (!this.data.hasMore || this.data.loading) return
    
    this.setData({ 
      page: this.data.page + 1 
    }, () => {
      this.loadContent()
    })
  },



  // 切换反馈状态
  toggleReaction(e) {
    const { contentId, type } = e.currentTarget.dataset
    console.log('Toggle reaction:', contentId, type)
    
    // 这里应该调用API更新反馈状态
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
