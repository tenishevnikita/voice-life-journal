"""LLM-based analysis service for journal entries."""

import logging

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field, field_validator

from src.config import config

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """Structured result from LLM analysis."""

    summary: str = Field(description="Brief summary of the entry in 1-2 sentences")
    mood_score: int = Field(
        description="Mood score from 1 (very bad) to 10 (excellent)", ge=1, le=10
    )
    tags: list[str] = Field(description="List of relevant tags (max 5)", default_factory=list)

    @field_validator("mood_score", mode="before")
    @classmethod
    def clamp_mood_score(cls, v: int) -> int:
        """Clamp mood score to valid range 1-10."""
        if isinstance(v, int):
            return max(1, min(10, v))
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def limit_tags(cls, v: list[str]) -> list[str]:
        """Limit tags to max allowed count."""
        if isinstance(v, list):
            return v[: config.analysis_max_tags]
        return v


class AnalysisError(Exception):
    """Base exception for analysis errors."""

    pass


class AnalysisAPIError(AnalysisError):
    """Error communicating with LLM API."""

    pass


class AnalysisRateLimitError(AnalysisError):
    """Rate limit exceeded."""

    pass


class AnalysisParseError(AnalysisError):
    """Error parsing LLM response."""

    pass


ANALYSIS_SYSTEM_PROMPT = """You are an assistant that analyzes voice journal entries.
Your task is to extract structured information from the text.

For each entry, provide:
1. A brief summary (1-2 sentences) capturing the main point
2. A mood score from 1 to 10 (1=very bad, 5=neutral, 10=excellent)
3. Up to 5 relevant tags describing the topics mentioned

Be concise and accurate. Match the language of the entry in your summary."""


class AnalysisService:
    """Service for analyzing journal entries using LLM."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        min_words: int | None = None,
        timeout: int | None = None,
        max_tags: int | None = None,
    ) -> None:
        """Initialize Analysis service.

        Args:
            api_key: OpenAI API key. Defaults to config value.
            model: LLM model to use. Defaults to config value.
            base_url: Custom base URL for API. Defaults to config value.
            min_words: Minimum words to trigger analysis. Defaults to config value.
            timeout: Request timeout in seconds. Defaults to config value.
            max_tags: Maximum number of tags. Defaults to config value.
        """
        self._api_key = api_key or config.openai_api_key
        self._model = model or config.analysis_model
        self._base_url = base_url if base_url is not None else config.openai_base_url
        self._min_words = min_words if min_words is not None else config.analysis_min_words
        self._timeout = timeout if timeout is not None else config.analysis_timeout
        self._max_tags = max_tags if max_tags is not None else config.analysis_max_tags

        if self._base_url:
            logger.info(f"Initializing Analysis service with custom base URL: {self._base_url}")
        else:
            logger.debug("Initializing Analysis service with default OpenAI base URL")

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=float(self._timeout),
        )

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    async def analyze(self, text: str) -> AnalysisResult | None:
        """Analyze journal entry text.

        Args:
            text: The transcription text to analyze.

        Returns:
            AnalysisResult if successful and text meets minimum length,
            None if text is too short.

        Raises:
            AnalysisError: If analysis fails.
            AnalysisAPIError: If API communication fails.
            AnalysisRateLimitError: If rate limit exceeded.
            AnalysisParseError: If response parsing fails.
        """
        if not text or not text.strip():
            return None

        word_count = self._count_words(text)
        if word_count < self._min_words:
            logger.debug(
                f"Text too short for analysis: {word_count} words < {self._min_words} minimum"
            )
            return None

        # Truncate very long text to avoid token limits
        max_chars = 16000  # ~4000 tokens
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        if len(text) > max_chars:
            logger.warning(f"Truncated text from {len(text)} to {max_chars} characters")

        try:
            logger.debug(f"Analyzing text: {word_count} words, model: {self._model}")

            response = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this journal entry:\n\n{truncated_text}"},
                ],
                response_format=AnalysisResult,
            )

            result = response.choices[0].message.parsed
            if result is None:
                raise AnalysisParseError("Failed to parse LLM response")

            # Ensure tags are limited
            result.tags = result.tags[: self._max_tags]

            logger.info(
                f"Analysis successful: mood={result.mood_score}, "
                f"tags={result.tags}, summary_len={len(result.summary)}"
            )
            return result

        except RateLimitError as e:
            logger.error(f"Analysis API rate limit exceeded: {e}")
            raise AnalysisRateLimitError(
                "Rate limit exceeded. Please try again later."
            ) from e
        except APIConnectionError as e:
            logger.error(f"Analysis API connection error: {e}")
            raise AnalysisAPIError(
                "Could not connect to analysis service. Please try again later."
            ) from e
        except APIError as e:
            logger.error(f"Analysis API error: {e}")
            raise AnalysisAPIError(f"Analysis failed: {e.message}") from e
        except AnalysisParseError:
            # Re-raise parse errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected analysis error: {e}", exc_info=True)
            raise AnalysisError(f"Analysis failed: {e}") from e


# Global service instance
analysis_service = AnalysisService()
