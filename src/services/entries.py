"""Entry service for CRUD operations on journal entries."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Entry

logger = logging.getLogger(__name__)


class EntryService:
    """Service for managing journal entries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize EntryService.

        Args:
            session: AsyncSession for database operations.
        """
        self._session = session

    async def create_entry(
        self,
        user_id: int,
        transcription: str,
        voice_file_id: str | None = None,
        voice_duration_seconds: int | None = None,
        sentiment: dict | None = None,
        summary: str | None = None,
        mood_score: int | None = None,
        tags: list[str] | None = None,
    ) -> Entry:
        """Create a new journal entry.

        Args:
            user_id: Telegram user ID.
            transcription: Transcribed text from voice message.
            voice_file_id: Optional Telegram voice file ID.
            voice_duration_seconds: Optional voice duration in seconds.
            sentiment: Optional sentiment analysis data.
            summary: Optional LLM-generated summary.
            mood_score: Optional mood score (1-10).
            tags: Optional list of tags.

        Returns:
            Created Entry object.

        Raises:
            ValueError: If user_id is invalid or transcription is empty.
        """
        if user_id <= 0:
            raise ValueError("user_id must be positive")
        if not transcription or not transcription.strip():
            raise ValueError("transcription cannot be empty")

        entry = Entry(
            user_id=user_id,
            transcription=transcription.strip(),
            voice_file_id=voice_file_id,
            voice_duration_seconds=voice_duration_seconds,
            sentiment=sentiment,
            summary=summary,
            mood_score=mood_score,
            tags=tags,
        )
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)

        logger.info(f"Created entry {entry.id} for user {user_id}")
        return entry

    async def get_entry_by_id(self, entry_id: uuid.UUID) -> Entry | None:
        """Get entry by ID.

        Args:
            entry_id: Entry UUID.

        Returns:
            Entry if found, None otherwise.
        """
        result = await self._session.execute(
            select(Entry).where(Entry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_entries_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]:
        """Get all entries for a user.

        Args:
            user_id: Telegram user ID.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of entries, ordered by created_at descending.
        """
        result = await self._session.execute(
            select(Entry)
            .where(Entry.user_id == user_id)
            .order_by(Entry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_entry(self, entry_id: uuid.UUID) -> bool:
        """Delete entry by ID.

        Args:
            entry_id: Entry UUID.

        Returns:
            True if entry was deleted, False if not found.
        """
        result = await self._session.execute(
            delete(Entry).where(Entry.id == entry_id)
        )
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted entry {entry_id}")
        return deleted

    async def count_entries_for_user(self, user_id: int) -> int:
        """Count entries for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            Number of entries for the user.
        """
        result = await self._session.execute(
            select(func.count()).select_from(Entry).where(Entry.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_entries_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]:
        """Get entries for a user within a date range.

        Args:
            user_id: Telegram user ID.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of entries within date range, ordered by created_at descending.
        """
        result = await self._session.execute(
            select(Entry)
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.created_at <= end_date,
            )
            .order_by(Entry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
