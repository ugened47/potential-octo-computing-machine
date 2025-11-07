# Spec Requirements: User Authentication

## Initial Description

User Authentication is a foundational feature that enables users to register, login, and manage their accounts. The system supports email/password authentication, Google OAuth integration, password reset functionality, and JWT-based session management. This feature is critical as it's a dependency for all other features in the application.

## Requirements Discussion

### First Round Questions

**Q1:** For password reset flow, I'm assuming we'll use email-based reset tokens with expiration (e.g., 1 hour). Should we store reset tokens in the database or use JWT-style signed tokens that don't require database storage?

**Answer:** Use JWT-style signed tokens for password reset - this avoids database storage and follows the same pattern as access/refresh tokens. Tokens should expire after 1 hour.

**Q2:** For Google OAuth, I'm assuming we'll use the standard OAuth 2.0 authorization code flow with redirect back to our app. Should we store the OAuth ID in the existing User model's `oauth_id` field, or create a separate OAuth accounts table for future multi-provider support?

**Answer:** For MVP, store OAuth ID directly in User model's existing `oauth_id` field. We can refactor to separate table later if needed for multi-provider support.

**Q3:** For frontend token storage, I'm assuming we'll use httpOnly cookies for security (to prevent XSS attacks). Should we also support localStorage as a fallback, or strictly enforce httpOnly cookies?

**Answer:** Use httpOnly cookies exclusively for token storage. No localStorage fallback - security is more important than convenience.

**Q4:** For protected routes, I'm assuming we'll use Next.js middleware to check authentication status and redirect unauthenticated users to `/login`. Should protected routes redirect back to the original destination after login, or always go to dashboard?

**Answer:** Redirect back to original destination after login - better UX for users who were trying to access a specific page.

**Q5:** For form validation, I'm assuming we'll use client-side validation with React Hook Form and Zod schemas, matching the backend Pydantic validation. Should we show validation errors inline as users type, or only on submit?

**Answer:** Show validation errors inline as users type (real-time validation) for better UX, but also validate on submit.

**Q6:** For Google OAuth button styling, I'm assuming we'll follow Google's brand guidelines (official Google sign-in button). Should we use Google's official button component or create a custom styled button that matches our Shadcn/ui design system?

**Answer:** Create a custom styled button that matches Shadcn/ui design system but follows Google's brand guidelines (use Google logo and colors).

**Q7:** For email verification, I see it's mentioned in TASKS.md but not fully specified. Should email verification be required before users can access the app, or optional (users can use the app but see a banner prompting verification)?

**Answer:** Email verification should be optional for MVP - users can access the app immediately but see a banner prompting verification. We'll add required verification as a post-MVP enhancement.

**Q8:** What features should be explicitly excluded from this spec? For example, two-factor authentication, social login beyond Google, account deletion, or profile picture upload?

**Answer:** Exclude: two-factor authentication, social login beyond Google, account deletion, profile picture upload, email change functionality, password strength meter (use basic validation only), remember me checkbox (always remember via refresh token).

### Existing Code to Reference

**Similar Features Identified:**
- Backend auth patterns: `backend/app/api/routes/auth.py` - Follow existing endpoint structure
- Backend auth service: `backend/app/services/auth.py` - Extend existing AuthService class
- Backend security utilities: `backend/app/core/security.py` - Reuse password hashing and JWT functions
- Backend user model: `backend/app/models/user.py` - User model already has oauth_id field
- Backend auth schemas: `backend/app/schemas/auth.py` - Follow existing Pydantic schema patterns
- Backend dependencies: `backend/app/api/deps.py` - Use existing get_current_user dependency
- Frontend design system: Shadcn/ui components (Button, Input, Card, Form) - Use existing component library
- Frontend styling: `frontend/src/app/globals.css` - Follow existing Tailwind CSS theme

### Follow-up Questions

None needed - all requirements are clear.

## Visual Assets

### Files Provided:
No visual files found.

### Visual Insights:
No visual assets provided. Will follow Shadcn/ui design system and existing project styling patterns.

## Requirements Summary

### Functional Requirements

**Backend:**
- Complete password reset flow (forgot password + reset password endpoints)
- Implement Google OAuth 2.0 authorization code flow
- Add email verification status tracking (optional verification for MVP)
- Write comprehensive auth tests (unit + integration)

**Frontend:**
- Create login page with email/password form
- Create register page with email/password/full_name form
- Create forgot password page with email input
- Create reset password page with token validation and new password form
- Implement Google OAuth button component
- Create auth context/provider for state management
- Implement httpOnly cookie-based token storage
- Implement auto-refresh on token expiry
- Create protected route middleware
- Implement redirect to original destination after login
- Add real-time form validation with React Hook Form + Zod
- Show inline validation errors

### Reusability Opportunities

- Backend: Extend existing AuthService class, reuse security utilities, follow existing API route patterns
- Frontend: Use Shadcn/ui components (Button, Input, Card, Form, Label), follow existing Tailwind CSS theme
- Patterns: Follow existing async/await patterns, error handling patterns, validation patterns

### Scope Boundaries

**In Scope:**
- Email/password registration and login
- Google OAuth integration
- Password reset flow (forgot + reset)
- JWT token management (access + refresh)
- Protected routes middleware
- Auth state management
- Form validation (client + server)
- Token auto-refresh
- Redirect to original destination after login

**Out of Scope:**
- Two-factor authentication
- Social login beyond Google
- Account deletion
- Profile picture upload
- Email change functionality
- Password strength meter (beyond basic validation)
- Remember me checkbox (always remember via refresh token)
- Required email verification (optional for MVP)
- Multi-provider OAuth (single Google provider for MVP)

### Technical Considerations

- Backend already partially implemented - extend existing code
- Use httpOnly cookies exclusively (no localStorage)
- Follow existing FastAPI async patterns
- Use React Hook Form + Zod for frontend validation
- Use Next.js middleware for route protection
- Store OAuth ID in existing User.oauth_id field
- Use JWT-style signed tokens for password reset (no database storage)
- Follow Shadcn/ui design system for all UI components
- Use Zustand for auth state management if needed
- Match backend Pydantic schemas with frontend Zod schemas

