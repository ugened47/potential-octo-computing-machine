# Task Breakdown: User Authentication Frontend

## Overview
Total Tasks: 6 task groups, 40+ sub-tasks

## Task List

### API Client & Token Management

#### Task Group 1: Auth API Client and Token Management
**Dependencies:** Backend Authentication API (already implemented)

- [x] 1.0 Complete API client layer
  - [ ] 1.1 Write 2-8 focused tests for auth API functions
    - Test login function with valid credentials
    - Test login function with invalid credentials
    - Test register function with valid data
    - Test register function with validation errors
    - Test token refresh function
    - Test logout function clears tokens
    - Test getCurrentUser function
    - Test forgotPassword and resetPassword functions
  - [x] 1.2 Create TypeScript type definitions for auth
    - Define User interface (id, email, full_name, is_active, created_at, oauth_provider)
    - Define AuthResponse interface (user, access_token, refresh_token, token_type)
    - Define TokenResponse interface (access_token, refresh_token, token_type)
    - Define LoginRequest interface (email, password)
    - Define RegisterRequest interface (email, password, full_name)
    - Define PasswordResetRequest interface (email)
    - Define PasswordReset interface (token, new_password)
    - Create file: `frontend/src/types/auth.ts`
  - [x] 1.3 Create auth API client functions
    - login(email, password): Calls POST /api/auth/login, returns Promise<AuthResponse>
    - register(email, password, full_name): Calls POST /api/auth/register, returns Promise<AuthResponse>
    - logout(): Calls POST /api/auth/logout, clears tokens from localStorage
    - refreshToken(refresh_token): Calls POST /api/auth/refresh, returns Promise<TokenResponse>
    - getCurrentUser(): Calls GET /api/auth/me, returns Promise<User>
    - updateUser(full_name): Calls PUT /api/auth/me, returns Promise<User>
    - forgotPassword(email): Calls POST /api/auth/forgot-password, returns Promise<void>
    - resetPassword(token, new_password): Calls POST /api/auth/reset-password, returns Promise<void>
    - All functions use apiClient with proper error handling and TypeScript types
    - Create file: `frontend/src/lib/auth-api.ts`
  - [x] 1.4 Extend apiClient with token refresh interceptor
    - Add response interceptor to handle 401 errors
    - On 401, attempt to refresh token using refresh_token from localStorage
    - Retry original request with new access_token after refresh
    - Handle refresh failure by redirecting to login
    - Update tokens in localStorage after successful refresh
    - Prevent infinite refresh loops
    - Update file: `frontend/src/lib/api.ts`
  - [x] 1.5 Implement token storage utilities
    - getAccessToken(): Retrieves access_token from localStorage
    - getRefreshToken(): Retrieves refresh_token from localStorage
    - setTokens(access_token, refresh_token): Stores tokens in localStorage
    - clearTokens(): Removes tokens from localStorage
    - hasValidToken(): Checks if access_token exists
    - Create file: `frontend/src/lib/token-storage.ts` or add to auth-api.ts
  - [ ] 1.6 Ensure API client tests pass
    - Run ONLY the 2-8 tests written in 1.1
    - Verify token refresh interceptor works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 1.1 pass
- All auth API functions work correctly
- Token refresh interceptor handles 401 errors automatically
- Tokens are stored and retrieved from localStorage correctly

### Auth State Management

#### Task Group 2: Auth Context/Provider and State Management
**Dependencies:** Task Group 1

- [x] 2.0 Complete auth state management
  - [ ] 2.1 Write 2-8 focused tests for auth state management
    - Test auth store initialization
    - Test login updates user state and tokens
    - Test logout clears user state and tokens
    - Test register updates user state
    - Test auth state persists across page refreshes
    - Test useAuth hook returns correct state
  - [x] 2.2 Create Zustand auth store (or React Context)
    - Store: user (User | null), isAuthenticated (boolean), isLoading (boolean)
    - Actions: login, logout, register, setUser, setLoading
    - Persist auth state to localStorage (user object)
    - Rehydrate auth state on app initialization
    - Use Zustand (already in dependencies) or React Context API
    - Create file: `frontend/src/store/auth-store.ts` or `frontend/src/contexts/AuthContext.tsx`
  - [x] 2.3 Create useAuth hook
    - Returns: { user, isAuthenticated, isLoading, login, logout, register }
    - Provides access to auth state and actions
    - Handles token management internally
    - Create file: `frontend/src/hooks/useAuth.ts` or include in context file
  - [x] 2.4 Implement auth state persistence
    - Save user object to localStorage on login/register
    - Load user from localStorage on app initialization
    - Clear localStorage on logout
    - Handle token expiration by checking token validity
  - [ ] 2.5 Ensure auth state tests pass
    - Run ONLY the 2-8 tests written in 2.1
    - Verify state persistence works correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 2.1 pass
- Auth state persists across page refreshes
- useAuth hook provides correct state and actions
- Login/logout updates state correctly

### Form Components

#### Task Group 3: Authentication Form Components
**Dependencies:** Task Group 1, Task Group 2

- [x] 3.0 Complete form components
  - [ ] 3.1 Write 2-8 focused tests for form components
    - Test LoginForm validation and submission
    - Test RegisterForm validation and submission
    - Test ForgotPasswordForm validation and submission
    - Test ResetPasswordForm validation and submission
    - Test form error display
    - Test loading states during submission
  - [x] 3.2 Create form validation utilities
    - validateEmail(email): Returns boolean, checks email format
    - validatePassword(password): Returns { valid: boolean, errors: string[] }
      - Checks minimum 8 characters
      - Checks for uppercase letter
      - Checks for lowercase letter
      - Checks for digit
    - validateFullName(name): Returns boolean, checks non-empty
    - Create file: `frontend/src/lib/validation.ts`
  - [x] 3.3 Create LoginForm component
    - Client component ('use client') with email and password fields
    - Real-time validation on blur matching backend requirements
    - Inline error messages below fields for validation errors
    - Loading state with disabled button and spinner during API call
    - Integrates GoogleOAuthButton component
    - Links to register and forgot password pages
    - Toast notifications for general errors (network failures)
    - Calls login API function on submit
    - Redirects to dashboard or returnUrl on success
    - Uses Input and Button components from Shadcn/ui
    - Create file: `frontend/src/components/auth/LoginForm.tsx`
  - [x] 3.4 Create RegisterForm component
    - Client component with email, password, and full_name fields
    - Password validation: minimum 8 characters, uppercase, lowercase, digit
    - Real-time validation on blur with inline error messages
    - Password strength validation matching backend Pydantic schema
    - Integrates GoogleOAuthButton component
    - Link to login page
    - Success redirect to dashboard after registration
    - Uses Input and Button components from Shadcn/ui
    - Create file: `frontend/src/components/auth/RegisterForm.tsx`
  - [x] 3.5 Create ForgotPasswordForm component
    - Client component with email input field
    - Real-time email validation on blur
    - Success message after submission (email sent confirmation)
    - Link back to login page
    - Loading state during API call
    - Uses Input and Button components from Shadcn/ui
    - Create file: `frontend/src/components/auth/ForgotPasswordForm.tsx`
  - [x] 3.6 Create ResetPasswordForm component
    - Client component with token validation from URL query parameter
    - New password and confirm password fields
    - Password validation matching backend requirements
    - Token expiration handling (show error if expired)
    - Success redirect to login after password reset
    - Loading state and error handling
    - Uses Input and Button components from Shadcn/ui
    - Create file: `frontend/src/components/auth/ResetPasswordForm.tsx`
  - [x] 3.7 Create GoogleOAuthButton component
    - Client component with OAuth button matching Shadcn/ui design system
    - Redirects to backend OAuth endpoint (`GET /api/auth/google`)
    - Handles OAuth callback with token exchange
    - Error handling for OAuth failures
    - Loading state during OAuth flow
    - Uses Button component from Shadcn/ui
    - Create file: `frontend/src/components/auth/GoogleOAuthButton.tsx`
  - [ ] 3.8 Ensure form component tests pass
    - Run ONLY the 2-8 tests written in 3.1
    - Verify all forms validate and submit correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 3.1 pass
- All form components render correctly
- Form validation matches backend requirements
- Forms handle errors and loading states correctly

### Authentication Pages

#### Task Group 4: Authentication Pages
**Dependencies:** Task Group 3

- [x] 4.0 Complete authentication pages
  - [ ] 4.1 Write 2-8 focused tests for auth pages
    - Test login page renders and navigates correctly
    - Test register page renders and navigates correctly
    - Test forgot password page renders and submits correctly
    - Test reset password page validates token and resets password
    - Test profile page displays and updates user info
  - [x] 4.2 Create login page (`/login`)
    - Next.js App Router page: `app/login/page.tsx`
    - Client component ('use client')
    - Renders LoginForm component
    - Handles returnUrl query parameter for redirect after login
    - Redirects to dashboard or returnUrl on successful login
    - Redirects authenticated users away from login page
  - [x] 4.3 Create register page (`/register`)
    - Next.js App Router page: `app/register/page.tsx`
    - Client component ('use client')
    - Renders RegisterForm component
    - Redirects to dashboard on successful registration
    - Redirects authenticated users away from register page
  - [x] 4.4 Create forgot password page (`/forgot-password`)
    - Next.js App Router page: `app/forgot-password/page.tsx`
    - Client component ('use client')
    - Renders ForgotPasswordForm component
    - Shows success message after email sent
    - Redirects authenticated users away from forgot password page
  - [x] 4.5 Create reset password page (`/reset-password`)
    - Next.js App Router page: `app/reset-password/page.tsx`
    - Client component ('use client')
    - Extracts token from URL query parameter
    - Validates token before showing form
    - Renders ResetPasswordForm component
    - Shows error if token is invalid or expired
    - Redirects to login on successful password reset
  - [x] 4.6 Create profile page (`/profile`)
    - Next.js App Router page: `app/profile/page.tsx`
    - Client component ('use client')
    - Displays current user information (email, full_name)
    - Update full_name form using `PUT /api/auth/me` endpoint
    - Shows success/error feedback on update
    - Loading state during update
    - Uses Input and Button components from Shadcn/ui
    - Protected route (requires authentication)
  - [ ] 4.7 Ensure auth page tests pass
    - Run ONLY the 2-8 tests written in 4.1
    - Verify all pages render and navigate correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 4.1 pass
- All authentication pages render correctly
- Pages handle navigation and redirects correctly
- Profile page updates user information correctly

### Protected Routes

#### Task Group 5: Protected Routes and Middleware
**Dependencies:** Task Group 2, Task Group 4

- [x] 5.0 Complete protected routes implementation
  - [ ] 5.1 Write 2-8 focused tests for protected routes
    - Test middleware redirects unauthenticated users to login
    - Test middleware preserves returnUrl query parameter
    - Test ProtectedRoute component redirects unauthenticated users
    - Test authenticated users can access protected routes
    - Test redirect back to returnUrl after login
  - [x] 5.2 Create Next.js middleware for route protection
    - Create `middleware.ts` in project root
    - Check for access_token in localStorage (via request headers or cookies)
    - Protect routes: `/dashboard`, `/profile`, and other authenticated pages
    - Redirect unauthenticated users to `/login?returnUrl=[original-path]`
    - Allow public routes: `/login`, `/register`, `/forgot-password`, `/reset-password`
    - Handle token validation
  - [x] 5.3 Create ProtectedRoute client component
    - Client component that wraps protected pages
    - Checks authentication status using useAuth hook
    - Shows loading state while checking auth
    - Redirects to login with returnUrl if not authenticated
    - Renders children if authenticated
    - Create file: `frontend/src/components/auth/ProtectedRoute.tsx`
  - [x] 5.4 Implement returnUrl redirect logic
    - Extract returnUrl from query parameters on login page
    - Store returnUrl during redirect to login
    - Redirect to returnUrl after successful login
    - Default to `/dashboard` if no returnUrl provided
    - Handle invalid returnUrl (redirect to dashboard)
  - [x] 5.5 Update protected pages to use ProtectedRoute
    - Wrap dashboard page with ProtectedRoute component
    - Wrap profile page with ProtectedRoute component
    - Ensure middleware and ProtectedRoute work together
  - [ ] 5.6 Ensure protected route tests pass
    - Run ONLY the 2-8 tests written in 5.1
    - Verify middleware and ProtectedRoute work correctly
    - Do NOT run the entire test suite at this stage

**Acceptance Criteria:**
- The 2-8 tests written in 5.1 pass
- Middleware protects routes server-side
- ProtectedRoute component protects routes client-side
- returnUrl redirect flow works correctly

### Testing

#### Task Group 6: Test Review & Gap Analysis
**Dependencies:** Task Groups 1-5

- [ ] 6.0 Review existing tests and fill critical gaps
  - [ ] 6.1 Review tests from Task Groups 1-5
    - Review API client tests (Task Group 1)
    - Review auth state management tests (Task Group 2)
    - Review form component tests (Task Group 3)
    - Review auth page tests (Task Group 4)
    - Review protected route tests (Task Group 5)
  - [ ] 6.2 Analyze test coverage gaps
    - Identify missing edge cases
    - Identify missing integration tests
    - Identify missing error handling tests
    - Check coverage for all auth flows
    - Check coverage for all components
  - [ ] 6.3 Write up to 10 additional strategic tests
    - Integration tests for complete auth flows (register → login → logout)
    - Integration tests for password reset flow (forgot → reset)
    - Integration tests for OAuth flow
    - Error handling tests (network errors, API errors)
    - Edge case tests (expired tokens, invalid tokens, malformed responses)
    - End-to-end tests for authentication user journeys
  - [ ] 6.4 Run feature-specific tests only
    - Run all authentication-related tests
    - Verify all tests pass
    - Do NOT run the entire test suite

**Acceptance Criteria:**
- All tests from Task Groups 1-5 pass
- Additional strategic tests are written and pass
- Test coverage is comprehensive for authentication feature
- No critical gaps in test coverage

## Execution Order
1. API Client & Token Management (Task Group 1)
2. Auth State Management (Task Group 2)
3. Form Components (Task Group 3)
4. Authentication Pages (Task Group 4)
5. Protected Routes (Task Group 5)
6. Test Review & Gap Analysis (Task Group 6)

