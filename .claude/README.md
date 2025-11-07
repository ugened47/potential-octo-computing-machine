# Claude Code Development Environment

> **AI Video Editor** - Comprehensive development setup for token-efficient, best-practice development

## Quick Start

New to this project? Start here:

1. **📖 Read [SETUP-GUIDE.md](SETUP-GUIDE.md)** - Complete guide to slash commands, skills, and workflows
2. **📋 Check [TASKS.md](TASKS.md)** - See what features need implementation
3. **🛠️ Review [CLAUDE.md](CLAUDE.md)** - Project-specific development guidelines
4. **🚀 Run `/setup`** - Initialize your development environment

## What's Included

### 📝 Documentation Files

| File | Purpose |
|------|---------|
| **CLAUDE.md** | Main development guide with tech stack, patterns, and project instructions |
| **SETUP-GUIDE.md** | How to use Claude Code features (commands, skills, task tracking) |
| **TASKS.md** | Complete feature tracking with status (🔴🟡🟢⚪) |
| **README.md** | This file - quick reference and navigation |

### ⚡ Slash Commands (8)

Quick automation for common workflows:

```bash
/api [name]        # Create FastAPI endpoint
/component [name]  # Create React component
/migration [desc]  # Database migration
/test [target]     # Run tests (backend/frontend/all)
/quality           # Code quality checks
/feature [name]    # Full-stack feature implementation
/docker [action]   # Docker operations
/setup             # Environment setup
```

**Learn more:** [SETUP-GUIDE.md#slash-commands](SETUP-GUIDE.md#slash-commands)

### 🧠 Skills (6)

Specialized AI agents that activate automatically:

1. **video-processing** - FFmpeg, PyAV, video optimization
2. **database-design** - PostgreSQL, SQLModel, query optimization
3. **api-design** - FastAPI, REST, authentication
4. **security-review** - OWASP, input validation, auth/auth
5. **frontend-architecture** - Next.js, React, Shadcn UI
6. **performance-optimization** - Backend/frontend performance

**Learn more:** [SETUP-GUIDE.md#skills](SETUP-GUIDE.md#skills)

### 📊 Task Tracking

**TASKS.md** tracks all features from PRD.md:

- **MVP Phase** - 9 MUST HAVE features (User Auth, Video Upload, etc.)
- **Post-MVP** - 6 SHOULD HAVE features (Auto-highlights, Batch processing, etc.)
- **Future** - 4 COULD HAVE features (Live streams, Mobile apps, etc.)
- **Cross-cutting** - Security, Performance, Monitoring, Testing

**Status tracking:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed
- ⚪ Blocked

**Learn more:** [TASKS.md](TASKS.md)

## Common Workflows

### Implementing a Feature

```bash
# 1. Check status
Open TASKS.md → Find feature → Check dependencies

# 2. Start implementation
/feature "Feature name from TASKS.md"

# 3. Claude will:
#    - Create plan with TodoWrite
#    - Guide through: database → backend → frontend → tests
#    - Use appropriate skills automatically
#    - Run quality checks

# 4. Before committing
/quality
/test all

# 5. Update TASKS.md status
Change 🟡 to 🟢
```

### Creating an API Endpoint

```bash
/api videos
# Creates service + route + tests
# Skills: api-design, security-review activate
# Runs type checking and linting
```

### Creating a Component

```bash
/component VideoUploader
# Creates component + types + tests
# Skill: frontend-architecture activates
# Runs type checking and linting
```

### Running Tests

```bash
/test backend      # Pytest with coverage
/test frontend     # Vitest + E2E
/test all          # Everything
```

### Code Quality

```bash
/quality
# Runs:
# - ruff format/check (backend)
# - prettier/eslint (frontend)
# - mypy (backend)
# - tsc (frontend)
```

### Docker Management

```bash
/docker up         # Start all services
/docker logs       # View logs
/docker restart    # Restart services
/docker reset      # Full reset (⚠️ deletes data)
```

## Development Best Practices

### ✅ Token Efficiency

**DO:**
- Use `/feature` for multi-step tasks
- Use specific slash commands for common tasks
- Reference files with `@filename`
- Let skills activate automatically

**DON'T:**
- Explore entire codebase at once
- Read files unnecessarily
- Repeat information from CLAUDE.md
- Run redundant tools

### ✅ Code Quality

Before every commit:

```bash
/quality    # Fix linting/formatting
/test all   # Verify tests pass
```

### ✅ Feature Implementation

Follow this order:

1. **Database** - Models and migrations
2. **Backend** - Service layer → API routes → Tests
3. **Frontend** - Types → Components → API integration → Tests
4. **Quality** - Linting, testing, review
5. **Documentation** - Update comments and docs

### ✅ Security First

Security skill will automatically check for:
- Input validation
- SQL injection prevention
- XSS prevention
- Authentication/authorization
- Secrets management

## Project Structure

```
video-editor/
├── .claude/
│   ├── CLAUDE.md              # Project guidelines ⭐
│   ├── SETUP-GUIDE.md         # This setup guide
│   ├── TASKS.md               # Feature tracking
│   ├── README.md              # Quick reference (you are here)
│   ├── commands/              # 8 slash commands
│   │   ├── api.md
│   │   ├── component.md
│   │   ├── migration.md
│   │   ├── test.md
│   │   ├── quality.md
│   │   ├── feature.md
│   │   ├── docker.md
│   │   └── setup.md
│   └── skills/                # 6 specialized skills
│       ├── video-processing/
│       ├── database-design/
│       ├── api-design/
│       ├── security-review/
│       ├── frontend-architecture/
│       └── performance-optimization/
├── backend/                   # Python FastAPI
├── frontend/                  # Next.js 14 TypeScript
├── docker-compose.yml
├── PRD.md                     # Product requirements
└── README.md                  # Project README
```

## Tech Stack

**Backend:**
- FastAPI + Python 3.11+
- PostgreSQL 15 + SQLModel
- Redis 7 + ARQ
- PyAV, FFmpeg, OpenAI Whisper
- AWS S3 + CloudFront

**Frontend:**
- Next.js 14 + App Router
- TypeScript + Shadcn UI
- Remotion, Video.js, React-Konva
- Wavesurfer.js

**Infrastructure:**
- Docker + Docker Compose
- GitHub Actions
- AWS (S3, CloudFront, EC2/ECS)

## MVP Features (MUST HAVE)

Track progress in [TASKS.md](TASKS.md):

1. 🔴 User Authentication (Email + Google OAuth)
2. 🔴 Video Upload (S3 presigned URLs, 2GB limit)
3. 🔴 Automatic Transcription (OpenAI Whisper)
4. 🔴 Silence Removal (Audio analysis, configurable)
5. 🔴 Keyword Search & Clipping (Full-text search)
6. 🔴 Timeline Editor (Waveform, drag-drop)
7. 🔴 Video Export (720p/1080p, multiple clips)
8. 🔴 Dashboard (Video management)

## Getting Help

### In this directory:

1. **CLAUDE.md** - How to develop (patterns, tech stack)
2. **SETUP-GUIDE.md** - How to use Claude Code tools
3. **TASKS.md** - What to build next

### Ask Claude:

```
"How do I implement video transcription?"
→ Uses video-processing skill

"Show me how to create a new API endpoint"
→ Uses api-design skill

"What's the next feature to implement?"
→ Check TASKS.md for 🔴 Not Started items
```

### External Resources:

- **FastAPI:** https://fastapi.tiangolo.com
- **Next.js 14:** https://nextjs.org/docs
- **Shadcn UI:** https://ui.shadcn.com
- **Claude Code Docs:** https://code.claude.com/docs

## Quick Reference Card

| Task | Command |
|------|---------|
| Start development | `/setup` |
| Implement feature | `/feature "name"` |
| Create API | `/api name` |
| Create component | `/component Name` |
| Database change | `/migration "desc"` |
| Run tests | `/test all` |
| Code quality | `/quality` |
| Docker start | `/docker up` |
| Check tasks | Open `TASKS.md` |
| Need help | Ask Claude + mention skill |

## Next Steps

### First Time Setup:

1. ✅ You're here - `.claude/` directory is set up
2. 📖 Read [SETUP-GUIDE.md](SETUP-GUIDE.md)
3. 🛠️ Run `/setup` to initialize environment
4. 📋 Open [TASKS.md](TASKS.md) to see what to build
5. 🚀 Start with `/feature "User Authentication"`

### Daily Development:

1. Check [TASKS.md](TASKS.md) for current sprint
2. Use `/feature [name]` to implement
3. Use `/quality` before committing
4. Use `/test all` to verify
5. Update [TASKS.md](TASKS.md) status

---

**Version:** 1.0
**Created:** 2025-11-07
**Project:** AI Video Editor
**Tech Stack:** FastAPI + Next.js 14 + PostgreSQL + Redis

For questions or issues with Claude Code setup, refer to [SETUP-GUIDE.md](SETUP-GUIDE.md) or ask Claude directly.
