# Test Fixtures

This directory contains test data for integration tests.

## Audio Samples

Integration tests require real audio files to test Whisper API transcription.

### Required Files

- `audio_en_sample.ogg` - English speech sample (< 1MB)
- `audio_ru_sample.ogg` - Russian speech sample (< 1MB)

### Creating Audio Samples

You can create test audio samples using any of these methods:

#### Method 1: Telegram Voice Messages (Recommended)

1. Send a short voice message to yourself in Telegram (5-10 seconds)
2. Download the `.ogg` file from Telegram
3. Rename to `audio_en_sample.ogg` or `audio_ru_sample.ogg`
4. Place in this directory

#### Method 2: Using ffmpeg

```bash
# Convert any audio file to OGG format (Telegram-compatible)
ffmpeg -i input.mp3 -c:a libopus -b:a 32k -ac 1 -ar 48000 audio_en_sample.ogg
```

#### Method 3: Record with Browser

1. Use https://voicerecorder.com or similar online recorder
2. Record 5-10 seconds of speech
3. Export as OGG format
4. Place in this directory

### Sample Content Suggestions

**English sample (`audio_en_sample.ogg`):**
> "This is a test of the Whisper API transcription service. The quick brown fox jumps over the lazy dog."

**Russian sample (`audio_ru_sample.ogg`):**
> "Это тест сервиса транскрипции Whisper API. Проверяем работу с русским языком."

### File Requirements

- **Format:** OGG (Opus codec) - compatible with Telegram voice messages
- **Size:** < 1MB (keep tests fast and cheap)
- **Duration:** 5-10 seconds
- **Sample rate:** 48kHz (Telegram standard)
- **Bitrate:** 32 kbps (Telegram standard)
- **Channels:** Mono

### Gitignore

Audio files are **not committed to git** to keep the repository size small. Each developer must create their own test fixtures locally.

If you need to run integration tests, create these files according to the instructions above.

### Verification

To verify your audio files are valid:

```bash
# Check file format
file tests/fixtures/audio_en_sample.ogg

# Check file size (should be < 1MB)
ls -lh tests/fixtures/audio_en_sample.ogg

# Run integration tests with your files
RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration/test_whisper_integration.py -v
```

---

**Last Updated:** 2026-01-14
