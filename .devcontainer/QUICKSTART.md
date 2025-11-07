# 🚀 AI Video Clipper - Devcontainer Quick Start

Welcome to your pre-configured development environment! Everything you need is already set up.

## ✅ First Steps

### 1. Check Your Environment
```bash
# Verify Python
python --version  # Should be 3.11+

# Verify Node.js
node --version    # Should be 20.x

# Verify services
pg_isready -h localhost -p 5432 -U postgres
redis-cli ping
```

### 2. Configure Environment Variables
```bash
# Edit .env with your credentials
nano .env

# At minimum, update:
# - OPENAI_API_KEY (for Whisper transcription)
# - AWS credentials (if using S3)
```

### 3. Start Development

**Option A: Run services directly (recommended for development)**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Worker:
```bash
cd backend
source venv/bin/activate
arq app.worker.WorkerSettings
```

Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

**Option B: Use docker-compose**
```bash
docker-compose up backend worker frontend
```

### 4. Access Your App
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

## 📋 Common Tasks

### Backend Development
```bash
# Navigate to backend
cd backend

# Activate virtual environment (ALWAYS do this first!)
source venv/bin/activate

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy app

# Create database migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Frontend Development
```bash
# Navigate to frontend
cd frontend

# Run dev server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Format code
npm run format

# Lint
npm run lint

# Type check
npm run type-check

# Build for production
npm run build
```

### Database Operations
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d videodb

# Useful psql commands:
# \dt          - List tables
# \d+ users    - Describe 'users' table
# \q           - Quit

# Use Redis CLI
redis-cli
# > PING
# > KEYS *
# > QUIT
```

### Docker Commands
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Rebuild a service
docker-compose up --build backend

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️  deletes data!)
docker-compose down -v
```

## 🎯 Slash Commands (Claude Code)

The project includes custom slash commands for common workflows:

```bash
/setup              # Initialize development environment
/test [target]      # Run tests (backend/frontend/all)
/api [name]         # Create new API endpoint with tests
/component [name]   # Create new React component
/migration [desc]   # Create database migration
/feature [name]     # Implement full-stack feature
/docker [cmd]       # Docker operations
/quality            # Run all code quality checks
```

## 🛠️ VS Code Tips

### Keyboard Shortcuts
- `Cmd/Ctrl + Shift + P` - Command Palette
- `Cmd/Ctrl + `` - Toggle Terminal
- `F5` - Start Debugging
- `Cmd/Ctrl + Shift + F` - Search in Files

### Debugging

**Debug Backend:**
1. Set breakpoint in Python file (click left of line number)
2. Press `F5` → Select "Python: FastAPI"
3. Make API request to trigger breakpoint

**Debug Frontend:**
1. Set breakpoint in TypeScript file
2. Press `F5` → Select "Next.js: debug server-side"
3. Visit page to trigger breakpoint

### Useful Extensions

- **SQLTools** - Query your database directly
  - Click elephant icon in sidebar
  - Select "videodb" connection
  - Write and run SQL queries

- **REST Client** - Test APIs without leaving VS Code
  - Create a `.http` file
  - Write requests, click "Send Request"

- **GitLens** - Enhanced Git features
  - View file history
  - See who changed what and when

## 🔍 Troubleshooting

### "Module not found" in Python
```bash
cd backend
source venv/bin/activate  # Always activate venv first!
pip install -r requirements.txt
```

### "Cannot find module" in Node.js
```bash
cd frontend
rm -rf node_modules
npm install
```

### Database connection errors
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Start database if stopped
docker-compose up -d db

# Check if migrations are applied
cd backend && source venv/bin/activate
alembic current
alembic upgrade head
```

### Port already in use
```bash
# Find what's using the port
lsof -i :8000  # or :3000, :5432, etc.

# Kill the process (replace PID)
kill -9 <PID>

# Or stop local services
brew services stop postgresql  # macOS
brew services stop redis
```

### Devcontainer won't start
1. Check Docker Desktop is running
2. Command Palette → "Dev Containers: Rebuild Container"
3. Check docker-compose logs: `docker-compose logs`

## 📚 Next Steps

1. ✅ Read **[.claude/CLAUDE.md](../.claude/CLAUDE.md)** - Complete development guide
2. ✅ Read **[.claude/SETUP-GUIDE.md](../.claude/SETUP-GUIDE.md)** - Slash commands & skills
3. ✅ Check **[.claude/TASKS.md](../.claude/TASKS.md)** - Features to implement
4. ✅ Review **[PRD.md](../PRD.md)** - Product requirements

## 💡 Pro Tips

1. **Always activate venv** when working with backend Python code
2. **Use `--reload` flag** for FastAPI to enable hot reloading
3. **Keep terminals organized** - one for backend, one for worker, one for frontend
4. **Check API docs** at http://localhost:8000/docs for interactive testing
5. **Use `.http` files** to save common API requests
6. **Commit often** with clear messages
7. **Run tests before committing** to catch issues early
8. **Use type hints** in Python and TypeScript for better IDE support

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com
- **Next.js 14**: https://nextjs.org/docs
- **SQLModel**: https://sqlmodel.tiangolo.com
- **Shadcn/ui**: https://ui.shadcn.com
- **PyAV**: https://pyav.org
- **Alembic**: https://alembic.sqlalchemy.org

---

**Need help?** Check the README files or ask your team! Happy coding! 🎉
