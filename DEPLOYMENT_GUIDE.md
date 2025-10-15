# 🚀 AI Calculator 部署指南

## 📋 部署架构

你的项目包含两个部分，需要分别部署：

```
┌─────────────────────┐         ┌─────────────────────┐
│   Frontend (HTML)   │  HTTPS  │  Backend (Python)   │
│  Cloudflare Pages   │────────▶│   Railway.app       │
│                     │         │   FastAPI + Claude  │
└─────────────────────┘         └─────────────────────┘
```

**重要说明**：
- ✅ Frontend 可以在 Cloudflare Pages 运行
- ❌ Backend **无法**在 Cloudflare Pages 运行（需要 Python）
- ✅ Backend 需要部署到支持 Python 的平台

---

## 🔥 方案 1：Railway.app（推荐，最简单）

### 后端部署 (Backend → Railway.app)

#### 1. 准备工作
确保你的 GitHub 仓库包含以下文件：
- ✅ `backend/requirements.txt`
- ✅ `Procfile` （已创建）
- ✅ `railway.json` （已创建）

#### 2. 部署步骤

1. **访问** https://railway.app
2. **使用 GitHub 登录**
3. **New Project** → **Deploy from GitHub repo**
4. **选择** `AI-calculator` 仓库
5. **配置环境变量**：
   ```
   CLAUDE_API_KEY=你的Claude API密钥
   PORT=${{PORT}}
   ```
6. **等待部署完成** (~2-3 分钟)
7. **复制你的后端 URL**（例如：`https://your-app.up.railway.app`）

#### 3. 验证后端
访问：`https://your-app.up.railway.app/api/health`

应该看到：
```json
{
  "status": "healthy",
  "claude_configured": true
}
```

---

### 前端部署 (Frontend → Cloudflare Pages)

#### 1. 修改前端配置

打开 `frontend/index_v2.html`，找到第 363 行：
```javascript
PRODUCTION: 'YOUR_BACKEND_URL_HERE',  // ⚠️ 修改这里！
```

**修改为你的 Railway 后端 URL**：
```javascript
PRODUCTION: 'https://your-app.up.railway.app',
```

同样修改 `frontend/index.html` 的配置（如果使用 V1）。

#### 2. 提交更改
```bash
git add frontend/
git commit -m "Configure production backend URL"
git push
```

#### 3. 部署到 Cloudflare Pages

1. **访问** https://dash.cloudflare.com
2. **Workers & Pages** → **Create application** → **Pages**
3. **Connect to Git** → 选择 `AI-calculator` 仓库
4. **Build settings**：
   - Build command: 留空
   - Build output directory: `/frontend`
5. **Save and Deploy**
6. **等待部署完成** (~1-2 分钟)

#### 4. 访问你的应用

Cloudflare 会给你一个 URL，例如：
- `https://ai-calculator.pages.dev`

---

## 📊 方案 2：Render.com（免费替代方案）

### 后端部署

1. **访问** https://render.com
2. **New** → **Web Service**
3. **Connect GitHub** → 选择 `AI-calculator`
4. **配置**：
   - Name: `ai-calculator-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **环境变量**：
   ```
   CLAUDE_API_KEY=你的密钥
   ```
6. **Create Web Service**

其余步骤同 Railway。

---

## ⚙️ 方案 3：Vercel（仅前端）

如果你想使用 Vercel 部署前端：

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署前端
cd frontend
vercel --prod
```

配置 `vercel.json`：
```json
{
  "version": 2,
  "public": true,
  "routes": [
    { "src": "/(.*)", "dest": "/$1" }
  ]
}
```

---

## 🔧 配置检查清单

部署前请确认：

### Backend (Railway/Render)
- [ ] `CLAUDE_API_KEY` 环境变量已设置
- [ ] 后端 URL 可访问（测试 `/api/health`）
- [ ] CORS 配置正确（允许你的前端域名）

### Frontend (Cloudflare/Vercel)
- [ ] `API_CONFIG.PRODUCTION` 已修改为实际后端 URL
- [ ] 前端可以访问
- [ ] 浏览器控制台没有 CORS 错误

---

## 🐛 常见问题

### 1. CORS 错误

**症状**：浏览器控制台显示 CORS policy 错误

**解决**：在后端 `backend/app/core/config.py` 中添加你的前端域名：

```python
ALLOWED_ORIGINS: list = [
    "http://localhost:8080",
    "https://your-frontend.pages.dev",  # 添加这一行
]
```

重新部署后端。

### 2. 后端 404 错误

**症状**：前端显示"后端 API 无法访问"

**检查**：
1. 后端 URL 是否正确
2. 后端是否成功部署
3. 访问 `https://your-backend-url/api/health` 确认

### 3. API Key 错误

**症状**：计算失败，显示 API key 相关错误

**解决**：
1. 确认在 Railway/Render 设置了 `CLAUDE_API_KEY`
2. 确认 API key 有效且有额度
3. 重启后端服务

### 4. 前端配置未生效

**症状**：还是连接到 localhost

**检查**：
1. 确认修改了正确的文件（`index_v2.html` 或 `index.html`）
2. 确认提交并推送了更改
3. 清除浏览器缓存（Ctrl+Shift+R 或 Cmd+Shift+R）
4. 重新部署前端

---

## 💰 成本估算

### 免费额度
- **Railway.app**: 每月 $5 免费额度（约 500小时运行时间）
- **Cloudflare Pages**: 无限免费（静态托管）
- **Render.com**: 750小时/月免费（睡眠模式）
- **Claude API**: 按使用量计费（~$0.30/次计算，使用 Haiku 模型）

### 预估成本
假设每天 100 次计算：
- Claude API: ~$9/月
- Railway: 免费（在额度内）
- Cloudflare: 免费

**总计**: ~$9/月

---

## 🎯 推荐配置

### 个人项目/演示
```
Frontend: Cloudflare Pages (免费)
Backend: Railway.app (免费额度)
总成本: ~$0 + Claude API 使用费
```

### 生产环境
```
Frontend: Cloudflare Pages (免费)
Backend: Railway Pro ($5/月) 或 Render ($7/月)
总成本: ~$5-7/月 + Claude API 使用费
```

---

## 📚 相关文档

- Railway 部署指南: https://docs.railway.app/
- Cloudflare Pages 文档: https://developers.cloudflare.com/pages/
- FastAPI 部署: https://fastapi.tiangolo.com/deployment/
- Claude API: https://docs.anthropic.com/

---

## ✅ 快速开始命令

```bash
# 1. 确保代码最新
git pull

# 2. 修改前端配置
# 编辑 frontend/index_v2.html 第 363 行

# 3. 提交更改
git add .
git commit -m "Configure production backend URL"
git push

# 4. 部署后端到 Railway
# 访问 railway.app 并连接 GitHub

# 5. 部署前端到 Cloudflare
# 访问 dash.cloudflare.com/pages 并连接 GitHub
```

---

**需要帮助？**
- GitHub Issues: https://github.com/iamleoluo/AI-calculator/issues
- Email: iamleo789@outlook.com
