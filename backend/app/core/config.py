"""
Configuration settings for the AI Calculator backend
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)


class Settings:
    """Application settings"""

    # API Keys
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")

    # Claude API settings
    CLAUDE_MODEL: str = "claude-3-5-haiku-20241022"  # Using Haiku 3.5 for lower cost
    CLAUDE_MAX_TOKENS: int = 8192
    CLAUDE_TEMPERATURE: float = 0.0

    # Verification settings
    ERROR_THRESHOLD: float = 0.05  # 5% relative error threshold
    MAX_ITERATIONS: int = 3

    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]

    @classmethod
    def validate(cls):
        """Validate required settings"""
        if not cls.CLAUDE_API_KEY:
            raise ValueError(
                "CLAUDE_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )


settings = Settings()
