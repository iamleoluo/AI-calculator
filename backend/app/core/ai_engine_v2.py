"""
Refactored AI Engine with streaming support and three invocation modes
"""
import json
import logging
from typing import Dict, Any, AsyncIterator
from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIEngineV2:
    """
    AI Engine for three-stage computation:
    1. Stream derivation (Markdown)
    2. Translate to code (JSON)
    3. Analyze errors (JSON)
    """

    def __init__(self):
        """Initialize AI engine with Claude client"""
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        logger.info("AIEngineV2 initialized")

    async def stream_derivation(self, prompt: str) -> AsyncIterator[str]:
        """
        Stream derivation process in Markdown format (Prompt 1).

        Args:
            prompt: Derivation prompt

        Yields:
            Chunks of Markdown text

        Raises:
            Exception: If API call fails
        """
        try:
            logger.info("Streaming derivation from Claude API")

            # Use streaming API
            with self.client.messages.stream(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text

            logger.info("Derivation streaming completed")

        except Exception as e:
            logger.error(f"Failed to stream derivation: {e}")
            raise

    async def translate_to_code(self, prompt: str) -> Dict[str, str]:
        """
        Translate derivation to executable Python code (Prompt 2).

        Args:
            prompt: Code translation prompt

        Returns:
            Dictionary with original_function and fourier_reconstruction code

        Raises:
            Exception: If API call fails or response cannot be parsed
        """
        try:
            logger.info("Calling Claude API for code translation")

            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            logger.debug(f"Raw response length: {len(response_text)} characters")

            # Parse JSON response
            parsed_response = self._parse_json_response(response_text)

            # Validate required fields
            if "original_function" not in parsed_response:
                raise ValueError("Response missing 'original_function' field")
            if "coefficients" not in parsed_response:
                raise ValueError("Response missing 'coefficients' field")

            # Validate coefficients structure
            coeffs = parsed_response["coefficients"]
            if "a0" not in coeffs:
                raise ValueError("Coefficients missing 'a0' field")
            if "an" not in coeffs or not isinstance(coeffs["an"], list):
                raise ValueError("Coefficients missing or invalid 'an' field")
            if "bn" not in coeffs or not isinstance(coeffs["bn"], list):
                raise ValueError("Coefficients missing or invalid 'bn' field")

            logger.info("Code translation successful")
            return parsed_response

        except Exception as e:
            logger.error(f"Failed to translate to code: {e}")
            logger.error(f"Response text: {response_text if 'response_text' in locals() else 'N/A'}")
            raise

    async def analyze_error(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze verification error and decide next action (Prompt 3).

        Args:
            prompt: Error analysis prompt

        Returns:
            Dictionary with error analysis and decision

        Raises:
            Exception: If API call fails or response cannot be parsed
        """
        try:
            logger.info("Calling Claude API for error analysis")

            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            logger.debug(f"Raw response length: {len(response_text)} characters")

            # Parse JSON response
            parsed_response = self._parse_json_response(response_text)

            # Validate required fields
            required_fields = [
                "error_category",
                "severity",
                "need_recalculation",
                "recalculation_target",
                "explanation",
                "suggestion_to_user",
                "auto_stop"
            ]

            for field in required_fields:
                if field not in parsed_response:
                    logger.warning(f"Response missing '{field}' field, setting default")
                    parsed_response[field] = self._get_default_value(field)

            logger.info(f"Error analysis completed: {parsed_response['error_category']}")
            return parsed_response

        except Exception as e:
            logger.error(f"Failed to analyze error: {e}")
            logger.error(f"Response text: {response_text if 'response_text' in locals() else 'N/A'}")
            raise

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from AI response, handling markdown code blocks and text prefix.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.rfind("```")
            response_text = response_text[start:end].strip()

        # Try parse again
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object by looking for { and }
        # This handles cases where AI adds explanation before JSON
        try:
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')

            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_text = response_text[first_brace:last_brace + 1]
                return json.loads(json_text)
        except json.JSONDecodeError:
            pass

        # Last resort: try to find JSON array
        try:
            first_bracket = response_text.find('[')
            last_bracket = response_text.rfind(']')

            if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                json_text = response_text[first_bracket:last_bracket + 1]
                return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error after all attempts: {e}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            raise ValueError(f"Failed to parse AI response as JSON: {e}")

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field in error analysis"""
        defaults = {
            "error_category": "unknown",
            "severity": "warning",
            "need_recalculation": False,
            "recalculation_target": None,
            "explanation": "無法分析錯誤原因",
            "suggestion_to_user": "請檢查輸入參數",
            "suggestion_to_ai": None,
            "auto_stop": True
        }
        return defaults.get(field, None)


# Backward compatibility: Create alias
SimpleAIEngineV2 = AIEngineV2
