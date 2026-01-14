"""Journal entry model."""

import uuid

from sqlalchemy import BigInteger, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.models.base import GUID, Base, TimestampMixin


class Entry(Base, TimestampMixin):
    """Journal entry model.

    Stores transcribed voice messages with metadata.
    """

    __tablename__ = "entries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    transcription: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    voice_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    voice_duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    sentiment: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    mood_score: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_entries_user_id_created_at", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"Entry(id={self.id!r}, user_id={self.user_id!r}, "
            f"created_at={self.created_at!r})"
        )
