"""Unit tests for database layer - TDD approach.

BDD Scenarios:
Given пользователь отправил голосовое сообщение
And Whisper вернул транскрипцию
When система сохраняет запись
Then в БД создается новая запись с transcription, user_id, timestamp
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base, Entry
from src.services.entries import EntryService


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
def entry_service(test_session: AsyncSession) -> EntryService:
    """Create EntryService with test session."""
    return EntryService(session=test_session)


class TestEntryModel:
    """Tests for Entry model."""

    async def test_entry_has_required_fields(self, test_session: AsyncSession):
        """Given Entry model, it should have all required fields."""
        entry = Entry(
            user_id=12345678,
            transcription="Test journal entry text",
        )
        test_session.add(entry)
        await test_session.commit()
        await test_session.refresh(entry)

        assert entry.id is not None
        assert isinstance(entry.id, uuid.UUID)
        assert entry.user_id == 12345678
        assert entry.transcription == "Test journal entry text"
        assert entry.created_at is not None
        assert entry.updated_at is not None

    async def test_entry_optional_fields(self, test_session: AsyncSession):
        """Given Entry model, optional fields should be nullable."""
        entry = Entry(
            user_id=12345678,
            transcription="Test entry",
            voice_file_id="voice_abc123",
            voice_duration_seconds=30,
            sentiment={"positive": 0.8, "negative": 0.1},
        )
        test_session.add(entry)
        await test_session.commit()
        await test_session.refresh(entry)

        assert entry.voice_file_id == "voice_abc123"
        assert entry.voice_duration_seconds == 30
        assert entry.sentiment == {"positive": 0.8, "negative": 0.1}


class TestEntryServiceCreate:
    """Tests for creating entries - BDD: When система сохраняет запись."""

    async def test_create_entry_saves_to_database(self, entry_service: EntryService):
        """
        Given пользователь отправил голосовое сообщение
        And Whisper вернул транскрипцию
        When система сохраняет запись
        Then в БД создается новая запись с transcription, user_id, timestamp
        """
        entry = await entry_service.create_entry(
            user_id=12345678,
            transcription="Сегодня был отличный день!",
        )

        assert entry.id is not None
        assert entry.user_id == 12345678
        assert entry.transcription == "Сегодня был отличный день!"
        assert entry.created_at is not None

    async def test_create_entry_with_voice_metadata(self, entry_service: EntryService):
        """Entry should be saved with voice file metadata."""
        entry = await entry_service.create_entry(
            user_id=12345678,
            transcription="Voice memo content",
            voice_file_id="AgACAgIAAxkBAAI",
            voice_duration_seconds=15,
        )

        assert entry.voice_file_id == "AgACAgIAAxkBAAI"
        assert entry.voice_duration_seconds == 15

    async def test_create_entry_validates_user_id(self, entry_service: EntryService):
        """Entry creation should validate user_id is positive."""
        with pytest.raises(ValueError, match="user_id must be positive"):
            await entry_service.create_entry(
                user_id=-1,
                transcription="Invalid entry",
            )

    async def test_create_entry_validates_empty_transcription(
        self, entry_service: EntryService
    ):
        """Entry creation should reject empty transcription."""
        with pytest.raises(ValueError, match="transcription cannot be empty"):
            await entry_service.create_entry(
                user_id=12345678,
                transcription="",
            )


class TestEntryServiceRead:
    """Tests for reading entries."""

    async def test_get_entry_by_id(self, entry_service: EntryService):
        """Should retrieve entry by its ID."""
        created = await entry_service.create_entry(
            user_id=12345678,
            transcription="Test entry for retrieval",
        )

        retrieved = await entry_service.get_entry_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.transcription == "Test entry for retrieval"

    async def test_get_entry_by_id_not_found(self, entry_service: EntryService):
        """Should return None for non-existent entry."""
        fake_id = uuid.uuid4()
        result = await entry_service.get_entry_by_id(fake_id)
        assert result is None

    async def test_get_entries_by_user(self, entry_service: EntryService):
        """Should retrieve all entries for a specific user."""
        user_id = 12345678
        await entry_service.create_entry(user_id=user_id, transcription="Entry 1")
        await entry_service.create_entry(user_id=user_id, transcription="Entry 2")
        await entry_service.create_entry(user_id=99999999, transcription="Other user")

        entries = await entry_service.get_entries_by_user(user_id)

        assert len(entries) == 2
        assert all(e.user_id == user_id for e in entries)

    async def test_get_entries_by_user_empty(self, entry_service: EntryService):
        """Should return empty list for user with no entries."""
        entries = await entry_service.get_entries_by_user(99999999)
        assert entries == []

    async def test_get_entries_by_user_ordered_by_date(self, entry_service: EntryService):
        """Entries should be returned in descending order by created_at."""
        user_id = 12345678
        await entry_service.create_entry(user_id=user_id, transcription="First")
        await entry_service.create_entry(user_id=user_id, transcription="Second")
        await entry_service.create_entry(user_id=user_id, transcription="Third")

        entries = await entry_service.get_entries_by_user(user_id)

        # Most recent first
        assert entries[0].transcription == "Third"
        assert entries[2].transcription == "First"


class TestEntryServiceDelete:
    """Tests for deleting entries."""

    async def test_delete_entry(self, entry_service: EntryService):
        """Should delete entry by ID."""
        entry = await entry_service.create_entry(
            user_id=12345678,
            transcription="To be deleted",
        )

        result = await entry_service.delete_entry(entry.id)

        assert result is True
        assert await entry_service.get_entry_by_id(entry.id) is None

    async def test_delete_entry_not_found(self, entry_service: EntryService):
        """Should return False when deleting non-existent entry."""
        fake_id = uuid.uuid4()
        result = await entry_service.delete_entry(fake_id)
        assert result is False


class TestEntryServiceCount:
    """Tests for counting entries."""

    async def test_count_entries_for_user(self, entry_service: EntryService):
        """Should count entries for a specific user."""
        user_id = 12345678
        await entry_service.create_entry(user_id=user_id, transcription="Entry 1")
        await entry_service.create_entry(user_id=user_id, transcription="Entry 2")
        await entry_service.create_entry(user_id=99999999, transcription="Other")

        count = await entry_service.count_entries_for_user(user_id)

        assert count == 2

    async def test_count_entries_for_user_empty(self, entry_service: EntryService):
        """Should return 0 for user with no entries."""
        count = await entry_service.count_entries_for_user(99999999)
        assert count == 0
