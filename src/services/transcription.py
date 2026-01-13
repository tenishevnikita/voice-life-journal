"""Whisper API transcription service."""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from src.config import config

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Base exception for transcription errors."""

    pass


class TranscriptionAPIError(TranscriptionError):
    """Error communicating with Whisper API."""

    pass


class TranscriptionRateLimitError(TranscriptionError):
    """Rate limit exceeded."""

    pass


class WhisperService:
    """Service for transcribing audio using OpenAI Whisper API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        """Initialize Whisper service.

        Args:
            api_key: OpenAI API key. Defaults to config value.
            model: Whisper model to use. Defaults to config value.
        """
        self._api_key = api_key or config.openai_api_key
        self._model = model or config.whisper_model
        self._client = AsyncOpenAI(api_key=self._api_key)

    async def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio file bytes (OGG/OGA format from Telegram).
            language: Optional language hint (ISO-639-1 code, e.g., 'en', 'ru').

        Returns:
            Transcribed text.

        Raises:
            TranscriptionError: If transcription fails.
            TranscriptionAPIError: If API communication fails.
            TranscriptionRateLimitError: If rate limit exceeded.
        """
        if not audio_data:
            raise TranscriptionError("Empty audio data provided")

        # Create temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            try:
                tmp_file.write(audio_data)
                tmp_file.flush()

                logger.debug(
                    f"Transcribing audio file: {len(audio_data)} bytes, "
                    f"model: {self._model}, language: {language or 'auto'}"
                )

                # Open and send to Whisper API
                with open(tmp_path, "rb") as audio_file:
                    response = await self._client.audio.transcriptions.create(
                        model=self._model,
                        file=audio_file,
                        language=language,
                    )

                text = response.text.strip()
                logger.info(f"Transcription successful: {len(text)} characters")
                return text

            except RateLimitError as e:
                logger.error(f"Whisper API rate limit exceeded: {e}")
                raise TranscriptionRateLimitError(
                    "Rate limit exceeded. Please try again later."
                ) from e
            except APIConnectionError as e:
                logger.error(f"Whisper API connection error: {e}")
                raise TranscriptionAPIError(
                    "Could not connect to transcription service. Please try again later."
                ) from e
            except APIError as e:
                logger.error(f"Whisper API error: {e}")
                raise TranscriptionAPIError(f"Transcription failed: {e.message}") from e
            except Exception as e:
                logger.error(f"Unexpected transcription error: {e}", exc_info=True)
                raise TranscriptionError(f"Transcription failed: {e}") from e
            finally:
                # Clean up temp file
                try:
                    tmp_path.unlink()
                    logger.debug(f"Cleaned up temp file: {tmp_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


# Global service instance
whisper_service = WhisperService()
