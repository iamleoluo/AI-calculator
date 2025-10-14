"""
Prompt builder for constructing Claude API prompts
"""


class PromptBuilder:
    """Builds structured prompts for Fourier series derivation"""

    @staticmethod
    def build_initial_prompt(function_expr: str, period: float, n_terms: int) -> str:
        """
        Build the initial prompt for Fourier series derivation.

        Args:
            function_expr: Python expression for the function (e.g., "np.sin(t)")
            period: Period of the function
            n_terms: Number of terms to calculate

        Returns:
            Formatted prompt string
        """
        return f"""你是一位數學教授和 Python 專家。請計算以下函數的傅立葉級數。

【問題】
函數表達式: f(t) = {function_expr}
週期: T = {period}
計算項數: n = {n_terms}

【任務】
1. 展示完整的數學推導過程
2. 計算傅立葉係數 a₀, aₙ, bₙ
3. 提供可執行的 Python 程式碼

【輸出格式要求】
請返回嚴格的 JSON 格式：

{{
  "thinking_process": {{
    "steps": [
      {{
        "step_number": 1,
        "title": "識別函數類型與對稱性",
        "explanation": "詳細說明...",
        "formula": "LaTeX 公式"
      }},
      {{
        "step_number": 2,
        "title": "計算 a₀ 係數",
        "explanation": "a₀ = (1/T) ∫₀ᵀ f(t) dt",
        "calculation": "具體計算過程",
        "result": "數值結果"
      }}
    ]
  }},
  "executable_code": {{
    "imports": ["numpy as np", "scipy.integrate as integrate"],
    "function_def": "def f(t):\\n    return {function_expr}",
    "coefficients": {{
      "a0": 0.0,
      "an": [0.0, 0.0, ...],
      "bn": [1.0, 0.0, ...]
    }}
  }},
  "final_result": {{
    "latex": "f(t) = a₀/2 + Σ(aₙcos(nω₀t) + bₙsin(nω₀t))",
    "series_terms": ["具體的前幾項"]
  }}
}}

【關鍵約束 - executable_code 部分】
⚠️ 這部分必須極度嚴格：
1. function_def 必須是完整可執行的 Python 函數定義
2. 不要包含 ```python 標記或任何 markdown
3. coefficients 必須是純數字（float），不是字串
4. 陣列長度必須正確（an 和 bn 各有 {n_terms} 個元素）
5. 使用 \\n 表示換行（在 JSON 字串中）

【傅立葉級數公式提醒】
f(t) = a₀/2 + Σ[aₙcos(nω₀t) + bₙsin(nω₀t)]

其中：
- ω₀ = 2π/T
- a₀ = (2/T) ∫₀ᵀ f(t) dt
- aₙ = (2/T) ∫₀ᵀ f(t)cos(nω₀t) dt
- bₙ = (2/T) ∫₀ᵀ f(t)sin(nω₀t) dt

請開始計算。"""

    @staticmethod
    def build_feedback_prompt(
        function_expr: str,
        period: float,
        n_terms: int,
        ai_coefficients: dict,
        numerical_coefficients: dict,
        error_percentage: float,
    ) -> str:
        """
        Build feedback prompt for iteration when verification fails.

        Args:
            function_expr: Original function expression
            period: Function period
            n_terms: Number of terms
            ai_coefficients: Coefficients from AI's previous attempt
            numerical_coefficients: Coefficients from numerical calculation
            error_percentage: Maximum error percentage

        Returns:
            Formatted feedback prompt
        """
        return f"""你上次的計算存在誤差，需要重新計算。

【原始問題】
函數: f(t) = {function_expr}
週期: T = {period}
項數: n = {n_terms}

【上次你計算的係數】
a₀ = {ai_coefficients.get('a0', 'N/A')}
aₙ = {ai_coefficients.get('an', [])}
bₙ = {ai_coefficients.get('bn', [])}

【數值驗證結果】
正確的 a₀ ≈ {numerical_coefficients.get('a0', 'N/A')}
正確的 aₙ ≈ {numerical_coefficients.get('an', [])}
正確的 bₙ ≈ {numerical_coefficients.get('bn', [])}

【誤差分析】
最大相對誤差: {error_percentage:.2f}%
閾值要求: 5%

【可能的問題】
1. 積分邊界：確認是從 0 到 T = {period}
2. 係數公式：注意 a₀ 的係數是 2/T（不是 1/T）
3. ω₀ 的值：ω₀ = 2π/T = {2 * 3.14159 / period:.6f}
4. 對稱性：檢查函數是否有奇偶對稱性

請重新仔細計算，特別注意以上幾點。

輸出格式與之前相同（JSON 格式，包含 thinking_process 和 executable_code）。"""
