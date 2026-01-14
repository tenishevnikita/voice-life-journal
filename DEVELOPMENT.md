# 🛠 Development Guide

Quick start guide for developers working on Voice Life Journal.

---

## 📋 Prerequisites

- Python 3.11 or higher
- uv (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Git

---

## 🚀 Quick Start

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv

# Or via Homebrew
brew install uv
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/tenishevnikita/voice-life-journal.git
cd voice-life-journal

# Install dependencies (automatically creates and manages virtual environment)
uv sync
```

### 3. Setup Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials:
# - TELEGRAM_BOT_TOKEN (from @BotFather)
# - OPENAI_API_KEY (from OpenAI platform)
```

### 4. Setup Git Hooks (Conventional Commits)

```bash
# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Test hooks (optional)
uv run pre-commit run --all-files
```

---

## 🧪 Running Tests

### Unit Tests (Fast, No API Calls)

Unit tests use mocks and run quickly without making real API calls:

```bash
# Run all unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_database.py

# Run with verbose output
uv run pytest -v
```

### Integration Tests (Real API Calls)

Integration tests make real API calls to external services and are **disabled by default**.

**Prerequisites:**
1. Real OpenAI API key (not `sk-test...`)
2. Audio test fixtures in `tests/fixtures/`
3. Set `RUN_INTEGRATION_TESTS=1` environment variable

**Setup:**

```bash
# 1. Ensure you have a real API key
export OPENAI_API_KEY=sk-proj-your-real-key-here

# 2. Create audio fixtures (see tests/fixtures/README.md)
# You need to create these files manually:
# - tests/fixtures/audio_en_sample.ogg (< 1MB, English speech)
# - tests/fixtures/audio_ru_sample.ogg (< 1MB, Russian speech)

# 3. Enable integration tests
export RUN_INTEGRATION_TESTS=1

# 4. Run integration tests
uv run pytest tests/integration/ -v
```

**Testing Custom base_url:**

If you use a custom OpenAI API endpoint (proxy, aggregator):

```bash
# Set custom base URL
export OPENAI_BASE_URL=https://your-proxy.com/v1

# Run integration tests with custom URL
RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration/ -v
```

**Cost Warning:** Integration tests make real API calls. Each test costs approximately:
- Whisper API: ~$0.006 per minute of audio
- With small fixtures (< 10 seconds each): ~$0.01-0.02 per full test run

**Why Integration Tests?**

Unit tests with mocks don't guarantee that:
- Real API calls work
- Custom `OPENAI_BASE_URL` functions correctly
- API contract hasn't changed
- Audio file format is compatible

Integration tests catch these issues before production.

---

## 🎨 Code Quality

### Formatting

```bash
# Format code with Black
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/
```

### Linting

```bash
# Run Ruff linter
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
```

### Type Checking

```bash
# Run MyPy type checker
uv run mypy src/
```

---

## 🏃 Running the Bot

```bash
# Run the bot (once implemented)
uv run python -m src.bot.main
```

---

## 📦 Dependencies

### Core Dependencies
- **aiogram** - Telegram Bot framework
- **openai** - OpenAI API client (Whisper)
- **sqlalchemy** - ORM for database
- **alembic** - Database migrations

### Dev Dependencies
- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Fast Python linter
- **mypy** - Static type checker
- **pre-commit** - Git hooks manager

---

## 📁 Project Structure

```
voice-life-journal/
├── src/
│   ├── bot/         # Telegram bot handlers
│   ├── services/    # External services (Whisper, DB)
│   └── models/      # Data models
├── tests/
│   ├── unit/        # Unit tests
│   └── integration/ # Integration tests
├── pyproject.toml   # Project configuration (uv)
├── .env.example     # Environment variables template
└── README.md        # Project documentation
```

---

## 🔒 Security

- Never commit `.env` files
- All secrets must be in environment variables
- API keys never in code
- Review CLAUDE.md for security paranoia guidelines

---

## 📚 Documentation

- [CLAUDE.md](./CLAUDE.md) - AI Coding Constitution
- [README.md](./README.md) - Project overview
- [project-status.md](./project-status.md) - Current status and roadmap
- [agents.md](./agents.md) - AI agent roles

---

## 🤝 Contributing

1. Read [CLAUDE.md](./CLAUDE.md) for development principles
2. Follow Conventional Commits format
3. Write tests for new features (70% coverage minimum)
4. Run pre-commit hooks before pushing
5. Link commits to GitHub issues: `ref #X` or `closes #X`

---

## 🐛 Common Issues

### uv not found
```bash
# Add uv to PATH (if installed via curl)
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall via Homebrew
brew install uv
```

### Pre-commit hooks failing
```bash
# Update hooks
uv run pre-commit autoupdate

# Clear cache and retry
uv run pre-commit clean
```

### Tests failing
```bash
# Check if .env is configured
cat .env

# Ensure dependencies are installed
uv sync
```

---

**Last Updated:** 2026-01-13
