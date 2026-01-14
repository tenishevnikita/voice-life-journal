"""Export service for exporting user entries to various formats."""

import csv
import io
import json
import logging
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Entry

logger = logging.getLogger(__name__)

# Maximum transcription length in export
MAX_TRANSCRIPTION_LENGTH = 500


class ExportFormat(Enum):
    """Supported export formats."""

    CSV = "csv"
    MARKDOWN = "md"
    JSON = "json"


def _truncate(text: str, max_length: int = MAX_TRANSCRIPTION_LENGTH) -> str:
    """Truncate text to max length with ellipsis.

    Args:
        text: Text to truncate.
        max_length: Maximum length.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


class ExportService:
    """Service for exporting user entries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ExportService.

        Args:
            session: AsyncSession for database operations.
        """
        self._session = session

    async def export_entries(
        self,
        user_id: int,
        export_format: ExportFormat,
    ) -> bytes:
        """Export all entries for a user.

        Args:
            user_id: Telegram user ID.
            export_format: Export format.

        Returns:
            File content as bytes.
        """
        # Fetch all entries
        result = await self._session.execute(
            select(Entry)
            .where(Entry.user_id == user_id)
            .order_by(Entry.created_at.asc())
        )
        entries = list(result.scalars().all())

        if export_format == ExportFormat.CSV:
            return self._export_csv(entries)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_markdown(entries)
        else:  # JSON
            return self._export_json(entries)

    def _export_csv(self, entries: list[Entry]) -> bytes:
        """Export entries to CSV format.

        Args:
            entries: List of entries.

        Returns:
            CSV content as bytes.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # Write header
        writer.writerow(
            ["date", "time", "transcription", "summary", "mood_score", "tags"]
        )

        # Write rows
        for entry in entries:
            date_str = entry.created_at.strftime("%Y-%m-%d")
            time_str = entry.created_at.strftime("%H:%M")
            transcription = _truncate(entry.transcription)
            summary = entry.summary or ""
            mood = entry.mood_score or ""
            tags = ",".join(entry.tags) if entry.tags else ""

            writer.writerow([date_str, time_str, transcription, summary, mood, tags])

        return output.getvalue().encode("utf-8")

    def _export_markdown(self, entries: list[Entry]) -> bytes:
        """Export entries to Markdown format.

        Args:
            entries: List of entries.

        Returns:
            Markdown content as bytes.
        """
        now = datetime.now(UTC)
        lines = [
            f"# Voice Journal Export - {now.strftime('%Y-%m-%d')}",
            "",
        ]

        current_date = None
        for entry in entries:
            date_str = entry.created_at.strftime("%Y-%m-%d")

            # Add date header if new day
            if date_str != current_date:
                current_date = date_str
                lines.append(f"## {date_str}")
                lines.append("")

            # Entry header
            time_str = entry.created_at.strftime("%H:%M")
            mood_str = f"Mood: {entry.mood_score}/10" if entry.mood_score else ""
            tags_str = ""
            if entry.tags:
                tags_str = " ".join(f"#{tag}" for tag in entry.tags)

            header_parts = [f"### {time_str}"]
            if mood_str:
                header_parts.append(mood_str)
            if tags_str:
                header_parts.append(f"🏷 {tags_str}")
            lines.append(" - ".join(header_parts))
            lines.append("")

            # Transcription as quote
            transcription = _truncate(entry.transcription)
            lines.append(f"> {transcription}")
            lines.append("")

            # Summary if present
            if entry.summary:
                lines.append(f"**Summary:** {entry.summary}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines).encode("utf-8")

    def _export_json(self, entries: list[Entry]) -> bytes:
        """Export entries to JSON format.

        Args:
            entries: List of entries.

        Returns:
            JSON content as bytes.
        """
        data = {
            "export_date": datetime.now(UTC).isoformat(),
            "total_entries": len(entries),
            "entries": [],
        }

        for entry in entries:
            entry_data = {
                "id": str(entry.id),
                "created_at": entry.created_at.isoformat(),
                "transcription": entry.transcription,
                "summary": entry.summary,
                "mood_score": entry.mood_score,
                "tags": entry.tags,
                "voice_duration_seconds": entry.voice_duration_seconds,
            }
            data["entries"].append(entry_data)

        return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def get_export_filename(export_format: ExportFormat) -> str:
    """Get filename for export.

    Args:
        export_format: Export format.

    Returns:
        Filename with appropriate extension.
    """
    now = datetime.now(UTC)
    date_str = now.strftime("%Y-%m-%d")
    extension = export_format.value
    return f"voice_journal_{date_str}.{extension}"


def parse_export_format(format_str: str | None) -> ExportFormat | None:
    """Parse export format string.

    Args:
        format_str: Format string (csv, md, json).

    Returns:
        ExportFormat if valid, None otherwise.
    """
    if not format_str:
        return ExportFormat.CSV

    format_lower = format_str.lower().strip()

    format_map = {
        "csv": ExportFormat.CSV,
        "md": ExportFormat.MARKDOWN,
        "markdown": ExportFormat.MARKDOWN,
        "json": ExportFormat.JSON,
    }

    return format_map.get(format_lower)
