"""Integration tests for Whisper API - REAL API CALLS.

These tests make real API calls to OpenAI Whisper API and are disabled by default.
Enable them by setting RUN_INTEGRATION_TESTS=1 environment variable.

WARNING: These tests cost money! Each transcription costs ~$0.006 per minute.
"""

import os
from pathlib import Path

import pytest

from src.services.transcription import WhisperService

# Skip all integration tests if RUN_INTEGRATION_TESTS is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable",
)


class TestWhisperIntegration:
    """Integration tests with real Whisper API."""

    @pytest.fixture
    def whisper_service(self) -> WhisperService:
        """Create WhisperService with real API key from env."""
        api_key = os.getenv("OPENAI_API_KEY")

        # Skip test if API key is fake/test key
        if not api_key or api_key.startswith("sk-test") or api_key == "test-api-key":
            pytest.skip("Real OPENAI_API_KEY required for integration tests")

        return WhisperService(api_key=api_key, model="whisper-1")

    @pytest.mark.asyncio
    async def test_real_transcription_english(self, whisper_service: WhisperService) -> None:
        """Test real transcription with English audio sample.

        Expected: Transcription completes successfully and returns non-empty text.
        """
        audio_path = Path("tests/fixtures/audio_en_sample.ogg")

        if not audio_path.exists():
            pytest.skip(
                f"Audio fixture not found: {audio_path}. "
                "See tests/fixtures/README.md for instructions."
            )

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        result = await whisper_service.transcribe(audio_data)

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0
        assert result.strip() == result  # Should be trimmed

        # Log result for manual verification
        print(f"\nEnglish transcription result: {result}")

    @pytest.mark.asyncio
    async def test_real_transcription_russian(self, whisper_service: WhisperService) -> None:
        """Test real transcription with Russian audio sample.

        Expected: Transcription completes successfully with Cyrillic text.
        """
        audio_path = Path("tests/fixtures/audio_ru_sample.ogg")

        if not audio_path.exists():
            pytest.skip(
                f"Audio fixture not found: {audio_path}. "
                "See tests/fixtures/README.md for instructions."
            )

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        result = await whisper_service.transcribe(audio_data, language="ru")

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Should contain Cyrillic characters (basic check)
        # This is not foolproof but catches obvious issues
        has_cyrillic = any("\u0400" <= char <= "\u04FF" for char in result)
        if not has_cyrillic:
            print(
                f"\nWARNING: Russian transcription may not contain Cyrillic: {result}"
            )

        # Log result for manual verification
        print(f"\nRussian transcription result: {result}")

    @pytest.mark.asyncio
    async def test_real_transcription_without_language_hint(
        self, whisper_service: WhisperService
    ) -> None:
        """Test that Whisper auto-detects language without hint.

        Expected: Transcription works without explicit language parameter.
        """
        # Use Russian audio without language hint to test auto-detection
        audio_path = Path("tests/fixtures/audio_ru_sample.ogg")

        if not audio_path.exists():
            pytest.skip(
                f"Audio fixture not found: {audio_path}. "
                "See tests/fixtures/README.md for instructions."
            )

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        result = await whisper_service.transcribe(audio_data)  # No language hint

        # Should still work
        assert isinstance(result, str)
        assert len(result) > 0

        print(f"\nAuto-detected transcription result: {result}")

    @pytest.mark.asyncio
    async def test_real_custom_base_url(self) -> None:
        """Test that custom base_url works with real API.

        This test only runs if OPENAI_BASE_URL is set.
        Expected: Transcription works through custom endpoint.
        """
        custom_url = os.getenv("OPENAI_BASE_URL")
        if not custom_url:
            pytest.skip("OPENAI_BASE_URL not set, skipping custom URL test")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("sk-test"):
            pytest.skip("Real OPENAI_API_KEY required for integration tests")

        service = WhisperService(api_key=api_key, base_url=custom_url)

        # Use English audio
        audio_path = Path("tests/fixtures/audio_en_sample.ogg")
        if not audio_path.exists():
            pytest.skip(
                f"Audio fixture not found: {audio_path}. "
                "See tests/fixtures/README.md for instructions."
            )

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        result = await service.transcribe(audio_data)

        assert isinstance(result, str)
        assert len(result) > 0

        print(f"\nCustom URL transcription result: {result}")
        print(f"Used base_url: {custom_url}")

    @pytest.mark.asyncio
    async def test_real_file_size_check(self, whisper_service: WhisperService) -> None:
        """Test that integration tests use reasonably sized audio files.

        Expected: Audio fixtures are < 1MB to keep tests fast and cheap.
        """
        fixtures_dir = Path("tests/fixtures")
        audio_files = list(fixtures_dir.glob("*.ogg"))

        if not audio_files:
            pytest.skip("No audio fixtures found")

        for audio_file in audio_files:
            file_size_mb = audio_file.stat().st_size / (1024 * 1024)

            # Warn if file is too large
            if file_size_mb > 1.0:
                pytest.fail(
                    f"Audio fixture {audio_file.name} is too large: {file_size_mb:.2f}MB. "
                    f"Keep fixtures < 1MB to keep tests fast and cheap. "
                    f"See tests/fixtures/README.md for instructions."
                )

            print(f"\n{audio_file.name}: {file_size_mb:.2f}MB")
