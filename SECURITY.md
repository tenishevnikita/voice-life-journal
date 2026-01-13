# Security Policy

## 🔒 Security Philosophy

Voice Life Journal follows **Paranoia Mode** security principles:

> "Don't trust anyone. Validate everything. No validation = vulnerability."

We treat all external input as potentially malicious and validate at every entry point.

---

## 🛡️ Security Measures

### 1. Secrets Management

**✅ What we do:**
- All secrets stored in environment variables (`.env` file)
- `.env` files in `.gitignore` (never committed)
- No hardcoded API keys or tokens in source code
- Configuration validation on application startup

**🔍 Verification:**
```bash
# Check no secrets in git history
git log --all --full-history -- .env

# Search for potential secrets in code
grep -r "sk-" src/
grep -r "TELEGRAM_BOT_TOKEN" src/
```

**Required environment variables:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (required)
- `OPENAI_API_KEY` - OpenAI API key for Whisper (required)
- `DATABASE_URL` - Database connection string (optional, defaults to SQLite)
- `ALLOWED_USER_IDS` - Comma-separated user IDs whitelist (optional)

---

### 2. Input Validation

**✅ User Authorization:**
- Optional user whitelist via `ALLOWED_USER_IDS` environment variable
- All handlers check `is_user_allowed()` before processing
- Unauthorized users receive rejection message
- Unauthorized access attempts logged

**✅ File Upload Validation:**
- Voice file size checked before download
- Configurable limit via `MAX_VOICE_FILE_SIZE_MB` (default: 20MB)
- Prevents memory exhaustion attacks
- Files exceeding limit rejected with user-friendly message

**✅ Command Parameter Validation:**
- `/summary` period parameter whitelisted: `["today", "week", "month"]`
- Invalid parameters rejected with usage instructions
- No arbitrary string execution

**✅ Data Validation:**
- `user_id` must be positive integer
- `transcription` must be non-empty string
- Input sanitized with `.strip()` before storage
- ValueError raised for invalid inputs

---

### 3. SQL Injection Protection

**✅ What we do:**
- SQLAlchemy ORM with parameterized queries
- All queries use `.where()` with bound parameters
- No string formatting or concatenation in SQL
- No raw SQL execution

**Example of safe query:**
```python
# ✅ SAFE - Parameterized query
select(Entry).where(Entry.user_id == user_id)

# ❌ UNSAFE - String formatting (we don't do this)
# f"SELECT * FROM entries WHERE user_id = {user_id}"
```

**Verification:**
```bash
# Check no string formatting in queries
grep -r "execute.*f[\"']" src/
grep -r "\.format\(" src/services/entries.py
```

---

### 4. Logging Security

**✅ What we log:**
- User IDs and usernames (public Telegram data)
- File sizes and durations (metadata only)
- Error types and stack traces
- Operation success/failure status

**❌ What we DON'T log:**
- API keys or tokens
- User message content (text or transcriptions)
- Database credentials (URLs logged without auth)
- Voice file contents

**Example:**
```python
# ✅ SAFE
logger.info(f"Saved entry for user {user_id}: {len(transcription)} chars")

# ❌ UNSAFE (we don't do this)
# logger.info(f"Transcription: {transcription}")
```

---

### 5. Rate Limiting

**Current status:** ⚠️ Not implemented yet

**Planned:**
- Per-user rate limits on voice messages
- Global rate limits on API calls
- Rate limit headers from Telegram and OpenAI respected

**Workaround:**
- User whitelist (`ALLOWED_USER_IDS`) limits exposure
- OpenAI SDK handles rate limits automatically
- Voice file size limits prevent resource exhaustion

---

### 6. HTTPS & Transport Security

**Current status:** ℹ️ Using long polling (no webhook)

**For webhook mode:**
- HTTPS required for webhook endpoint
- Valid SSL/TLS certificate required
- Webhook URL validation by Telegram

---

## 🔍 Security Audit Checklist

- [x] **Environment Variables:** All secrets in `.env`, not in git
- [x] **User Authorization:** `is_user_allowed()` checks in all handlers
- [x] **File Size Limits:** Validated before download
- [x] **SQL Injection:** Parameterized queries only
- [x] **Logging:** No sensitive data in logs
- [x] **Input Validation:** All user inputs validated
- [x] **Error Handling:** Errors don't expose internal details
- [x] **Dependencies:** Regular updates (managed by uv)

---

## 🚨 Vulnerability Reporting

If you discover a security vulnerability, please report it responsibly:

**DO:**
1. Email: [your-email@example.com] with subject "SECURITY: Voice Life Journal"
2. Provide detailed description of the vulnerability
3. Include steps to reproduce (if applicable)
4. Give us reasonable time to fix before public disclosure

**DON'T:**
- Post vulnerability details publicly (GitHub issues, Twitter, etc.)
- Exploit the vulnerability maliciously
- Test on production systems without permission

We will:
- Acknowledge receipt within 48 hours
- Provide timeline for fix
- Credit you in CHANGELOG (if desired)

---

## 🔐 Best Practices for Users

### For Personal Use:

1. **Protect your `.env` file:**
   ```bash
   chmod 600 .env  # Read/write only for owner
   ```

2. **Use user whitelist:**
   ```bash
   # Only allow your Telegram ID
   ALLOWED_USER_IDS=123456789
   ```

3. **Regular backups:**
   ```bash
   # Backup your database
   cp voice_journal.db voice_journal.db.backup
   ```

### For Deployment:

1. **Use separate `.env` files:**
   - `.env.development` - Local development
   - `.env.staging` - Staging environment
   - `.env.production` - Production (never commit!)

2. **Secure your server:**
   - Use firewall (only allow necessary ports)
   - Keep system packages updated
   - Use non-root user to run bot
   - Enable automatic security updates

3. **Monitor logs:**
   ```bash
   # Watch for unauthorized access attempts
   tail -f logs/bot.log | grep "Unauthorized"
   ```

4. **Database security:**
   - Use PostgreSQL with password authentication
   - Create dedicated database user with minimal privileges
   - Enable SSL for database connections
   - Regular backups with encryption

---

## 📚 Security Resources

### OWASP Top 10 Coverage:

- ✅ **A01: Broken Access Control** - User whitelist, authorization checks
- ✅ **A03: Injection** - Parameterized queries, input validation
- ✅ **A05: Security Misconfiguration** - Secure defaults, validation
- ✅ **A07: Identification/Auth Failures** - User ID validation
- ✅ **A09: Security Logging Failures** - No sensitive data in logs

### Dependencies:

We use `uv` for dependency management with automatic security updates:

```bash
# Check for vulnerabilities
uv pip list --outdated

# Update dependencies
uv sync --upgrade
```

### Tools:

- **bandit** - Python security linter (planned)
- **safety** - Dependency vulnerability scanner (planned)
- **pre-commit** - Git hooks for security checks

---

## 📝 Security Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-14 | Initial security audit | Baseline security measures |
| 2026-01-14 | Fix: Remove user message content from logs | Privacy improvement |

---

## ⚖️ License

This security policy is part of the Voice Life Journal project and follows the MIT License.

---

**Last Updated:** 2026-01-14
**Security Contact:** [Create an issue with "SECURITY" label]
