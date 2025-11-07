---
description: Run tests for backend and/or frontend
argument-hint: [backend|frontend|all]
allowed-tools: Bash(pytest:*), Bash(npm:test*), Bash(cd:*)
---

Run tests for $1:

**Backend tests** (if $1 is "backend" or "all"):
```bash
cd backend && pytest --cov=app --cov-report=term-missing -v
```

**Frontend tests** (if $1 is "frontend" or "all"):
```bash
cd frontend && npm test
```

**Full suite** (if $1 is "all" or not specified):
```bash
cd backend && pytest --cov=app --cov-report=html -v
cd frontend && npm test
cd frontend && npm run test:e2e
```

After running tests:
1. Review any failures
2. Check coverage reports (should be >80% for backend)
3. Fix failing tests before committing
4. Update tests if behavior changed intentionally

For specific test files, use pytest or vitest directly with file paths.
