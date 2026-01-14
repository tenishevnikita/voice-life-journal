"""Unit tests for AnalysisService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import APIConnectionError, APIError, RateLimitError

from src.services.analysis import (
    AnalysisAPIError,
    AnalysisError,
    AnalysisParseError,
    AnalysisRateLimitError,
    AnalysisResult,
    AnalysisService,
)


class TestAnalysisResult:
    """Tests for AnalysisResult Pydantic model."""

    def test_valid_result(self) -> None:
        """Test creating a valid AnalysisResult."""
        result = AnalysisResult(
            summary="Test summary",
            mood_score=7,
            tags=["work", "idea"],
        )
        assert result.summary == "Test summary"
        assert result.mood_score == 7
        assert result.tags == ["work", "idea"]

    def test_mood_score_clamp_low(self) -> None:
        """Test mood score is clamped to minimum 1."""
        result = AnalysisResult(
            summary="Test",
            mood_score=0,
            tags=[],
        )
        assert result.mood_score == 1

    def test_mood_score_clamp_high(self) -> None:
        """Test mood score is clamped to maximum 10."""
        result = AnalysisResult(
            summary="Test",
            mood_score=15,
            tags=[],
        )
        assert result.mood_score == 10

    def test_mood_score_negative(self) -> None:
        """Test negative mood score is clamped to 1."""
        result = AnalysisResult(
            summary="Test",
            mood_score=-5,
            tags=[],
        )
        assert result.mood_score == 1

    def test_tags_limit(self) -> None:
        """Test tags are limited to max count."""
        result = AnalysisResult(
            summary="Test",
            mood_score=5,
            tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],
        )
        # Should be limited by validator (configured max is 5)
        assert len(result.tags) <= 5

    def test_empty_tags(self) -> None:
        """Test empty tags list is valid."""
        result = AnalysisResult(
            summary="Test",
            mood_score=5,
            tags=[],
        )
        assert result.tags == []


class TestAnalysisService:
    """Tests for AnalysisService."""

    @pytest.fixture
    def analysis_service(self) -> AnalysisService:
        """Create AnalysisService with test config."""
        return AnalysisService(
            api_key="test-key",
            model="gpt-4o-mini",
            min_words=10,
            timeout=30,
            max_tags=5,
        )

    async def test_analyze_returns_none_for_empty_text(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze returns None for empty text."""
        result = await analysis_service.analyze("")
        assert result is None

        result = await analysis_service.analyze("   ")
        assert result is None

    async def test_analyze_returns_none_for_short_text(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze returns None for text below minimum word count."""
        # Less than 10 words
        result = await analysis_service.analyze("Hello world test")
        assert result is None

    async def test_analyze_valid_response(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze with valid LLM response."""
        # Create mock response
        mock_parsed = AnalysisResult(
            summary="Test summary of the entry",
            mood_score=7,
            tags=["work", "idea"],
        )
        mock_choice = MagicMock()
        mock_choice.message.parsed = mock_parsed
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        # Setup mock
        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        # Long enough text (> 10 words)
        text = "This is a test journal entry with more than ten words to trigger analysis."
        result = await analysis_service.analyze(text)

        assert result is not None
        assert result.summary == "Test summary of the entry"
        assert result.mood_score == 7
        assert result.tags == ["work", "idea"]

    async def test_analyze_rate_limit_error(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze raises AnalysisRateLimitError on rate limit."""
        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        with pytest.raises(AnalysisRateLimitError):
            await analysis_service.analyze(text)

    async def test_analyze_api_connection_error(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze raises AnalysisAPIError on connection error."""
        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        with pytest.raises(AnalysisAPIError):
            await analysis_service.analyze(text)

    async def test_analyze_api_error(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze raises AnalysisAPIError on API error."""
        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            side_effect=APIError(
                message="API error",
                request=MagicMock(),
                body=None,
            )
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        with pytest.raises(AnalysisAPIError):
            await analysis_service.analyze(text)

    async def test_analyze_parse_error(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze raises AnalysisParseError when parsing fails."""
        mock_choice = MagicMock()
        mock_choice.message.parsed = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        with pytest.raises(AnalysisParseError):
            await analysis_service.analyze(text)

    async def test_analyze_unexpected_error(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze raises AnalysisError on unexpected error."""
        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        with pytest.raises(AnalysisError):
            await analysis_service.analyze(text)

    async def test_analyze_truncates_long_text(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze truncates very long text."""
        mock_parsed = AnalysisResult(
            summary="Summary",
            mood_score=5,
            tags=["test"],
        )
        mock_choice = MagicMock()
        mock_choice.message.parsed = mock_parsed
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        # Create very long text (> 16000 chars)
        long_text = "word " * 5000  # ~25000 chars

        result = await analysis_service.analyze(long_text)
        assert result is not None

        # Verify the call was made with truncated text
        call_args = analysis_service._client.beta.chat.completions.parse.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[1]["content"]
        # The text should be truncated
        assert len(user_message) < 20000

    def test_count_words(self, analysis_service: AnalysisService) -> None:
        """Test word counting."""
        assert analysis_service._count_words("one two three") == 3
        assert analysis_service._count_words("single") == 1
        assert analysis_service._count_words("") == 0
        assert analysis_service._count_words("  spaced   words  ") == 2

    async def test_analyze_limits_tags(
        self, analysis_service: AnalysisService
    ) -> None:
        """Test analyze limits tags to max_tags."""
        mock_parsed = AnalysisResult(
            summary="Summary",
            mood_score=5,
            tags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7"],
        )
        mock_choice = MagicMock()
        mock_choice.message.parsed = mock_parsed
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        analysis_service._client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        text = "This is a test journal entry with more than ten words to trigger analysis."
        result = await analysis_service.analyze(text)

        assert result is not None
        # Max tags is 5
        assert len(result.tags) <= 5
