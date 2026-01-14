"""Stats service for calculating user statistics."""

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Entry

logger = logging.getLogger(__name__)

# Day names for Russian locale
DAY_NAMES_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


@dataclass
class StatsResult:
    """Result of stats calculation."""

    total_entries: int
    avg_mood: float | None
    mood_by_day: dict[str, float]
    trend: float | None
    top_tags: list[tuple[str, int]]


def mood_to_bar(mood: float, max_width: int = 10) -> str:
    """Convert mood score to ASCII bar.

    Args:
        mood: Mood score (1-10).
        max_width: Maximum bar width.

    Returns:
        ASCII bar representation.
    """
    filled = int(mood)
    empty = max_width - filled
    return "█" * filled + "░" * empty


def get_trend_emoji(trend: float | None) -> str:
    """Get emoji for trend direction.

    Args:
        trend: Trend value (positive = improving).

    Returns:
        Emoji representing trend direction.
    """
    if trend is None:
        return ""
    if trend > 0.3:
        return "↗️ улучшается"
    elif trend < -0.3:
        return "↘️ ухудшается"
    else:
        return "→ стабильно"


class StatsService:
    """Service for calculating user statistics."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize StatsService.

        Args:
            session: AsyncSession for database operations.
        """
        self._session = session

    async def get_stats(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> StatsResult | None:
        """Get stats for a user within a date range.

        Args:
            user_id: Telegram user ID.
            start_date: Start of date range (inclusive).
            end_date: End of date range (inclusive).

        Returns:
            StatsResult if user has entries, None otherwise.
        """
        # Get entries for current period
        result = await self._session.execute(
            select(Entry)
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= start_date,
                Entry.created_at <= end_date,
            )
            .order_by(Entry.created_at.asc())
        )
        entries = list(result.scalars().all())

        if not entries:
            return None

        # Calculate total entries
        total_entries = len(entries)

        # Calculate average mood (exclude NULL values)
        moods = [e.mood_score for e in entries if e.mood_score is not None]
        avg_mood = sum(moods) / len(moods) if moods else None

        # Calculate mood by day of week
        mood_by_day = self._calculate_mood_by_day(entries)

        # Calculate trend compared to previous period
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date

        prev_result = await self._session.execute(
            select(func.avg(Entry.mood_score))
            .where(
                Entry.user_id == user_id,
                Entry.created_at >= prev_start,
                Entry.created_at < prev_end,
                Entry.mood_score.isnot(None),
            )
        )
        prev_avg = prev_result.scalar()

        trend = None
        if avg_mood is not None and prev_avg is not None:
            trend = round(avg_mood - float(prev_avg), 1)

        # Calculate top tags
        top_tags = self._calculate_top_tags(entries)

        return StatsResult(
            total_entries=total_entries,
            avg_mood=round(avg_mood, 1) if avg_mood else None,
            mood_by_day=mood_by_day,
            trend=trend,
            top_tags=top_tags,
        )

    def _calculate_mood_by_day(
        self, entries: list[Entry]
    ) -> dict[str, float]:
        """Calculate average mood by day of week.

        Args:
            entries: List of entries.

        Returns:
            Dict mapping day name to average mood.
        """
        day_moods: dict[int, list[int]] = {}

        for entry in entries:
            if entry.mood_score is not None:
                weekday = entry.created_at.weekday()
                if weekday not in day_moods:
                    day_moods[weekday] = []
                day_moods[weekday].append(entry.mood_score)

        result = {}
        for weekday, moods in day_moods.items():
            day_name = DAY_NAMES_RU[weekday]
            result[day_name] = round(sum(moods) / len(moods), 1)

        return result

    def _calculate_top_tags(
        self, entries: list[Entry], limit: int = 5
    ) -> list[tuple[str, int]]:
        """Calculate top tags from entries.

        Args:
            entries: List of entries.
            limit: Maximum number of tags to return.

        Returns:
            List of (tag, count) tuples sorted by count descending.
        """
        tag_counter: Counter[str] = Counter()

        for entry in entries:
            if entry.tags:
                for tag in entry.tags:
                    tag_counter[tag] += 1

        return tag_counter.most_common(limit)

    def format_stats_message(self, stats: StatsResult, period_label: str) -> str:
        """Format stats result as a message.

        Args:
            stats: Stats result to format.
            period_label: Human-readable period label.

        Returns:
            Formatted message string.
        """
        lines = [f"📊 Твоя статистика за {period_label}", ""]

        # Basic stats
        lines.append(f"📝 Записей: {stats.total_entries}")

        if stats.avg_mood is not None:
            lines.append(f"😊 Среднее настроение: {stats.avg_mood}/10")

        if stats.trend is not None:
            trend_str = f"+{stats.trend}" if stats.trend > 0 else str(stats.trend)
            trend_emoji = get_trend_emoji(stats.trend)
            lines.append(f"📈 Тренд: {trend_emoji} ({trend_str} от прошлого периода)")

        # Mood chart by day
        if stats.mood_by_day:
            lines.append("")
            lines.append("Настроение по дням:")
            for day_name in DAY_NAMES_RU:
                if day_name in stats.mood_by_day:
                    mood = stats.mood_by_day[day_name]
                    bar = mood_to_bar(mood)
                    lines.append(f"{day_name}: {bar} {mood}")

        # Top tags
        if stats.top_tags:
            lines.append("")
            tags_str = ", ".join(
                f"#{tag} ({count})" for tag, count in stats.top_tags
            )
            lines.append(f"🏷 Топ теги: {tags_str}")

        return "\n".join(lines)


def get_period_dates(period: str) -> tuple[datetime, datetime, str]:
    """Get date range for a period.

    Args:
        period: Period string (week, month, all).

    Returns:
        Tuple of (start_date, end_date, period_label).
    """
    now = datetime.now(UTC)

    if period == "week":
        start_date = now - timedelta(days=7)
        period_label = "неделю"
    elif period == "month":
        start_date = now - timedelta(days=30)
        period_label = "месяц"
    else:  # all
        start_date = datetime(2000, 1, 1, tzinfo=UTC)
        period_label = "всё время"

    return start_date, now, period_label
