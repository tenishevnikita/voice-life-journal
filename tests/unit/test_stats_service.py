"""Unit tests for StatsService."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Base, Entry
from src.services.stats import (
    StatsService,
    get_period_dates,
    get_trend_emoji,
    mood_to_bar,
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
def stats_service(test_session: AsyncSession) -> StatsService:
    """Create StatsService with test session."""
    return StatsService(session=test_session)


class TestMoodToBar:
    """Tests for mood_to_bar utility function."""

    def test_mood_to_bar_full(self):
        """Mood 10 should produce full bar."""
        result = mood_to_bar(10, max_width=10)
        assert result == "██████████"

    def test_mood_to_bar_half(self):
        """Mood 5 should produce half-filled bar."""
        result = mood_to_bar(5, max_width=10)
        assert result == "█████░░░░░"

    def test_mood_to_bar_empty(self):
        """Mood 0 should produce empty bar."""
        result = mood_to_bar(0, max_width=10)
        assert result == "░░░░░░░░░░"

    def test_mood_to_bar_custom_width(self):
        """Bar width should be customizable."""
        result = mood_to_bar(4, max_width=8)
        assert result == "████░░░░"


class TestGetTrendEmoji:
    """Tests for get_trend_emoji utility function."""

    def test_trend_positive(self):
        """Positive trend should show improving emoji."""
        result = get_trend_emoji(0.5)
        assert "улучшается" in result

    def test_trend_negative(self):
        """Negative trend should show declining emoji."""
        result = get_trend_emoji(-0.5)
        assert "ухудшается" in result

    def test_trend_stable(self):
        """Small change should show stable."""
        result = get_trend_emoji(0.1)
        assert "стабильно" in result

    def test_trend_none(self):
        """None trend should return empty string."""
        result = get_trend_emoji(None)
        assert result == ""


class TestGetPeriodDates:
    """Tests for get_period_dates utility function."""

    def test_period_week(self):
        """Week period should return 7 days ago."""
        start, end, label = get_period_dates("week")
        assert (end - start).days == 7
        assert label == "неделю"

    def test_period_month(self):
        """Month period should return 30 days ago."""
        start, end, label = get_period_dates("month")
        assert (end - start).days == 30
        assert label == "месяц"

    def test_period_all(self):
        """All period should return very old start date."""
        start, end, label = get_period_dates("all")
        assert start.year == 2000
        assert label == "всё время"


class TestStatsServiceGetStats:
    """Tests for StatsService.get_stats method."""

    async def test_get_stats_no_entries(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Should return None when user has no entries."""
        now = datetime.now(timezone.utc)
        result = await stats_service.get_stats(
            user_id=12345678,
            start_date=now - timedelta(days=7),
            end_date=now,
        )
        assert result is None

    async def test_get_stats_with_entries(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Should return stats when user has entries."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create entries with mood scores
        for i, mood in enumerate([6, 7, 8, 5, 9]):
            entry = Entry(
                user_id=user_id,
                transcription=f"Entry {i}",
                mood_score=mood,
                tags=["work", "ideas"] if i % 2 == 0 else ["rest"],
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(days=i)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=7),
            end_date=now,
        )

        assert result is not None
        assert result.total_entries == 5
        assert result.avg_mood == 7.0  # (6+7+8+5+9) / 5 = 7.0

    async def test_get_stats_avg_mood_calculation(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Average mood should be calculated correctly."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create 5 entries with moods [6, 7, 8, 5, 9] -> avg = 7.0
        moods = [6, 7, 8, 5, 9]
        for i, mood in enumerate(moods):
            entry = Entry(
                user_id=user_id,
                transcription=f"Entry {i}",
                mood_score=mood,
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(hours=i)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=1),
            end_date=now,
        )

        assert result is not None
        assert result.avg_mood == 7.0

    async def test_get_stats_excludes_null_mood(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Entries without mood_score should be excluded from average."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create entries with and without mood
        entry1 = Entry(user_id=user_id, transcription="With mood", mood_score=8)
        test_session.add(entry1)
        await test_session.flush()
        entry1.created_at = now - timedelta(hours=1)

        entry2 = Entry(user_id=user_id, transcription="Without mood", mood_score=None)
        test_session.add(entry2)
        await test_session.flush()
        entry2.created_at = now - timedelta(hours=2)

        entry3 = Entry(user_id=user_id, transcription="With mood 2", mood_score=6)
        test_session.add(entry3)
        await test_session.flush()
        entry3.created_at = now - timedelta(hours=3)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=1),
            end_date=now,
        )

        assert result is not None
        assert result.total_entries == 3
        assert result.avg_mood == 7.0  # (8 + 6) / 2 = 7.0

    async def test_get_stats_top_tags(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Top tags should be calculated correctly."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create entries with tags
        tags_list = [
            ["work", "ideas"],  # work: 1, ideas: 1
            ["work"],  # work: 2
            ["rest", "work"],  # work: 3, rest: 1
            ["ideas"],  # ideas: 2
            None,  # No tags
        ]
        for i, tags in enumerate(tags_list):
            entry = Entry(
                user_id=user_id,
                transcription=f"Entry {i}",
                mood_score=7,
                tags=tags,
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(hours=i)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=1),
            end_date=now,
        )

        assert result is not None
        assert len(result.top_tags) > 0
        # work should be most common (3)
        assert result.top_tags[0] == ("work", 3)
        # ideas should be second (2)
        assert result.top_tags[1] == ("ideas", 2)


class TestStatsServiceTrend:
    """Tests for trend calculation."""

    async def test_trend_improving(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Trend should be positive when current period mood is higher."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Previous period entries (7-14 days ago) with lower mood
        for i in range(3):
            entry = Entry(
                user_id=user_id,
                transcription=f"Old entry {i}",
                mood_score=5,
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(days=10 + i)

        # Current period entries (last 7 days) with higher mood
        for i in range(3):
            entry = Entry(
                user_id=user_id,
                transcription=f"New entry {i}",
                mood_score=8,
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(days=i + 1)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=7),
            end_date=now,
        )

        assert result is not None
        assert result.trend is not None
        assert result.trend > 0  # Improvement

    async def test_trend_none_when_no_previous(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Trend should be None when no previous period data."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Only current period entries
        entry = Entry(
            user_id=user_id,
            transcription="Current entry",
            mood_score=7,
        )
        test_session.add(entry)
        await test_session.flush()
        entry.created_at = now - timedelta(days=1)
        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=7),
            end_date=now,
        )

        assert result is not None
        assert result.trend is None


class TestStatsServiceFormatMessage:
    """Tests for stats message formatting."""

    async def test_format_stats_message(
        self, stats_service: StatsService, test_session: AsyncSession
    ):
        """Should format stats as readable message."""
        user_id = 12345678
        now = datetime.now(timezone.utc)

        # Create entries
        for i in range(3):
            entry = Entry(
                user_id=user_id,
                transcription=f"Entry {i}",
                mood_score=7,
                tags=["work"],
            )
            test_session.add(entry)
            await test_session.flush()
            entry.created_at = now - timedelta(days=i)

        await test_session.commit()

        result = await stats_service.get_stats(
            user_id=user_id,
            start_date=now - timedelta(days=7),
            end_date=now,
        )

        message = stats_service.format_stats_message(result, "неделю")

        assert "Твоя статистика" in message
        assert "Записей: 3" in message
        assert "Среднее настроение: 7.0/10" in message
        assert "#work" in message
