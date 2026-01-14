# 🎙 Voice Life Journal

> A zero-friction voice journaling Telegram bot with AI transcription

**Status:** 🏗 In Development (Foundation Phase)
**Version:** 0.1.0-alpha
**License:** MIT

---

## 🎯 Why: The Problem

**Traditional journaling sucks for busy people.**

You've tried 10 times. You failed 10 times. Why?

- 🌙 **Evening fatigue:** Too tired to open Notion and type
- 🚶 **Lost insights:** Best thoughts come while walking, doing dishes, commuting
- 📱 **Friction:** By the time you open an app, the thought is gone
- 😔 **Guilt:** Apps nag you with notifications when you skip days
- 📊 **No reflection:** Your life flies by, insights vanish, you can't remember why you were sad last Tuesday

**The core issue:** Tools that require discipline fail. We need a tool that adapts to *you*, not vice versa.

---

## 💡 What: The Solution

**A Telegram bot for voice journaling that requires zero effort.**

You don't open an app. You don't type. You just:
1. Open Telegram (already in your pocket)
2. Hold the mic button
3. Dump your stream of consciousness
4. Done.

The bot:
- 🎧 Listens silently (receives voice message)
- 📝 Transcribes your rambling into clean text (via Whisper AI)
- 💾 Archives it safely
- 🧠 (Future) Analyzes mood and extracts insights via LLM

**Zero friction. Zero guilt. Zero discipline required.**

---

## 🎬 Use Cases

### 1️⃣ Insight on the Go
> Walking down the street, idea hits: "What if we refactor the auth module?"
> → Tap Telegram, record voice note, forget about it
> → Bot transcribes and saves it
> → Later: search for "auth refactor" and find the exact thought

### 2️⃣ Emotional Decompression
> Terrible day at work, rage building up
> → Record angry 2-minute rant to bot
> → Bot accepts without judgment
> → (Future) Bot says: "You were angry at colleagues today, but calmed by evening. Day rating: 4/10"

### 3️⃣ Weekly Reflection
> Sunday evening, feeling reflective
> → `/summary week`
> → Bot: "Tuesday: X idea. Thursday: Y breakthrough. Friday: relaxation."
> → You realize you accomplished more than you thought

---

## 🛠 How: Technical Architecture

### Stack ✅ Decided: Python 3.11+

**Decision:** Python 3.11+ with modern async ecosystem

**Rationale:**
- ✅ **pytest mandatory** (per CLAUDE.md constitution)
- ✅ **OpenAI Python SDK** - native Whisper API integration
- ✅ **aiogram 3.x** - modern async Telegram bot framework
- ✅ **Rapid MVP** - faster development (Happiness First)
- ✅ **Concise code** - better for Small Contexts principle
- ✅ **Strong typing** - Python 3.11+ type hints + mypy

**Core Stack:**
- **Bot:** aiogram 3.x (async Telegram framework)
- **Transcription:** OpenAI Python SDK (Whisper API)
- **Database:** SQLAlchemy 2.0 + Alembic (async ORM + migrations)
- **Testing:** pytest + pytest-asyncio + pytest-cov
- **Code Quality:** black, ruff, mypy, pre-commit hooks

See [DEVELOPMENT.md](./DEVELOPMENT.md) for setup instructions.

### Core Components

```
┌─────────────┐
│   User      │
│ (Telegram)  │
└──────┬──────┘
       │ voice message
       ▼
┌─────────────────┐
│  Telegram Bot   │  ← Receives messages, handles commands
│   (aiogram 3.x) │
└────────┬────────┘
         │
         ├─→ /start, /summary  → Command Handlers
         │
         └─→ Voice Message     → Download audio
                  │
                  ▼
         ┌────────────────┐
         │ Whisper API    │  ← Transcribe speech to text
         │  (OpenAI)      │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │   Database     │  ← Save entries (user_id, timestamp, text)
         │ (SQLite/Postgres)
         └────────────────┘
```

### Data Model (Draft)

```python
from datetime import datetime
from typing import Optional
from uuid import UUID

class JournalEntry:
    """Voice journal entry model."""

    id: UUID                      # Unique entry ID
    user_id: int                  # Telegram user ID
    created_at: datetime          # Timestamp
    voice_file_id: Optional[str]  # Telegram file ID (optional)
    transcription: str            # Whisper output
    sentiment: Optional[dict]     # Future: LLM analysis
                                  # {"mood": str, "score": float}
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- uv (package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Telegram Bot Token (from @BotFather)
- OpenAI API Key (for Whisper)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/tenishevnikita/voice-life-journal.git
cd voice-life-journal

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env and add your tokens:
# - TELEGRAM_BOT_TOKEN (get from @BotFather)
# - OPENAI_API_KEY (get from OpenAI platform)

# 4. Run the bot
uv run python -m src.bot.main
```

### Running Tests

```bash
# Run unit tests (fast, no API calls)
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_handlers.py -v

# Run integration tests (requires real OPENAI_API_KEY, makes real API calls)
RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration/ -v
```

**Note:** Integration tests are disabled by default as they make real API calls and cost money. See [DEVELOPMENT.md](./DEVELOPMENT.md) for details on setting up integration tests.

---

## 📈 Roadmap

See [project-status.md](./project-status.md) for detailed tracking.

### Phase 1: Foundation ✅ Complete
- [x] #1 Project vision
- [x] #2 Documentation (README, project-status, agents, CLAUDE)
- [x] #3 Tech stack (Python 3.11+) + project structure

### Phase 2: MVP Bot 🔄 In Progress
- [x] #4 Telegram bot (commands, message handling)
- [ ] #5 Whisper integration
- [ ] #6 Database persistence

### Phase 3: Features
- [ ] #7 Summary commands (daily/weekly/monthly)

### Phase 4: Production
- [ ] #8 Test coverage (70%+)
- [ ] #9 Security audit

---

## 🧬 Development Principles

This project follows **AI Coding Course** methodology.

**📖 For detailed development rules, see [CLAUDE.md](./CLAUDE.md) - the constitution for AI agents.**

### 1. Vibe Coding
- Code is disposable, specifications are permanent
- RMRF approach: delete and regenerate anytime
- Focus on *what* and *why*, not *how*

### 2. Small Contexts
- Files max 300-500 lines
- Easy to understand and regenerate
- Better for AI context windows

### 3. Contracts First
- Define API contracts before implementation
- Frontend and backend can develop in parallel
- JSON Schema for validation

### 4. Happiness First
- Build what removes toil and pain
- No features for features' sake
- Optimize for developer and user joy

### 5. Git as Story
- Conventional Commits (feat, fix, docs, refactor)
- Commits explain *why*, not *what*
- Link to issues: `ref #X`, `closes #X`

### 6. Zero Friction Philosophy
**This tool adapts to you:**
- No discipline required
- No guilt trips
- No rigid structure
- Record 10 messages in a row? Fine.
- Silent for 3 days? Also fine.

---

## 📁 Project Structure

```
voice-life-journal/
├── src/
│   ├── bot/                 # Telegram bot handlers (aiogram)
│   ├── services/            # External services (Whisper, database)
│   └── models/              # Data models (SQLAlchemy)
├── tests/
│   ├── unit/                # Unit tests (pytest)
│   └── integration/         # Integration tests
├── CLAUDE.md                # AI Coding Constitution
├── DEVELOPMENT.md           # Developer setup guide
├── README.md                # Project overview (you are here)
├── project-status.md        # Roadmap and current status
├── agents.md                # AI agent roles
├── pyproject.toml           # Project dependencies (uv)
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── .pre-commit-config.yaml  # Git hooks configuration
```

---

## 🔒 Security & Privacy

**Paranoia Mode Enabled:** We don't trust anyone. All entry points are validated.

### Security Measures

✅ **Secrets Protection**
- All API keys and tokens in environment variables (`.env` file)
- `.env` files in `.gitignore` (never committed to git)
- No hardcoded secrets in source code
- Configuration validation on startup

✅ **Input Validation**
- User ID authorization whitelist (optional `ALLOWED_USER_IDS`)
- Voice file size limits (configurable `MAX_VOICE_FILE_SIZE_MB`, default: 20MB)
- Period parameter validation for `/summary` command (whitelist: today/week/month)
- Transcription text validation (non-empty, sanitized)

✅ **SQL Injection Protection**
- SQLAlchemy ORM with parameterized queries
- No string formatting in SQL queries
- All database operations use prepared statements

✅ **Logging Security**
- No API keys or tokens in logs
- User messages not logged (only metadata)
- Database URLs logged without credentials
- Only file sizes logged, not content

✅ **File Upload Security**
- Size validation before download (prevents memory exhaustion)
- Only voice messages accepted (Telegram validates format)
- Temporary files cleaned up after processing

### Privacy

- 🔐 Your journal entries are stored locally (SQLite) or in your own database
- 🚫 No data sharing with third parties
- 📦 You own your data 100%
- 🗑 Delete entries anytime (future: `/delete` command)

### Security Best Practices

For deployment, we recommend:
- Use `ALLOWED_USER_IDS` to whitelist authorized users
- Set `MAX_VOICE_FILE_SIZE_MB` based on your needs (default: 20MB)
- Use environment-specific `.env` files (`.env.production`, `.env.staging`)
- Enable HTTPS for webhook mode (if using webhooks instead of polling)
- Regular database backups
- Monitor logs for unauthorized access attempts

See [SECURITY.md](./SECURITY.md) for detailed security documentation and vulnerability reporting.

---

## 🤝 Contributing

This is a personal project, but if you're interested:
1. Read [CLAUDE.md](./CLAUDE.md) for AI Coding Constitution and development rules
2. Read [agents.md](./agents.md) for AI agent roles and workflow
3. Check [project-status.md](./project-status.md) for current tasks and roadmap
4. All issues include test descriptions in natural language (pytest framework)
5. Open an issue or PR following Conventional Commits format

---

## 📜 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- **OpenAI Whisper** for speech-to-text
- **Telegram** for the bot platform
- **AI Coding Course** for development methodology

---

**Made with 🎙 and 🤖 by @tenishevnikita**

*"Your life is worth remembering. Make it effortless."*
