# 微信小程序API接入说明

## 🔧 已完成的功能

### 1. API配置
- **API基础地址**: `https://flask-xp0n-166034-6-1256841508.sh.run.tcloudbase.com/api`
- **请求封装**: 已封装统一的请求函数，支持错误处理
- **数据处理**: 自动将API数据转换为小程序所需格式

### 2. 数据映射
根据您提供的SQL查询结果，已实现以下数据映射：

```javascript
// API数据 -> 小程序数据
{
  title: item.title,           // 标题
  content: item.content,       // 内容
  content_type: item.content_type, // 内容类型
  media_files: [               // 媒体文件
    {
      file_type: 'image',      // 文件类型
      file_path: 'https://...' // 文件路径
    }
  ]
}
```

### 3. 内容类型支持
- 📝 **博客** (blog)
- 🔗 **网址** (link) 
- 📄 **文档** (document)
- 💾 **软件** (software)

### 4. 页面功能
- ✅ **首页**: 显示内容列表，支持下拉刷新、上拉加载
- ✅ **搜索页**: 支持关键词搜索，搜索历史记录
- ✅ **调试页**: 测试API连接状态

## 🚀 使用方法

### 1. 测试API连接
1. 在小程序中进入"调试页面"
2. 查看API连接状态
3. 如果连接失败，检查网络和API地址

### 2. 查看数据
- 首页会自动加载最新发布的内容
- 支持下拉刷新获取最新数据
- 支持上拉加载更多历史数据

### 3. 搜索功能
- 在搜索页面输入关键词
- 支持标题和内容的模糊搜索
- 自动保存搜索历史

## 📋 API接口说明

### 获取内容列表
```
GET /api/contents?status=published&page=1&per_page=20
```

### 搜索内容
```
GET /api/contents?search=关键词&status=published&page=1&per_page=50
```

## 🔧 配置说明

### 1. 域名配置
已在 `project.config.json` 中设置：
```json
{
  "setting": {
    "urlCheck": false  // 允许访问外部API
  }
}
```

### 2. API配置文件
位置：`utils/api.js`
- 可修改 `API_BASE_URL` 更改API地址
- 可调整请求参数和数据处理逻辑

## 📱 页面路径

- 首页: `/pages/index/index`
- 搜索: `/pages/search/search`  
- 调试: `/pages/debug/debug`

## 🐛 故障排除

### 1. API连接失败
- 检查网络连接
- 确认API服务器状态
- 检查域名配置

### 2. 数据显示异常
- 查看调试页面的数据格式
- 检查API返回的数据结构
- 确认媒体文件路径是否正确

### 3. 搜索功能异常
- 确认搜索关键词
- 检查API搜索接口返回数据
- 查看控制台错误信息

## 📞 技术支持

如遇问题，请提供：
1. 错误信息截图
2. 调试页面的状态信息
3. 控制台错误日志

---

*现在您的微信小程序已经可以从MySQL数据库获取真实数据了！* 