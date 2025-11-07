# Spec Requirements: User Authentication Frontend

## Initial Description

User authentication frontend implementation, Google OAuth integration, and password reset functionality.

## Requirements Discussion

### First Round Questions

**Q1:** Page Structure: I'm assuming we'll create separate Next.js pages for `/login`, `/register`, `/forgot-password`, and `/reset-password` using the App Router. Should these be separate pages, or would you prefer a modal/dialog approach for login/register on the homepage?

**Answer:** Use separate Next.js pages for `/login`, `/register`, `/forgot-password`, and `/reset-password` using the App Router. This provides better SEO, URL sharing, and browser history support.

**Q2:** Google OAuth Flow: I see the backend OAuth endpoints aren't implemented yet. Should the frontend implement the OAuth button and redirect flow assuming the backend endpoints (`GET /api/auth/google` and `POST /api/auth/google/callback`) will be available, or should we coordinate with backend implementation first?

**Answer:** Implement the frontend OAuth flow assuming the backend endpoints will be available. The frontend will handle the OAuth button click, redirect to Google, and handle the callback with token exchange.

**Q3:** Password Reset Flow: I notice password reset backend endpoints (`POST /api/auth/forgot-password` and `POST /api/auth/reset-password`) aren't implemented yet. Should the frontend implement the forgot password form and reset password page assuming these endpoints will exist, or coordinate with backend first?

**Answer:** Implement the frontend password reset flow assuming the backend endpoints will be available. The frontend will handle the forgot password form, reset password page with token validation, and success/error states.

**Q4:** Token Storage & Management: I see you're already using `localStorage` for access tokens in the API client. Should we continue with localStorage for both access and refresh tokens, or use httpOnly cookies? Also, should we implement automatic token refresh when the access token expires?

**Answer:** Continue using localStorage for both access and refresh tokens. Implement automatic token refresh when the access token expires using an axios interceptor that calls the refresh endpoint and updates tokens.

**Q5:** Protected Routes: For protecting routes like `/dashboard`, should we use Next.js middleware, a client-side route guard component, or both? Should unauthenticated users be redirected to `/login` with a return URL?

**Answer:** Use both Next.js middleware for server-side protection and a client-side route guard component for additional security. Redirect unauthenticated users to `/login` with a `returnUrl` query parameter to redirect back after login.

**Q6:** Form Validation: Should we use client-side validation matching the backend requirements (password must have uppercase, lowercase, digit, min 8 chars), and display validation errors in real-time as users type, or only on submit?

**Answer:** Implement client-side validation matching backend requirements. Display validation errors in real-time as users type (on blur for better UX) and also validate on submit. Show inline error messages below form fields.

**Q7:** User Profile Management: Should we include a user profile/settings page where users can update their full name (using the existing `PUT /api/auth/me` endpoint), or is that out of scope for this spec?

**Answer:** Include a user profile/settings page where users can view and update their full name using the existing `PUT /api/auth/me` endpoint. This completes the authentication user experience.

**Q8:** Error Handling & UX: For authentication errors (invalid credentials, expired tokens, etc.), should we display inline error messages below form fields, toast notifications, or both? Should we show loading states during API calls?

**Answer:** Use both inline error messages below form fields for field-specific errors and toast notifications for general errors (like network failures). Show loading states during API calls with disabled buttons and loading spinners.

### Existing Code to Reference

**Similar Features Identified:**
- API Client Pattern: `frontend/src/lib/api.ts` - Existing axios client with token interceptor pattern to follow
- Form Components: `frontend/src/components/ui/input.tsx` and `frontend/src/components/ui/button.tsx` - Shadcn/ui components to reuse
- Error Handling Pattern: `frontend/src/components/transcript/TranscriptPanel.tsx` - Shows error handling with useState, try/catch, and conditional rendering
- Loading State Pattern: `frontend/src/components/transcript/TranscriptionProgress.tsx` - Shows loading states and error display patterns
- API Function Pattern: `frontend/src/lib/transcript-api.ts` - Shows how to structure API client functions with TypeScript types

**Components to potentially reuse:**
- Input component from `frontend/src/components/ui/input.tsx`
- Button component from `frontend/src/components/ui/button.tsx`
- Error display patterns from transcript components

**Backend logic to reference:**
- Auth API routes: `backend/app/api/routes/auth.py` - Shows available endpoints and request/response patterns
- Auth schemas: `backend/app/schemas/auth.py` - Shows validation requirements and response types

### Follow-up Questions

None needed - all requirements clarified.

## Visual Assets

### Files Provided:
No visual files found in the visuals folder.

### Visual Insights:
No visual assets provided. Will follow Shadcn/ui design system and existing project styling patterns from transcript components.

## Requirements Summary

### Functional Requirements

**Frontend Pages:**
- `/login` - Login page with email/password form and Google OAuth button
- `/register` - Registration page with email, password, and full name fields
- `/forgot-password` - Forgot password page with email input
- `/reset-password` - Reset password page with token validation and new password form
- `/profile` or `/settings` - User profile page to view and update full name

**Authentication Components:**
- LoginForm component - Email/password form with validation
- RegisterForm component - Registration form with password strength validation
- ForgotPasswordForm component - Email input form
- ResetPasswordForm component - New password form with token validation
- GoogleOAuthButton component - OAuth button with redirect handling
- ProtectedRoute component - Client-side route guard
- AuthProvider/Context - Global auth state management

**Token Management:**
- Store access_token and refresh_token in localStorage
- Automatic token refresh on 401 errors using axios interceptor
- Token refresh logic calling `/api/auth/refresh` endpoint
- Clear tokens on logout

**Form Validation:**
- Email validation (client-side)
- Password validation matching backend requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
- Real-time validation on blur
- Submit-time validation
- Inline error messages below fields

**Error Handling:**
- Inline error messages below form fields for field-specific errors
- Toast notifications for general errors (network failures, etc.)
- Loading states with disabled buttons and spinners
- Error messages from API responses displayed appropriately

**Protected Routes:**
- Next.js middleware for server-side route protection
- Client-side ProtectedRoute component for additional security
- Redirect to `/login?returnUrl=/dashboard` when unauthenticated
- Redirect back to returnUrl after successful login

**User Profile:**
- Display current user information (email, full name)
- Update full name form using `PUT /api/auth/me`
- Show success/error feedback on update

### Reusability Opportunities

- **UI Components:** Reuse Input and Button components from Shadcn/ui (`frontend/src/components/ui/`)
- **API Client:** Extend existing `apiClient` from `frontend/src/lib/api.ts` with auth interceptors
- **Error Patterns:** Follow error handling patterns from `TranscriptPanel` component
- **Loading Patterns:** Follow loading state patterns from `TranscriptionProgress` component
- **API Function Pattern:** Follow structure from `transcript-api.ts` for auth API functions
- **Backend Patterns:** Reference auth routes and schemas for request/response structure

### Scope Boundaries

**In Scope:**
- Login page with email/password and Google OAuth
- Registration page with validation
- Forgot password flow (form + email sent confirmation)
- Reset password page (token validation + new password form)
- User profile/settings page (view and update full name)
- Token storage and automatic refresh
- Protected route middleware and components
- Form validation matching backend requirements
- Error handling and loading states
- Redirect flow with returnUrl support

**Out of Scope:**
- Email service implementation (backend handles this)
- OAuth backend endpoints (assumed to exist)
- Password reset backend endpoints (assumed to exist)
- Multi-factor authentication (MFA)
- Social login providers other than Google
- Account deletion
- Email verification flow
- Password strength meter visualization (basic validation only)

### Technical Considerations

- **Next.js 14 App Router:** Use App Router for pages (`app/login/page.tsx`, etc.)
- **Client Components:** Use 'use client' directive for interactive forms
- **TypeScript:** Full type safety for all components and API functions
- **Shadcn/ui:** Use existing Input, Button, and other UI components
- **Axios Interceptors:** Extend existing apiClient with auth token refresh logic
- **localStorage:** Store tokens in localStorage (already in use)
- **State Management:** Use React Context or Zustand for global auth state (Zustand already in dependencies)
- **Form Validation:** Client-side validation matching backend Pydantic schemas
- **Error Handling:** Follow existing patterns from transcript components
- **Loading States:** Disable buttons and show spinners during API calls
- **Route Protection:** Next.js middleware + client-side guard component

