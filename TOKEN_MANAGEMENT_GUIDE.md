# Token管理功能使用指南

## 功能概述

我们已经为您的CS:GO饰品价差分析系统添加了完整的Token管理功能，允许您通过Web界面手动更新Buff和悠悠有品的认证信息，确保API正常工作。

## 🚀 主要功能

### 1. Web界面管理
- **设置页面**：点击系统右上角的"设置"按钮
- **Token管理标签**：切换到"Token管理"标签页
- **实时状态显示**：显示当前Token配置状态
- **一键测试连接**：验证Token是否有效

### 2. 支持的平台
- **Buff.163.com**：Session Cookie + CSRF Token
- **悠悠有品(youpin898.com)**：Device ID + UK + 其他设备信息

### 3. 自动功能
- **配置持久化**：Token保存在 `tokens_config.json` 文件中
- **动态加载**：API客户端自动使用最新配置
- **状态监控**：实时显示Token有效性

## 📋 使用步骤

### 更新Buff Token

1. **获取Token**
   ```
   1. 浏览器登录 buff.163.com
   2. 打开开发者工具 (F12) → Network 标签
   3. 刷新页面，查找对 /api/market/goods 的请求
   4. 复制请求头中的 session 和 csrf_token cookies
   ```

2. **在Web界面更新**
   - 打开设置 → Token管理
   - 填入Session Cookie和CSRF Token
   - 可选：添加其他cookies (JSON格式)
   - 点击"更新Buff Token"
   - 点击"测试连接"验证

### 更新悠悠有品Token

1. **获取Token**
   ```
   1. 浏览器访问 youpin898.com
   2. 打开开发者工具 → Network 标签
   3. 查找对 api.youpin898.com 的请求
   4. 复制请求头中的 deviceid、uk、b3 等参数
   ```

2. **在Web界面更新**
   - 填入Device ID、Device UK、UK、B3等信息
   - 点击"更新悠悠有品Token"
   - 点击"测试连接"验证

## 🔧 技术实现

### 文件结构
```
token_manager.py          # Token管理核心逻辑
tokens_config.json        # Token配置文件（自动生成）
api.py                    # 新增Token管理API端点
integrated_price_system.py # 更新了BuffAPIClient
youpin_working_api.py     # 更新了YoupinWorkingAPI
static/index.html         # 新增Token管理界面
```

### API端点
- `GET /api/tokens/status` - 获取Token状态
- `POST /api/tokens/buff` - 更新Buff Token
- `POST /api/tokens/youpin` - 更新悠悠有品Token
- `POST /api/tokens/test/buff` - 测试Buff连接
- `POST /api/tokens/test/youpin` - 测试悠悠有品连接

### 配置文件格式
```json
{
  "buff": {
    "cookies": {
      "session": "xxx",
      "csrf_token": "xxx",
      "Device-Id": "xxx"
    },
    "headers": {...},
    "last_updated": "2025-06-03T15:20:03.474762",
    "status": "已配置"
  },
  "youpin": {
    "device_id": "xxx",
    "device_uk": "xxx", 
    "uk": "xxx",
    "b3": "xxx",
    "headers": {...},
    "last_updated": "2025-06-03T15:20:03.476763",
    "status": "已配置"
  }
}
```

## 🛡️ 安全特性

### 1. 验证机制
- **必填检查**：确保关键Token字段不为空
- **格式验证**：JSON格式cookies验证
- **连接测试**：实际API调用验证Token有效性

### 2. 错误处理
- **友好提示**：详细的错误信息和解决建议
- **回滚机制**：无效Token不会覆盖有效配置
- **日志记录**：详细的操作日志便于排查

### 3. 状态监控
- **实时状态**：Token配置状态实时显示
- **有效性检查**：自动检测Token完整性
- **更新时间**：显示最后更新时间

## 🎯 使用场景

### 1. Token过期处理
当API返回认证错误时：
1. 打开Token管理界面
2. 获取新的Token
3. 更新配置并测试
4. 系统自动使用新Token

### 2. 多环境配置
- 开发环境和生产环境使用不同Token
- 快速切换不同账号的Token
- 备份和恢复Token配置

### 3. 团队协作
- 团队成员可以共享有效Token
- 统一的Token管理界面
- 标准化的Token更新流程

## 🚨 注意事项

### 1. Token安全
- **不要公开分享**：Token包含敏感的认证信息
- **定期更新**：建议定期更换Token
- **备份配置**：重要Token配置建议备份

### 2. API限制
- **频率限制**：遵守平台API调用频率限制
- **有效期**：Token有时效性，需要定期更新
- **账号安全**：避免频繁更换Token引起账号异常

### 3. 配置文件
- **自动生成**：首次运行会创建默认配置
- **手动编辑**：也可以直接编辑 `tokens_config.json`
- **格式正确**：确保JSON格式正确

## 🎉 优势总结

1. **用户友好**：直观的Web界面，无需修改代码
2. **实时验证**：一键测试Token有效性
3. **自动应用**：无需重启系统，配置即时生效
4. **安全可靠**：完善的验证和错误处理机制
5. **灵活配置**：支持完整的Token参数配置

通过这个Token管理系统，您可以轻松维护API认证信息，确保价差分析系统持续稳定运行！ 