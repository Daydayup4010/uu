# CS:GO 饰品价差监控系统 - 部署指南

## 📋 概述

本系统已配置为在 `https://www.2333tv.top/csgo/` 路径下运行，与现有网站共享域名。

## 🚀 快速部署

### 1. 启动CS:GO监控系统

#### 方法一：使用批处理文件（推荐）
```bash
./start_csgo.bat
```

#### 方法二：使用Python直接启动
```bash
python start_csgo.py
```

### 2. 访问地址

- **线上地址**: https://www.2333tv.top/csgo/
- **本地测试**: http://localhost:5000/csgo/
- **健康检查**: http://localhost:5000/health

## 🔧 系统架构

### URL路径映射

| 路径 | 服务 | 端口 | 说明 |
|------|------|------|------|
| `/` | 主站 | 3600 | 现有网站 |
| `/api` | 主站API | 3601 | 现有API |
| `/csgo` | CS监控 | 5000 | CS:GO价差监控 |
| `/csgo/static/` | 静态资源 | 5000 | 优化的静态资源 |

### 技术实现

1. **Flask蓝图**: 使用Blueprint实现URL前缀 `/csgo`
2. **前端适配**: JavaScript自动检测路径并添加BASE_PATH
3. **Nginx代理**: 路径转发到不同的后端服务
4. **静态资源**: 优化的缓存配置

## 📁 核心文件

### 启动文件
- `start_csgo.py` - 主启动脚本（支持/csgo路径）
- `start_csgo.bat` - Windows批处理启动文件

### 配置文件
- `nginx.conf` - 更新的Nginx配置
- `static/index.html` - 修改后的前端文件（支持BASE_PATH）

### 自动修复脚本
- `fix_api_paths.py` - API路径修复脚本

## 🛠️ 部署前检查

1. **端口检查**: 确认5000端口未被占用
2. **依赖检查**: 确认所有Python依赖已安装
3. **日志目录**: 系统会自动创建logs目录
4. **Nginx重载**: 部署后需要重载Nginx配置

## 🌐 Nginx配置更新

新增的配置已添加到nginx.conf：

```nginx
# CS:GO 价差监控系统
location /csgo {
    proxy_pass http://localhost:5000;
    # 代理头设置...
}

# CS:GO 静态资源优化
location /csgo/static/ {
    proxy_pass http://localhost:5000;
    expires 1h;
    add_header Cache-Control "public, immutable";
}
```

## 📊 功能特性

- ✅ 自动价差分析
- ✅ 增量和全量更新  
- ✅ 实时价格监控
- ✅ 增强增量更新（价格同步）
- ✅ 完整日志记录
- ✅ Token管理系统
- ✅ 流式分析界面
- ✅ 健康检查接口

## 🔍 监控和调试

### 日志文件
- 应用日志: `logs/` 目录
- Nginx日志: 根据Nginx配置

### 健康检查
```bash
curl http://localhost:5000/health
```

### API测试
```bash
curl http://localhost:5000/csgo/api/status
```

## 🛡️ 安全考虑

1. **CORS配置**: 已配置跨域请求头
2. **代理头**: 正确转发客户端IP
3. **静态资源**: 缓存优化，避免频繁请求

## 🚨 故障排除

### 常见问题

1. **端口冲突**: 检查5000端口是否被占用
2. **路径问题**: 确认BASE_PATH正确识别
3. **API失败**: 检查后端服务是否正常启动
4. **静态资源**: 确认文件路径正确

### 检查命令

```bash
# 检查端口占用
netstat -ano | findstr :5000

# 检查服务状态
curl -I http://localhost:5000/health

# 检查日志
tail -f logs/latest.log
```

## 📈 性能优化

1. **静态资源缓存**: 1小时缓存时间
2. **数据更新策略**: 30秒自动刷新
3. **异步处理**: 非阻塞的数据更新
4. **内存优化**: 合理的数据存储策略

## 🔄 更新和维护

### 更新步骤
1. 停止服务
2. 更新代码
3. 重启服务
4. 验证功能

### 维护任务
- 定期清理日志文件
- 监控系统资源使用
- 检查API调用限制
- 更新Token配置

---

**注意**: 部署完成后，记得重载Nginx配置使新的路由生效。 