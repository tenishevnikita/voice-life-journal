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

### Stack (TBD in Issue #3)
**Option A: TypeScript (Node.js)**
- ✅ Strong typing
- ✅ Excellent Telegram bot ecosystem (grammY, Telegraf)
- ✅ Easy deployment (Vercel, Railway, fly.io)

**Option B: Python**
- ✅ Simpler for rapid prototyping
- ✅ Great AI/ML libraries
- ✅ python-telegram-bot or aiogram

**Decision pending:** See issue #3

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
│  (grammY/aiogram)│
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

```typescript
interface JournalEntry {
  id: string;              // UUID
  userId: number;          // Telegram user ID
  createdAt: Date;         // Timestamp
  voiceFileId?: string;    // Telegram file ID (optional)
  transcription: string;   // Whisper output
  sentiment?: {            // Future: LLM analysis
    mood: string;
    score: number;
  };
}
```

---

## 🚀 Roadmap

See [project-status.md](./project-status.md) for detailed tracking.

### Phase 1: Foundation ✅ In Progress
- [x] #1 Project vision
- [ ] #2 Documentation (this file)
- [ ] #3 Tech stack + project structure

### Phase 2: MVP Bot
- [ ] #4 Telegram bot (commands, message handling)
- [ ] #5 Whisper integration
- [ ] #6 Database persistence

### Phase 3: Features
- [ ] #7 Summary commands (daily/weekly/monthly)

### Phase 4: Production
- [ ] #8 Test coverage (70%+)
- [ ] #9 Security audit

---

## 🧬 Development Principles

This project follows **AI Coding Course** methodology:

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
├── docs/
│   ├── project-status.md    # Roadmap, milestones, current status
│   └── agents.md            # AI agent roles and workflows
├── src/
│   ├── bot/                 # Telegram bot handlers
│   ├── services/            # Whisper, database, etc.
│   └── types/               # TypeScript types / data models
├── tests/
│   ├── unit/
│   └── integration/
├── .env.example
├── .gitignore
└── README.md                # You are here
```

---

## 🔒 Security & Privacy

**Paranoia Mode Enabled:**

- 🔐 All API keys in environment variables (never in code)
- ✅ Input validation on all Telegram messages
- 🛡 SQL injection protection (prepared statements)
- 📏 File size limits on voice uploads
- 🚦 Rate limiting on bot endpoints
- 🔍 No sensitive data in logs
- 🌐 HTTPS for webhooks (if used)

**Privacy:**
- Your journal entries are stored securely
- No data sharing with third parties
- You own your data (export anytime)

---

## 🤝 Contributing

This is a personal project, but if you're interested:
1. Read [agents.md](./docs/agents.md) for development workflow
2. Check [project-status.md](./docs/project-status.md) for current tasks
3. Open an issue or PR following Conventional Commits

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
