---
description: Implement a full-stack feature
argument-hint: [feature-name]
---

Implement full-stack feature: "$ARGUMENTS"

Follow the complete development workflow:

## 1. Planning Phase
- Read PRD.md to understand project requirements
- Search codebase for related functionality
- Create detailed implementation plan with TodoWrite
- Ask for user approval if approach is unclear

## 2. Database Layer (if needed)
- Design database schema
- Update SQLModel models in backend/app/models/
- Create migration: `/migration $ARGUMENTS`
- Test migration up/down

## 3. Backend Implementation
- Create service layer in backend/app/services/
  - Business logic with async/await
  - Type hints for all functions
  - Error handling
  - Docstrings
- Create API routes in backend/app/api/routes/
  - Pydantic schemas for validation
  - Dependency injection
  - Proper status codes
- Write backend tests (>80% coverage)

## 4. Frontend Implementation
- Define TypeScript types in frontend/src/types/
- Create UI components in frontend/src/components/
  - Use Shadcn UI components
  - Server Components by default
  - Client Components only when needed
- Create API client functions in frontend/src/services/
- Add loading and error states
- Write component tests

## 5. Integration
- Connect frontend to backend API
- Test end-to-end flow manually
- Handle edge cases and errors
- Add loading states for async operations

## 6. Quality Assurance
- Run `/quality` to check code standards
- Run `/test all` to verify all tests pass
- Manual testing of the complete feature
- Update documentation if needed

## 7. Review
- Review all changes made
- Ensure security best practices followed
- Check performance implications
- Verify user experience is smooth

Ask for user feedback before marking feature complete.
