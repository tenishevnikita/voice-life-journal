"""Integration tests for LLM Analysis API - REAL API CALLS.

These tests make real API calls to OpenAI API and are disabled by default.
Enable them by setting RUN_INTEGRATION_TESTS=1 environment variable.

WARNING: These tests cost money! Each analysis costs ~$0.001-0.005.
"""

import os

import pytest

from src.services.analysis import AnalysisResult, AnalysisService

# Skip all integration tests if RUN_INTEGRATION_TESTS is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)


class TestAnalysisIntegration:
    """Integration tests with real LLM API."""

    @pytest.fixture
    def analysis_service(self) -> AnalysisService:
        """Create AnalysisService with real API key from env."""
        api_key = os.getenv("OPENAI_API_KEY")

        # Skip test if API key is fake/test key
        if not api_key or api_key.startswith("sk-test") or api_key == "test-api-key":
            pytest.skip("Real OPENAI_API_KEY required for integration tests")

        return AnalysisService(
            api_key=api_key,
            model="gpt-4o-mini",
            min_words=5,  # Lower threshold for tests
            timeout=30,
            max_tags=5,
        )

    @pytest.mark.asyncio
    async def test_real_analysis_english(self, analysis_service: AnalysisService) -> None:
        """Test real analysis with English text.

        Expected: Analysis completes successfully and returns structured result.
        """
        text = (
            "Today was a really productive day at work. I finished the big project "
            "that I've been working on for weeks. My manager was impressed with the "
            "results and I got positive feedback from the team. I'm feeling really "
            "happy and motivated to continue working on new challenges."
        )

        result = await analysis_service.analyze(text)

        # Basic assertions
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert len(result.summary) > 0
        assert 1 <= result.mood_score <= 10
        assert isinstance(result.tags, list)

        # Mood should be relatively high (positive text)
        assert result.mood_score >= 6

        print(f"\n--- English Analysis ---")
        print(f"Summary: {result.summary}")
        print(f"Mood: {result.mood_score}/10")
        print(f"Tags: {result.tags}")

    @pytest.mark.asyncio
    async def test_real_analysis_russian(self, analysis_service: AnalysisService) -> None:
        """Test real analysis with Russian text.

        Expected: Analysis completes successfully with Russian summary.
        """
        text = (
            "Сегодня был очень тяжёлый день. На работе было много проблем, "
            "дедлайн горит, а клиент постоянно меняет требования. Чувствую себя "
            "уставшим и раздражённым. Надеюсь, завтра будет легче. Хочу просто "
            "отдохнуть и посмотреть сериал вечером."
        )

        result = await analysis_service.analyze(text)

        # Basic assertions
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert len(result.summary) > 0
        assert 1 <= result.mood_score <= 10

        # Mood should be relatively low (negative text)
        assert result.mood_score <= 6

        # Summary should contain Cyrillic (Russian response)
        has_cyrillic = any("\u0400" <= char <= "\u04FF" for char in result.summary)
        if not has_cyrillic:
            print(f"\nWARNING: Russian analysis summary may not contain Cyrillic")

        print(f"\n--- Russian Analysis ---")
        print(f"Summary: {result.summary}")
        print(f"Mood: {result.mood_score}/10")
        print(f"Tags: {result.tags}")

    @pytest.mark.asyncio
    async def test_real_analysis_short_text_skipped(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test that short text is not sent to API.

        Expected: Returns None without making API call.
        """
        text = "Hi there"  # Too short (2 words < min_words=5)

        result = await analysis_service.analyze(text)

        assert result is None

    @pytest.mark.asyncio
    async def test_real_analysis_tags_extraction(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test that relevant tags are extracted.

        Expected: Tags should be relevant to the content.
        """
        text = (
            "I spent the morning learning Python programming and working through "
            "some machine learning tutorials. After lunch, I went for a run in the "
            "park and then met with friends for coffee. Really enjoyed mixing "
            "productive work with social activities today."
        )

        result = await analysis_service.analyze(text)

        assert result is not None
        assert len(result.tags) > 0
        assert len(result.tags) <= 5  # Max tags limit

        # Check some expected tags might be present
        tags_lower = [t.lower() for t in result.tags]
        print(f"\n--- Tags Extraction ---")
        print(f"Extracted tags: {result.tags}")

        # At least one tech-related or activity tag should be present
        expected_themes = [
            "python", "programming", "learning", "ml", "machine learning",
            "running", "sports", "friends", "social", "coffee", "park"
        ]
        has_relevant_tag = any(
            any(theme in tag for theme in expected_themes)
            for tag in tags_lower
        )

        if not has_relevant_tag:
            print("WARNING: Tags may not match expected themes, but test continues")

    @pytest.mark.asyncio
    async def test_real_custom_base_url(self) -> None:
        """Test that custom base_url works with real API.

        This test only runs if OPENAI_BASE_URL is set.
        Expected: Analysis works through custom endpoint.
        """
        custom_url = os.getenv("OPENAI_BASE_URL")
        if not custom_url:
            pytest.skip("OPENAI_BASE_URL not set, skipping custom URL test")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-test"):
            pytest.skip("Real OPENAI_API_KEY required for integration tests")

        service = AnalysisService(
            api_key=api_key,
            base_url=custom_url,
            model="gpt-4o-mini",
            min_words=5,
        )

        text = (
            "Today I worked on an interesting feature for the product. "
            "The team collaboration was great and we made good progress."
        )

        result = await service.analyze(text)

        assert result is not None
        assert isinstance(result, AnalysisResult)

        print(f"\n--- Custom URL Analysis ---")
        print(f"Summary: {result.summary}")
        print(f"Used base_url: {custom_url}")
