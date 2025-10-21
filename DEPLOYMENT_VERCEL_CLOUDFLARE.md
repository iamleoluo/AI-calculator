# AI Calculator 部署指南：Vercel + Cloudflare Pages

本指南将帮助你部署 AI Calculator 到生产环境：
- **后端**: Vercel（Python Serverless Functions）
- **前端**: Cloudflare Pages（静态托管）

---

## 📋 前置要求

### 账号准备
1. **Vercel 账号**: https://vercel.com（支持 GitHub 登录）
2. **Cloudflare 账号**: https://dash.cloudflare.com/sign-up
3. **Claude API Key**: https://console.anthropic.com/

### 本地准备
- Git 仓库（已推送到 GitHub）
- Claude API Key（用于后端）

---

## 🚀 第一步：部署后端到 Vercel

### 1.1 创建 Vercel 项目

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 **"Add New..."** → **"Project"**
3. 选择你的 GitHub 仓库（AI Calculator）
4. Vercel 会自动检测到项目配置

### 1.2 配置构建设置

在项目配置页面：

**Framework Preset**: Other
**Root Directory**: `./` (保持根目录)
**Build Command**: (留空)
**Output Directory**: `api`

### 1.3 配置环境变量

在 **Environment Variables** 部分添加：

```
CLAUDE_API_KEY = sk-ant-xxxxx (你的 Claude API Key)
```

可选环境变量：
```
CLAUDE_MODEL = claude-3-5-haiku-20241022
ERROR_THRESHOLD = 0.05
MAX_ITERATIONS = 3
```

### 1.4 部署

1. 点击 **"Deploy"**
2. 等待部署完成（约 2-3 分钟）
3. 部署成功后，你会看到：
   ```
   ✅ Deployment Ready
   https://your-project.vercel.app
   ```

### 1.5 测试后端

访问以下 URL 测试：
```bash
# 健康检查
curl https://your-project.vercel.app/

# 应该返回:
{
  "message": "AI Calculator - Fourier Series API",
  "docs": "/docs",
  "health": "/api/health"
}
```

⚠️ **记下你的 Vercel 后端 URL**，下一步需要用到！

---

## 🌐 第二步：部署前端到 Cloudflare Pages

### 2.1 修改前端配置

在部署前端之前，你需要修改配置文件指向你的 Vercel 后端。

**选项 A：直接修改 `frontend/config.js`**（推荐）

编辑 `frontend/config.js` 第 29 行：

```javascript
// 修改前：
return 'https://your-vercel-backend.vercel.app';

// 修改为你的实际 Vercel URL：
return 'https://your-project.vercel.app';
```

**选项 B：创建生产配置文件**

```bash
# 复制示例配置
cp frontend/config.example.js frontend/config.production.js

# 编辑 config.production.js，修改 API_BASE_URL
# 然后修改 HTML 文件引用 config.production.js
```

提交更改：
```bash
git add frontend/config.js
git commit -m "配置生产环境后端 URL"
git push
```

### 2.2 创建 Cloudflare Pages 项目

1. 访问 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Workers & Pages** → **Pages**
3. 点击 **"Create application"**
4. 选择 **"Connect to Git"**
5. 授权 GitHub 并选择你的仓库

### 2.3 配置构建设置

```
Project name: ai-calculator (或你喜欢的名称)
Production branch: main (或 master)
Build command: (留空)
Build output directory: frontend
Root directory: (留空)
```

### 2.4 部署

1. 点击 **"Save and Deploy"**
2. 等待部署完成（约 1-2 分钟）
3. 部署成功后，你会看到：
   ```
   ✅ Success
   https://ai-calculator.pages.dev
   ```

### 2.5 配置自定义域名（可选）

在 Cloudflare Pages 项目设置中：
1. 点击 **"Custom domains"**
2. 添加你的域名
3. Cloudflare 会自动配置 DNS

---

## 🔧 第三步：配置 CORS

### 3.1 更新后端 CORS 设置

回到你的代码仓库，编辑 `backend/app/core/config.py`：

```python
# CORS settings
ALLOWED_ORIGINS: list = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    # 添加你的 Cloudflare Pages URL
    "https://ai-calculator.pages.dev",
    "https://your-custom-domain.com",  # 如果有自定义域名
]
```

### 3.2 提交并重新部署

```bash
git add backend/app/core/config.py
git commit -m "添加生产环境 CORS 配置"
git push
```

Vercel 会自动检测到推送并重新部署。

---

## ✅ 第四步：验证部署

### 4.1 访问前端

打开你的 Cloudflare Pages URL：
```
https://ai-calculator.pages.dev
```

### 4.2 测试功能

1. 在输入框中输入：`\sin(t)`
2. 设置周期为：`6.283185`（2π）
3. 点击 **"计算傅立葉級數"**
4. 观察是否正常显示结果

### 4.3 检查控制台

按 F12 打开浏览器控制台，确认：
- 没有 CORS 错误
- API 请求正常返回
- 没有 404 错误

---

## 📊 部署架构

```
用户浏览器
    ↓
Cloudflare Pages (前端静态文件)
    ↓ API 请求
Vercel Serverless Function (后端 FastAPI)
    ↓
Claude API (AI 推理)
```

---

## ⚙️ 高级配置

### Vercel 性能优化

编辑 `vercel.json`：

```json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 60,      // 最大执行时间（Pro: 900秒）
      "memory": 1024          // 内存限制（MB）
    }
  },
  "regions": ["iad1"]         // 服务器区域（北弗吉尼亚）
}
```

可用区域：
- `iad1`: 华盛顿特区（北美东部）
- `sfo1`: 旧金山（北美西部）
- `hnd1`: 东京（亚洲）
- `fra1`: 法兰克福（欧洲）

### Cloudflare Pages 缓存策略

创建 `frontend/_headers`：

```
/*.js
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: no-cache, must-revalidate
```

---

## ⚠️ 已知限制

### Vercel 限制

1. **执行时间限制**
   - Hobby（免费）: 10 秒
   - Pro: 60 秒（本配置）
   - Enterprise: 900 秒

   如果 AI 请求超时，考虑：
   - 减少 `n_terms` 参数
   - 升级到 Pro 计划
   - 或使用其他平台（Railway, Render）

2. **内存限制**
   - 最大 1024 MB（本配置）
   - 对于复杂计算可能不够

3. **冷启动**
   - Serverless functions 可能有 1-3 秒冷启动时间
   - 频繁使用会保持 warm

### Cloudflare Pages 限制

1. **构建限制**
   - 每月 500 次构建（免费）
   - 每次构建 20 分钟超时

2. **文件大小**
   - 单个文件最大 25 MB
   - 总项目大小无限制

---

## 🐛 故障排查

### 后端问题

**问题**: 部署成功但 API 返回 500 错误
**解决**:
1. 检查 Vercel 部署日志
2. 确认 `CLAUDE_API_KEY` 环境变量已设置
3. 查看 Runtime Logs

**问题**: `ModuleNotFoundError`
**解决**:
1. 确认 `requirements.txt` 包含所有依赖
2. 重新部署项目

### 前端问题

**问题**: CORS 错误
**解决**:
1. 检查 `backend/app/core/config.py` 中的 `ALLOWED_ORIGINS`
2. 确保包含你的 Cloudflare Pages URL
3. 重新部署后端

**问题**: API 请求失败（404）
**解决**:
1. 检查 `frontend/config.js` 中的 `API_BASE_URL`
2. 确保 URL 正确（不要有尾部斜杠）
3. 测试后端 URL 是否可访问

### 检查清单

- [ ] Vercel 后端 URL 可以访问
- [ ] Claude API Key 已设置在 Vercel 环境变量中
- [ ] `frontend/config.js` 中的 API URL 已更新
- [ ] CORS 配置包含 Cloudflare Pages URL
- [ ] 前端可以正常加载
- [ ] API 请求成功返回数据

---

## 💰 费用说明

### Vercel
- **Hobby（免费）**:
  - 100 GB 带宽/月
  - 6,000 分钟执行时间/月
  - 10秒函数超时

- **Pro ($20/月）**:
  - 1 TB 带宽/月
  - 40,000 分钟执行时间/月
  - 60秒函数超时（本项目使用）

### Cloudflare Pages
- **免费计划**:
  - 无限带宽
  - 500 次构建/月
  - 免费 DDoS 防护
  - 无限请求

### Claude API
- 按实际使用的 tokens 计费
- Claude 3.5 Haiku（本项目使用）:
  - Input: $1.00 / MTok
  - Output: $5.00 / MTok
- 预估每次计算约 $0.01-0.05

**总计**: 使用免费套餐可以免费运行，仅支付 Claude API 费用。

---

## 📚 相关资源

- [Vercel Documentation](https://vercel.com/docs)
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Mangum (AWS Lambda/Vercel adapter)](https://mangum.io/)
- [Claude API Documentation](https://docs.anthropic.com/)

---

## 🆘 获取帮助

如果遇到问题：
1. 查看 [GitHub Issues](https://github.com/your-repo/issues)
2. 检查 Vercel 和 Cloudflare 的部署日志
3. 联系开发者

---

**祝部署顺利！** 🎉
