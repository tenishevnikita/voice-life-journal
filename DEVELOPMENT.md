# 🛠 Development Guide

Quick start guide for developers working on Voice Life Journal.

---

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Git

---

## 🚀 Quick Start

### 1. Install Poetry

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or via pip
pip install poetry
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/tenishevnikita/voice-life-journal.git
cd voice-life-journal

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
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
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg

# Test hooks (optional)
poetry run pre-commit run --all-files
```

---

## 🧪 Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_database.py

# Run with verbose output
poetry run pytest -v
```

---

## 🎨 Code Quality

### Formatting

```bash
# Format code with Black
poetry run black src/ tests/

# Check formatting without changes
poetry run black --check src/ tests/
```

### Linting

```bash
# Run Ruff linter
poetry run ruff check src/ tests/

# Auto-fix issues
poetry run ruff check --fix src/ tests/
```

### Type Checking

```bash
# Run MyPy type checker
poetry run mypy src/
```

---

## 🏃 Running the Bot

```bash
# Run the bot (once implemented)
poetry run python -m src.bot.main
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
├── pyproject.toml   # Poetry configuration
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

### Poetry not found
```bash
# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Pre-commit hooks failing
```bash
# Update hooks
poetry run pre-commit autoupdate

# Clear cache and retry
poetry run pre-commit clean
```

### Tests failing
```bash
# Check if .env is configured
cat .env

# Ensure dependencies are installed
poetry install --with dev
```

---

**Last Updated:** 2026-01-13
