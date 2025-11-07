# AI Video Clipper - Development Guide

## Project Overview

AI-powered web application for automatic video slicing, silence removal, and highlight generation. Built with FastAPI (Python) backend and Next.js (React TypeScript) frontend.

## Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL 15 with SQLModel
- **Queue**: Redis 7 + ARQ (async task queue)
- **Video Processing**: PyAV, FFmpeg, audio-slicer, PySceneDetect
- **AI/ML**: OpenAI Whisper API, YOLOv8 (optional)
- **Storage**: AWS S3 + CloudFront CDN
- **Auth**: JWT tokens

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **UI Components**: Shadcn/ui (Radix UI + Tailwind CSS)
- **Video**: Remotion Player, Video.js
- **Timeline**: React-Konva
- **Audio**: Wavesurfer.js
- **Real-time**: Server-Sent Events (SSE)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (S3, CloudFront, EC2/ECS)

## Project Structure

```
video-editor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/          # API endpoints
│   │   │   │   ├── auth.py
│   │   │   │   ├── videos.py
│   │   │   │   ├── clips.py
│   │   │   │   └── processing.py
│   │   │   └── deps.py          # Dependencies
│   │   ├── core/
│   │   │   ├── config.py        # Settings
│   │   │   ├── security.py      # Auth utilities
│   │   │   └── db.py            # Database connection
│   │   ├── models/              # SQLModel models
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   └── clip.py
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   │   ├── video_processor.py
│   │   │   ├── transcription.py
│   │   │   ├── silence_remover.py
│   │   │   └── s3_storage.py
│   │   └── worker.py            # ARQ worker
│   ├── tests/
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 14 app directory
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── videos/
│   │   │   │   └── editor/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/              # Shadcn components
│   │   │   ├── video/
│   │   │   ├── timeline/
│   │   │   └── transcript/
│   │   ├── hooks/
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── lib/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── PRD.md
└── README.md
```

## Development Workflow

### 1. Before Starting Any Task

**ALWAYS:**
1. **Read relevant files FIRST** - Use Read tool to understand existing code
2. **Search codebase** - Use Grep/Glob to find related implementations
3. **Create detailed plan** - Use TodoWrite to track multi-step tasks
4. **Ask for approval** - For complex changes, confirm approach with user

### 2. Code Quality Standards

**Backend (Python):**
- Use **Ruff** for linting and formatting
- Use **mypy** for type checking
- Follow **PEP 8** conventions
- Write **type hints** for all functions
- Minimum **80% test coverage**

**Frontend (TypeScript):**
- Use **ESLint** + **Prettier**
- Strict TypeScript mode
- Follow **React best practices** (hooks, composition)
- Component tests with **Vitest**
- E2E tests with **Playwright**

### 3. Implementation Steps

For every feature:

1. **Database First** (if needed)
   - Create migration with Alembic
   - Add SQLModel models
   - Test migration up/down

2. **Backend Implementation**
   - Create service layer (business logic)
   - Add API endpoints
   - Write unit tests
   - Add integration tests

3. **Frontend Implementation**
   - Create TypeScript types
   - Build UI components
   - Connect to API
   - Add loading/error states
   - Write component tests

4. **Testing**
   - Run linters: `ruff check .` (backend), `npm run lint` (frontend)
   - Run type checkers: `mypy app`, `tsc --noEmit`
   - Run tests: `pytest`, `npm test`
   - Manual testing

5. **Documentation**
   - Update relevant comments
   - Add docstrings for complex functions
   - Update API documentation (if endpoints changed)

### 4. Running the Application

**Full stack (Docker):**
```bash
docker-compose up
```

**Backend only:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Worker (for background tasks):**
```bash
cd backend
arq app.worker.WorkerSettings
```

**Frontend only:**
```bash
cd frontend
npm run dev
```

**Database migrations:**
```bash
cd backend
alembic upgrade head  # Apply migrations
alembic revision --autogenerate -m "Description"  # Create new migration
```

**Run tests:**
```bash
# Backend
cd backend
pytest --cov=app --cov-report=html

# Frontend
cd frontend
npm test
npm run test:e2e
```

## Key Technologies & Patterns

### Backend Patterns

**1. Async/Await Everywhere**
```python
async def process_video(video_id: UUID) -> Video:
    async with get_db() as db:
        video = await db.get(Video, video_id)
        # Process...
        await db.commit()
        return video
```

**2. Dependency Injection (FastAPI)**
```python
from fastapi import Depends
from app.api.deps import get_current_user

@router.get("/videos")
async def list_videos(user: User = Depends(get_current_user)):
    return user.videos
```

**3. Background Jobs (ARQ)**
```python
async def transcribe_video(ctx, video_id: str):
    # Long-running task
    await ctx['redis'].set(f"progress:{video_id}", "50")
```

**4. Real-time Progress (SSE)**
```python
from sse_starlette.sse import EventSourceResponse

@router.get("/progress/{job_id}")
async def stream_progress(job_id: str):
    async def event_generator():
        while True:
            progress = await redis.get(f"progress:{job_id}")
            yield {"event": "progress", "data": progress}
    return EventSourceResponse(event_generator())
```

### Frontend Patterns

**1. Server Components by Default (Next.js 14)**
```typescript
// app/videos/page.tsx
export default async function VideosPage() {
  const videos = await fetchVideos(); // Server-side
  return <VideoList videos={videos} />;
}
```

**2. Client Components When Needed**
```typescript
'use client'
import { useState } from 'react';

export function VideoUploader() {
  const [file, setFile] = useState<File | null>(null);
  // Interactive UI
}
```

**3. Shadcn UI Components**
```typescript
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";

<Button variant="outline">Upload</Button>
```

**4. API Client with Error Handling**
```typescript
async function uploadVideo(file: File) {
  try {
    const { uploadUrl } = await api.post('/upload/presigned-url');
    await fetch(uploadUrl, { method: 'PUT', body: file });
  } catch (error) {
    toast.error('Upload failed');
  }
}
```

## Security Checklist

- [ ] HTTPS only in production
- [ ] JWT tokens with 30-minute expiration
- [ ] Refresh tokens for longer sessions
- [ ] Rate limiting (5 uploads/hour per user)
- [ ] File type validation (video formats only)
- [ ] File size limits (2GB max)
- [ ] CORS whitelist (no wildcard in production)
- [ ] SQL injection protection (SQLModel parameterized queries)
- [ ] XSS protection (React auto-escaping)
- [ ] S3 presigned URLs with expiration
- [ ] Environment variables for secrets (never commit)

## Performance Guidelines

**Backend:**
- Use **connection pooling** for database (SQLAlchemy async pool)
- **Cache** frequently accessed data in Redis
- **Offload** heavy processing to ARQ workers
- **Stream** large files (don't load into memory)
- **Optimize** database queries (use indexes, avoid N+1)

**Frontend:**
- Use Next.js **Image component** for optimization
- **Lazy load** timeline/editor components
- **Debounce** search and user inputs
- **Virtualize** long lists (react-window)
- **Code split** routes automatically (Next.js)

**Video Processing:**
- Use **PyAV** for performance-critical operations
- **Parallel processing** where possible
- **Stream** processing (don't load entire video)
- **GPU acceleration** for ML models (YOLOv8)

## Common Commands

```bash
# Install dependencies
cd backend && pip install -e ".[dev]"
cd frontend && npm install

# Format code
cd backend && ruff format .
cd frontend && npm run format

# Type check
cd backend && mypy app
cd frontend && tsc --noEmit

# Run linters
cd backend && ruff check .
cd frontend && npm run lint

# Database
cd backend && alembic upgrade head

# Reset database (dev only)
docker-compose down -v && docker-compose up -d db

# View logs
docker-compose logs -f backend
docker-compose logs -f worker

# Access database
docker-compose exec db psql -U postgres videodb
```

## Troubleshooting

**Backend won't start:**
- Check database is running: `docker-compose ps`
- Check migrations applied: `alembic current`
- Check environment variables: `.env` file exists

**Worker not processing:**
- Check Redis is running: `docker-compose ps redis`
- Check worker logs: `docker-compose logs worker`
- Check job queue: `redis-cli KEYS "arq:*"`

**Frontend build fails:**
- Clear `.next`: `rm -rf .next`
- Reinstall deps: `rm -rf node_modules && npm install`
- Check TypeScript errors: `tsc --noEmit`

**Video upload fails:**
- Check S3 credentials in `.env`
- Check CORS settings on S3 bucket
- Check file size limits

## Resources

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com
- Next.js 14: https://nextjs.org/docs
- Shadcn/ui: https://ui.shadcn.com
- Remotion: https://remotion.dev
- SQLModel: https://sqlmodel.tiangolo.com

**API Documentation:**
- OpenAI Whisper: https://platform.openai.com/docs/guides/speech-to-text
- AWS S3: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html

## Contact & Support

For questions during development:
1. Check this CLAUDE.md file
2. Check PRD.md for product requirements
3. Check inline code comments
4. Ask the user for clarification

## Notes for Claude

- **Always read files before editing** - Never assume file structure
- **Test after changes** - Run relevant tests
- **Commit often** - Small, focused commits
- **Clear messages** - Descriptive commit messages
- **Ask when uncertain** - Better to clarify than assume
- **Security first** - Always validate user input
- **Performance matters** - Consider scalability
- **User experience** - Add loading states, error handling
