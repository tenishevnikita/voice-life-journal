"""Telegram bot message handlers."""

import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.config import config
from src.database import get_session
from src.services.entries import EntryService
from src.services.transcription import (
    TranscriptionAPIError,
    TranscriptionError,
    TranscriptionRateLimitError,
    whisper_service,
)

logger = logging.getLogger(__name__)

# Create router for handlers
router = Router()


async def save_journal_entry(
    user_id: int,
    transcription: str,
    voice_file_id: str,
    voice_duration_seconds: int,
) -> None:
    """Save journal entry to database.

    Args:
        user_id: Telegram user ID.
        transcription: Transcribed text.
        voice_file_id: Telegram voice file ID.
        voice_duration_seconds: Voice message duration.
    """
    async with get_session() as session:
        entry_service = EntryService(session)
        await entry_service.create_entry(
            user_id=user_id,
            transcription=transcription,
            voice_file_id=voice_file_id,
            voice_duration_seconds=voice_duration_seconds,
        )


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
/summary [period] - Get summary of your entries
  • today - entries from today
  • week - last 7 days (default)
  • month - last 30 days

**Ready?** Just send me a voice message and let your thoughts flow! 🌊
"""

    await message.answer(welcome_message, parse_mode="Markdown")


@router.message(Command("summary"))
async def cmd_summary(message: Message, command: CommandObject) -> None:
    """Handle /summary command to show entries for a period.

    Usage: /summary [period]
    Period options: today, week, month (default: week)
    """
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else "Unknown"

    logger.info(f"User {user_id} ({username}) requested summary")

    if user_id and not await is_user_allowed(user_id):
        await message.answer("🚫 Sorry, you are not authorized to use this bot.")
        logger.warning(f"Unauthorized user {user_id} ({username}) tried to access summary")
        return

    # Parse period argument (default: week)
    period = "week"
    if command.args:
        period = command.args.strip().lower()
        if period not in ["today", "week", "month"]:
            await message.answer(
                "⚠️ Invalid period. Use: `today`, `week`, or `month`\n\n"
                "Example: `/summary week`",
                parse_mode="Markdown",
            )
            return

    # Calculate date range based on period
    now = datetime.now(timezone.utc)
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        period_label = "today"
    elif period == "week":
        start_date = now - timedelta(days=7)
        end_date = now
        period_label = "last 7 days"
    elif period == "month":
        start_date = now - timedelta(days=30)
        end_date = now
        period_label = "last 30 days"
    else:
        # Should not reach here due to validation above
        await message.answer("⚠️ Invalid period.")
        return

    # Fetch entries from database
    try:
        async with get_session() as session:
            entry_service = EntryService(session)
            entries = await entry_service.get_entries_by_date_range(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )

        # Handle empty results
        if not entries:
            await message.answer(
                f"📭 No entries found for {period_label}.\n\n"
                "Send a voice message to create your first entry!"
            )
            return

        # Format and send summary
        summary_text = f"📊 **Summary for {period_label}**\n\n"
        summary_text += f"Total entries: {len(entries)}\n\n"

        for entry in entries:
            # Format date as "Jan 14, 15:30"
            entry_date = entry.created_at.strftime("%b %d, %H:%M")
            # Truncate long transcriptions
            transcription = entry.transcription
            if len(transcription) > 100:
                transcription = transcription[:97] + "..."

            summary_text += f"**{entry_date}**\n{transcription}\n\n"

        await message.answer(summary_text, parse_mode="Markdown")
        logger.info(f"Sent summary to user {user_id}: {len(entries)} entries for {period}")

    except Exception as e:
        logger.error(f"Error fetching summary for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Failed to fetch summary. Please try again later."
        )


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

        # Save to database
        try:
            await save_journal_entry(
                user_id=user_id,
                transcription=transcription,
                voice_file_id=message.voice.file_id,
                voice_duration_seconds=message.voice.duration,
            )
            logger.info(f"Saved entry for user {user_id}: {len(transcription)} chars")
        except Exception as e:
            logger.error(f"Failed to save entry for user {user_id}: {e}", exc_info=True)
            # Continue to show transcription even if save fails

        # Reply with transcription and save confirmation
        await message.answer(
            f"📝 **Your journal entry (saved):**\n\n{transcription}"
        )

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
