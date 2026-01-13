"""Telegram bot message handlers."""

import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import config
from src.services.transcription import (
    TranscriptionAPIError,
    TranscriptionError,
    TranscriptionRateLimitError,
    whisper_service,
)

logger = logging.getLogger(__name__)

# Create router for handlers
router = Router()


async def is_user_allowed(user_id: int) -> bool:
    """Check if user is allowed to use the bot."""
    if config.allowed_user_ids is None:
        # No whitelist - allow all users
        return True
    return user_id in config.allowed_user_ids


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else "Unknown"

    logger.info(f"User {user_id} ({username}) started the bot")

    if user_id and not await is_user_allowed(user_id):
        await message.answer("🚫 Sorry, you are not authorized to use this bot.")
        logger.warning(f"Unauthorized user {user_id} ({username}) tried to access the bot")
        return

    welcome_message = """
🎙 **Welcome to Voice Life Journal!**

This is your personal voice diary with zero friction.

**How to use:**
Just send me a voice message anytime, and I'll:
- 🎧 Listen silently
- 📝 Transcribe it to text
- 💾 Save it to your journal

**Commands:**
/start - Show this message
/summary - Get summary of your entries (coming soon)

**Ready?** Just send me a voice message and let your thoughts flow! 🌊
"""

    await message.answer(welcome_message, parse_mode="Markdown")


@router.message(lambda message: message.voice is not None)
async def handle_voice(message: Message, bot: Bot) -> None:
    """Handle voice messages and transcribe them using Whisper API."""
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else "Unknown"

    logger.info(
        f"Received voice message from {user_id} ({username}), "
        f"duration: {message.voice.duration}s, size: {message.voice.file_size} bytes"
    )

    if user_id and not await is_user_allowed(user_id):
        await message.answer("🚫 Sorry, you are not authorized to use this bot.")
        logger.warning(f"Unauthorized user {user_id} ({username}) tried to send voice message")
        return

    # Check file size
    max_size_bytes = config.max_voice_file_size_mb * 1024 * 1024
    if message.voice.file_size and message.voice.file_size > max_size_bytes:
        await message.answer(
            f"⚠️ Voice message is too large. "
            f"Maximum size is {config.max_voice_file_size_mb}MB."
        )
        logger.warning(
            f"Voice message from {user_id} exceeds size limit: "
            f"{message.voice.file_size} bytes"
        )
        return

    # React to show we're processing
    await message.react([{"type": "emoji", "emoji": "👂"}])

    try:
        # Download voice file from Telegram
        file = await bot.get_file(message.voice.file_id)
        file_data = await bot.download_file(file.file_path)

        if file_data is None:
            logger.error(f"Failed to download voice file from {user_id}")
            await message.answer("❌ Failed to download voice message. Please try again.")
            return

        # Read bytes from BytesIO object
        audio_bytes = file_data.read()

        logger.debug(f"Downloaded voice file: {len(audio_bytes)} bytes")

        # Transcribe using Whisper
        transcription = await whisper_service.transcribe(audio_bytes)

        if not transcription:
            await message.answer(
                "🤔 I couldn't detect any speech in your voice message. "
                "Please try again with clearer audio."
            )
            return

        # Store in memory for now (database integration in issue #6)
        # TODO: Save to database in issue #6
        logger.info(f"Transcription for user {user_id}: {len(transcription)} chars")

        # Reply with transcription
        await message.answer(f"📝 **Your journal entry:**\n\n{transcription}")

    except TranscriptionRateLimitError:
        logger.warning(f"Rate limit hit for user {user_id}")
        await message.answer(
            "⏳ Too many requests. Please wait a moment and try again."
        )
    except TranscriptionAPIError as e:
        logger.error(f"API error for user {user_id}: {e}")
        await message.answer(
            "🔧 Transcription service is temporarily unavailable. "
            "Please try again in a few minutes."
        )
    except TranscriptionError as e:
        logger.error(f"Transcription error for user {user_id}: {e}")
        await message.answer(
            "❌ Failed to transcribe your voice message. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error processing voice from {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Something went wrong. Please try again later."
        )


@router.message(lambda message: message.text is not None)
async def handle_text(message: Message) -> None:
    """Handle text messages."""
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else "Unknown"

    logger.info(f"Received text message from {user_id} ({username}): {message.text}")

    if user_id and not await is_user_allowed(user_id):
        await message.answer("🚫 Sorry, you are not authorized to use this bot.")
        logger.warning(f"Unauthorized user {user_id} ({username}) tried to send text message")
        return

    # For now, inform user to use voice messages
    await message.answer(
        "💬 I see you sent a text message!\n\n"
        "This bot works best with **voice messages** 🎙\n\n"
        "Try sending a voice message instead - just hold the mic button "
        "in Telegram and speak your thoughts!"
    )
