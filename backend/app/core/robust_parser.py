"""
Robust Response Parser for AI-generated outputs
Handles various formatting issues and provides fallback mechanisms
"""

import json
import re
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Custom exception for parsing errors"""
    pass


class RobustResponseParser:
    """
    Parses AI responses with multiple fallback strategies to handle
    formatting inconsistencies in LLM outputs.
    """

    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        """
        Args:
            anthropic_client: Optional Anthropic client for AI-assisted repair
        """
        self.client = anthropic_client
        self.parse_attempts = []  # Track all parsing attempts for debugging

    def parse_with_fallback(self, response: str) -> Dict[str, Any]:
        """
        Main parsing method with multiple fallback strategies.

        Args:
            response: Raw response string from AI

        Returns:
            Parsed dictionary with validated structure

        Raises:
            ParseError: If all parsing strategies fail
        """
        self.parse_attempts = []

        # Strategy 1: Direct JSON parsing
        try:
            result = self._parse_direct(response)
            self._log_success("direct_json")
            return self._validate_structure(result)
        except Exception as e:
            self._log_attempt("direct_json", False, str(e))

        # Strategy 2: Clean common formatting issues
        try:
            result = self._parse_with_cleanup(response)
            self._log_success("cleaned_json")
            return self._validate_structure(result)
        except Exception as e:
            self._log_attempt("cleaned_json", False, str(e))

        # Strategy 3: Extract from code blocks
        try:
            result = self._extract_from_codeblock(response)
            self._log_success("codeblock_extraction")
            return self._validate_structure(result)
        except Exception as e:
            self._log_attempt("codeblock_extraction", False, str(e))

        # Strategy 4: Regex-based extraction
        try:
            result = self._extract_with_regex(response)
            self._log_success("regex_extraction")
            return self._validate_structure(result)
        except Exception as e:
            self._log_attempt("regex_extraction", False, str(e))

        # Strategy 5: AI-assisted repair (if client available)
        if self.client:
            try:
                result = self._ai_assisted_repair(response)
                self._log_success("ai_repair")
                return self._validate_structure(result)
            except Exception as e:
                self._log_attempt("ai_repair", False, str(e))

        # All strategies failed
        raise ParseError(
            f"Failed to parse response after {len(self.parse_attempts)} attempts. "
            f"Attempts: {self.parse_attempts}"
        )

    def _parse_direct(self, response: str) -> Dict[str, Any]:
        """Strategy 1: Direct JSON parsing"""
        return json.loads(response)

    def _parse_with_cleanup(self, response: str) -> Dict[str, Any]:
        """Strategy 2: Clean common formatting issues before parsing"""
        cleaned = response.strip()

        # Remove markdown code block markers
        cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
        cleaned = re.sub(r'\n```\s*$', '', cleaned)

        # Fix trailing commas in objects and arrays
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

        # Fix missing commas between elements (common AI mistake)
        # e.g., {"a": 1 "b": 2} -> {"a": 1, "b": 2}
        cleaned = re.sub(r'"\s*\n\s*"', '",\n"', cleaned)

        # Fix unescaped newlines in strings
        cleaned = re.sub(r'(?<!\\)\n(?=[^"]*"[^"]*(?:"[^"]*"[^"]*)*$)', r'\\n', cleaned)

        # Replace single quotes with double quotes (if not inside a string)
        # This is a simplified approach - might need refinement
        cleaned = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', cleaned)

        return json.loads(cleaned)

    def _extract_from_codeblock(self, response: str) -> Dict[str, Any]:
        """Strategy 3: Extract JSON from markdown code blocks"""
        # Pattern to match ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
            r'```json(.*?)```',
            r'```(.*?)```'
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Try cleanup on extracted content
                    return self._parse_with_cleanup(json_str)

        raise ValueError("No code block found in response")

    def _extract_with_regex(self, response: str) -> Dict[str, Any]:
        """Strategy 4: Use regex to extract key JSON structures"""
        # Find anything that looks like a JSON object
        json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)

        # Try parsing each match, starting with the longest
        matches.sort(key=len, reverse=True)

        for match in matches:
            try:
                result = json.loads(match)
                # Check if it has the expected structure
                if 'thinking_process' in result or 'executable_code' in result:
                    return result
            except json.JSONDecodeError:
                continue

        raise ValueError("No valid JSON structure found with regex")

    def _ai_assisted_repair(self, response: str) -> Dict[str, Any]:
        """Strategy 5: Use AI to repair malformed JSON"""
        repair_prompt = f"""The following text should be valid JSON but contains formatting errors.
Please output ONLY the corrected JSON, with no additional text or explanation.

Original text:
{response[:3000]}  # Limit to avoid token overflow

Output only the corrected JSON:"""

        try:
            repair_response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use faster, cheaper model
                max_tokens=4096,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": repair_prompt
                }]
            )

            repaired_text = repair_response.content[0].text

            # Try to parse the repaired response
            return self._parse_with_cleanup(repaired_text)

        except Exception as e:
            raise ParseError(f"AI-assisted repair failed: {e}")

    def _validate_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the parsed data has the expected structure.

        Expected structure:
        {
            "thinking_process": {
                "steps": [...]
            },
            "executable_code": {
                "imports": [...],
                "function_original": "...",
                "coefficients": {...}
            },
            "final_result": {...}
        }
        """
        errors = []

        # Check top-level keys
        required_keys = ['thinking_process', 'executable_code', 'final_result']
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Validate thinking_process structure
        if 'thinking_process' in data:
            if 'steps' not in data['thinking_process']:
                errors.append("thinking_process missing 'steps' key")
            elif not isinstance(data['thinking_process']['steps'], list):
                errors.append("thinking_process.steps must be a list")

        # Validate executable_code structure
        if 'executable_code' in data:
            exec_code = data['executable_code']
            if 'coefficients' not in exec_code:
                errors.append("executable_code missing 'coefficients' key")
            else:
                coeffs = exec_code['coefficients']
                # Validate coefficient types
                if 'a0' in coeffs and not isinstance(coeffs['a0'], (int, float)):
                    # Try to convert string to float
                    try:
                        coeffs['a0'] = float(coeffs['a0'])
                    except (ValueError, TypeError):
                        errors.append(f"Invalid a0 coefficient: {coeffs['a0']}")

                # Validate an and bn arrays
                for coeff_name in ['an', 'bn']:
                    if coeff_name in coeffs:
                        if not isinstance(coeffs[coeff_name], list):
                            errors.append(f"{coeff_name} must be a list")
                        else:
                            # Convert string numbers to floats
                            try:
                                coeffs[coeff_name] = [
                                    float(x) if isinstance(x, str) else x
                                    for x in coeffs[coeff_name]
                                ]
                            except (ValueError, TypeError) as e:
                                errors.append(f"Invalid {coeff_name} values: {e}")

        if errors:
            logger.warning(f"Validation warnings: {errors}")
            # Don't raise error for warnings, just log them
            # The system can still work with minor issues

        return data

    def _log_attempt(self, strategy: str, success: bool, error: str = ""):
        """Log parsing attempt"""
        self.parse_attempts.append({
            "strategy": strategy,
            "success": success,
            "error": error
        })
        logger.debug(f"Parse attempt - {strategy}: {'SUCCESS' if success else 'FAILED'} {error}")

    def _log_success(self, strategy: str):
        """Log successful parsing"""
        self._log_attempt(strategy, True)
        logger.info(f"Successfully parsed response using strategy: {strategy}")


class ExecutableCodeExtractor:
    """
    Extracts and validates executable Python code from AI responses.
    More focused than the general parser, specifically for code execution.
    """

    @staticmethod
    def extract_function_code(executable_code: Dict[str, Any]) -> str:
        """
        Extract clean Python code from executable_code section.

        Args:
            executable_code: The executable_code dict from AI response

        Returns:
            Clean Python code string ready for exec()
        """
        parts = []

        # Add imports
        if 'imports' in executable_code:
            imports = executable_code['imports']
            if isinstance(imports, list):
                for imp in imports:
                    # Clean up import statements
                    imp = imp.strip()
                    if not imp.startswith('import ') and not imp.startswith('from '):
                        imp = f"import {imp}"
                    parts.append(imp)

        # Add function definition
        if 'function_original' in executable_code:
            func_code = executable_code['function_original']
            # Remove markdown code block markers if present
            func_code = re.sub(r'^```python\s*\n', '', func_code)
            func_code = re.sub(r'\n```\s*$', '', func_code)
            func_code = func_code.strip()
            parts.append(func_code)

        return '\n\n'.join(parts)

    @staticmethod
    def validate_code_safety(code: str) -> List[str]:
        """
        Check for potentially unsafe code patterns.

        Returns:
            List of warnings (empty if safe)
        """
        warnings = []

        dangerous_patterns = [
            (r'\bexec\b', "Contains exec() call"),
            (r'\beval\b', "Contains eval() call"),
            (r'\b__import__\b', "Contains __import__"),
            (r'\bopen\b', "Contains file operations"),
            (r'\bos\.', "Contains os module access"),
            (r'\bsys\.', "Contains sys module access"),
            (r'\bsubprocess\b', "Contains subprocess"),
            (r'while\s+True\s*:', "Contains potential infinite loop"),
        ]

        for pattern, warning in dangerous_patterns:
            if re.search(pattern, code):
                warnings.append(warning)

        return warnings


# Example usage and testing
if __name__ == "__main__":
    # Test cases for different formatting issues

    test_cases = [
        # Test 1: Valid JSON
        '''{"thinking_process": {"steps": []}, "executable_code": {"coefficients": {"a0": 0.5}}, "final_result": {}}''',

        # Test 2: JSON in code block
        '''```json
        {"thinking_process": {"steps": []}, "executable_code": {"coefficients": {"a0": 0.5}}, "final_result": {}}
        ```''',

        # Test 3: Trailing commas
        '''{"thinking_process": {"steps": [],}, "executable_code": {"coefficients": {"a0": 0.5,}}, "final_result": {}}''',

        # Test 4: String numbers
        '''{"thinking_process": {"steps": []}, "executable_code": {"coefficients": {"a0": "0.5", "an": ["1.0", "2.0"]}}, "final_result": {}}''',
    ]

    parser = RobustResponseParser()

    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        try:
            result = parser.parse_with_fallback(test)
            print(f"✓ Successfully parsed")
            print(f"  Strategy used: {parser.parse_attempts[-1]['strategy']}")
            print(f"  Coefficients: {result.get('executable_code', {}).get('coefficients')}")
        except ParseError as e:
            print(f"✗ Failed to parse: {e}")
