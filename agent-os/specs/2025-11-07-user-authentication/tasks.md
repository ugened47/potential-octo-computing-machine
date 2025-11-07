# Task Breakdown: User Authentication

## Overview
Total Tasks: 4 task groups, 20+ sub-tasks

## Task List

### Database Layer

#### Task Group 1: User Model Updates
**Dependencies:** None

- [ ] 1.0 Complete database layer updates
  - [ ] 1.1 Write 2-8 focused tests for User model email_verified field
    - Test email_verified defaults to False
    - Test email_verified can be set to True
    - Test User model with OAuth fields (oauth_id, oauth_provider)
  - [ ] 1.2 Add email_verified field to User model
    - Field: email_verified (bool, default=False, nullable=False)
    - Add to User model in `backend/app/models/user.py`
  - [ ] 1.3 Create migration for email_verified field
    - Add email_verified column to users table
    - Set default to False for existing users
  - [ ] 1.4 Ensure database layer tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify migration runs successfully
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- User model includes email_verified field
- Migration runs successfully
- Existing users have email_verified=False

### Backend API Layer

#### Task Group 2: Password Reset & OAuth Endpoints
**Dependencies:** Task Group 1

- [ ] 2.0 Complete password reset and OAuth API endpoints
  - [ ] 2.1 Write 2-8 focused tests for password reset and OAuth endpoints
    - Test POST /api/auth/forgot-password generates reset token
    - Test POST /api/auth/reset-password validates token and updates password
    - Test POST /api/auth/google/callback handles OAuth flow
    - Test password reset token expiration (1 hour)
  - [ ] 2.2 Implement password reset service methods in AuthService
    - Add forgot_password method: generate JWT reset token, send email
    - Add reset_password method: validate token, update password
    - Use existing JWT functions from security.py for reset tokens
  - [ ] 2.3 Add password reset API endpoints
    - POST /api/auth/forgot-password: Accept email, generate reset token, send email
    - POST /api/auth/reset-password: Accept token and new password, update password
    - Follow existing route pattern from `backend/app/api/routes/auth.py`
  - [ ] 2.4 Implement Google OAuth service method
    - Add google_oauth_callback method: handle OAuth callback, create/update user
    - Store OAuth ID in User.oauth_id field
    - Handle email conflicts (existing email with password auth)
  - [ ] 2.5 Add Google OAuth API endpoint
    - GET /api/auth/google: Redirect to Google OAuth consent screen
    - POST /api/auth/google/callback: Handle OAuth callback, return tokens
    - Follow OAuth 2.0 authorization code flow
  - [ ] 2.6 Add email service integration
    - Create email service utility for sending reset emails
    - Use existing email service pattern (or create simple SMTP service)
    - Send reset link with token in email
  - [ ] 2.7 Ensure API layer tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify password reset flow works end-to-end
    - Verify Google OAuth flow works
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Password reset endpoints work correctly
- Google OAuth endpoints work correctly
- Reset tokens expire after 1 hour
- Email service sends reset emails

### Frontend Components

#### Task Group 3: Authentication UI & State Management
**Dependencies:** Task Group 2

- [ ] 3.0 Complete frontend authentication implementation
  - [ ] 3.1 Write 2-8 focused tests for auth components and hooks
    - Test login form validation and submission
    - Test register form validation and submission
    - Test auth context/provider state management
    - Test protected route redirect
  - [ ] 3.2 Create API client utility
    - Set up Axios or fetch with httpOnly cookie support
    - Implement request interceptor for token refresh (handle 401 responses)
    - Implement response interceptor for auto-refresh logic
    - Handle errors consistently
  - [ ] 3.3 Create auth context/provider
    - Create AuthContext with React Context API or Zustand store
    - Provide useAuth hook for components
    - Track user object, loading state, authentication status
    - Implement login, logout, register methods
  - [ ] 3.4 Create login page
    - Email/password form with React Hook Form
    - Real-time validation with Zod schemas
    - Google OAuth button component
    - Links to register and forgot password
    - Error handling and success states
    - Follow Shadcn/ui design system
  - [ ] 3.5 Create register page
    - Email/password/full_name form with React Hook Form
    - Real-time validation with Zod schemas
    - Google OAuth button component
    - Link to login page
    - Error handling and success states
    - Follow Shadcn/ui design system
  - [ ] 3.6 Create forgot password page
    - Email input form with React Hook Form
    - Real-time validation with Zod
    - Success message after submission
    - Link back to login
    - Follow Shadcn/ui design system
  - [ ] 3.7 Create reset password page
    - Token validation on page load
    - New password form with React Hook Form
    - Password strength validation (matching backend rules)
    - Success/error states
    - Link back to login
    - Follow Shadcn/ui design system
  - [ ] 3.8 Create Google OAuth button component
    - Custom styled button matching Shadcn/ui design system
    - Follow Google brand guidelines (logo, colors)
    - Handle OAuth redirect flow
  - [ ] 3.9 Implement protected routes middleware
    - Create Next.js middleware.ts file
    - Check authentication status on protected routes
    - Redirect unauthenticated users to /login with return URL
    - Protect routes: /dashboard, /videos, /editor, etc.
    - Allow public routes: /, /login, /register, /forgot-password, /reset-password
  - [ ] 3.10 Implement redirect to original destination after login
    - Capture return URL from middleware redirect
    - Store return URL in auth flow
    - Redirect to original destination after successful login
  - [ ] 3.11 Add email verification banner (optional)
    - Show banner if email_verified is False
    - Banner prompts user to verify email
    - Dismissible banner component
  - [ ] 3.12 Ensure UI component tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify forms validate correctly
    - Verify auth flows work end-to-end
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All auth pages render correctly
- Forms validate in real-time
- Protected routes redirect correctly
- Token auto-refresh works
- Google OAuth flow works
- Matches Shadcn/ui design system

### Testing

#### Task Group 4: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-3

- [ ] 4.0 Review existing tests and fill critical gaps only
  - [ ] 4.1 Review tests from Task Groups 1-3
    - Review the 2-8 tests written by database-engineer (Task 1.1)
    - Review the 2-8 tests written by api-engineer (Task 2.1)
    - Review the 2-8 tests written by ui-designer (Task 3.1)
    - Total existing tests: approximately 6-24 tests
  - [ ] 4.2 Analyze test coverage gaps for THIS feature only
    - Identify critical user workflows that lack test coverage
    - Focus ONLY on gaps related to auth feature requirements
    - Do NOT assess entire application test coverage
    - Prioritize end-to-end workflows over unit test gaps
  - [ ] 4.3 Write up to 10 additional strategic tests maximum
    - Add maximum of 10 new tests to fill identified critical gaps
    - Focus on integration points and end-to-end workflows
    - Examples: Complete password reset flow E2E, Google OAuth flow E2E, token refresh flow
    - Do NOT write comprehensive coverage for all scenarios
    - Skip edge cases, performance tests, and accessibility tests unless business-critical
  - [ ] 4.4 Run feature-specific tests only
    - Run ONLY tests related to auth feature (tests from 1.1, 2.1, 3.1, and 4.3)
    - Expected total: approximately 16-34 tests maximum
    - Do NOT run the entire application test suite
    - Verify critical auth workflows pass

**Acceptance Criteria:**
- All feature-specific tests pass (approximately 16-34 tests total)
- Critical user workflows for auth feature are covered
- No more than 10 additional tests added when filling in testing gaps
- Testing focused exclusively on auth feature requirements

## Execution Order

Recommended implementation sequence:
1. Database Layer (Task Group 1) - Add email_verified field
2. Backend API Layer (Task Group 2) - Complete password reset and OAuth
3. Frontend Components (Task Group 3) - Build all auth UI and state management
4. Test Review & Gap Analysis (Task Group 4) - Fill critical test gaps

## Notes

- Backend auth is partially complete (register, login, refresh, logout, me endpoints exist)
- Focus on completing missing backend features (password reset, OAuth) and all frontend implementation
- Reuse existing backend patterns and extend AuthService class
- Follow Shadcn/ui design system for all frontend components
- Use httpOnly cookies exclusively for token storage (security-first approach)

