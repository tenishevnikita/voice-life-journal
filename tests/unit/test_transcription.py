"""Unit tests for transcription service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIConnectionError, APIError, RateLimitError

from src.services.transcription import (
    TranscriptionAPIError,
    TranscriptionError,
    TranscriptionRateLimitError,
    WhisperService,
)


class TestWhisperService:
    """Test Whisper transcription service."""

    @pytest.fixture
    def whisper_service(self) -> WhisperService:
        """Create a WhisperService instance for testing."""
        return WhisperService(api_key="test-api-key", model="whisper-1")

    @pytest.mark.asyncio
    async def test_transcribe_success(self, whisper_service: WhisperService) -> None:
        """Test successful transcription."""
        mock_response = MagicMock()
        mock_response.text = "  Hello, this is a test transcription.  "

        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await whisper_service.transcribe(b"fake audio data")

        assert result == "Hello, this is a test transcription."

    @pytest.mark.asyncio
    async def test_transcribe_with_language_hint(
        self, whisper_service: WhisperService
    ) -> None:
        """Test transcription with language hint."""
        mock_response = MagicMock()
        mock_response.text = "Привет, это тест."

        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            result = await whisper_service.transcribe(b"fake audio data", language="ru")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["language"] == "ru"
        assert result == "Привет, это тест."

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_data(
        self, whisper_service: WhisperService
    ) -> None:
        """Test that empty audio data raises error."""
        with pytest.raises(TranscriptionError, match="Empty audio data"):
            await whisper_service.transcribe(b"")

    @pytest.mark.asyncio
    async def test_transcribe_rate_limit_error(
        self, whisper_service: WhisperService
    ) -> None:
        """Test handling of rate limit error."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=mock_response,
                body=None,
            ),
        ):
            with pytest.raises(TranscriptionRateLimitError, match="Rate limit"):
                await whisper_service.transcribe(b"fake audio data")

    @pytest.mark.asyncio
    async def test_transcribe_api_connection_error(
        self, whisper_service: WhisperService
    ) -> None:
        """Test handling of API connection error."""
        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            side_effect=APIConnectionError(request=MagicMock()),
        ):
            with pytest.raises(TranscriptionAPIError, match="Could not connect"):
                await whisper_service.transcribe(b"fake audio data")

    @pytest.mark.asyncio
    async def test_transcribe_api_error(self, whisper_service: WhisperService) -> None:
        """Test handling of general API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}

        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            side_effect=APIError(
                message="Internal server error",
                request=MagicMock(),
                body=None,
            ),
        ):
            with pytest.raises(TranscriptionAPIError, match="Transcription failed"):
                await whisper_service.transcribe(b"fake audio data")

    @pytest.mark.asyncio
    async def test_transcribe_unexpected_error(
        self, whisper_service: WhisperService
    ) -> None:
        """Test handling of unexpected errors."""
        with patch.object(
            whisper_service._client.audio.transcriptions,
            "create",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            with pytest.raises(TranscriptionError, match="Transcription failed"):
                await whisper_service.transcribe(b"fake audio data")

    def test_service_initialization_defaults(self) -> None:
        """Test that service uses config defaults."""
        with patch("src.services.transcription.config") as mock_config:
            mock_config.openai_api_key = "config-api-key"
            mock_config.whisper_model = "whisper-1"
            mock_config.openai_base_url = None

            service = WhisperService()

            assert service._api_key == "config-api-key"
            assert service._model == "whisper-1"

    def test_service_initialization_custom(self) -> None:
        """Test service with custom parameters."""
        service = WhisperService(api_key="custom-key", model="custom-model")

        assert service._api_key == "custom-key"
        assert service._model == "custom-model"

    def test_service_initialization_with_base_url(self) -> None:
        """Test service with custom base_url."""
        service = WhisperService(
            api_key="test-key", model="whisper-1", base_url="https://custom-proxy.com/v1"
        )

        assert service._base_url == "https://custom-proxy.com/v1"
        # OpenAI client adds trailing slash to base_url
        assert str(service._client.base_url) == "https://custom-proxy.com/v1/"

    def test_service_initialization_base_url_from_config(self) -> None:
        """Test that service uses base_url from config."""
        with patch("src.services.transcription.config") as mock_config:
            mock_config.openai_api_key = "config-api-key"
            mock_config.whisper_model = "whisper-1"
            mock_config.openai_base_url = "https://config-proxy.com/v1"

            service = WhisperService()

            assert service._base_url == "https://config-proxy.com/v1"

    def test_service_initialization_base_url_priority(self) -> None:
        """Test that constructor base_url has priority over config."""
        with patch("src.services.transcription.config") as mock_config:
            mock_config.openai_api_key = "config-api-key"
            mock_config.whisper_model = "whisper-1"
            mock_config.openai_base_url = "https://config-proxy.com/v1"

            service = WhisperService(base_url="https://custom-proxy.com/v1")

            assert service._base_url == "https://custom-proxy.com/v1"

    def test_service_initialization_no_base_url(self) -> None:
        """Test that service works without base_url (uses OpenAI default)."""
        with patch("src.services.transcription.config") as mock_config:
            mock_config.openai_api_key = "test-key"
            mock_config.whisper_model = "whisper-1"
            mock_config.openai_base_url = None

            service = WhisperService()

            assert service._base_url is None
