"""Unit tests for bot handlers."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message, User, Voice

from src.bot.handlers import cmd_start, handle_text, handle_voice, is_user_allowed


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
    async def test_voice_message_acknowledged(self, mock_voice_message: Message) -> None:
        """Test that voice message is acknowledged."""
        await handle_voice(mock_voice_message)

        # Should react with emoji
        mock_voice_message.react.assert_called_once()

        # Should send acknowledgment message
        mock_voice_message.answer.assert_called_once()
        call_args = mock_voice_message.answer.call_args
        assert "got your voice message" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_voice_message_too_large(self, mock_voice_message: Message) -> None:
        """Test that oversized voice messages are rejected."""
        # Set file size to 25MB (exceeds 20MB limit)
        if mock_voice_message.voice:
            mock_voice_message.voice.file_size = 25 * 1024 * 1024

        await handle_voice(mock_voice_message)

        # Should send rejection message
        mock_voice_message.answer.assert_called_once()
        call_args = mock_voice_message.answer.call_args
        assert "too large" in call_args[0][0].lower()

        # Should NOT react with emoji
        mock_voice_message.react.assert_not_called()

    @pytest.mark.asyncio
    async def test_voice_message_unauthorized_user(self, mock_voice_message: Message) -> None:
        """Test that unauthorized users cannot send voice messages."""
        with patch("src.bot.handlers.config.allowed_user_ids", [99999999]):
            await handle_voice(mock_voice_message)

            mock_voice_message.answer.assert_called_once()
            call_args = mock_voice_message.answer.call_args
            assert "not authorized" in call_args[0][0].lower()


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
