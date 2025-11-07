# AI Video Editor

AI-powered web application for automatic video slicing, silence removal, and highlight generation.

## Overview

Transform hours of manual video editing into minutes of AI-powered automation. This application automatically transcribes videos, removes silence, finds highlights, and generates clips ready for social media.

**Key Features:**
- 🎙️ Automatic transcription with word-level timestamps
- ✂️ Smart silence removal
- 🔍 Keyword-based clipping
- ⚡ Timeline editor with real-time preview
- 📤 Export in multiple resolutions (720p, 1080p)

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **Queue**: Redis 7 + ARQ
- **Video Processing**: PyAV, FFmpeg, PySceneDetect
- **AI**: OpenAI Whisper API
- **Storage**: AWS S3 + CloudFront

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI**: Shadcn/ui (Radix UI + Tailwind CSS)
- **Video**: Remotion Player, Video.js
- **Timeline**: React-Konva
- **Audio Viz**: Wavesurfer.js

### Infrastructure
- **Containers**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (S3, CloudFront, EC2/ECS)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd potential-octo-computing-machine
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` and add your API keys:
   - `OPENAI_API_KEY` - OpenAI API key for Whisper
   - `AWS_ACCESS_KEY_ID` - AWS credentials for S3
   - `AWS_SECRET_ACCESS_KEY` - AWS secret key
   - `S3_BUCKET` - Your S3 bucket name

### Run with Docker Compose

Start all services:
```bash
docker-compose up
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Worker

```bash
cd backend
source venv/bin/activate
arq app.worker.WorkerSettings
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
video-editor/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # Configuration, database
│   │   ├── models/         # SQLModel database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── main.py         # FastAPI app
│   │   └── worker.py       # ARQ background worker
│   ├── tests/              # Backend tests
│   └── alembic/            # Database migrations
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js 14 app directory
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   └── public/            # Static files
├── .claude/
│   └── CLAUDE.md          # Development guide for Claude
├── PRD.md                 # Product Requirements Document
├── docker-compose.yml     # Docker orchestration
└── README.md             # This file
```

## Development Workflow

1. **Read the guides:**
   - [`.claude/CLAUDE.md`](.claude/CLAUDE.md) - Development guidelines
   - [`PRD.md`](PRD.md) - Product requirements

2. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

3. **Make changes:**
   - Backend: Edit files in `backend/app/`
   - Frontend: Edit files in `frontend/src/`

4. **Test your changes:**
```bash
# Backend tests
cd backend
pytest --cov=app

# Frontend tests
cd frontend
npm test
```

5. **Lint and format:**
```bash
# Backend
cd backend
ruff check .
ruff format .
mypy app

# Frontend
cd frontend
npm run lint
npm run format
```

6. **Commit and push:**
```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

## Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1  # Rollback one migration
```

## Testing

### Backend Tests

```bash
cd backend
pytest                          # Run all tests
pytest tests/test_auth.py       # Run specific test file
pytest --cov=app                # With coverage
pytest -v                       # Verbose output
```

### Frontend Tests

```bash
cd frontend
npm test                        # Unit tests (Vitest)
npm run test:e2e               # E2E tests (Playwright)
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

See deployment guides:
- [Backend Deployment](backend/README.md) (to be created)
- [Frontend Deployment](frontend/README.md) (to be created)

## Architecture

### System Overview

```
┌────────────┐
│   Client   │
│  (Browser) │
└─────┬──────┘
      │
      ▼
┌─────────────┐
│  Next.js    │
│  Frontend   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   FastAPI   │
│   Backend   │
└─────┬───────┘
      │
  ┌───┴────┐
  ▼        ▼
┌────┐  ┌─────┐
│ DB │  │Redis│
└────┘  └──┬──┘
           │
           ▼
      ┌────────┐
      │  ARQ   │
      │Worker  │
      └────┬───┘
           │
           ▼
      ┌────────┐
      │  S3    │
      │Storage │
      └────────┘
```

### Processing Flow

1. **Upload**: Client → Frontend → S3 (presigned URL)
2. **Transcode**: ARQ Worker → FFmpeg → S3
3. **Transcribe**: ARQ Worker → Whisper API → Database
4. **Process**: User edits → Timeline → Export job
5. **Export**: ARQ Worker → FFmpeg → S3 → Download

## Environment Variables

See [`.env.example`](.env.example) for all available options.

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key

**Optional:**
- `AWS_ACCESS_KEY_ID` - AWS credentials (if using S3)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `S3_BUCKET` - S3 bucket name
- `CLOUDFRONT_DOMAIN` - CloudFront distribution

## Troubleshooting

### Backend won't start
- Check database is running: `docker-compose ps db`
- Check migrations: `alembic current`
- Check logs: `docker-compose logs backend`

### Frontend build fails
- Clear cache: `rm -rf .next node_modules`
- Reinstall: `npm install`
- Check TypeScript: `tsc --noEmit`

### Worker not processing
- Check Redis: `docker-compose ps redis`
- Check worker logs: `docker-compose logs worker`
- Check job queue: `redis-cli KEYS "arq:*"`

### Video upload fails
- Check S3 credentials in `.env`
- Check bucket CORS settings
- Check file size limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Documentation](https://nextjs.org/docs)
- [Shadcn/ui Components](https://ui.shadcn.com)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)

## Support

For issues and questions:
- GitHub Issues: [Create an issue](../../issues)
- Documentation: See `.claude/CLAUDE.md` and `PRD.md`

---

**Built with ❤️ using FastAPI, Next.js, and AI**
