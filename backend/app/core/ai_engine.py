"""
AI Engine for calling Claude API and parsing responses
"""
import json
import logging
from typing import Dict, Any
from anthropic import Anthropic

from app.core.config import settings
from app.core.robust_parser import RobustResponseParser

logger = logging.getLogger(__name__)


class AIEngine:
    """Handles Claude API calls and response parsing"""

    def __init__(self):
        """Initialize AI engine with Claude client"""
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        self.parser = RobustResponseParser(anthropic_client=self.client)

    async def derive_fourier_series(self, prompt: str) -> Dict[str, Any]:
        """
        Call Claude API to derive Fourier series.

        Args:
            prompt: Structured prompt for derivation

        Returns:
            Parsed response dictionary with thinking_process and executable_code

        Raises:
            Exception: If API call fails or response cannot be parsed
        """
        try:
            logger.info("Calling Claude API for Fourier series derivation")

            # Call Claude API
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            response_text = response.content[0].text
            logger.debug(f"Raw response length: {len(response_text)} characters")

            # Parse response with robust parser
            parsed_response = self.parser.parse_with_fallback(response_text)

            logger.info(
                f"Successfully parsed response using strategy: "
                f"{self.parser.parse_attempts[-1]['strategy']}"
            )

            return parsed_response

        except Exception as e:
            logger.error(f"Failed to derive Fourier series: {e}")
            if hasattr(self, "parser") and self.parser.parse_attempts:
                logger.error(f"Parse attempts: {self.parser.parse_attempts}")
            raise


class SimpleAIEngine:
    """
    Simplified AI engine without robust parsing for initial testing.
    Use this if you want to see raw responses and debug prompt issues.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)

    async def derive_fourier_series(self, prompt: str) -> Dict[str, Any]:
        """
        Call Claude API with minimal parsing.

        Args:
            prompt: Structured prompt

        Returns:
            Parsed JSON response
        """
        logger.info("Calling Claude API (SimpleAIEngine)")

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            temperature=settings.CLAUDE_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        logger.info(f"Raw response (first 1000 chars):\n{response_text[:1000]}")
        logger.info(f"Response length: {len(response_text)} characters")

        # Try direct JSON parse
        try:
            # Remove markdown code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.rfind("```")
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.rfind("```")
                response_text = response_text[start:end].strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Response text:\n{response_text}")
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
