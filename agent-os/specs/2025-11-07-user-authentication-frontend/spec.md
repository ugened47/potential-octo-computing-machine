# Specification: User Authentication Frontend

## Goal
Implement the frontend user authentication system with login, registration, Google OAuth integration, password reset functionality, and protected route handling to complete the authentication flow.

## User Stories
- As a user, I want to login and register with email/password or Google OAuth so that I can access the platform
- As a user, I want to reset my password via email so that I can regain access if I forget it
- As a user, I want my session to persist across page refreshes so that I don't have to login repeatedly

## Specific Requirements

**Authentication Pages**
- Create `/login` page with email/password form and Google OAuth button
- Create `/register` page with email, password, and full_name fields
- Create `/forgot-password` page with email input form
- Create `/reset-password` page with token validation and new password form
- Create `/profile` page to view and update user full name
- All pages use Next.js 14 App Router structure (`app/[page]/page.tsx`)
- Pages are client components ('use client') for interactivity

**LoginForm Component**
- Email and password input fields with validation
- Real-time validation on blur matching backend requirements
- Inline error messages below fields for validation errors
- Loading state with disabled button and spinner during API call
- Google OAuth button integration
- Links to register and forgot password pages
- Toast notifications for general errors (network failures)

**RegisterForm Component**
- Email, password, and full_name input fields
- Password validation: minimum 8 characters, uppercase, lowercase, digit
- Real-time validation on blur with inline error messages
- Password strength validation matching backend Pydantic schema
- Google OAuth button integration
- Link to login page
- Success redirect to dashboard after registration

**ForgotPasswordForm Component**
- Email input field with validation
- Real-time email validation on blur
- Success message after submission (email sent confirmation)
- Link back to login page
- Loading state during API call

**ResetPasswordForm Component**
- Token validation from URL query parameter
- New password and confirm password fields
- Password validation matching backend requirements
- Token expiration handling (show error if expired)
- Success redirect to login after password reset
- Loading state and error handling

**GoogleOAuthButton Component**
- OAuth button matching Shadcn/ui design system
- Redirects to backend OAuth endpoint (`GET /api/auth/google`)
- Handles OAuth callback with token exchange
- Error handling for OAuth failures
- Loading state during OAuth flow

**AuthProvider/Context (Global State Management)**
- Use Zustand store or React Context for auth state
- Track user object, loading state, authentication status
- Provide useAuth hook for components
- Implement login, logout, register methods
- Persist auth state across page refreshes
- Clear state on logout

**Token Management & API Client**
- Store access_token and refresh_token in localStorage
- Extend existing apiClient from `frontend/src/lib/api.ts` with refresh interceptor
- Automatic token refresh on 401 errors using axios response interceptor
- Token refresh logic calls `/api/auth/refresh` endpoint
- Update tokens in localStorage after refresh
- Clear tokens on logout

**Protected Routes**
- Next.js middleware (`middleware.ts`) for server-side route protection
- Client-side ProtectedRoute component for additional security
- Redirect unauthenticated users to `/login?returnUrl=[original-path]`
- Redirect back to returnUrl after successful login
- Protect routes: `/dashboard`, `/profile`, and other authenticated pages

**Form Validation**
- Email validation (client-side format check)
- Password validation matching backend requirements: min 8 chars, uppercase, lowercase, digit
- Real-time validation on blur for better UX
- Submit-time validation before API call
- Inline error messages below form fields
- Match backend Pydantic schema validation rules

**User Profile Page**
- Display current user information (email, full_name)
- Update full_name form using `PUT /api/auth/me` endpoint
- Show success/error feedback on update
- Loading state during update
- Use existing Input and Button components from Shadcn/ui

**Error Handling & UX**
- Inline error messages below form fields for field-specific errors
- Toast notifications for general errors (network failures, API errors)
- Loading states with disabled buttons and spinners during API calls
- Display API error messages appropriately
- Handle 401 errors with automatic token refresh
- Handle 403/404 errors with appropriate user feedback

## Visual Design
No visual assets provided. Follow Shadcn/ui design system and existing project styling patterns from transcript components.

## Existing Code to Leverage

**API Client Pattern**
- Extend existing `apiClient` from `frontend/src/lib/api.ts` with auth token refresh interceptor
- Follow axios interceptor pattern already established for token injection
- Use same error handling approach from existing API client

**API Function Pattern**
- Follow structure from `frontend/src/lib/transcript-api.ts` for auth API functions
- Create `frontend/src/lib/auth-api.ts` with functions: login, register, logout, refreshToken, getCurrentUser, updateUser, forgotPassword, resetPassword
- Use TypeScript types matching backend Pydantic schemas
- Return typed responses with proper error handling

**UI Components**
- Reuse Input component from `frontend/src/components/ui/input.tsx`
- Reuse Button component from `frontend/src/components/ui/button.tsx`
- Follow Shadcn/ui design system for all form elements
- Use existing styling patterns from transcript components

**Error Handling Pattern**
- Follow error handling patterns from `TranscriptPanel` component (useState, try/catch, conditional rendering)
- Use same loading state patterns from `TranscriptionProgress` component
- Display errors consistently with existing error display patterns

**Backend API Reference**
- Reference auth routes from `backend/app/api/routes/auth.py` for endpoint structure
- Match request/response types from `backend/app/schemas/auth.py` Pydantic schemas
- Follow same authentication patterns (Bearer token in Authorization header)

## Out of Scope
- Email service implementation (backend handles sending reset emails)
- OAuth backend endpoints implementation (assumed to exist: `GET /api/auth/google`, `POST /api/auth/google/callback`)
- Password reset backend endpoints implementation (assumed to exist: `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`)
- Multi-factor authentication (MFA)
- Social login providers other than Google
- Account deletion functionality
- Email verification flow
- Password strength meter visualization (basic validation only, no visual meter)
- Remember me checkbox (always remember via refresh token)
- Session management beyond token storage (no server-side session tracking)

