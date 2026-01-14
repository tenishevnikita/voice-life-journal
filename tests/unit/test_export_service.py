"""Unit tests for ExportService."""

import csv
import io
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base, Entry
from src.services.export import (
    ExportFormat,
    ExportService,
    get_export_filename,
    parse_export_format,
)


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create a test database session."""
    factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture
def export_service(test_session: AsyncSession) -> ExportService:
    """Create ExportService with test session."""
    return ExportService(session=test_session)


class TestParseExportFormat:
    """Tests for parse_export_format utility function."""

    def test_parse_csv(self):
        """Should parse csv format."""
        result = parse_export_format("csv")
        assert result == ExportFormat.CSV

    def test_parse_md(self):
        """Should parse md format."""
        result = parse_export_format("md")
        assert result == ExportFormat.MARKDOWN

    def test_parse_markdown(self):
        """Should parse markdown format as alias."""
        result = parse_export_format("markdown")
        assert result == ExportFormat.MARKDOWN

    def test_parse_json(self):
        """Should parse json format."""
        result = parse_export_format("json")
        assert result == ExportFormat.JSON

    def test_parse_case_insensitive(self):
        """Should be case insensitive."""
        assert parse_export_format("CSV") == ExportFormat.CSV
        assert parse_export_format("Json") == ExportFormat.JSON

    def test_parse_invalid(self):
        """Should return None for invalid format."""
        result = parse_export_format("xml")
        assert result is None

    def test_parse_none_default_csv(self):
        """Should return CSV for None input."""
        result = parse_export_format(None)
        assert result == ExportFormat.CSV


class TestGetExportFilename:
    """Tests for get_export_filename utility function."""

    def test_csv_filename(self):
        """Should generate CSV filename with date."""
        filename = get_export_filename(ExportFormat.CSV)
        assert filename.startswith("voice_journal_")
        assert filename.endswith(".csv")

    def test_md_filename(self):
        """Should generate Markdown filename with date."""
        filename = get_export_filename(ExportFormat.MARKDOWN)
        assert filename.endswith(".md")

    def test_json_filename(self):
        """Should generate JSON filename with date."""
        filename = get_export_filename(ExportFormat.JSON)
        assert filename.endswith(".json")


class TestExportServiceCSV:
    """Tests for CSV export."""

    async def test_export_csv_empty(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should return empty CSV with only headers for no entries."""
        result = await export_service.export_entries(
            user_id=12345678,
            export_format=ExportFormat.CSV,
        )

        csv_content = result.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 1  # Only header
        assert rows[0] == ["date", "time", "transcription", "summary", "mood_score", "tags"]

    async def test_export_csv_with_entries(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should export entries to CSV format."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test transcription",
            summary="Test summary",
            mood_score=8,
            tags=["work", "ideas"],
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.CSV,
        )

        csv_content = result.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 2  # Header + 1 entry
        assert rows[1][2] == "Test transcription"
        assert rows[1][3] == "Test summary"
        assert rows[1][4] == "8"
        assert rows[1][5] == "work,ideas"

    async def test_export_csv_escapes_special_chars(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should properly escape commas and quotes in CSV."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription='Test with "quotes" and, commas',
            summary=None,
            mood_score=None,
            tags=None,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.CSV,
        )

        csv_content = result.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        # CSV should properly parse the escaped content
        assert 'Test with "quotes" and, commas' in rows[1][2]

    async def test_export_csv_utf8_encoding(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should handle Russian text correctly."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Привет, мир! Сегодня отличный день.",
            summary="Хорошее настроение",
            mood_score=9,
            tags=["работа"],
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.CSV,
        )

        csv_content = result.decode("utf-8")
        assert "Привет, мир!" in csv_content
        assert "Хорошее настроение" in csv_content


class TestExportServiceMarkdown:
    """Tests for Markdown export."""

    async def test_export_md_empty(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should return header only for no entries."""
        result = await export_service.export_entries(
            user_id=12345678,
            export_format=ExportFormat.MARKDOWN,
        )

        md_content = result.decode("utf-8")
        assert "# Voice Journal Export" in md_content

    async def test_export_md_with_entries(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should export entries to Markdown format."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test transcription for markdown",
            summary="Test summary",
            mood_score=8,
            tags=["work", "ideas"],
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.MARKDOWN,
        )

        md_content = result.decode("utf-8")
        assert "# Voice Journal Export" in md_content
        assert "Test transcription for markdown" in md_content
        assert "Mood: 8/10" in md_content
        assert "#work" in md_content
        assert "#ideas" in md_content
        assert "**Summary:**" in md_content

    async def test_export_md_groups_by_date(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should group entries by date."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create entries on different days
        entry1 = Entry(
            user_id=user_id,
            transcription="Entry 1",
            mood_score=7,
        )
        test_session.add(entry1)
        await test_session.flush()
        entry1.created_at = now

        entry2 = Entry(
            user_id=user_id,
            transcription="Entry 2",
            mood_score=8,
        )
        test_session.add(entry2)
        await test_session.flush()
        entry2.created_at = now - timedelta(days=1)

        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.MARKDOWN,
        )

        md_content = result.decode("utf-8")
        # Should have date headers (## format)
        assert md_content.count("## ") >= 2


class TestExportServiceJSON:
    """Tests for JSON export."""

    async def test_export_json_empty(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should return valid JSON with empty entries."""
        result = await export_service.export_entries(
            user_id=12345678,
            export_format=ExportFormat.JSON,
        )

        data = json.loads(result.decode("utf-8"))
        assert "export_date" in data
        assert "total_entries" in data
        assert data["total_entries"] == 0
        assert data["entries"] == []

    async def test_export_json_with_entries(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should export entries to JSON format."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test JSON export",
            summary="Summary text",
            mood_score=7,
            tags=["test"],
            voice_duration_seconds=30,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.JSON,
        )

        data = json.loads(result.decode("utf-8"))
        assert data["total_entries"] == 1
        assert len(data["entries"]) == 1

        entry_data = data["entries"][0]
        assert entry_data["transcription"] == "Test JSON export"
        assert entry_data["summary"] == "Summary text"
        assert entry_data["mood_score"] == 7
        assert entry_data["tags"] == ["test"]
        assert entry_data["voice_duration_seconds"] == 30

    async def test_export_json_valid_format(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should produce valid, parseable JSON."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        entry = Entry(
            user_id=user_id,
            transcription="Test entry",
            mood_score=5,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.JSON,
        )

        # Should not raise exception
        data = json.loads(result.decode("utf-8"))
        assert isinstance(data, dict)


class TestExportServiceTruncation:
    """Tests for transcription truncation in exports."""

    async def test_long_transcription_truncated(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """Should truncate very long transcriptions in CSV/MD."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        long_text = "A" * 1000  # 1000 characters
        entry = Entry(
            user_id=user_id,
            transcription=long_text,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.CSV,
        )

        csv_content = result.decode("utf-8")
        # Should be truncated (max 500 chars)
        assert len(csv_content) < 1100  # Header + truncated content
        assert "..." in csv_content

    async def test_json_no_truncation(
        self, export_service: ExportService, test_session: AsyncSession
    ):
        """JSON should not truncate transcriptions."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        long_text = "B" * 1000
        entry = Entry(
            user_id=user_id,
            transcription=long_text,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now
        await test_session.commit()

        result = await export_service.export_entries(
            user_id=user_id,
            export_format=ExportFormat.JSON,
        )

        data = json.loads(result.decode("utf-8"))
        # JSON should preserve full text
        assert len(data["entries"][0]["transcription"]) == 1000
