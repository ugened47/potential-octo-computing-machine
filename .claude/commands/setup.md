---
description: Set up development environment
---

Set up the complete development environment for AI Video Editor:

## 1. Prerequisites Check
Verify required tools are installed:
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

## 2. Clone and Environment Setup

Create `.env` file from template:
```bash
cp .env.example .env
```

Update `.env` with:
- Database credentials
- Redis URL
- AWS S3 credentials
- OpenAI API key
- JWT secret

## 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## 4. Frontend Setup

```bash
cd frontend
npm install
```

## 5. Database Setup

Start database with Docker:
```bash
docker-compose up -d db redis
```

Run migrations:
```bash
cd backend
alembic upgrade head
```

## 6. Verify Installation

**Backend**:
```bash
cd backend && uvicorn app.main:app --reload
```
Visit: http://localhost:8000/docs

**Frontend**:
```bash
cd frontend && npm run dev
```
Visit: http://localhost:3000

**Worker**:
```bash
cd backend && arq app.worker.WorkerSettings
```

## 7. Run Tests

```bash
cd backend && pytest
cd frontend && npm test
```

## 8. Code Quality Setup

Install pre-commit hooks (optional but recommended):
```bash
pip install pre-commit
pre-commit install
```

## Next Steps

- Review CLAUDE.md for development guidelines
- Review PRD.md for product requirements
- Use `/feature [name]` to start implementing features
- Use `/quality` before committing changes

Setup complete! Ready for development.
