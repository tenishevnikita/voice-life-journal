"""Integration tests for /stats and /export handlers."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.filters import CommandObject
from aiogram.types import Chat, Message, User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bot.handlers import cmd_export, cmd_stats
from src.models import Base, Entry


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create a test database session."""
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram user."""
    return User(
        id=12345678,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="ru",
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram chat."""
    return Chat(id=12345678, type="private")


@pytest.fixture
def mock_stats_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock message for /stats command."""
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = 1234567890
    message.chat = mock_chat
    message.from_user = mock_user
    message.text = "/stats"
    message.voice = None
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_export_message(mock_user: User, mock_chat: Chat) -> MagicMock:
    """Create a mock message for /export command."""
    message = MagicMock(spec=Message)
    message.message_id = 2
    message.date = 1234567890
    message.chat = mock_chat
    message.from_user = mock_user
    message.text = "/export"
    message.voice = None
    message.answer = AsyncMock()
    message.answer_document = AsyncMock()
    return message


class TestStatsHandler:
    """Integration tests for /stats command handler."""

    async def test_stats_no_entries(
        self,
        mock_stats_message: MagicMock,
        test_session: AsyncSession,
        test_engine,
    ):
        """Should show message when user has no entries."""
        command = CommandObject(prefix="/", command="stats", args=None)

        # Mock get_session to use test session
        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_stats(mock_stats_message, command)

        mock_stats_message.answer.assert_called()
        call_args = mock_stats_message.answer.call_args[0][0]
        assert "нет записей" in call_args

    async def test_stats_with_entries(
        self,
        mock_stats_message: MagicMock,
        test_session: AsyncSession,
        test_engine,
    ):
        """Should show stats when user has entries."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create test entries
        for i in range(3):
            entry = Entry(
                user_id=user_id,
                transcription=f"Entry {i}",
                mood_score=7,
                tags=["work"],
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(days=i)

        await test_session.commit()

        command = CommandObject(prefix="/", command="stats", args=None)

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_stats(mock_stats_message, command)

        mock_stats_message.answer.assert_called()
        call_args = mock_stats_message.answer.call_args[0][0]
        assert "статистика" in call_args
        assert "Записей: 3" in call_args

    async def test_stats_invalid_period(
        self,
        mock_stats_message: MagicMock,
    ):
        """Should show error for invalid period."""
        command = CommandObject(prefix="/", command="stats", args="invalid")

        await cmd_stats(mock_stats_message, command)

        mock_stats_message.answer.assert_called()
        call_args = mock_stats_message.answer.call_args[0][0]
        assert "Неверный период" in call_args

    async def test_stats_with_period_month(
        self,
        mock_stats_message: MagicMock,
        test_session: AsyncSession,
    ):
        """Should accept month period."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test entry",
            mood_score=8,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now - timedelta(days=15)
        await test_session.commit()

        command = CommandObject(prefix="/", command="stats", args="month")

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_stats(mock_stats_message, command)

        mock_stats_message.answer.assert_called()
        call_args = mock_stats_message.answer.call_args[0][0]
        assert "месяц" in call_args


class TestExportHandler:
    """Integration tests for /export command handler."""

    async def test_export_no_entries(
        self,
        mock_export_message: MagicMock,
        test_session: AsyncSession,
    ):
        """Should show message when user has no entries to export."""
        command = CommandObject(prefix="/", command="export", args=None)

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_export(mock_export_message, command)

        # Should first answer "Generating..." then answer no entries
        assert mock_export_message.answer.call_count >= 1

    async def test_export_csv_with_entries(
        self,
        mock_export_message: MagicMock,
        test_session: AsyncSession,
    ):
        """Should export CSV when user has entries."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test export entry",
            mood_score=7,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        command = CommandObject(prefix="/", command="export", args="csv")

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_export(mock_export_message, command)

        # Should send document
        mock_export_message.answer_document.assert_called()
        call_kwargs = mock_export_message.answer_document.call_args[1]
        assert "caption" in call_kwargs
        assert "экспорт готов" in call_kwargs["caption"]

    async def test_export_invalid_format(
        self,
        mock_export_message: MagicMock,
    ):
        """Should show error for invalid format."""
        command = CommandObject(prefix="/", command="export", args="xml")

        await cmd_export(mock_export_message, command)

        mock_export_message.answer.assert_called()
        call_args = mock_export_message.answer.call_args[0][0]
        assert "Неверный формат" in call_args

    async def test_export_json_format(
        self,
        mock_export_message: MagicMock,
        test_session: AsyncSession,
    ):
        """Should export JSON when format is json."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test JSON export",
            mood_score=8,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        command = CommandObject(prefix="/", command="export", args="json")

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=test_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            await cmd_export(mock_export_message, command)

        mock_export_message.answer_document.assert_called()
        call_kwargs = mock_export_message.answer_document.call_args[1]
        document = call_kwargs["document"]
        assert document.filename.endswith(".json")


class TestHandlerAuthorization:
    """Tests for handler authorization checks."""

    async def test_stats_unauthorized_user(
        self,
        mock_stats_message: MagicMock,
    ):
        """Should reject unauthorized users for /stats."""
        command = CommandObject(prefix="/", command="stats", args=None)

        with patch("src.bot.handlers.is_user_allowed", return_value=False):
            await cmd_stats(mock_stats_message, command)

        mock_stats_message.answer.assert_called()
        call_args = mock_stats_message.answer.call_args[0][0]
        assert "not authorized" in call_args

    async def test_export_unauthorized_user(
        self,
        mock_export_message: MagicMock,
    ):
        """Should reject unauthorized users for /export."""
        command = CommandObject(prefix="/", command="export", args=None)

        with patch("src.bot.handlers.is_user_allowed", return_value=False):
            await cmd_export(mock_export_message, command)

        mock_export_message.answer.assert_called()
        call_args = mock_export_message.answer.call_args[0][0]
        assert "not authorized" in call_args
