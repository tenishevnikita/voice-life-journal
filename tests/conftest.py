"""Shared pytest fixtures for tests."""

import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Set environment variables before importing application modules
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
os.environ.setdefault("OPENAI_API_KEY", "sk-test1234567890")
os.environ.setdefault("OPENAI_BASE_URL", "")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("ALLOWED_USER_IDS", "")
os.environ.setdefault("WHISPER_MODEL", "whisper-1")
os.environ.setdefault("MAX_VOICE_FILE_SIZE_MB", "20")

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, User, Voice

from src.bot.handlers import router


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for tests."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test1234567890")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ALLOWED_USER_IDS", "")
    monkeypatch.setenv("WHISPER_MODEL", "whisper-1")
    monkeypatch.setenv("MAX_VOICE_FILE_SIZE_MB", "20")


@pytest.fixture
async def bot() -> AsyncGenerator[Bot, None]:
    """Create a mock bot instance."""
    bot = Bot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    yield bot
    await bot.session.close()


@pytest.fixture
async def dp() -> Dispatcher:
    """Create a dispatcher with handlers registered."""
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram user."""
    return User(
        id=12345678,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="en",
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram chat."""
    return Chat(id=12345678, type="private")


@pytest.fixture
def mock_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock text message."""
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = 1234567890
    message.chat = mock_chat
    message.from_user = mock_user
    message.text = "/start"
    message.voice = None
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message


@pytest.fixture
def mock_voice_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock voice message."""
    voice = MagicMock(spec=Voice)
    voice.file_id = "voice_file_id_123"
    voice.file_unique_id = "unique_voice_123"
    voice.duration = 5
    voice.file_size = 50000  # 50KB

    message = MagicMock(spec=Message)
    message.message_id = 2
    message.date = 1234567890
    message.chat = mock_chat
    message.from_user = mock_user
    message.voice = voice
    message.text = None
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message


@pytest.fixture
def mock_bot() -> MagicMock:
    """Create a mock Bot instance for testing voice handlers."""
    import io

    bot = MagicMock(spec=Bot)

    # Mock get_file to return a file object
    mock_file = MagicMock()
    mock_file.file_path = "voice/file_123.ogg"
    bot.get_file = AsyncMock(return_value=mock_file)

    # Mock download_file to return audio bytes
    mock_audio_data = io.BytesIO(b"fake audio data for testing")
    bot.download_file = AsyncMock(return_value=mock_audio_data)

    return bot


@pytest.fixture
def mock_text_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock regular text message."""
    message = MagicMock(spec=Message)
    message.message_id = 3
    message.date = 1234567890
    message.chat = mock_chat
    message.from_user = mock_user
    message.text = "Hello, this is a test message!"
    message.voice = None
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message
