// debug.js - API调试页面
const { api } = require('../../utils/api.js')

Page({
  data: {
    apiStatus: '未测试',
    testResults: [],
    loading: false
  },

  onLoad() {
    this.testAPI()
  },

  // 测试API连接
  testAPI() {
    this.setData({ 
      loading: true,
      apiStatus: '测试中...' 
    })

    api.getContents({ page: 1, per_page: 5 })
      .then(result => {
        this.setData({
          apiStatus: '连接成功',
          testResults: result.contents,
          loading: false
        })
        
        console.log('API测试成功:', result)
      })
      .catch(error => {
        this.setData({
          apiStatus: `连接失败: ${error.message}`,
          loading: false
        })
        
        console.error('API测试失败:', error)
      })
  },

  // 重新测试
  retryTest() {
    this.testAPI()
  },

  // 复制错误信息
  copyError() {
    wx.setClipboardData({
      data: this.data.apiStatus,
      success: () => {
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success'
        })
      }
    })
  }
}) 