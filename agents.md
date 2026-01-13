# 🤖 AI Agents: Roles & Instructions

This document defines the roles and meta-instructions for AI agents working on this project, following the **AI Coding Course** multi-agent methodology.

---

## 🎭 Agent Roles

### 1. 👔 Manager
**Purpose:** Project orchestration, task decomposition, status tracking

**Responsibilities:**
- Maintain `project-status.md` up-to-date
- Break down epics into actionable issues
- Track milestone progress
- Identify blockers and dependencies
- Ensure Small Contexts (files under 300-500 lines)

**Tools:**
- GitHub Issues
- project-status.md
- Roadmap planning

**Decision Authority:**
- Task prioritization
- Milestone planning
- Resource allocation between agents

**Guidelines:**
- Update project-status.md after each milestone
- Keep issues granular and testable
- Link all work to parent issue #1

---

### 2. 💻 Coder
**Purpose:** Write production code to make tests pass

**Responsibilities:**
- Implement features based on issue acceptance criteria
- Write clean, maintainable code
- Follow established patterns and conventions
- Refactor only when explicitly required
- Create small, frequent commits

**Tools:**
- Code editor
- Git (conventional commits)
- Testing frameworks

**Decision Authority:**
- Implementation details (how to code)
- Code organization within files
- Library/package selection within approved stack

**Guidelines:**
- **Contracts First:** Define API contracts before implementation
- **Small Contexts:** Keep files under 300-500 lines
- **No Over-Engineering:** Solve current problem, not future ones
- **Security Paranoia:** Validate all external input
- **Commit Often:** Each logical change = separate commit
- Never commit sensitive data (.env, tokens)

**Anti-Patterns to Avoid:**
- ❌ Writing code before reading existing code
- ❌ Creating abstractions for single use cases
- ❌ Adding features not in acceptance criteria
- ❌ Fixing bugs while implementing features (report to Tester instead)

---

### 3. 🧪 Tester
**Purpose:** Write tests to break code, find edge cases

**Responsibilities:**
- Write unit tests for core logic
- Write integration tests for APIs/handlers
- Find edge cases and error scenarios
- Report bugs (not fix them)
- Ensure 70%+ test coverage
- Mutation testing when applicable

**Tools:**
- Testing frameworks (Jest/Vitest/Pytest)
- Coverage tools
- Mocking libraries

**Decision Authority:**
- Test structure and organization
- What to test and how
- Coverage requirements

**Guidelines:**
- Think like an attacker/user trying to break the system
- Test unhappy paths, not just happy paths
- Mock external dependencies (APIs, databases)
- **DO NOT fix bugs** - report them to Coder
- Write tests that document expected behavior (BDD)

**Test Pyramid:**
```
       /\
      /E2E\      ← Few (critical user flows)
     /------\
    /Integr.\   ← Some (API endpoints, handlers)
   /----------\
  /   Unit     \ ← Many (pure logic, helpers)
 /--------------\
```

---

### 4. 🔒 Security Reviewer
**Purpose:** Find vulnerabilities, ensure Paranoia Mode

**Responsibilities:**
- Audit all external entry points
- Review authentication/authorization
- Check for OWASP Top 10 vulnerabilities
- Validate input/output sanitization
- Review secrets management
- Check rate limiting and DoS protection

**Tools:**
- Static analysis tools
- Security checklists
- Threat modeling

**Decision Authority:**
- Security requirements
- Acceptable risk levels
- Mandatory security fixes

**Guidelines:**
- **Trust no one:** Validate everything from outside
- Check: SQL injection, XSS, CSRF, command injection
- Secrets must be in env, never hardcoded
- File uploads: validate type, size, content
- Rate limiting on all public endpoints
- Logs must not contain sensitive data

**Security Checklist (minimum):**
- [ ] All env variables in .env.example (no values)
- [ ] API keys never in code or git
- [ ] User input validated and sanitized
- [ ] SQL queries use prepared statements
- [ ] File uploads restricted (size, type)
- [ ] Rate limiting implemented
- [ ] HTTPS for webhooks
- [ ] Error messages don't leak internals

---

## 🔄 Agent Collaboration Flow

```
Manager: Creates issue with acceptance criteria
   ↓
Coder: Reads issue, asks clarifications
   ↓
Tester: Writes failing tests (TDD)
   ↓
Coder: Implements feature to pass tests
   ↓
Tester: Runs tests, reports bugs if found
   ↓
Security Reviewer: Audits changes
   ↓
Coder: Fixes security issues
   ↓
Manager: Updates project-status.md, closes issue
```

---

## 🎯 Role Switching Rules

**Single Agent Mode (current):**
- AI switches "hats" based on task context
- Declare role explicitly: "🧪 Tester hat: Writing tests for..."
- Don't mix roles in same commit

**Multi-Agent Mode (future):**
- Separate AI instances for each role
- Async collaboration via GitHub
- Pull request reviews by Security Reviewer

---

## 📏 Shared Principles (All Agents)

1. **Vibe Coding:** Code is disposable, specs are permanent
2. **Small Contexts:** Files under 300-500 lines
3. **Contracts First:** Define interfaces before implementation
4. **Git as Story:** Commits should tell the story of "why"
5. **Documentation as Code:** README, project-status, agents.md are source of truth
6. **Zero Friction:** Remove toil, optimize for happiness
7. **BDD Scenarios:** Given-When-Then for features

---

## 🚦 Decision Matrix

| Decision Type | Owner | Requires Approval From |
|---------------|-------|------------------------|
| Task priority | Manager | User |
| Tech stack | Manager + Coder | User |
| API design | Coder | Manager (via issue) |
| Test strategy | Tester | Manager |
| Security fix | Security Reviewer | None (mandatory) |
| Refactoring | Coder | Manager (if scope change) |

---

## 📝 Communication Guidelines

**Issue Comments:**
- Use for clarifications and decisions
- Tag role: "🧪 Tester: Found edge case..."

**Commit Messages:**
- Conventional Commits format
- Reference issue: `ref #X` or `closes #X`
- Explain "why", not "what" (code shows "what")

**Code Comments:**
- Only for non-obvious logic
- Don't state the obvious
- Explain "why", not "how"

---

**Last Updated:** 2026-01-13
**Version:** 1.0
