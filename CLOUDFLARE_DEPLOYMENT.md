# Cloudflare Pages 部署指南

本專案使用**混合架構**：Cloudflare Pages (前端 + Worker 代理) + Railway (Python 後端)

## 🏗️ 架構概覽

```
瀏覽器
  ↓
Cloudflare Pages (靜態前端)
  ↓
/api/* 請求
  ↓
Cloudflare Workers (JavaScript 代理層)
  ↓
Railway (Python FastAPI 後端)
  ↓
Claude API
```

## 📦 檔案結構

```
AI calculator/
├── frontend/
│   ├── index.html          # V1 前端 (同步 API)
│   └── index_v2.html       # V2 前端 (串流 API)
├── functions/              # Cloudflare Workers
│   └── api/
│       ├── health.js                      # 健康檢查
│       ├── fourier-series.js              # V1 API 代理
│       └── v2/
│           └── fourier-series/
│               └── stream.js              # V2 串流 API 代理
├── backend/                # Python FastAPI (部署到 Railway)
├── wrangler.toml          # Cloudflare 配置
└── .dev.vars              # 本地開發環境變數 (不提交)
```

## 🚀 部署步驟

### 1. 部署 Python 後端到 Railway

1. 前往 [Railway.app](https://railway.app)
2. 登入並創建新專案
3. 選擇 "Deploy from GitHub repo"
4. 選擇此倉庫
5. 配置環境變數：
   ```
   CLAUDE_API_KEY=your_api_key_here
   ```
6. Railway 會自動檢測 `Procfile` 並部署
7. 記下你的部署 URL，例如：`https://your-app.railway.app`

### 2. 部署前端到 Cloudflare Pages

#### 方法 A: 使用 Cloudflare Dashboard (推薦)

1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 進入 Pages → Create a project
3. 選擇 "Connect to Git"
4. 授權並選擇此倉庫
5. 配置構建設定：
   - **Build command**: 留空 (純靜態)
   - **Build output directory**: `frontend`
   - **Root directory**: 留空
6. 設定環境變數：
   - Key: `BACKEND_URL`
   - Value: `https://your-app.railway.app` (你的 Railway URL)
7. 點擊 "Save and Deploy"

#### 方法 B: 使用 Wrangler CLI

1. 安裝 Wrangler:
   ```bash
   npm install -g wrangler
   ```

2. 登入 Cloudflare:
   ```bash
   wrangler login
   ```

3. 部署:
   ```bash
   wrangler pages deploy frontend --project-name=ai-calculator
   ```

4. 在 Cloudflare Dashboard 設定環境變數 `BACKEND_URL`

### 3. 配置環境變數

在 Cloudflare Pages 專案設定中，添加以下環境變數：

| 變數名 | 值 | 說明 |
|--------|-----|------|
| `BACKEND_URL` | `https://your-app.railway.app` | Railway 後端 URL |

**重要**: 不要包含結尾的斜線 `/`

## 🧪 本地測試

### 1. 啟動 Python 後端

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

後端運行在 `http://localhost:8000`

### 2. 啟動 Cloudflare Workers 本地環境

創建 `.dev.vars` 文件（已在 .gitignore 中）：
```bash
BACKEND_URL=http://localhost:8000
```

使用 Wrangler 啟動本地開發伺服器：
```bash
wrangler pages dev frontend --port 8788
```

### 3. 訪問前端

- V1 版本: http://localhost:8788/index.html
- V2 版本: http://localhost:8788/index_v2.html
- 健康檢查: http://localhost:8788/api/health

## 🔍 API 端點

所有 API 請求都透過 Cloudflare Workers 代理到 Railway 後端：

| 前端路徑 | Worker 函數 | 後端端點 |
|---------|------------|---------|
| `/api/health` | `functions/api/health.js` | `GET /api/health` |
| `/api/fourier-series` | `functions/api/fourier-series.js` | `POST /api/fourier-series` |
| `/api/v2/fourier-series/stream` | `functions/api/v2/fourier-series/stream.js` | `POST /api/v2/fourier-series/stream` |

## ✅ 優點

1. **無 CORS 問題**: 前端和 API 在同一來源
2. **邊緣加速**: Cloudflare 全球 CDN
3. **自動 HTTPS**: Cloudflare 提供免費 SSL
4. **成本優化**:
   - Cloudflare Pages: 免費（靜態託管 + Workers）
   - Railway: 免費額度 $5/月
5. **簡單部署**: Git push 自動部署

## 🐛 故障排除

### 前端無法連接到後端

1. 檢查 Cloudflare Pages 環境變數 `BACKEND_URL` 是否正確
2. 檢查 Railway 後端是否正常運行
3. 訪問 `/api/health` 檢查狀態

### Workers 出錯

1. 查看 Cloudflare Pages 的 Functions 日誌
2. 確認 `functions/` 目錄結構正確
3. 檢查 Worker 代碼中的 `console.log` 輸出

### Railway 後端問題

1. 檢查 Railway 日誌
2. 確認 `CLAUDE_API_KEY` 環境變數已設定
3. 檢查 `Procfile` 配置

## 📚 相關資源

- [Cloudflare Pages 文檔](https://developers.cloudflare.com/pages/)
- [Cloudflare Pages Functions](https://developers.cloudflare.com/pages/platform/functions/)
- [Railway 文檔](https://docs.railway.app/)
- [Wrangler CLI 文檔](https://developers.cloudflare.com/workers/wrangler/)

## 🔐 安全注意事項

1. **永遠不要**在前端代碼中暴露 `CLAUDE_API_KEY`
2. API Key 只存在於 Railway 後端的環境變數中
3. Workers 只轉發請求，不處理敏感資料
4. 建議在 Railway 添加 IP 白名單（如果需要）

## 🎯 下一步

部署完成後，你可以：

1. 設定自訂網域（在 Cloudflare Pages 設定）
2. 啟用 Cloudflare Analytics
3. 添加 Rate Limiting（在 Worker 中實現）
4. 設定 Webhook 用於 CI/CD

---

有問題請查看主要的 [README.md](./README.md) 和 [ARCHITECTURE.md](./ARCHITECTURE.md)
