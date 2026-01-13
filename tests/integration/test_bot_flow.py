"""Integration tests for bot message flow."""

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Message


class TestBotStartFlow:
    """Test /start command flow."""

    @pytest.mark.asyncio
    async def test_start_command_flow(
        self, bot: Bot, dp: Dispatcher, mock_message: Message
    ) -> None:
        """Test complete /start command processing flow."""
        mock_message.text = "/start"

        # Simulate update processing
        await dp.feed_update(bot, {"message": mock_message.model_dump(mode="python")})

        # Verify bot responded
        mock_message.answer.assert_called_once()
        response_text = mock_message.answer.call_args[0][0]

        # Check response contains expected content
        assert "Welcome" in response_text
        assert "Voice Life Journal" in response_text
        assert "/start" in response_text
        assert "/summary" in response_text


class TestBotVoiceFlow:
    """Test voice message flow."""

    @pytest.mark.asyncio
    async def test_voice_message_flow(
        self, bot: Bot, dp: Dispatcher, mock_voice_message: Message
    ) -> None:
        """Test complete voice message processing flow."""
        # Simulate update processing
        await dp.feed_update(bot, {"message": mock_voice_message.model_dump(mode="python")})

        # Verify bot reacted
        mock_voice_message.react.assert_called_once()

        # Verify bot responded
        mock_voice_message.answer.assert_called_once()
        response_text = mock_voice_message.answer.call_args[0][0]

        # Check response acknowledges voice message
        assert "voice message" in response_text.lower()


class TestBotTextFlow:
    """Test text message flow."""

    @pytest.mark.asyncio
    async def test_text_message_flow(
        self, bot: Bot, dp: Dispatcher, mock_text_message: Message
    ) -> None:
        """Test complete text message processing flow."""
        # Simulate update processing
        await dp.feed_update(bot, {"message": mock_text_message.model_dump(mode="python")})

        # Verify bot responded
        mock_text_message.answer.assert_called_once()
        response_text = mock_text_message.answer.call_args[0][0]

        # Check response suggests voice messages
        assert "voice" in response_text.lower()
