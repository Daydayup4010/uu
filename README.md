# Buff差价监控系统

一个自动监控Buff与悠悠有品饰品价差的智能系统，帮助用户发现套利机会，实现自动化监控和快速跳转购买。

## 🚀 核心功能

### 📊 数据采集
- **多平台监控**：同时监控 [Buff](https://buff.163.com/) 和 [悠悠有品](https://www.youpin898.com/) 两个平台
- **实时价格获取**：定时抓取饰品名称、磨损值、当前价格等详细信息
- **智能匹配**：自动匹配两个平台上的相同饰品

### 💰 差价分析
- **智能计算**：自动计算价差和利润率
- **可配置阈值**：支持自定义价差阈值（默认20元）
- **多维度筛选**：支持按价格区间、分类等多种条件筛选
- **实时排序**：按价差或利润率动态排序

### 🔗 快速跳转
- **一键购买**：为每个差价饰品生成直接购买链接
- **标准化链接**：统一的Buff购买链接格式
- **新窗口打开**：点击按钮直接跳转到对应商品页面

### 🎯 智能监控
- **后台运行**：7x24小时自动监控，无需人工干预
- **定时更新**：每5分钟轻量检查，每小时完整扫描
- **实时提醒**：发现高价差商品时自动提醒

## 📦 系统架构

```
Buff差价监控系统/
├── 数据采集层/
│   ├── Buff爬虫 (BuffScraper)
│   ├── 悠悠有品爬虫 (YoupinScraper)
│   └── 数据收集器 (DataCollector)
├── 业务逻辑层/
│   ├── 价差分析器 (PriceDiffAnalyzer)
│   ├── 监控服务 (PriceMonitor)
│   └── 配置管理 (Config)
├── API接口层/
│   └── FastAPI应用 (api.py)
└── 前端界面层/
    └── 现代化Web界面 (static/index.html)
```

## 🛠️ 技术栈

- **后端框架**：FastAPI + Python 3.8+
- **数据采集**：Requests + BeautifulSoup + Selenium
- **数据处理**：Pandas + JSON
- **任务调度**：Schedule + Threading
- **前端界面**：HTML5 + TailwindCSS + JavaScript
- **图标库**：FontAwesome

## 📋 环境要求

- Python 3.8+
- Chrome浏览器（用于Selenium）
- ChromeDriver（自动下载）
- Windows/Linux/macOS

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd buff-price-monitor
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动系统
```bash
# 启动完整Web界面（推荐）
python main.py web

# 仅后台监控
python main.py monitor

# 执行单次扫描
python main.py scan

# 查看系统状态
python main.py status
```

### 4. 访问界面
打开浏览器访问：`http://localhost:8000`

## 🎮 使用说明

### Web界面功能

#### 📈 统计面板
- **总饰品数**：当前监控的差价饰品总数
- **平均价差**：所有差价饰品的平均价差
- **最大价差**：当前最大的单个价差
- **更新时间**：最后一次数据更新时间

#### 🔍 筛选和排序
- **最小价差过滤**：只显示价差大于指定值的饰品
- **排序方式**：按价差或利润率排序
- **显示数量**：控制列表显示的饰品数量

#### 📝 饰品列表
- **饰品信息**：显示名称、图片、两平台价格
- **价差数据**：突出显示价差金额和利润率
- **购买按钮**：一键跳转到Buff购买页面

#### ⚙️ 系统设置
- **价差阈值**：调整筛选阈值
- **监控状态**：查看后台监控运行状态

### 命令行操作

```bash
# 自定义端口启动
python main.py web --port 8080

# 设置价差阈值
python main.py web --threshold 30

# 仅后台监控（适合服务器部署）
python main.py monitor --threshold 25

# 单次扫描并输出结果
python main.py scan
```

## 📊 API接口

系统提供完整的RESTful API接口：

### 获取差价饰品列表
```http
GET /api/items?limit=100&min_diff=20&sort_by=price_diff
```

### 获取系统状态
```http
GET /api/status
```

### 获取统计信息
```http
GET /api/statistics
```

### 强制更新数据
```http
POST /api/update
```

### 更新配置
```http
POST /api/config/threshold
Content-Type: application/json

{
  "threshold": 30.0
}
```

## ⚙️ 配置说明

系统配置通过 `.env` 文件管理，主要参数：

```env
# 价差阈值（元）
PRICE_DIFF_THRESHOLD=20.0

# 监控间隔（秒）
MONITOR_INTERVAL=300

# 请求延迟（秒）- 避免被反爬
REQUEST_DELAY=2

# 最大重试次数
MAX_RETRIES=3

# API服务配置
API_HOST=0.0.0.0
API_PORT=8000
```

## 📁 目录结构

```
buff-price-monitor/
├── main.py              # 主启动文件
├── api.py               # FastAPI应用
├── config.py            # 配置管理
├── models.py            # 数据模型
├── scrapers.py          # 爬虫模块
├── analyzer.py          # 价差分析器
├── monitor.py           # 监控服务
├── requirements.txt     # 依赖包
├── README.md           # 说明文档
├── .env                # 环境配置（自动生成）
├── static/             # 前端静态文件
│   └── index.html      # 主界面
├── data/               # 数据存储目录
│   ├── items.json      # 原始饰品数据
│   └── price_diff.json # 差价分析结果
└── logs/               # 日志文件目录
```

## 🔧 高级配置

### 自定义爬虫策略
可以在 `scrapers.py` 中调整：
- 请求头配置
- 重试策略
- 解析规则
- 延迟控制

### 监控任务调度
在 `monitor.py` 中可以调整：
- 监控频率
- 数据更新策略
- 提醒阈值
- 缓存策略

### 前端界面定制
在 `static/index.html` 中可以：
- 修改界面样式
- 调整数据展示
- 添加新功能
- 定制交互逻辑

## 🚨 注意事项

1. **合规使用**：请遵守目标网站的robots.txt和使用条款
2. **频率控制**：已内置请求延迟，避免过于频繁的请求
3. **数据准确性**：价格数据仅供参考，实际交易前请核实
4. **网络环境**：确保网络连接稳定，可能需要配置代理
5. **反爬措施**：如遇到访问限制，可调整请求策略

## 🐛 常见问题

### Q: 程序无法启动？
A: 检查Python版本（需要3.8+）和依赖包是否正确安装

### Q: 抓取不到数据？
A: 可能是网站结构变化或反爬限制，检查网络连接和调整爬虫参数

### Q: 界面显示空白？
A: 检查API服务是否正常运行，查看浏览器控制台错误信息

### Q: 如何部署到服务器？
A: 使用 `python main.py monitor` 后台运行，配合supervisor等进程管理工具

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📞 支持

如有问题请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至开发者

---

**免责声明**：本工具仅用于学习和研究目的，使用者需自行承担使用风险，遵守相关法律法规。 