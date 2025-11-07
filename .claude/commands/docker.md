---
description: Docker operations for the project
argument-hint: [up|down|restart|logs|build]
allowed-tools: Bash(docker:*), Bash(docker-compose:*)
---

Docker operation: $1

**Start services** (if $1 is "up"):
```bash
docker-compose up -d
```

**Stop services** (if $1 is "down"):
```bash
docker-compose down
```

**Restart services** (if $1 is "restart"):
```bash
docker-compose restart
```

**View logs** (if $1 is "logs"):
```bash
docker-compose logs -f --tail=100
```

**Rebuild containers** (if $1 is "build"):
```bash
docker-compose build --no-cache
docker-compose up -d
```

**Full reset** (if $1 is "reset"):
```bash
docker-compose down -v
docker-compose up -d
```

## Service Status
Check running services:
```bash
docker-compose ps
```

## Individual Service Logs
- Backend: `docker-compose logs -f backend`
- Frontend: `docker-compose logs -f frontend`
- Worker: `docker-compose logs -f worker`
- Database: `docker-compose logs -f db`
- Redis: `docker-compose logs -f redis`

## Troubleshooting
- If containers won't start, check `.env` file exists
- For database issues, try: `docker-compose down -v` (WARNING: deletes data)
- For build issues, try: `docker-compose build --no-cache`
