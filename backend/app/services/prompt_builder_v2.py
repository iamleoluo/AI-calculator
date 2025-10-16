"""
Refactored Prompt Builder for three-stage prompt generation
"""
from typing import Dict, Any, Optional


class PromptBuilderV2:
    """
    Builds structured prompts for three-stage computation:
    1. Derivation (Markdown symbolic derivation)
    2. Code Translation (Convert derivation to executable code)
    3. Error Analysis (Structured error analysis and decision)
    """

    @staticmethod
    def build_derivation_prompt(
        function_expr: str,
        period: float,
        n_terms: int,
        instruction_type: str = "fourier_series",
        retry_hint: Optional[str] = None
    ) -> str:
        """
        Build Prompt 1: Symbolic derivation in Markdown format.

        Args:
            function_expr: Python expression for the function (e.g., "np.sin(t)")
            period: Period of the function
            n_terms: Number of terms to calculate
            instruction_type: Type of mathematical operation (default: "fourier_series")
            retry_hint: Optional hint for retry attempts (from error analysis)

        Returns:
            Formatted prompt string for derivation
        """
        # Build base instruction based on type
        if instruction_type == "fourier_series":
            instruction = f"請計算此函數的傅立葉級數展開（前 {n_terms} 項）"
            formula_reference = """
【傅立葉級數公式提醒】
f(t) = a₀/2 + Σ[aₙcos(nω₀t) + bₙsin(nω₀t)]

其中：
- ω₀ = 2π/T
- a₀ = (2/T) ∫₀ᵀ f(t) dt
- aₙ = (2/T) ∫₀ᵀ f(t)cos(nω₀t) dt
- bₙ = (2/T) ∫₀ᵀ f(t)sin(nω₀t) dt
"""
        else:
            # Future: other mathematical operations
            instruction = f"請計算此函數的 {instruction_type}"
            formula_reference = ""

        # Build retry section if needed
        retry_section = ""
        if retry_hint:
            retry_section = f"""
【重要提示 - 請特別注意】
{retry_hint}

請根據以上提示重新仔細推導。
"""

        prompt = f"""你是一位數學教授。請為學生展示完整的數學推導過程。

【問題】
函數表達式: f(t) = {function_expr}
週期: T = {period}
計算項數: n = {n_terms}

【任務】
{instruction}

請以 **Markdown 格式** 展示完整的推導過程：

## 步驟 1：識別函數特性
- 分析函數的對稱性（奇函數、偶函數、一般函數）
- 判斷週期性
- 識別不連續點（如果有）

## 步驟 2：計算 a₀ 係數
- 寫出積分公式
- 展示積分計算過程
- 得出 **符號形式** 的結果（不需要數值）

## 步驟 3：計算 aₙ 係數
- 寫出積分公式
- 對每一項進行計算
- 得出 **符號形式** 的通項公式或各項結果

## 步驟 4：計算 bₙ 係數
- 寫出積分公式
- 對每一項進行計算
- 得出 **符號形式** 的通項公式或各項結果

## 步驟 5：寫出最終級數形式
- 組合所有係數
- 寫出完整的傅立葉級數表達式

{formula_reference}

【輸出格式要求】
1. 使用 Markdown 格式
2. 使用 LaTeX 數學公式（用 $ 或 $$ 包圍）
3. 詳細說明每一步的推理過程
4. **不需要計算數值**，保持符號形式即可
5. 清晰標註各個步驟的標題
{retry_section}
請開始推導。"""

        return prompt

    @staticmethod
    def build_code_translation_prompt(
        derivation_markdown: str,
        function_expr: str,
        period: float,
        n_terms: int
    ) -> str:
        """
        Build Prompt 2: Extract coefficients from symbolic derivation.

        Args:
            derivation_markdown: The Markdown derivation from Prompt 1
            function_expr: Original function expression
            period: Function period
            n_terms: Number of terms

        Returns:
            Formatted prompt for coefficient extraction
        """
        prompt = f"""你剛才推導了傅立葉級數。現在請給我兩個東西：

1. 原始函數的 Python 代碼
2. 你推導出的傅立葉係數數值

【你的推導過程】
\"\"\"
{derivation_markdown}
\"\"\"

【原始問題】
- 函數：f(t) = {function_expr}
- 週期：T = {period}
- 項數：n = {n_terms}

【輸出格式】
請返回 **嚴格的 JSON 格式**：

{{
  "original_function": "import numpy as np\\n\\ndef f(t):\\n    return np.sin(t) + np.cos(t)",
  "coefficients": {{
    "a0": 0.0,
    "an": [1.0, 0.0, 0.0],
    "bn": [1.0, 0.0, 0.0]
  }}
}}

【說明】
- original_function: 必須包含 import，可以直接用 exec() 執行
- coefficients.a0: 常數項係數（數值）
- coefficients.an: 餘弦項係數列表（長度為 {n_terms}）
- coefficients.bn: 正弦項係數列表（長度為 {n_terms}）

【重要】
- 係數必須是**數值**（float），不是符號
- 根據你的推導結果填寫
- an[0] 對應 a₁，an[1] 對應 a₂，以此類推
- 使用 \\n 表示換行

請給我結果。"""

        return prompt

    @staticmethod
    def build_error_analysis_prompt(
        derivation_markdown: str,
        code_response: Dict[str, str],
        verification_result: Dict[str, Any],
        function_expr: str,
        period: float,
        n_terms: int
    ) -> str:
        """
        Build Prompt 3: Analyze verification failure and decide next action.

        Args:
            derivation_markdown: The derivation from Prompt 1
            code_response: The code from Prompt 2
            verification_result: Verification result with error metrics
            function_expr: Original function expression
            period: Function period
            n_terms: Number of terms

        Returns:
            Formatted prompt for error analysis
        """
        # Extract verification metrics
        max_error = verification_result.get("max_relative_error", 0)
        mean_error = verification_result.get("mean_absolute_error", 0)
        max_error_location = verification_result.get("max_error_location", 0)
        error_type = verification_result.get("error_type", "unknown")

        # Build error context
        if error_type == "code_execution_error":
            error_context = f"""
【代碼執行錯誤】
錯誤訊息: {verification_result.get("error_message", "Unknown error")}

這表示生成的 Python 代碼無法執行，可能是語法錯誤或運行時錯誤。
"""
        else:
            error_context = f"""
【數值驗證失敗】
- 最大相對誤差: {max_error:.2%}
- 平均絕對誤差: {mean_error:.6f}
- 最大誤差位置: t = {max_error_location:.3f}
- 驗證閾值: 5%
"""

        # Extract coefficients for display
        coeffs = code_response.get("coefficients", {})
        a0 = coeffs.get("a0", "N/A")
        an = coeffs.get("an", [])
        bn = coeffs.get("bn", [])

        prompt = f"""你是數學和數值計算專家。請分析以下傅立葉級數計算的驗證結果。

【原始問題】
函數: f(t) = {function_expr}
週期: T = {period}
項數: n = {n_terms}

【你的推導過程】
\"\"\"
{derivation_markdown[:2000]}...
\"\"\"

【你給出的係數】
- a₀ = {a0}
- aₙ = {an}
- bₙ = {bn}

【原始函數代碼】
```python
{code_response.get("original_function", "N/A")}
```

{error_context}

【可能的原因分類】
1. **gibbs_phenomenon**: Gibbs 現象（不連續函數的固有誤差）- 屬於正常現象
2. **insufficient_terms**: 項數不足（n 太小）- 可接受或建議增加項數
3. **derivation_error**: 推導錯誤（積分計算、係數公式錯誤）- 需要重新推導
4. **code_translation_error**: 代碼翻譯錯誤（公式轉代碼時出錯）- 只需重新生成代碼
5. **numerical_precision**: 數值精度問題 - 通常可接受

【任務】
請分析這個錯誤的原因，並判斷是否需要重新計算。

請以 **嚴格的 JSON 格式** 返回分析結果：

{{
  "error_category": "gibbs_phenomenon | insufficient_terms | derivation_error | code_translation_error | numerical_precision",

  "severity": "acceptable | warning | critical",

  "need_recalculation": true | false,

  "recalculation_target": null | "derivation" | "code_only",

  "explanation": "詳細的錯誤分析（給用戶看，中文說明）",

  "suggestion_to_user": "給用戶的建議（中文）",

  "suggestion_to_ai": "如果需要重算，給 AI 自己的提示（檢查哪些地方，中文）",

  "auto_stop": true | false
}}

【欄位說明】
- error_category: 從上述5種分類中選擇
- severity:
  - acceptable: 誤差可接受，不影響教學目的
  - warning: 有問題但不嚴重
  - critical: 嚴重錯誤，必須修正
- need_recalculation: 是否需要重新計算
- recalculation_target:
  - null: 不需要重算
  - "derivation": 需要重新推導（完整重做）
  - "code_only": 推導正確，只需重新生成代碼
- auto_stop:
  - true: 自動停止迭代，接受當前結果（即使未通過驗證）
  - false: 繼續迭代嘗試

請開始分析。"""

        return prompt
