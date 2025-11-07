---
description: Create a new FastAPI endpoint with tests
argument-hint: [endpoint-name]
---

Create a new FastAPI endpoint named "$1" following these steps:

1. **Read existing code** - Check backend/app/api/routes/ for similar endpoints
2. **Create service layer** - Add business logic in backend/app/services/$1.py with:
   - Async functions
   - Type hints for all parameters and returns
   - Proper error handling
   - Docstrings for complex logic

3. **Create route** - Add endpoint in backend/app/api/routes/$1.py with:
   - FastAPI router
   - Pydantic schemas for request/response
   - Dependency injection for auth/db
   - Proper HTTP status codes
   - OpenAPI documentation

4. **Write tests** - Create backend/tests/test_$1.py with:
   - Unit tests for service layer
   - Integration tests for endpoints
   - Minimum 80% coverage

5. **Verify quality**:
   - Run type check: `cd backend && mypy app`
   - Run linter: `cd backend && ruff check .`
   - Run tests: `cd backend && pytest tests/test_$1.py -v`

Follow patterns from existing routes and maintain consistency with project standards.
