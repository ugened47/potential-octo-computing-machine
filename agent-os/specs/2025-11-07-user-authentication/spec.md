# Specification: User Authentication

## Goal
Enable users to register, login, and manage their accounts with email/password authentication, Google OAuth integration, password reset functionality, and JWT-based session management.

## User Stories
- As a new user, I want to register with email and password so that I can access the platform
- As a user, I want to login with Google OAuth so that I can quickly access my account without creating a password
- As a user, I want to reset my password via email so that I can regain access if I forget it
- As a user, I want my session to persist across page refreshes so that I don't have to login repeatedly

## Specific Requirements

**Password Reset Flow**
- POST /api/auth/forgot-password: Accept email, generate JWT-style reset token (1 hour expiration), send email with reset link
- POST /api/auth/reset-password: Accept token and new password, validate token expiration, update user password, invalidate token
- Use JWT-style signed tokens (no database storage) for reset tokens
- Frontend forgot password page with email input and form validation
- Frontend reset password page with token validation and new password form
- Email service integration for sending reset emails (use existing email service pattern)

**Google OAuth Integration**
- Implement OAuth 2.0 authorization code flow with Google
- POST /api/auth/google/callback: Handle OAuth callback, create/update user with Google credentials
- Store OAuth ID in User.oauth_id field (single provider for MVP)
- Frontend Google OAuth button component matching Shadcn/ui design system
- Redirect to Google OAuth consent screen, then back to app with authorization code
- Handle existing email conflicts (if email exists with password auth, link accounts or show error)

**Frontend Authentication Pages**
- Login page: Email/password form with real-time validation, Google OAuth button, link to register/forgot password
- Register page: Email/password/full_name form with real-time validation, Google OAuth button, link to login
- Forgot password page: Email input form with validation, success message after submission
- Reset password page: Token validation, new password form with strength validation, success/error states
- All pages follow Shadcn/ui design system and existing Tailwind CSS theme

**Auth State Management**
- Create AuthContext/Provider using React Context API or Zustand
- Store access token and refresh token in httpOnly cookies (no localStorage)
- Implement auto-refresh on token expiry (intercept 401 responses, refresh token, retry request)
- Provide useAuth hook for components to access auth state and methods
- Track user object, loading state, and authentication status

**Protected Routes Middleware**
- Create Next.js middleware to check authentication status on protected routes
- Redirect unauthenticated users to /login with return URL parameter
- After successful login, redirect back to original destination
- Protect routes like /dashboard, /videos, /editor, etc.
- Allow public routes: /, /login, /register, /forgot-password, /reset-password

**Form Validation**
- Client-side validation with React Hook Form and Zod schemas, matching backend Pydantic validation
- Show validation errors inline as users type (real-time validation)
- Validate on submit as well
- Match backend password requirements: min 8 chars, at least one uppercase, one lowercase, one digit

**Email Verification (Optional for MVP)**
- Add email_verified field to User model (boolean, default False)
- Create migration for email_verified field
- Show optional banner prompting verification if email_verified is False
- Dismissible banner component
- Required email verification excluded from MVP scope

**Backend Extensions**
- Extend existing AuthService class with password reset methods (forgot_password, reset_password)
- Add Google OAuth service method (google_oauth_callback) to AuthService
- Reuse existing JWT functions from security.py for reset tokens
- Follow existing API route patterns from auth.py
- Use existing get_current_user dependency for protected endpoints

## Visual Design
No visual assets provided. Follow Shadcn/ui design system for all authentication pages and components.

## Existing Code to Leverage

**Backend Auth Routes**
- Follow existing endpoint structure from `backend/app/api/routes/auth.py`
- Use same async/await patterns and error handling
- Extend router with new password reset and OAuth endpoints

**Backend Auth Service**
- Extend existing AuthService class in `backend/app/services/auth.py`
- Reuse register_user and login_user patterns for new methods
- Follow same database query patterns and error handling

**Backend Security Utilities**
- Reuse password hashing and JWT functions from `backend/app/core/security.py`
- Use create_access_token pattern for reset tokens (with different expiration)
- Leverage decode_token for token validation

**User Model**
- User model already has oauth_id and oauth_provider fields in `backend/app/models/user.py`
- Add email_verified field following same pattern
- Reuse existing field types and validations

**Backend Auth Schemas**
- Follow existing Pydantic schema patterns from `backend/app/schemas/auth.py`
- Create PasswordResetRequest and PasswordReset schemas matching existing style
- Reuse validation patterns and error messages

**Backend Dependencies**
- Use existing get_current_user dependency from `backend/app/api/deps.py`
- Follow same authentication/authorization patterns

**Frontend Design System**
- Use Shadcn/ui components (Button, Input, Card, Form, Label) from existing component library
- Follow existing Tailwind CSS theme from `frontend/src/app/globals.css`
- Match styling patterns from existing pages

**Frontend Patterns**
- Follow Next.js 14 App Router with Server/Client component separation
- Use Zustand for auth state management if needed, following project conventions
- Match existing form validation patterns

## Out of Scope
- Two-factor authentication (2FA)
- Social login providers beyond Google (Facebook, Twitter, etc.)
- Account deletion functionality
- Profile picture upload
- Email change functionality
- Password strength meter (beyond basic validation)
- Remember me checkbox (always remember via refresh token)
- Required email verification (optional for MVP)
- Multi-provider OAuth support (single Google provider for MVP)
- Password history or password expiration policies
