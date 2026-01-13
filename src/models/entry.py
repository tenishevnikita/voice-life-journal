"""Journal entry model."""

import uuid
from typing import Optional

from sqlalchemy import BigInteger, Index, Text, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.models.base import Base, GUID, TimestampMixin


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
    voice_file_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    voice_duration_seconds: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    sentiment: Mapped[Optional[dict]] = mapped_column(
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
