# Agent OS Knowledge Base

**Last Updated:** November 7, 2025  
**Purpose:** Comprehensive knowledge base for Agent OS to understand project context, conventions, and workflows

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Workflows](#development-workflows)
3. [Architecture Patterns](#architecture-patterns)
4. [Code Quality Standards](#code-quality-standards)
5. [Common Tasks & Commands](#common-tasks--commands)
6. [Best Practices](#best-practices)
7. [Project Structure](#project-structure)
8. [Key Conventions](#key-conventions)

---

## Project Overview

### Product: AI Video Clipper

**Mission:** Transform hours of manual video editing into minutes of AI-powered automation.

**Core Features:**
- Automatic video transcription with timestamps
- Silence removal
- Keyword-based clipping
- Timeline editor with waveform
- Video export (720p/1080p)

**Current Status:** MVP Phase 1 (Foundation) - ~40% complete
- ✅ Backend authentication system
- ✅ Basic project infrastructure
- 🔄 Frontend authentication UI
- 🔴 Core video processing features

**Tech Stack:**
- **Backend:** FastAPI (Python 3.11+), PostgreSQL 15, Redis 7, ARQ
- **Frontend:** Next.js 14 (App Router), TypeScript, Shadcn/ui
- **Infrastructure:** Docker Compose, AWS S3, CloudFront
- **AI/ML:** OpenAI Whisper API

---

## Development Workflows

### Standard Feature Implementation Flow

1. **Check Requirements**
   - Read `PRD.md` for feature specifications
   - Check `.claude/TASKS.md` for status and dependencies
   - Review `agent-os/product/roadmap.md` for phase context

2. **Plan Implementation**
   - Use TodoWrite for multi-step tasks
   - Follow order: Database → Backend → Frontend → Tests
   - Consider dependencies and blockers

3. **Implement**
   - **Database:** Create migration, update SQLModel models
   - **Backend:** Service layer → API routes → Tests
   - **Frontend:** Types → Components → API integration → Tests

4. **Quality Checks**
   ```bash
   # Backend
   cd backend && ruff format . && ruff check . && mypy app
   
   # Frontend
   cd frontend && npm run format && npm run lint && npx tsc --noEmit
   ```

5. **Testing**
   ```bash
   # Backend
   cd backend && pytest --cov=app
   
   # Frontend
   cd frontend && npm test
   ```

6. **Update Documentation**
   - Update `.claude/TASKS.md` status
   - Add comments for complex logic
   - Update relevant docs

### Using Agent OS Commands

**Available Commands:**
- `/plan-product` - Create/update product documentation
- `/shape-spec` - Gather requirements and create spec
- `/write-spec` - Write detailed specification document
- `/create-tasks` - Generate implementation tasks from spec
- `/implement-tasks` - Implement tasks systematically
- `/orchestrate-tasks` - Coordinate multiple tasks

**Workflow:**
1. Plan product → `/plan-product`
2. Shape spec → `/shape-spec [feature-name]`
3. Write spec → `/write-spec`
4. Create tasks → `/create-tasks`
5. Implement → `/implement-tasks`

---

## Architecture Patterns

### Backend: FastAPI Async Patterns

**Dependency Injection:**
```python
from fastapi import Depends
from app.api.deps import get_current_user, get_db

@router.get("/videos")
async def list_videos(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Use db and user here
    pass
```

**Database Access (SQLModel + AsyncPG):**
```python
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

async def get_video(db: AsyncSession, video_id: UUID) -> Video | None:
    result = await db.execute(select(Video).where(Video.id == video_id))
    return result.scalar_one_or_none()
```

**Service Layer Pattern:**
- Business logic in `app/services/`
- API routes call services, not direct DB access
- Services handle validation and error handling

**Background Jobs (ARQ):**
```python
# In worker.py
async def process_video(ctx, video_id: str):
    # Long-running task
    await ctx['redis'].set(f"progress:{video_id}", "50")
    # Process video...
    return {"status": "complete"}

# Enqueue job from API
await redis.enqueue_job('process_video', video_id=str(video.id))
```

### Frontend: Next.js 14 Patterns

**Server Components (Default):**
```typescript
// app/videos/page.tsx
export default async function VideosPage() {
  // Fetch data on server
  const videos = await fetchVideos();
  return <VideoList videos={videos} />;
}
```

**Client Components (When Needed):**
```typescript
'use client'
import { useState } from 'react';

export function VideoUploader() {
  const [file, setFile] = useState<File | null>(null);
  // Interactive UI with hooks
}
```

**API Client Pattern:**
- Centralized API client in `src/lib/api.ts`
- Error handling wrapper
- Authentication interceptors
- Type-safe request/response

**State Management:**
- Server state: React Server Components + fetch
- Client state: Zustand for global state
- Form state: React Hook Form
- URL state: Next.js searchParams

---

## Code Quality Standards

### Backend (Python)

**Linting & Formatting:**
- **Ruff**: Fast linter and formatter
- **MyPy**: Static type checking (strict mode)
- **Line Length**: 100 characters
- **Type Hints**: Required on all functions

**Testing:**
- **Framework**: pytest with asyncio support
- **Coverage Target**: 80%+
- **Test Structure**: Unit tests + integration tests
- **Fixtures**: Use pytest fixtures for common setup

**Code Style:**
- Follow PEP 8 with Ruff modifications
- Use async/await for all I/O operations
- Type hints required
- Docstrings for public functions/classes

### Frontend (TypeScript)

**Linting & Formatting:**
- **ESLint**: With Next.js config
- **Prettier**: Code formatting
- **TypeScript**: Strict mode enabled

**Testing:**
- **Unit Tests**: Vitest
- **E2E Tests**: Playwright
- **Component Tests**: React Testing Library

**Code Style:**
- Use Server Components by default
- Client Components only when needed
- TypeScript strict mode
- Meaningful component names

---

## Common Tasks & Commands

### Development Environment

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up db redis
docker-compose up backend worker
docker-compose up frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f worker

# Stop services
docker-compose down

# Reset database (WARNING: deletes data)
docker-compose down -v
```

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend locally
uvicorn app.main:app --reload --port 8000

# Run worker locally
arq app.worker.WorkerSettings

# Database migrations
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "Message" # Create migration
alembic downgrade -1                          # Rollback

# Code quality
ruff format .                # Format code
ruff check .                 # Lint
ruff check . --fix          # Auto-fix
mypy app                     # Type check

# Testing
pytest                       # Run all tests
pytest tests/test_auth.py    # Specific file
pytest -v                    # Verbose
pytest --cov=app             # With coverage
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run frontend locally
npm run dev                  # Dev server (http://localhost:3000)
npm run build                # Production build
npm start                    # Run production build

# Code quality
npm run lint                 # ESLint
npm run format               # Prettier
npx tsc --noEmit             # Type check

# Testing
npm test                     # Vitest unit tests
npm run test:e2e            # Playwright E2E tests
```

### Database Access

```bash
# Connect to database
docker-compose exec db psql -U postgres videodb

# Run SQL query
echo "SELECT * FROM users;" | docker-compose exec -T db psql -U postgres videodb

# Check migration status
docker-compose exec backend alembic current
```

---

## Best Practices

### Token Efficiency

**DO:**
- ✅ Use Agent OS commands for structured workflows
- ✅ Reference specific files when you know what you need
- ✅ Use TodoWrite for complex, multi-step tasks
- ✅ Let skills activate automatically based on context

**DON'T:**
- ❌ Explore entire codebase at once
- ❌ Read files unnecessarily
- ❌ Repeat information already documented
- ❌ Run tools that aren't needed

### Security

**Always:**
- Validate all user inputs (use Pydantic schemas)
- Use parameterized queries (SQLModel handles this)
- JWT tokens with expiration (30 minutes)
- Rate limiting on uploads (5 per hour per user)
- File type validation (video formats only)
- File size limits (2GB max)
- HTTPS only in production
- CORS whitelist (no wildcard in production)
- S3 presigned URLs with expiration

### Performance

**Backend:**
- Use async/await for all I/O operations
- Offload heavy processing to ARQ workers
- Use database connection pooling
- Cache frequently accessed data in Redis
- Stream large files (don't load into memory)
- Use indexes on frequently queried columns

**Frontend:**
- Server Components by default
- Client Components only when needed
- Lazy load heavy components
- Debounce search inputs
- Virtualize long lists
- Optimize images with Next.js Image

**Video Processing:**
- Use PyAV for performance-critical operations
- Stream processing (chunk-based)
- Parallel processing where possible
- Monitor memory usage

### Error Handling

**Backend:**
- Use FastAPI exception handlers
- Return appropriate HTTP status codes
- Log errors with context
- Don't expose internal errors to clients

**Frontend:**
- Handle API errors gracefully
- Show user-friendly error messages
- Provide retry mechanisms
- Log errors for debugging

---

## Project Structure

```
potential-octo-computing-machine/
├── agent-os/                    # Agent OS configuration
│   ├── commands/               # Agent OS commands
│   ├── standards/              # Coding standards
│   ├── product/                # Product documentation
│   │   ├── mission.md
│   │   ├── roadmap.md
│   │   ├── tech-stack.md
│   │   └── analysis.md
│   └── knowledge.md            # This file
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── core/               # Config, DB, security
│   │   ├── models/             # SQLModel models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   ├── main.py             # FastAPI app
│   │   └── worker.py           # ARQ worker
│   ├── tests/                  # Backend tests
│   └── alembic/                # Migrations
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js app directory
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities
│   │   └── types/              # TypeScript types
│   └── public/                 # Static files
├── .claude/                    # Claude Code setup
│   ├── CLAUDE.md               # Development guide
│   ├── SETUP-GUIDE.md          # Claude Code guide
│   ├── TASKS.md                # Feature tracking
│   ├── commands/               # Slash commands
│   └── skills/                 # Claude skills
├── docker-compose.yml          # Docker services
├── PRD.md                      # Product requirements
└── README.md                   # Project README
```

---

## Key Conventions

### Naming Conventions

**Backend (Python):**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Frontend (TypeScript):**
- Files: `PascalCase.tsx` (components), `camelCase.ts` (utilities)
- Components: `PascalCase`
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Types/Interfaces: `PascalCase`

**Database:**
- Tables: `plural_snake_case` (e.g., `users`, `videos`)
- Columns: `snake_case`
- Indexes: `idx_table_column`

**API Endpoints:**
- RESTful: `/api/resource` (plural nouns)
- Nested: `/api/resource/{id}/sub-resource`
- Query params: `?page=1&limit=20&sort=created_at`

### File Organization

**Backend:**
- One class per file
- Services in `app/services/`
- Routes in `app/api/routes/`
- Models in `app/models/`
- Schemas in `app/schemas/`

**Frontend:**
- One component per file
- Components in `src/components/`
- Pages in `src/app/`
- Utilities in `src/lib/`
- Types in `src/types/`

### Git Workflow

**Branches:**
- `main` - Production-ready code
- `feature/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `refactor/component-name` - Refactoring

**Commits:**
- Use conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Clear, descriptive messages
- Reference issue numbers if applicable

### Documentation

**Code Comments:**
- Docstrings for public functions/classes
- Inline comments for complex logic
- TODO comments for future improvements

**Documentation Files:**
- `PRD.md` - Product requirements
- `.claude/TASKS.md` - Feature tracking
- `agent-os/product/*.md` - Product documentation
- `README.md` - Project overview
- `.claude/CLAUDE.md` - Development guide

---

## Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)
- `JWT_SECRET_KEY` - JWT signing key

**For Production:**
- `OPENAI_API_KEY` - OpenAI API key (Whisper)
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS secret
- `S3_BUCKET` - S3 bucket name
- `AWS_REGION` - AWS region (default: us-east-1)
- `CLOUDFRONT_DOMAIN` - CloudFront distribution domain

**Development:**
- `ENVIRONMENT` - `development` or `production`
- `DEBUG` - `true` or `false`
- `ALLOWED_ORIGINS` - CORS allowed origins

---

## Common Issues & Solutions

### Backend Won't Start
```bash
# Check database is running
docker-compose ps db

# Check migrations applied
docker-compose exec backend alembic current

# Check environment variables
cat .env
```

### Worker Not Processing Jobs
```bash
# Check Redis is running
docker-compose ps redis

# Check worker logs
docker-compose logs -f worker

# Check job queue
docker-compose exec redis redis-cli KEYS "arq:*"
```

### Frontend Build Fails
```bash
# Clear build cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules && npm install

# Check TypeScript errors
npx tsc --noEmit
```

### Database Connection Issues
```bash
# Test connection
docker-compose exec db psql -U postgres videodb -c "\dt"

# Reset database (WARNING: deletes data)
docker-compose down -v && docker-compose up -d db

# Apply migrations
docker-compose exec backend alembic upgrade head
```

---

## Resources

### Project Documentation
- `PRD.md` - Product requirements and feature specs
- `.claude/TASKS.md` - Current feature status
- `.claude/CLAUDE.md` - Development guidelines
- `.claude/SETUP-GUIDE.md` - Claude Code setup
- `agent-os/product/` - Product documentation

### External Resources
- **FastAPI:** https://fastapi.tiangolo.com
- **Next.js 14:** https://nextjs.org/docs
- **Shadcn/ui:** https://ui.shadcn.com
- **SQLModel:** https://sqlmodel.tiangolo.com
- **OpenAI Whisper:** https://platform.openai.com/docs/guides/speech-to-text

---

## Notes for Agent OS

### When Working on Tasks

1. **Read First** - Always read relevant files before making changes
2. **Follow Patterns** - Match existing code patterns and conventions
3. **Use Standards** - Follow `agent-os/standards/` guidelines
4. **Test Changes** - Run tests after making changes
5. **Update Docs** - Update relevant documentation
6. **Check Dependencies** - Verify dependencies in `.claude/TASKS.md`

### When Creating Specs

1. **Reference Product Docs** - Use `agent-os/product/` for context
2. **Follow Standards** - Use `agent-os/standards/` for conventions
3. **Search Codebase** - Find reusable components/patterns
4. **Document Decisions** - Explain architectural choices

### When Implementing Features

1. **Database First** - Create models and migrations
2. **Backend Second** - Implement services and APIs
3. **Frontend Third** - Build UI components
4. **Tests Last** - Write comprehensive tests
5. **Quality Check** - Run linters and formatters

---

**This knowledge base should be referenced when:**
- Understanding project context
- Following development workflows
- Making architectural decisions
- Implementing new features
- Debugging issues
- Reviewing code

