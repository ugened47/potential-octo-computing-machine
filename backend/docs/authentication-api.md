# Authentication API Documentation

## Overview

The AI Video Editor backend provides a comprehensive JWT-based authentication system with the following features:

- User registration with email/password
- Secure login with bcrypt password hashing
- JWT access tokens (30-minute expiration)
- JWT refresh tokens (30-day expiration)
- User profile management
- OAuth readiness (Google provider support)
- Inactive user handling
- Token-based authorization

## Base URL

```
http://localhost:8000/api/auth
```

## Endpoints

### 1. Register New User

Create a new user account.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"  // optional
}
```

**Password Requirements:**
- Minimum 8 characters
- Maximum 100 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Success Response (201 Created):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2025-11-09T12:00:00Z",
    "oauth_provider": null
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- **400 Bad Request** - Email already registered
```json
{
  "detail": "Email already registered"
}
```

- **422 Unprocessable Entity** - Validation error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "fields": [
        {
          "field": "password",
          "message": "Password must contain at least one uppercase letter",
          "type": "value_error"
        }
      ]
    }
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

---

### 2. Login

Authenticate an existing user.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2025-11-09T12:00:00Z",
    "oauth_provider": null
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid credentials
```json
{
  "detail": "Incorrect email or password"
}
```

- **403 Forbidden** - Inactive user account
```json
{
  "detail": "User account is inactive"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

---

### 3. Refresh Access Token

Get a new access token using a refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid or expired refresh token
```json
{
  "detail": "Invalid refresh token"
}
```

- **401 Unauthorized** - Wrong token type (access token provided instead)
```json
{
  "detail": "Invalid token type"
}
```

- **403 Forbidden** - User account is inactive
```json
{
  "detail": "User account is inactive"
}
```

- **404 Not Found** - User not found
```json
{
  "detail": "User not found"
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

---

### 4. Get Current User

Get information about the currently authenticated user.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-11-09T12:00:00Z",
  "oauth_provider": null
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid or expired token
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Could not validate credentials"
  }
}
```

- **403 Forbidden** - No credentials provided

**Example cURL:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 5. Update Current User

Update the current user's profile information.

**Endpoint:** `PUT /api/auth/me`

**Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `full_name` (string, required) - New full name

**Success Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "created_at": "2025-11-09T12:00:00Z",
  "oauth_provider": null
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid or expired token

**Example cURL:**
```bash
curl -X PUT "http://localhost:8000/api/auth/me?full_name=Jane%20Doe" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 6. Logout

Logout the current user (client-side token removal).

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Notes:**
- JWT tokens are stateless, so logout is primarily handled client-side by removing tokens from storage
- This endpoint exists for consistency and can be extended for token blacklisting if needed

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Authentication Flow

### Registration Flow

```
1. User submits registration form
   ↓
2. Backend validates email format and password strength
   ↓
3. Backend checks if email already exists
   ↓
4. Backend hashes password with bcrypt
   ↓
5. Backend creates user in database
   ↓
6. Backend generates JWT access & refresh tokens
   ↓
7. Backend returns user data and tokens
   ↓
8. Client stores tokens (localStorage/sessionStorage)
```

### Login Flow

```
1. User submits login credentials
   ↓
2. Backend retrieves user by email
   ↓
3. Backend verifies password with bcrypt
   ↓
4. Backend checks if user is active
   ↓
5. Backend generates new JWT tokens
   ↓
6. Backend returns user data and tokens
   ↓
7. Client stores tokens
```

### Token Refresh Flow

```
1. Access token expires (30 minutes)
   ↓
2. Client receives 401 Unauthorized
   ↓
3. Client sends refresh token to /refresh endpoint
   ↓
4. Backend validates refresh token
   ↓
5. Backend checks user is still active
   ↓
6. Backend generates new access & refresh tokens
   ↓
7. Client stores new tokens
   ↓
8. Client retries original request with new access token
```

### Protected Endpoint Access

```
1. Client includes access token in Authorization header
   ↓
2. Backend extracts token from header
   ↓
3. Backend decodes and verifies JWT signature
   ↓
4. Backend checks token type is "access"
   ↓
5. Backend retrieves user from database by ID in token
   ↓
6. Backend checks user is active
   ↓
7. Backend allows request to proceed
```

---

## Token Structure

### Access Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // User ID
  "type": "access",
  "exp": 1699545600  // Expiration timestamp (30 minutes from creation)
}
```

### Refresh Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // User ID
  "type": "refresh",
  "exp": 1702224000  // Expiration timestamp (30 days from creation)
}
```

---

## Security Considerations

### Password Security
- Passwords are hashed using bcrypt with automatic salt generation
- Passwords are truncated to 72 bytes (bcrypt limitation)
- Plain-text passwords are never stored in the database
- Password strength validation enforces:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit

### Token Security
- Tokens are signed with HS256 algorithm
- Secret key is configurable via environment variable `JWT_SECRET_KEY`
- Access tokens expire after 30 minutes
- Refresh tokens expire after 30 days
- Token type verification prevents using refresh tokens as access tokens
- Tokens include expiration timestamp (`exp` claim)

### API Security
- CORS middleware configured with allowed origins
- Rate limiting middleware (100 requests/minute by default)
- GZip compression for responses
- Comprehensive error handling with appropriate status codes
- Input validation using Pydantic schemas
- Database integrity constraints (unique email)

### Best Practices
1. **Always use HTTPS in production** - Tokens are not encrypted, only signed
2. **Store tokens securely** - Use httpOnly cookies or secure storage
3. **Implement token refresh** - Don't wait for access token to expire
4. **Handle 401 errors** - Automatically refresh token and retry
5. **Logout on client** - Clear tokens from storage
6. **Monitor failed login attempts** - Consider implementing rate limiting per user
7. **Rotate secret keys** - Invalidates all existing tokens

### Security Headers
The application includes security-focused error handling:
- 400: Bad Request (validation errors)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 422: Unprocessable Entity (validation errors)
- 429: Too Many Requests (rate limit exceeded)

---

## OAuth Integration (Planned)

The User model includes OAuth fields for future integration:
- `oauth_provider` - Provider name (e.g., "google")
- `oauth_id` - Provider-specific user ID

OAuth endpoints are not yet implemented but the database schema is ready.

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context (only in development mode)
    }
  }
}
```

Common error codes:
- `VALIDATION_ERROR` - Input validation failed
- `AUTHENTICATION_ERROR` - Invalid or missing credentials
- `AUTHORIZATION_ERROR` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `CONFLICT` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_SERVER_ERROR` - Unexpected error

---

## Testing

### Manual Testing with cURL

**1. Register a user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'
```

**2. Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

**3. Get current user (replace TOKEN):**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

**4. Refresh token (replace REFRESH_TOKEN):**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"REFRESH_TOKEN"}'
```

**5. Update profile (replace TOKEN):**
```bash
curl -X PUT "http://localhost:8000/api/auth/me?full_name=New%20Name" \
  -H "Authorization: Bearer TOKEN"
```

**6. Logout (replace TOKEN):**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer TOKEN"
```

### Automated Testing

Comprehensive test suite available in:
- `backend/tests/test_api_auth.py` - API endpoint tests
- `backend/tests/test_core_security.py` - Security utility tests
- `backend/tests/test_services_auth.py` - Authentication service tests

Run tests with:
```bash
# Using Docker
docker-compose exec backend pytest tests/test_api_auth.py -v

# Local (requires PostgreSQL)
cd backend && pytest tests/test_api_auth.py -v --cov=app.services.auth --cov=app.core.security
```

---

## Configuration

Authentication behavior is configured via environment variables in `.env`:

```env
# JWT Settings
JWT_SECRET_KEY=your-secret-key-here  # Change in production!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Security
SECRET_KEY=your-app-secret-key  # For general app encryption

# Rate Limiting
RATE_LIMIT_API_PER_MINUTE=100
```

**⚠️ Important:** Always change `JWT_SECRET_KEY` and `SECRET_KEY` in production environments!

---

## Migration Guide

The user authentication system requires the following database migration:

```bash
# Apply migrations
docker-compose exec backend alembic upgrade head

# Or locally
cd backend && alembic upgrade head
```

Migration creates the `users` table with:
- `id` (UUID, primary key)
- `email` (string, unique, indexed)
- `hashed_password` (string)
- `full_name` (string, nullable)
- `is_active` (boolean, default: true)
- `is_superuser` (boolean, default: false)
- `created_at` (datetime)
- `updated_at` (datetime)
- `oauth_provider` (string, nullable)
- `oauth_id` (string, nullable)

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints and schemas
- Test API calls directly from the browser
- See request/response examples
- Download OpenAPI specification (JSON/YAML)
