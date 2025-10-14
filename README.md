# AI Calculator - Fourier Series Demo

一個展示 AI 數學推理能力的教學平台，透過計算傅立葉級數來展示 AI 的完整推導過程、數值驗證與自我修正能力。

## 🎯 核心特色

- **透明化推理**: 展示 AI 的完整數學推導過程
- **自動驗證**: 使用 NumPy/SciPy 數值積分驗證 AI 結果
- **迭代修正**: 當驗證失敗時，AI 會根據反饋重新計算（最多 3 次）
- **視覺化比較**: 圖表展示原始函數與傅立葉重建的比較

## 📁 專案結構

```
AI calculator/
├── backend/              # FastAPI 後端
│   ├── app/
│   │   ├── api/         # API 端點
│   │   ├── core/        # 核心引擎（AI、驗證、解析）
│   │   ├── services/    # 業務邏輯
│   │   ├── schemas/     # Pydantic schemas
│   │   └── main.py      # FastAPI 應用入口
│   └── requirements.txt
│
├── frontend/            # 簡單的 HTML 前端
│   └── index.html
│
└── CLAUDE.md           # Claude Code 開發指南
```

## 🚀 快速開始

### 前置需求

- Python 3.11+
- Anthropic API Key ([獲取 API Key](https://console.anthropic.com/))

### 1. 設置後端

```bash
# 進入後端目錄
cd backend

# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設置環境變數
cp .env.example .env
# 編輯 .env 文件，填入你的 CLAUDE_API_KEY

# 啟動後端服務
cd app
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

後端將運行在 `http://localhost:8000`

API 文檔: `http://localhost:8000/docs`

### 2. 啟動前端

```bash
# 在專案根目錄
cd frontend

# 使用 Python 內建的 HTTP 服務器
python -m http.server 8080
```

前端將運行在 `http://localhost:8080`

在瀏覽器打開 `http://localhost:8080` 即可使用。

## 📝 使用範例

### 範例 1: 正弦函數

```
函數: np.sin(t)
週期: 6.283185 (2π)
項數: 5
```

結果：AI 會識別這是奇函數，所有 a₀ 和 aₙ 應該為 0，只有 b₁ ≈ 1.0

### 範例 2: 方波函數

```
函數: 1 if t < 3.14159 else -1
週期: 6.283185 (2π)
項數: 10
```

注意：由於前端是簡化版，條件表達式可能不支援。可以改用數學近似。

### 範例 3: 餘弦函數

```
函數: np.cos(t)
週期: 6.283185 (2π)
項數: 5
```

結果：AI 會識別這是偶函數，所有 bₙ 應該為 0，只有 a₁ ≈ 1.0

## 🔧 API 使用

### 計算傅立葉級數

**POST** `/api/fourier-series`

**Request Body:**
```json
{
  "function_expr": "np.sin(t)",
  "period": 6.283185,
  "n_terms": 5
}
```

**Response:**
```json
{
  "success": true,
  "iterations": 1,
  "thinking_process": { "steps": [...] },
  "coefficients": {
    "a0": 0.0,
    "an": [0.0, 0.0, 0.0, 0.0, 0.0],
    "bn": [1.0, 0.0, 0.0, 0.0, 0.0]
  },
  "verification": {
    "is_verified": true,
    "max_error": 0.001,
    "mean_error": 0.0005
  },
  "visualization": {
    "t_points": [...],
    "original_values": [...],
    "reconstructed_values": [...]
  }
}
```

## 🧪 技術細節

### AI 引擎
- 使用 Claude Sonnet 4.5 模型
- Temperature = 0.0 確保一致性
- 結構化 Prompt 確保輸出格式

### 驗證引擎
- 使用 SciPy 的 `quad` 函數進行數值積分
- 計算相對誤差（閾值 5%）
- 對接近零的值使用絕對誤差

### 迭代機制
- 最大迭代次數: 3
- 失敗時構建詳細反饋給 AI
- 記錄所有迭代歷史

## ⚙️ 配置選項

在 `backend/app/core/config.py` 或 `.env` 中可以調整：

- `CLAUDE_API_KEY`: Anthropic API 金鑰 (必須)
- `CLAUDE_MODEL`: Claude 模型 (預設: claude-sonnet-4-5-20250929)
- `ERROR_THRESHOLD`: 驗證誤差閾值 (預設: 0.05 = 5%)
- `MAX_ITERATIONS`: 最大迭代次數 (預設: 3)

## 🐛 疑難排解

### 問題: "CLAUDE_API_KEY is required"
**解決**: 確保在 `backend/.env` 中設置了 `CLAUDE_API_KEY`

### 問題: CORS 錯誤
**解決**: 確保前端和後端都在運行，且前端訪問 `http://localhost:8000`

### 問題: "Verification failed"
**解決**: 這是正常的，系統會自動迭代修正。如果 3 次迭代後仍失敗，可能是:
- 函數表達式太複雜
- AI 對該函數類型不熟悉
- 嘗試增加 `ERROR_THRESHOLD` 或減少 `n_terms`

### 問題: 前端圖表無法顯示
**解決**:
- 檢查瀏覽器控制台是否有錯誤
- 確認 Chart.js CDN 可以訪問
- 檢查後端是否正確返回 visualization 數據

## 📊 系統工作流程

```
用戶輸入函數
    ↓
構建結構化 Prompt
    ↓
Claude API 推導
    ↓
解析 AI 響應 (robust_parser)
    ↓
提取傅立葉係數
    ↓
數值驗證 (SciPy 積分)
    ↓
比較誤差
    ↓
是否通過?
  ├─ 是 → 返回結果 + 視覺化
  └─ 否 → 構建反饋 → 重新推導 (最多 3 次)
```

## 🎓 未來擴展方向

見 `CLAUDE.md` 中的長期規劃：

1. **符號驗證**: 使用 SymPy 進行符號層面的驗證
2. **自由推理模式**: 讓 AI 完全自由地解題，事後提取驗證構件
3. **更多數學主題**: 泰勒級數、拉普拉斯變換、微分方程等
4. **教學模式**: 學生練習模式、提示系統、錯誤分析

## 📄 授權

本專案為教學演示用途。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📧 聯繫

如有問題，請查看 `CLAUDE.md` 或提交 Issue。
