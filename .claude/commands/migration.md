---
description: Create database migration
argument-hint: [description]
---

Create a new database migration for "$ARGUMENTS":

1. **Plan changes** - Determine what database changes are needed:
   - New tables
   - Modified columns
   - New indexes
   - Data migrations

2. **Update models** - Modify SQLModel models in backend/app/models/:
   - Add type hints
   - Define relationships
   - Add constraints
   - Update __tablename__ if needed

3. **Generate migration**:
   ```bash
   cd backend && alembic revision --autogenerate -m "$ARGUMENTS"
   ```

4. **Review migration** - Check generated file in backend/alembic/versions/:
   - Verify upgrade() operations
   - Verify downgrade() operations
   - Add manual changes if autogenerate missed anything
   - Add data migrations if needed

5. **Test migration**:
   - Apply: `cd backend && alembic upgrade head`
   - Verify: Check database schema
   - Test rollback: `cd backend && alembic downgrade -1`
   - Reapply: `cd backend && alembic upgrade head`

6. **Update tests** - Modify tests to work with new schema

Always test both upgrade and downgrade paths!
