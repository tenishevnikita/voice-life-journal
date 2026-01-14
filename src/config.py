"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration."""

    # Telegram Bot
    telegram_bot_token: str

    # OpenAI
    openai_api_key: str
    openai_base_url: Optional[str]

    # Database
    database_url: str

    # Application
    environment: str
    log_level: str

    # Security
    allowed_user_ids: Optional[list[int]]

    # Whisper
    whisper_model: str
    max_voice_file_size_mb: int

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        openai_base_url = os.getenv("OPENAI_BASE_URL")
        # Convert empty string to None
        if not openai_base_url or not openai_base_url.strip():
            openai_base_url = None

        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./voice_journal.db")
        environment = os.getenv("ENVIRONMENT", "development")
        log_level = os.getenv("LOG_LEVEL", "INFO")

        # Parse allowed user IDs
        allowed_user_ids_str = os.getenv("ALLOWED_USER_IDS", "")
        allowed_user_ids: Optional[list[int]] = None
        if allowed_user_ids_str.strip():
            try:
                allowed_user_ids = [
                    int(uid.strip())
                    for uid in allowed_user_ids_str.split(",")
                    if uid.strip()
                ]
            except ValueError as e:
                raise ValueError(f"Invalid ALLOWED_USER_IDS format: {e}")

        whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        max_voice_file_size_mb = int(os.getenv("MAX_VOICE_FILE_SIZE_MB", "20"))

        return cls(
            telegram_bot_token=telegram_bot_token,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            database_url=database_url,
            environment=environment,
            log_level=log_level,
            allowed_user_ids=allowed_user_ids,
            whisper_model=whisper_model,
            max_voice_file_size_mb=max_voice_file_size_mb,
        )


# Global config instance
config = Config.from_env()
