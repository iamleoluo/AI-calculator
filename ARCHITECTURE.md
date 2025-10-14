# AI Calculator - 系統架構流程圖

## 📋 專案概述

**AI Calculator** 是一個透明化的 AI 數學推理平台，展示 AI 如何進行傅立葉級數推導、數值驗證與自我修正。

**開發日期**: 2025-10-14
**狀態**: MVP Demo 完成

---

## 🏗️ 整體系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         用戶界面層                                │
│                    (Frontend - HTML/JS)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ LaTeX 輸入   │  │ 係數顯示     │  │ 視覺化圖表   │         │
│  │ 週期/項數    │  │ 驗證狀態     │  │ (Chart.js)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                        API 層 (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  POST /api/fourier-series                                │  │
│  │  - 請求驗證 (Pydantic)                                    │  │
│  │  - 響應格式化                                             │  │
│  │  - 錯誤處理                                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      業務邏輯層 (Services)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           FourierSeriesService (主協調器)                 │  │
│  │  - 管理迭代流程 (最多 3 次)                               │  │
│  │  - 協調 AI 引擎與驗證引擎                                 │  │
│  │  - 生成視覺化數據                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            ↓                          ↓                  ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Prompt Builder │    │    AI Engine     │    │ Verification     │
│                  │    │                  │    │    Engine        │
│ - 初始 Prompt    │    │ - Claude API 調用│    │ - 數值積分       │
│ - 反饋 Prompt    │    │ - JSON 解析      │    │ - 誤差計算       │
│ - Few-shot 範例  │    │ - 重試機制       │    │ - 錯誤報告       │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                ↓
                    ┌──────────────────────┐
                    │  Claude API          │
                    │  (Haiku 3.5)         │
                    │  - 數學推理          │
                    │  - 係數計算          │
                    └──────────────────────┘
```

---

## 🔄 完整數據流程

### 階段 1: 用戶請求
```
用戶輸入:
├─ 函數表達式 (例: np.sin(t))
├─ 週期 T (例: 6.283185 ≈ 2π)
└─ 項數 n (例: 5)
         ↓
    前端驗證
         ↓
POST /api/fourier-series
```

### 階段 2: Prompt 構建
```
PromptBuilder.build_initial_prompt()
         ↓
生成結構化 Prompt:
├─ 問題描述 (函數、週期、項數)
├─ 輸出格式要求 (JSON schema)
│  ├─ thinking_process (推理步驟)
│  └─ executable_code (可執行代碼)
├─ 約束條件 (精確度要求)
└─ 傅立葉級數公式提醒
```

### 階段 3: AI 推導 (迭代循環)
```
FOR iteration = 1 TO 3:
    ┌─────────────────────────────────────┐
    │ 1. AI Engine 調用                    │
    │    └─ Claude API (Haiku 3.5)        │
    │       └─ 返回 JSON 響應              │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ 2. Response Parser                   │
    │    ├─ 提取 thinking_process          │
    │    ├─ 提取 executable_code           │
    │    └─ 解析 coefficients (a0,an,bn)  │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ 3. Numerical Verification            │
    │    ├─ 使用 SciPy 數值積分            │
    │    ├─ 計算正確的係數                 │
    │    └─ 比較 AI 係數 vs 數值係數      │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ 4. Error Analysis                    │
    │    ├─ 計算相對誤差                   │
    │    │  (特殊處理接近零的值)           │
    │    ├─ 判斷是否通過閾值 (5%)         │
    │    └─ 生成錯誤報告                   │
    └─────────────────────────────────────┘
              ↓
         誤差 < 5%?
         ├─ YES → 跳出循環 ✓
         └─ NO  → 構建反饋 Prompt → 下一次迭代
END FOR
```

### 階段 4: 視覺化數據生成
```
無論驗證是否通過，都生成:
         ↓
┌─────────────────────────────────────┐
│ Visualization Generator              │
│  ├─ 生成 500 個時間點 (0 到 2T)     │
│  ├─ 計算原始函數值                   │
│  ├─ 計算傅立葉重建值                 │
│  └─ 計算逐點誤差                     │
└─────────────────────────────────────┘
         ↓
返回給前端:
├─ t_points: [...]
├─ original_values: [...]
├─ reconstructed_values: [...]
├─ pointwise_error: [...]
├─ max_pointwise_error
└─ mean_pointwise_error
```

### 階段 5: 前端渲染
```
接收 JSON 響應
         ↓
┌─────────────────────────────────────┐
│ displayResults(data)                 │
│  ├─ 顯示迭代資訊                     │
│  ├─ 顯示驗證徽章 (通過/失敗)        │
│  ├─ 顯示傅立葉係數                   │
│  ├─ 繪製比較圖表 (Chart.js)         │
│  ├─ 繪製誤差圖表                     │
│  └─ 顯示 AI 推理步驟                │
└─────────────────────────────────────┘
```

---

## 🧩 關鍵組件詳解

### 1. Prompt Builder
**檔案**: `backend/app/services/prompt_builder.py`

**職責**:
- 構建初始推導 Prompt
- 構建反饋修正 Prompt (迭代時)
- 定義嚴格的 JSON 輸出格式

**關鍵特性**:
```python
def build_initial_prompt(function_expr, period, n_terms):
    - 問題描述
    - JSON 格式要求 (thinking_process + executable_code)
    - 嚴格約束 (不要 markdown, 純數字係數)
    - 傅立葉公式提醒
```

### 2. AI Engine
**檔案**: `backend/app/core/ai_engine.py`

**職責**:
- 調用 Claude API
- 解析 JSON 響應
- 處理格式錯誤

**配置**:
- 模型: `claude-3-5-haiku-20241022` (成本優化)
- Temperature: `0.0` (確保一致性)
- Max tokens: `8192`

### 3. Verification Engine
**檔案**: `backend/app/core/verification.py`

**職責**:
- 使用 SciPy 數值積分計算正確係數
- 比較 AI 係數與數值係數
- 計算誤差指標

**誤差計算邏輯**:
```python
def _relative_error(ai_value, numerical_value):
    if |numerical_value| < 1e-6 and |ai_value| < 1e-6:
        # 兩者都接近零 → 使用絕對誤差
        return |ai_value - numerical_value|
    elif |numerical_value| < 1e-6:
        # 數值接近零但 AI 不是 → 絕對誤差
        return |ai_value - numerical_value|
    else:
        # 正常情況 → 相對誤差
        return |ai_value - numerical_value| / |numerical_value|
```

### 4. Robust Parser
**檔案**: `backend/app/core/robust_parser.py`

**職責**: 處理 AI 響應的格式變異

**五層解析策略**:
1. 直接 JSON 解析
2. 清理後解析 (移除 markdown, 修復逗號)
3. 從代碼塊提取
4. 正則表達式提取
5. AI 輔助修復 (使用另一個 AI call)

---

## 📊 數據結構

### API Request
```json
{
  "function_expr": "np.sin(t)",
  "period": 6.283185,
  "n_terms": 5
}
```

### AI Response (Internal)
```json
{
  "thinking_process": {
    "steps": [
      {
        "step_number": 1,
        "title": "識別函數類型",
        "explanation": "...",
        "formula": "LaTeX 公式"
      }
    ]
  },
  "executable_code": {
    "imports": ["numpy as np", "scipy.integrate as integrate"],
    "function_def": "def f(t):\n    return np.sin(t)",
    "coefficients": {
      "a0": 0.0,
      "an": [0.0, 0.0, 0.0, 0.0, 0.0],
      "bn": [1.0, 0.0, 0.0, 0.0, 0.0]
    }
  }
}
```

### API Response (Success)
```json
{
  "success": true,
  "iterations": 1,
  "thinking_process": {...},
  "coefficients": {
    "a0": 0.0,
    "an": [...],
    "bn": [...]
  },
  "verification": {
    "is_verified": true,
    "max_error": 0.0001,
    "mean_error": 0.00005,
    "numerical_coefficients": {...}
  },
  "visualization": {
    "t_points": [...],
    "original_values": [...],
    "reconstructed_values": [...],
    "pointwise_error": [...]
  }
}
```

---

## 🎯 核心設計原則

### 1. 雙軌輸出原則
```
AI 響應同時服務兩個目標:
├─ Human-Readable (thinking_process)
│  └─ 給用戶看的推理過程
└─ Machine-Readable (executable_code)
   └─ 給系統驗證的精確代碼
```

### 2. 閉環驗證原則
```
AI 推導 → 數值驗證 → 誤差分析 → 反饋修正
   ↑                                    ↓
   └────────── 最多 3 次迭代 ───────────┘
```

### 3. 透明化原則
```
展示完整過程:
├─ AI 推理步驟
├─ 計算結果
├─ 驗證過程
└─ 誤差分析
```

---

## 🛠️ 技術棧

### 後端
- **框架**: FastAPI (Python 3.11+)
- **AI**: Anthropic Claude API (Haiku 3.5)
- **數值計算**: NumPy, SciPy
- **驗證**: Pydantic

### 前端
- **基礎**: HTML5 + Vanilla JavaScript
- **圖表**: Chart.js 4.4.0
- **數學渲染**: MathJax 3.x (預留)
- **樣式**: CSS3 (漸變、動畫)

### 部署
- **後端**: Uvicorn (ASGI server)
- **前端**: Python HTTP server (開發) / Vercel (生產)

---

## 📈 性能與成本

### API 調用成本 (Haiku 3.5)
- **輸入**: ~$0.25 / million tokens
- **輸出**: ~$1.25 / million tokens
- **單次計算**: 約 1000-2000 tokens
- **預估成本**: ~$0.001-0.003 / 次

### 響應時間
- **AI 推導**: 10-20 秒
- **數值驗證**: < 1 秒
- **視覺化生成**: < 1 秒
- **總計**: 11-22 秒 / 次

### 誤差閾值
- **相對誤差**: 5%
- **絕對誤差** (近零值): 1e-6
- **驗證通過率**: ~90% (第一次)

---

## 🔐 安全考量

### 代碼執行安全
```python
# 受限的命名空間
safe_namespace = {
    'np': np,
    'sin': np.sin,
    'cos': np.cos,
    # ... 只允許數學函數
}
exec(ai_code, safe_namespace)  # 沙箱執行
```

### CORS 配置
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]
```

---

## 🚀 未來擴展方向

### 短期 (1-2 週)
- [ ] 增加更多測試案例
- [ ] 改進 Prompt 精確度
- [ ] 優化前端 UI/UX
- [ ] 添加更多函數範例

### 中期 (1-2 月)
- [ ] 支持更多數學主題
  - 泰勒級數
  - 拉普拉斯變換
  - 微分方程
- [ ] 使用 SymPy 符號驗證
- [ ] 學生練習模式
- [ ] 錯誤模式資料庫

### 長期 (3-6 月)
- [ ] 自由推理模式 (不限制步驟)
- [ ] 元學習 (從錯誤中學習)
- [ ] 多模型比較
- [ ] 資料庫持久化

---

## 📝 開發日誌

**2025-10-14**:
- ✅ 完成 MVP 架構設計
- ✅ 實現後端核心引擎
- ✅ 實現數值驗證機制
- ✅ 實現迭代修正流程
- ✅ 完成前端視覺化
- ✅ 修復 CORS 問題
- ✅ 優化誤差計算邏輯
- ✅ 切換至 Haiku 3.5 降低成本
- ✅ 確保失敗時也顯示視覺化

**測試狀態**:
- ✓ sin(t) 計算正確
- ✓ 驗證機制正常
- ✓ 視覺化圖表顯示
- ✓ 迭代修正功能工作

---

## 🎓 結論

成功構建了一個**透明化 AI 數學推理平台**的 MVP，實現了：

1. **AI 完整推導** - 展示思考過程
2. **數值驗證** - 確保結果正確性
3. **自動修正** - 迭代改進能力
4. **視覺化展示** - 直觀比較結果

系統具有良好的**可擴展性**，可以應用到更多數學領域。

---

**文檔版本**: v1.0
**最後更新**: 2025-10-14
**作者**: AI Calculator Team
