---
description: Run all code quality checks
allowed-tools: Bash(ruff:*), Bash(mypy:*), Bash(npm:*), Bash(cd:*)
---

Run comprehensive code quality checks for the project:

## Backend Quality Checks

1. **Format code**:
   ```bash
   cd backend && ruff format .
   ```

2. **Lint code**:
   ```bash
   cd backend && ruff check . --fix
   ```

3. **Type check**:
   ```bash
   cd backend && mypy app
   ```

## Frontend Quality Checks

1. **Format code**:
   ```bash
   cd frontend && npm run format
   ```

2. **Lint code**:
   ```bash
   cd frontend && npm run lint -- --fix
   ```

3. **Type check**:
   ```bash
   cd frontend && tsc --noEmit
   ```

## Summary

After running all checks:
- Fix any errors that couldn't be auto-fixed
- Review warnings for potential issues
- Ensure all type checks pass
- Commit formatted code changes

Run this before creating PRs to ensure code quality standards are met.
