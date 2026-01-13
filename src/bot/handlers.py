"""Telegram bot message handlers."""

import logging
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import config

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
async def handle_voice(message: Message) -> None:
    """Handle voice messages."""
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

    # For now, just acknowledge receipt
    # TODO: Integrate Whisper transcription in issue #5
    await message.react([{"type": "emoji", "emoji": "👂"}])
    await message.answer(
        "🎧 Got your voice message! "
        "(Transcription coming soon in the next update)"
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
