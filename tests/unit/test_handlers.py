"""Unit tests for bot handlers."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User, Voice

from src.bot.handlers import cmd_start, cmd_summary, handle_text, handle_voice, is_user_allowed, save_journal_entry
from src.services.transcription import (
    TranscriptionAPIError,
    TranscriptionError,
    TranscriptionRateLimitError,
)


class TestUserAuthorization:
    """Test user authorization checks."""

    @pytest.mark.asyncio
    async def test_is_user_allowed_no_whitelist(self) -> None:
        """Test that all users are allowed when whitelist is disabled."""
        with patch("src.bot.handlers.config.allowed_user_ids", None):
            assert await is_user_allowed(12345678) is True
            assert await is_user_allowed(99999999) is True

    @pytest.mark.asyncio
    async def test_is_user_allowed_with_whitelist(self) -> None:
        """Test that only whitelisted users are allowed."""
        with patch("src.bot.handlers.config.allowed_user_ids", [12345678, 87654321]):
            assert await is_user_allowed(12345678) is True
            assert await is_user_allowed(87654321) is True
            assert await is_user_allowed(99999999) is False

    @pytest.mark.asyncio
    async def test_is_user_allowed_empty_whitelist(self) -> None:
        """Test that no users are allowed with empty whitelist."""
        with patch("src.bot.handlers.config.allowed_user_ids", []):
            assert await is_user_allowed(12345678) is False


class TestStartCommand:
    """Test /start command handler."""

    @pytest.mark.asyncio
    async def test_start_command_sends_welcome_message(self, mock_message: Message) -> None:
        """Test that /start command sends welcome message."""
        mock_message.text = "/start"
        await cmd_start(mock_message)

        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Welcome to Voice Life Journal" in call_args[0][0]
        assert "voice message" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_start_command_unauthorized_user(self, mock_message: Message) -> None:
        """Test that unauthorized users get rejection message."""
        with patch("src.bot.handlers.config.allowed_user_ids", [99999999]):
            await cmd_start(mock_message)

            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "not authorized" in call_args[0][0].lower()


class TestVoiceMessageHandler:
    """Test voice message handler."""

    @pytest.mark.asyncio
    async def test_voice_message_transcribed(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test that voice message is transcribed and returned."""
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            return_value="This is a test transcription.",
        ):
            await handle_voice(mock_voice_message, mock_bot)

        # Should react with emoji
        mock_voice_message.react.assert_called_once()

        # Should send transcription
        mock_voice_message.answer.assert_called_once()
        call_args = mock_voice_message.answer.call_args
        assert "test transcription" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_too_large(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test that oversized voice messages are rejected."""
        # Set file size to 25MB (exceeds 20MB limit)
        if mock_voice_message.voice:
            mock_voice_message.voice.file_size = 25 * 1024 * 1024

        await handle_voice(mock_voice_message, mock_bot)

        # Should send rejection message
        mock_voice_message.answer.assert_called_once()
        call_args = mock_voice_message.answer.call_args
        assert "too large" in call_args[0][0].lower()

        # Should NOT react with emoji
        mock_voice_message.react.assert_not_called()

    @pytest.mark.asyncio
    async def test_voice_message_unauthorized_user(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test that unauthorized users cannot send voice messages."""
        with patch("src.bot.handlers.config.allowed_user_ids", [99999999]):
            await handle_voice(mock_voice_message, mock_bot)

            mock_voice_message.answer.assert_called_once()
            call_args = mock_voice_message.answer.call_args
            assert "not authorized" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_empty_transcription(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test handling of empty transcription result."""
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            return_value="",
        ):
            await handle_voice(mock_voice_message, mock_bot)

        call_args = mock_voice_message.answer.call_args
        assert "couldn't detect" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_rate_limit_error(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test handling of rate limit error."""
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            side_effect=TranscriptionRateLimitError("Rate limit"),
        ):
            await handle_voice(mock_voice_message, mock_bot)

        call_args = mock_voice_message.answer.call_args
        assert "too many requests" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_api_error(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test handling of API error."""
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            side_effect=TranscriptionAPIError("API error"),
        ):
            await handle_voice(mock_voice_message, mock_bot)

        call_args = mock_voice_message.answer.call_args
        assert "temporarily unavailable" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_transcription_error(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test handling of general transcription error."""
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            side_effect=TranscriptionError("Transcription failed"),
        ):
            await handle_voice(mock_voice_message, mock_bot)

        call_args = mock_voice_message.answer.call_args
        assert "failed to transcribe" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_download_failed(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """Test handling of failed file download."""
        mock_bot.download_file = AsyncMock(return_value=None)

        await handle_voice(mock_voice_message, mock_bot)

        call_args = mock_voice_message.answer.call_args
        assert "failed to download" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_saved_to_database(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """
        BDD Test: Given voice message transcribed, When processing complete,
        Then entry is saved to database with correct data.
        """
        test_transcription = "This is my journal entry for today."

        mock_save = AsyncMock()

        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            return_value=test_transcription,
        ), patch(
            "src.bot.handlers.save_journal_entry",
            mock_save,
        ), patch(
            "src.bot.handlers.analysis_service.analyze",
            new_callable=AsyncMock,
            return_value=None,  # Short text - no analysis
        ):
            await handle_voice(mock_voice_message, mock_bot)

        # Verify entry was saved with correct data
        mock_save.assert_called_once_with(
            user_id=mock_voice_message.from_user.id,
            transcription=test_transcription,
            voice_file_id=mock_voice_message.voice.file_id,
            voice_duration_seconds=mock_voice_message.voice.duration,
            analysis_result=None,
        )

    @pytest.mark.asyncio
    async def test_voice_message_confirms_save(
        self, mock_voice_message: Message, mock_bot: MagicMock
    ) -> None:
        """
        BDD Test: Given entry saved to database, When sending confirmation,
        Then user sees save confirmation in response.
        """
        with patch(
            "src.bot.handlers.whisper_service.transcribe",
            new_callable=AsyncMock,
            return_value="Test entry content",
        ), patch(
            "src.bot.handlers.save_journal_entry",
            new_callable=AsyncMock,
        ), patch(
            "src.bot.handlers.analysis_service.analyze",
            new_callable=AsyncMock,
            return_value=None,  # Short text - no analysis
        ):
            await handle_voice(mock_voice_message, mock_bot)

        # Verify response includes save confirmation (Russian or English)
        call_args = mock_voice_message.answer.call_args[0][0]
        assert "записано" in call_args.lower() or "saved" in call_args.lower()


class TestTextMessageHandler:
    """Test text message handler."""

    @pytest.mark.asyncio
    async def test_text_message_suggests_voice(self, mock_text_message: Message) -> None:
        """Test that text messages suggest using voice instead."""
        await handle_text(mock_text_message)

        mock_text_message.answer.assert_called_once()
        call_args = mock_text_message.answer.call_args
        assert "voice message" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_text_message_unauthorized_user(self, mock_text_message: Message) -> None:
        """Test that unauthorized users cannot send text messages."""
        with patch("src.bot.handlers.config.allowed_user_ids", [99999999]):
            await handle_text(mock_text_message)

            mock_text_message.answer.assert_called_once()
            call_args = mock_text_message.answer.call_args
            assert "not authorized" in call_args[0][0].lower()


class TestSummaryCommand:
    """Test /summary command handler - BDD: User requests summary of entries."""

    @pytest.mark.asyncio
    async def test_summary_command_with_entries(self, mock_message: Message) -> None:
        """
        Given пользователь написал 3 записи за последнюю неделю
        When пользователь отправляет /summary week
        Then бот возвращает список записей с датами и количеством
        """
        mock_message.text = "/summary week"

        # Mock CommandObject
        mock_command = MagicMock()
        mock_command.args = "week"

        # Mock entries
        now = datetime.now(timezone.utc)
        mock_entries = [
            MagicMock(
                created_at=now - timedelta(days=1),
                transcription="Entry from yesterday",
            ),
            MagicMock(
                created_at=now - timedelta(days=3),
                transcription="Entry from 3 days ago",
            ),
        ]

        mock_entry_service = MagicMock()
        mock_entry_service.get_entries_by_date_range = AsyncMock(return_value=mock_entries)

        with patch("src.bot.handlers.get_session") as mock_get_session:
            # Setup async context manager for session
            mock_session = MagicMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            # Patch EntryService constructor
            with patch("src.bot.handlers.EntryService", return_value=mock_entry_service):
                await cmd_summary(mock_message, mock_command)

        # Verify response contains summary
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Summary" in call_args
        assert "Total entries: 2" in call_args
        assert "Entry from yesterday" in call_args
        assert "Entry from 3 days ago" in call_args

    @pytest.mark.asyncio
    async def test_summary_command_no_entries(self, mock_message: Message) -> None:
        """
        Given пользователь не имеет записей
        When пользователь отправляет /summary
        Then бот возвращает сообщение об отсутствии записей
        """
        mock_message.text = "/summary"

        mock_command = MagicMock()
        mock_command.args = None  # Default to week

        mock_entry_service = MagicMock()
        mock_entry_service.get_entries_by_date_range = AsyncMock(return_value=[])

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.EntryService", return_value=mock_entry_service):
                await cmd_summary(mock_message, mock_command)

        # Verify response indicates no entries
        call_args = mock_message.answer.call_args[0][0]
        assert "No entries found" in call_args

    @pytest.mark.asyncio
    async def test_summary_command_invalid_period(self, mock_message: Message) -> None:
        """Test that invalid period triggers error message."""
        mock_message.text = "/summary invalid"

        mock_command = MagicMock()
        mock_command.args = "invalid"

        await cmd_summary(mock_message, mock_command)

        # Should send error message without querying database
        call_args = mock_message.answer.call_args[0][0]
        assert "Invalid period" in call_args
        assert "today" in call_args.lower()
        assert "week" in call_args.lower()
        assert "month" in call_args.lower()

    @pytest.mark.asyncio
    async def test_summary_command_period_today(self, mock_message: Message) -> None:
        """Test /summary today calculates correct date range."""
        mock_message.text = "/summary today"

        mock_command = MagicMock()
        mock_command.args = "today"

        mock_entry_service = MagicMock()
        mock_entry_service.get_entries_by_date_range = AsyncMock(return_value=[])

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.EntryService", return_value=mock_entry_service):
                await cmd_summary(mock_message, mock_command)

        # Verify date range passed to service
        call_kwargs = mock_entry_service.get_entries_by_date_range.call_args[1]
        start_date = call_kwargs["start_date"]
        end_date = call_kwargs["end_date"]

        # Should be today (midnight to now)
        assert start_date.hour == 0
        assert start_date.minute == 0
        assert (end_date - start_date).days == 0

    @pytest.mark.asyncio
    async def test_summary_command_unauthorized_user(self, mock_message: Message) -> None:
        """Test that unauthorized users cannot access summary."""
        mock_command = MagicMock()
        mock_command.args = None

        with patch("src.bot.handlers.config.allowed_user_ids", [99999999]):
            await cmd_summary(mock_message, mock_command)

        call_args = mock_message.answer.call_args[0][0]
        assert "not authorized" in call_args.lower()

    @pytest.mark.asyncio
    async def test_summary_command_truncates_long_entries(self, mock_message: Message) -> None:
        """Test that long transcriptions are truncated in summary."""
        mock_message.text = "/summary"

        mock_command = MagicMock()
        mock_command.args = None

        # Create entry with long transcription (> 100 chars)
        long_text = "A" * 150
        mock_entries = [
            MagicMock(
                created_at=datetime.now(timezone.utc),
                transcription=long_text,
            ),
        ]

        mock_entry_service = MagicMock()
        mock_entry_service.get_entries_by_date_range = AsyncMock(return_value=mock_entries)

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.EntryService", return_value=mock_entry_service):
                await cmd_summary(mock_message, mock_command)

        # Verify response has truncated text
        call_args = mock_message.answer.call_args[0][0]
        # Should be truncated to 97 chars + "..."
        assert "AAA..." in call_args
        # Original long text should not be fully present
        assert long_text not in call_args

    @pytest.mark.asyncio
    async def test_summary_command_period_month(self, mock_message: Message) -> None:
        """Test /summary month calculates correct date range."""
        mock_message.text = "/summary month"

        mock_command = MagicMock()
        mock_command.args = "month"

        mock_entry_service = MagicMock()
        mock_entry_service.get_entries_by_date_range = AsyncMock(return_value=[])

        with patch("src.bot.handlers.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.EntryService", return_value=mock_entry_service):
                await cmd_summary(mock_message, mock_command)

        # Verify date range passed to service
        call_kwargs = mock_entry_service.get_entries_by_date_range.call_args[1]
        start_date = call_kwargs["start_date"]
        end_date = call_kwargs["end_date"]

        # Should be last 30 days
        assert (end_date - start_date).days >= 29  # Allow for time drift
        assert (end_date - start_date).days <= 31
