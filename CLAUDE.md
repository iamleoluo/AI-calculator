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
