# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered web application for automatic video slicing, silence removal, and highlight generation. Built with FastAPI (Python) backend and Next.js 14 (React TypeScript) frontend.

**Current Status:** MVP Phase - Foundation stage (basic project structure in place)

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+) with async/await
- PostgreSQL 15 (SQLModel ORM)
- Redis 7 + ARQ (async task queue)
- PyAV, FFmpeg for video processing
- OpenAI Whisper API for transcription
- AWS S3 for storage

**Frontend:**
- Next.js 14 (App Router)
- TypeScript (strict mode)
- Shadcn/ui (Radix UI + Tailwind CSS)
- React-Konva (timeline), Wavesurfer.js (audio viz), Video.js (player)

**Infrastructure:**
- Docker + Docker Compose
- GitHub Actions (CI/CD)

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── api/routes/          # API endpoints (to implement)
│   ├── core/                # config.py, db.py, security.py
│   ├── models/              # SQLModel database models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   └── worker.py            # ARQ background worker
├── tests/                   # pytest tests
├── alembic/                 # Database migrations
├── pyproject.toml           # Python config (ruff, mypy, pytest)
└── requirements.txt

frontend/
├── src/
│   ├── app/                 # Next.js 14 app directory
│   ├── components/          # React components
│   │   └── ui/             # Shadcn components (to add)
│   ├── lib/                 # Utilities
│   └── types/              # TypeScript types
├── package.json
└── tsconfig.json

.claude/
├── CLAUDE.md               # This file
├── SETUP-GUIDE.md          # Slash commands, skills, workflows
├── TASKS.md                # Feature tracking
├── commands/               # 8 slash commands (use /command)
└── skills/                 # 6 AI skills (auto-activate)

docker-compose.yml          # Services: db, redis, backend, worker, frontend
PRD.md                      # Product requirements
```

## Essential Commands

### Development Environment

```bash
# Start all services (Docker)
docker-compose up

# Start individual services
docker-compose up db redis              # Just infrastructure
docker-compose up backend worker        # Backend + worker
docker-compose up frontend              # Frontend only

# View logs
docker-compose logs -f backend
docker-compose logs -f worker

# Stop all services
docker-compose down

# Reset database (WARNING: deletes all data)
docker-compose down -v
```

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt
# OR with dev tools (ruff, mypy, pytest)
pip install -e ".[dev]"

# Run backend locally (without Docker)
uvicorn app.main:app --reload --port 8000

# Run worker locally
arq app.worker.WorkerSettings

# Database migrations
alembic upgrade head                          # Apply migrations
alembic revision --autogenerate -m "Message" # Create migration
alembic downgrade -1                          # Rollback one migration

# Code quality
ruff format .                # Format code
ruff check .                 # Lint
ruff check . --fix          # Auto-fix issues
mypy app                     # Type check

# Testing
pytest                       # Run all tests
pytest tests/test_auth.py    # Run specific test file
pytest -v                    # Verbose output
pytest --cov=app             # With coverage
pytest --cov=app --cov-report=html  # HTML coverage report
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run frontend locally (without Docker)
npm run dev                  # Dev server (http://localhost:3000)
npm run build                # Production build
npm start                    # Run production build

# Code quality
npm run lint                 # ESLint
npm run format               # Prettier

# Type checking
npx tsc --noEmit

# Testing
npm test                     # Vitest unit tests
npm run test:e2e            # Playwright E2E tests
```

### Database Access

```bash
# Connect to database (when running in Docker)
docker-compose exec db psql -U postgres videodb

# Run SQL query
echo "SELECT * FROM users;" | docker-compose exec -T db psql -U postgres videodb

# Check database status
docker-compose exec backend alembic current
```

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

**Real-time Progress (Server-Sent Events):**
```python
from sse_starlette.sse import EventSourceResponse

@router.get("/progress/{job_id}")
async def stream_progress(job_id: str):
    async def event_generator():
        while True:
            progress = await redis.get(f"progress:{job_id}")
            if progress:
                yield {"event": "progress", "data": progress}
            await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())
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

**Client Components:**
```typescript
'use client'
import { useState } from 'react';

export function VideoUploader() {
  const [file, setFile] = useState<File | null>(null);
  // Interactive UI with hooks
}
```

**API Client with Error Handling:**
```typescript
async function uploadVideo(file: File) {
  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    if (!response.ok) throw new Error('Upload failed');
    return await response.json();
  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
}
```

## Code Quality Standards

### Backend (Python)
- **Linting:** Ruff (configured in pyproject.toml)
- **Type Checking:** mypy strict mode
- **Formatting:** Ruff formatter (100 char line length)
- **Testing:** pytest with asyncio support, 80%+ coverage target
- **Type Hints:** Required on all functions

### Frontend (TypeScript)
- **Linting:** ESLint with Next.js config
- **Type Checking:** TypeScript strict mode
- **Formatting:** Prettier
- **Testing:** Vitest (unit), Playwright (E2E)
- **Conventions:** React hooks, Server Components by default

## Development Workflow

### For Every Feature

1. **Check Requirements**
   - Read PRD.md for feature requirements
   - Check .claude/TASKS.md for status and dependencies

2. **Plan Implementation**
   - Use TodoWrite for multi-step tasks
   - Consider: Database → Backend → Frontend → Tests

3. **Implement**
   - **Database:** Create migration, update models
   - **Backend:** Add service layer, API endpoints, tests
   - **Frontend:** Create types, components, connect API

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
   - Update .claude/TASKS.md status
   - Add comments for complex logic

## Environment Variables

Copy `.env.example` to `.env` and configure:

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)

**For Production:**
- `OPENAI_API_KEY` - OpenAI API key (Whisper)
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS secret
- `S3_BUCKET` - S3 bucket name
- `AWS_REGION` - AWS region (default: us-east-1)

## Slash Commands & Skills

This project includes Claude Code automation:

**Slash Commands:** Use `/command-name` for common workflows
- `/setup` - Initialize development environment
- `/api [name]` - Create FastAPI endpoint with tests
- `/component [name]` - Create React component
- `/migration [description]` - Create database migration
- `/test [backend|frontend|all]` - Run tests
- `/quality` - Run all linters and formatters
- `/feature [name]` - Implement full-stack feature
- `/docker [up|down|logs|etc]` - Docker operations

**Skills:** Auto-activate based on task context
- `video-processing` - FFmpeg, PyAV, video optimization
- `database-design` - PostgreSQL, SQLModel, migrations
- `api-design` - REST, FastAPI, authentication
- `security-review` - OWASP, input validation
- `frontend-architecture` - Next.js, React optimization
- `performance-optimization` - Query optimization, caching

See `.claude/SETUP-GUIDE.md` for detailed usage.

## Common Issues

**Backend won't start:**
```bash
# Check database is running
docker-compose ps db
# Check migrations applied
docker-compose exec backend alembic current
# Check environment variables
cat .env
```

**Worker not processing jobs:**
```bash
# Check Redis is running
docker-compose ps redis
# Check worker logs
docker-compose logs -f worker
# Check job queue
docker-compose exec redis redis-cli KEYS "arq:*"
```

**Frontend build fails:**
```bash
# Clear build cache
rm -rf .next
# Reinstall dependencies
rm -rf node_modules && npm install
# Check TypeScript errors
npx tsc --noEmit
```

**Database connection issues:**
```bash
# Test connection
docker-compose exec db psql -U postgres videodb -c "\dt"
# Reset database (WARNING: deletes data)
docker-compose down -v && docker-compose up -d db
# Apply migrations
docker-compose exec backend alembic upgrade head
```

## Security Checklist

- [ ] Use environment variables for secrets (never commit to git)
- [ ] Validate all user inputs (use Pydantic schemas)
- [ ] Use parameterized queries (SQLModel handles this)
- [ ] JWT tokens with expiration (30 minutes)
- [ ] Rate limiting on uploads (5 per hour per user)
- [ ] File type validation (video formats only)
- [ ] File size limits (2GB max)
- [ ] HTTPS only in production
- [ ] CORS whitelist (no wildcard in production)
- [ ] S3 presigned URLs with expiration

## Performance Guidelines

**Backend:**
- Use async/await for all I/O operations
- Offload heavy processing to ARQ workers
- Use database connection pooling (SQLAlchemy handles this)
- Cache frequently accessed data in Redis
- Stream large files (don't load into memory)
- Use indexes on frequently queried columns

**Frontend:**
- Server Components by default
- Client Components only when needed (interactivity, hooks)
- Next.js Image component for images
- Lazy load heavy components (timeline editor)
- Debounce search inputs
- Virtualize long lists

**Video Processing:**
- Use PyAV for performance-critical operations
- Stream processing (chunk-based, not full file in memory)
- Parallel processing where possible
- Monitor memory usage (video files are large)

## Resources

- **PRD.md** - Product requirements and feature specs
- **.claude/TASKS.md** - Current feature status
- **.claude/SETUP-GUIDE.md** - Slash commands and skills
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Next.js 14 Docs:** https://nextjs.org/docs
- **Shadcn/ui:** https://ui.shadcn.com
- **SQLModel:** https://sqlmodel.tiangolo.com

## Notes for Claude Code

- **Read files first** - Never assume project structure
- **Use slash commands** - Leverage .claude/commands/ for common tasks
- **Track progress** - Use TodoWrite for complex, multi-step features
- **Test after changes** - Run tests before marking tasks complete
- **Security first** - Always validate inputs, never expose secrets
- **Ask when uncertain** - Better to clarify than make assumptions
- **Performance matters** - Video processing is resource-intensive
- **Focus on UX** - Add loading states, error handling, progress indicators
