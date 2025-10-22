# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered mathematical education platform** that demonstrates AI's mathematical reasoning capabilities through transparent, step-by-step derivations. The primary focus is Fourier series calculations, where AI not only computes results but shows complete derivation processes with self-verification.

**Core Philosophy**: Unlike traditional black-box calculators, this system emphasizes transparency - showing reasoning, calculations, and verification at every step.

## Core Architecture Principles

### 1. Dual-Output Principle (Two Worlds)

Every AI response serves two distinct audiences:

- **World 1 (Human-Readable)**: Teaching-focused content with natural language explanations, LaTeX formulas, and reasoning steps
- **World 2 (Machine-Readable)**: Strictly formatted, executable Python code for numerical verification

The system maintains separation between these two outputs throughout the data flow.

### 2. Closed-Loop Verification

The system implements an iterative verification cycle:

```
AI Derivation → Numerical Verification → Error Analysis → Feedback Correction → Re-verification
```

If error exceeds threshold (default 1%), the system constructs detailed feedback and requests AI to recalculate (max 5 iterations).

### 3. Data Flow

```
User Input (LaTeX + parameters)
  ↓
Prompt Construction (with strict format requirements)
  ↓
Claude API Call
  ↓
├─→ thinking_process → Frontend Display (steps, formulas, explanations)
└─→ executable_code → Backend Execution → Numerical Comparison → Error Check
                                                                    ↓
                                                          Pass? → Complete
                                                          Fail? → Iteration
```

## Planned Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI**: Anthropic Python SDK (Claude API)
- **Numerical Computing**: NumPy, SciPy, SymPy
- **Validation**: Pydantic schemas

### Frontend
- **Framework**: Next.js 14+ (React 18+, TypeScript)
- **UI**: Tailwind CSS + shadcn/ui
- **Math Rendering**: KaTeX
- **Visualization**: Plotly.js
- **State Management**: Zustand

### Database
- **Primary**: PostgreSQL 15+
- **Cache**: Redis 7+

## Key Components

### Backend Core Modules

1. **Prompt Builder** (`backend/app/services/prompt_builder.py`)
   - Constructs structured prompts for Claude API
   - Defines strict format requirements for executable code
   - Builds feedback prompts for iteration cycles
   - Critical: Prompt engineering is the foundation of the entire system

2. **AI Engine** (`backend/app/core/ai_engine.py`)
   - Handles Claude API communication
   - Parses and validates JSON responses
   - Implements retry mechanisms
   - Configuration: `model="claude-sonnet-4-5-20250929"`, `temperature=0.0`

3. **Code Executor** (`backend/app/core/executor.py`)
   - **Security Critical**: Safely executes AI-generated Python code
   - Uses whitelist for allowed modules (numpy, scipy, math)
   - Implements restricted namespace with `exec()`
   - Computes numerical Fourier coefficients independently

4. **Verification Engine** (`backend/app/core/verification.py`)
   - Compares AI results with numerical calculations
   - Calculates relative errors for all coefficients
   - Generates detailed error reports
   - Default error threshold: 1% (configurable)

5. **Fourier Service** (`backend/app/services/fourier_service.py`)
   - Orchestrates the complete computation workflow
   - Manages iteration state (max 5 iterations)
   - Coordinates between AI engine and verification
   - Returns complete history of all iterations

### Frontend Components

1. **Thinking Display** (`components/thinking-display/`)
   - Step-by-step derivation visualization
   - LaTeX formula rendering with KaTeX
   - Expandable/collapsible step cards

2. **Visualization** (`components/visualization/`)
   - Plotly.js charts comparing original vs reconstructed functions
   - Interactive visual verification

3. **LaTeX Editor** (`components/latex-editor/`)
   - Input interface for mathematical functions
   - Real-time LaTeX preview

## Database Schema

Key tables:
- `problems`: Stores input parameters (latex_input, period, n_terms)
- `ai_solutions`: AI-generated solutions with thinking_process and coefficients (JSONB)
- `verifications`: Verification results with error_metrics (JSONB)
- `iteration_history`: Complete iteration logs for analysis

## Development Commands

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # Runs on http://localhost:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

### Testing
```bash
# Backend tests
cd backend
pytest tests/

# Key test files:
# - tests/test_verification.py: Coefficient comparison logic
# - tests/test_fourier_service.py: Full computation flow
```

## Critical Implementation Notes

### Prompt Engineering

The success of this system depends entirely on prompt quality:

1. **Strict Output Format**: Prompts must explicitly define JSON structure for both `thinking_process` and `executable_code`
2. **Few-Shot Examples**: Include complete examples in prompts to ensure consistent formatting
3. **Executable Code Constraints**:
   - Must be pure Python (no markdown code blocks)
   - Must be directly executable with `exec()`
   - No comments or extra formatting
   - All coefficients must be numeric (float), not strings

### Security Considerations

1. **Code Execution**: Never execute AI-generated code without sandboxing
2. **Module Whitelist**: Only allow numpy, scipy, math in execution namespace
3. **Timeout Mechanisms**: Set execution time limits
4. **Input Validation**: Use Pydantic for all API inputs

### Error Handling

1. **Relative Error Calculation**: For values near zero (< 1e-10), use absolute error
2. **Error Thresholds**: May need adjustment based on function complexity
3. **Feedback Quality**: Error reports must be specific and actionable for AI

## API Endpoints

### POST `/api/v1/fourier-series`

**Request**:
```json
{
  "latex_input": "\\sin(t)",
  "period": 6.283185,
  "n_terms": 5
}
```

**Response**:
```json
{
  "thinking_process": {
    "steps": [/* array of step objects */]
  },
  "code_display": "formatted Python code",
  "final_result": {
    "latex": "f(t) = ..."
  },
  "verification": {
    "is_verified": true,
    "error_metrics": {/* error details */}
  },
  "iterations": 1
}
```

## Project Goals

1. **Educational Value**: Show complete mathematical reasoning, not just results
2. **AI Capability Demonstration**: Prove AI can perform rigorous mathematical derivations
3. **Self-Verification**: Demonstrate AI's ability to check and correct its own work
4. **Transparency**: Every step is visible and explainable

## Extensibility

The architecture is designed to support multiple mathematical topics beyond Fourier series:
- Taylor series expansions
- Laplace transforms
- Differential equations
- Other integral transforms

The core data flow (input → AI derivation → verification → feedback) is topic-agnostic.

## Configuration Files

- Environment variables should include:
  - `CLAUDE_API_KEY`: Anthropic API key (required)
  - `DATABASE_URL`: PostgreSQL connection string
  - `REDIS_URL`: Redis connection string (optional, for caching)
  - `ERROR_THRESHOLD`: Verification error threshold (default: 0.01)
  - `MAX_ITERATIONS`: Maximum iteration attempts (default: 5)

---

## 📚 Project Documentation

All project documentation is organized in the `docs/` directory. **Note**: Some documents contain outdated information from the planning phase.

### ✅ Current & Active Documents

**Deployment**:
- `docs/reports/DEPLOYMENT_SUCCESS_20251021.md` - **最新部署報告** (Vercel + Cloudflare Pages)
  - Current production architecture
  - CORS solutions for Vercel Serverless
  - Session management with `/tmp` directory
  - All deployment issues and solutions

**Testing**:
- `docs/reports/20251015_V2_TEST_RESULTS.md` - V2 版本測試結果
  - Three-stage streaming workflow tests
  - Valid for current V2 API implementation

### ⚠️ Historical Documents (Reference Only)

**Architecture** (2025-10-14):
- `docs/architecture/20251014_ARCHITECTURE.md` - 初始架構設計
  - **注意**: 設計時規劃使用 Next.js 前端，實際部署使用靜態 HTML
  - **注意**: 設計時規劃使用 PostgreSQL + Redis，實際使用 `/tmp` session 存儲
  - 核心概念（Dual-Output、Closed-Loop Verification）仍然有效

**Planning** (2025-10-14):
- `docs/planning/20251014_專案大綱.md` - 初始專案規劃
  - **注意**: 包含未實現的功能（用戶認證、資料庫等）
- `docs/planning/20251014_技術實作方案.md` - 初始技術方案
  - **注意**: 規劃的技術棧與實際部署不同

**Deployment** (2025-10-15 - Deprecated):
- `docs/deployment/20251015_DEPLOYMENT_GUIDE_Railway.md` - Railway 部署指南
  - **已棄用**: 專案最終部署在 Vercel + Cloudflare，不是 Railway
  - 僅作為替代方案參考

### 📖 Document Usage Guide

When working with this codebase:

1. **For current deployment info**: Refer to `docs/reports/DEPLOYMENT_SUCCESS_20251021.md`
2. **For architecture concepts**: Use `docs/architecture/20251014_ARCHITECTURE.md` for core principles, but note implementation differences
3. **For planning reference**: Historical planning docs are useful for understanding original intent, but verify against actual code

### 🔄 Current vs. Planned Differences

| Aspect | Original Plan | Current Implementation |
|--------|---------------|------------------------|
| Frontend | Next.js + React + TypeScript | Static HTML + Vanilla JS |
| Backend Host | Railway | Vercel Serverless |
| Frontend Host | Vercel | Cloudflare Pages |
| Database | PostgreSQL + Redis | No database (session in `/tmp`) |
| API Style | Streaming (SSE) | Synchronous (streaming 不穩定) |
| CORS | Middleware only | Explicit headers + global exception handler |

### 📝 Documentation Maintenance

- All documents are timestamped (YYYYMMDD_filename.md)
- Historical documents are marked with ⚠️ in `docs/README.md`
- Current production state is in `docs/reports/DEPLOYMENT_SUCCESS_20251021.md`

**When in doubt, trust the code over the docs.**
