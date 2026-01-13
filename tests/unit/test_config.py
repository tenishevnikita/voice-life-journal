"""Unit tests for configuration."""

import pytest

from src.config import Config


class TestConfig:
    """Test configuration loading from environment variables."""

    def test_config_loads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that configuration loads correctly from environment."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
        monkeypatch.setenv("OPENAI_API_KEY", "test_api_key_456")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("ALLOWED_USER_IDS", "123,456,789")
        monkeypatch.setenv("WHISPER_MODEL", "whisper-2")
        monkeypatch.setenv("MAX_VOICE_FILE_SIZE_MB", "15")

        config = Config.from_env()

        assert config.telegram_bot_token == "test_token_123"
        assert config.openai_api_key == "test_api_key_456"
        assert config.database_url == "sqlite:///test.db"
        assert config.environment == "production"
        assert config.log_level == "ERROR"
        assert config.allowed_user_ids == [123, 456, 789]
        assert config.whisper_model == "whisper-2"
        assert config.max_voice_file_size_mb == 15

    def test_config_missing_telegram_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing TELEGRAM_BOT_TOKEN raises error."""
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
            Config.from_env()

    def test_config_missing_openai_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing OPENAI_API_KEY raises error."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Config.from_env()

    def test_config_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that config uses defaults when optional vars not set."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("ALLOWED_USER_IDS", raising=False)
        monkeypatch.delenv("WHISPER_MODEL", raising=False)
        monkeypatch.delenv("MAX_VOICE_FILE_SIZE_MB", raising=False)

        config = Config.from_env()

        assert config.database_url == "sqlite+aiosqlite:///./voice_journal.db"
        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.allowed_user_ids is None
        assert config.whisper_model == "whisper-1"
        assert config.max_voice_file_size_mb == 20

    def test_config_empty_allowed_user_ids(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that empty ALLOWED_USER_IDS results in None."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("ALLOWED_USER_IDS", "")

        config = Config.from_env()

        assert config.allowed_user_ids is None

    def test_config_invalid_allowed_user_ids(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that invalid ALLOWED_USER_IDS format raises error."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("ALLOWED_USER_IDS", "123,abc,456")

        with pytest.raises(ValueError, match="Invalid ALLOWED_USER_IDS"):
            Config.from_env()
