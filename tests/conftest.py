"""Shared pytest fixtures for tests."""

import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, User, Voice

from src.bot.handlers import router


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for tests."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test1234567890")
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
def mock_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock text message."""
    message = Message(
        message_id=1,
        date=1234567890,
        chat=mock_chat,
        from_user=mock_user,
        text="/start",
    )
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message


@pytest.fixture
def mock_voice_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock voice message."""
    voice = Voice(
        file_id="voice_file_id_123",
        file_unique_id="unique_voice_123",
        duration=5,
        file_size=50000,  # 50KB
    )
    message = Message(
        message_id=2,
        date=1234567890,
        chat=mock_chat,
        from_user=mock_user,
        voice=voice,
    )
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message


@pytest.fixture
def mock_text_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock regular text message."""
    message = Message(
        message_id=3,
        date=1234567890,
        chat=mock_chat,
        from_user=mock_user,
        text="Hello, this is a test message!",
    )
    message.answer = AsyncMock()
    message.react = AsyncMock()
    return message
