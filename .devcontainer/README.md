# AI Video Clipper - Dev Container

This devcontainer provides a complete, reproducible development environment for the AI Video Clipper project with all dependencies and tools pre-configured.

## What's Included

### Languages & Runtimes
- **Python 3.11** - Backend development with FastAPI
- **Node.js 20 LTS** - Frontend development with Next.js 14
- **npm, pnpm, yarn** - Package managers

### Development Tools
- **Python Tools**: ruff, mypy, black, pytest, ipython, alembic
- **Node Tools**: ESLint, Prettier, TypeScript
- **Git**: git, git-lfs, GitHub CLI
- **Docker**: Docker-in-Docker support
- **Database Clients**: psql, redis-cli

### System Libraries
- **FFmpeg** - Video/audio processing
- **OpenCV** - Computer vision
- **Audio Libraries** - libsndfile, portaudio
- **Build Tools** - gcc, cmake, pkg-config

### Services (via docker-compose)
- **PostgreSQL 15** - Main database
- **Redis 7** - Cache and message broker

### VS Code Extensions
- Python development (Pylance, Ruff, mypy)
- JavaScript/TypeScript (ESLint, Prettier)
- Database tools (SQLTools)
- Docker support
- Git integration (GitLens)
- And more...

## Getting Started

### Prerequisites
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Opening the Project

1. **Open in VS Code:**
   ```bash
   code /path/to/video-editor
   ```

2. **Open in Container:**
   - VS Code will detect the devcontainer and prompt you to "Reopen in Container"
   - Or use Command Palette (Cmd/Ctrl+Shift+P) → "Dev Containers: Reopen in Container"

3. **Wait for Setup:**
   - First time setup takes 5-10 minutes
   - Subsequent starts are much faster
   - The `post-create.sh` script will:
     - Create `.env` from `.env.example`
     - Install Python dependencies in venv
     - Install Node.js dependencies
     - Run database migrations
     - Create necessary directories

### Development Workflow

#### Backend Development

```bash
# Activate Python virtual environment
cd backend
source venv/bin/activate

# Run FastAPI server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the worker
arq app.worker.WorkerSettings

# Run tests
pytest --cov=app

# Format code
ruff format .

# Type check
mypy app
```

#### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Run Next.js dev server
npm run dev

# Run tests
npm test

# Format code
npm run format

# Lint
npm run lint
```

#### Database Operations

```bash
# Access PostgreSQL
psql -h localhost -U postgres -d videodb

# Create migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

#### Using Docker Compose

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up backend worker frontend

# View logs
docker-compose logs -f backend

# Rebuild services
docker-compose up --build

# Stop services
docker-compose down
```

### Environment Variables

1. The devcontainer automatically creates `.env` from `.env.example`
2. Update `.env` with your actual credentials:
   - AWS credentials (if using S3)
   - OpenAI API key (for Whisper transcription)
   - Database credentials (default: postgres/postgres)

### Accessing Services

Once the container is running:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js app |
| Backend | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| PostgreSQL | localhost:5432 | Database (use psql or DB client) |
| Redis | localhost:6379 | Cache/Queue (use redis-cli) |

### VS Code Features

#### Keyboard Shortcuts
- **Cmd/Ctrl+Shift+P**: Command Palette
- **Cmd/Ctrl+`**: Toggle Terminal
- **F5**: Start debugging (configured for both Python and Node)
- **Shift+F5**: Stop debugging

#### Debugging

**Backend (Python):**
1. Set breakpoints in Python code
2. Press F5 → Select "Python: FastAPI"
3. Debug at http://localhost:8000

**Frontend (Node.js):**
1. Set breakpoints in TypeScript code
2. Press F5 → Select "Next.js: debug server-side"
3. Debug at http://localhost:3000

#### Extensions Usage

- **SQLTools**: Connect to PostgreSQL and run queries
  - Click SQLTools icon in sidebar
  - Use existing "videodb" connection

- **REST Client**: Test API endpoints
  - Create `.http` files with requests
  - Click "Send Request" above requests

- **GitLens**: Advanced Git features
  - View file history, blame, and more
  - Inline git annotations

## Troubleshooting

### Container fails to start

**Check Docker:**
```bash
docker ps
docker-compose ps
```

**View logs:**
```bash
docker-compose logs devcontainer
docker-compose logs db
docker-compose logs redis
```

**Rebuild container:**
- Command Palette → "Dev Containers: Rebuild Container"

### Database connection fails

**Check PostgreSQL is running:**
```bash
pg_isready -h localhost -p 5432 -U postgres
```

**Manually start database:**
```bash
docker-compose up -d db
```

### Python packages not found

**Activate virtual environment:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend dependencies missing

**Reinstall:**
```bash
cd frontend
rm -rf node_modules
npm install
```

### Ports already in use

**Check what's using ports:**
```bash
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

**Stop conflicting services:**
```bash
# Stop local PostgreSQL
brew services stop postgresql  # macOS
sudo systemctl stop postgresql  # Linux

# Stop local Redis
brew services stop redis  # macOS
sudo systemctl stop redis  # Linux
```

### Reset everything

**Complete reset:**
```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Rebuild devcontainer
# Command Palette → "Dev Containers: Rebuild Container"
```

## Customization

### Adding VS Code Extensions

Edit `.devcontainer/devcontainer.json`:
```json
"extensions": [
  "existing-extension-id",
  "your-new-extension-id"
]
```

### Installing Additional Tools

Edit `.devcontainer/Dockerfile`:
```dockerfile
RUN apt-get update && apt-get install -y \
    your-package-here \
    && rm -rf /var/lib/apt/lists/*
```

### Modifying Post-Create Script

Edit `.devcontainer/post-create.sh` to add custom setup steps.

## Best Practices

1. **Use the integrated terminal** - It's pre-configured with correct paths
2. **Commit often** - Container state persists, but not forever
3. **Use virtual environment** - Always activate `backend/venv` for Python work
4. **Check git status** - devcontainer git config is isolated
5. **Update .env** - Don't commit secrets, use environment variables

## Performance Tips

1. **Use volume mounts** - node_modules and .next are in named volumes for speed
2. **Don't sync node_modules** - It's excluded from sync for performance
3. **Limit file watching** - Configure ignore patterns for large directories
4. **Use BuildKit** - Docker BuildKit speeds up builds

## Resources

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose](https://docs.docker.com/compose/)
- [Project CLAUDE.md](../.claude/CLAUDE.md) - Full development guide
- [Project SETUP-GUIDE.md](../.claude/SETUP-GUIDE.md) - Slash commands & skills

## Support

If you encounter issues:
1. Check this README
2. Check `.claude/CLAUDE.md` for project-specific guidance
3. Check container logs: `docker-compose logs devcontainer`
4. Rebuild container if needed
5. Report issues to the team

---

Happy coding! 🚀
