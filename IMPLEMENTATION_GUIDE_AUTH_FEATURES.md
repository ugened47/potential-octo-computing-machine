# Implementation Guide: Missing Auth Features

## Overview

This guide provides complete specifications and implementation steps for the three missing authentication features:
1. Password Reset
2. Email Verification
3. Google OAuth

## Status

- **Current Completion:** 40%
- **With These Features:** 100%
- **Estimated Time:** 4-6 hours
- **Priority:** Medium (nice-to-have for MVP)

---

## 1. Password Reset

### Database Changes (Already Applied)

The User model now includes:
```python
password_reset_token: str | None
password_reset_expires: datetime | None
```

### Migration Needed

Create migration:
```bash
cd backend
alembic revision --autogenerate -m "add password reset fields"
alembic upgrade head
```

Or manual migration:
```python
# backend/alembic/versions/XXXXX_add_password_reset.py
def upgrade():
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
```

### Backend Implementation

#### 1.1 Update Schemas

```python
# backend/app/schemas/auth.py

from pydantic import BaseModel, EmailStr

class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset."""
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    """Response for password reset initiation."""
    message: str
    email: str

class ResetPasswordRequest(BaseModel):
    """Request to reset password."""
    token: str
    new_password: str = Field(min_length=8, max_length=100)

class ResetPasswordResponse(BaseModel):
    """Response for password reset."""
    message: str
```

#### 1.2 Create Password Reset Service

```python
# backend/app/services/password_reset.py

import secrets
from datetime import datetime, timedelta
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash

class PasswordResetService:
    """Service for password reset operations."""

    @staticmethod
    def generate_reset_token() -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    async def initiate_reset(db: AsyncSession, email: str) -> User | None:
        """
        Generate reset token for user.

        Returns:
            User if found, None otherwise
        """
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Generate token (valid for 1 hour)
        user.password_reset_token = PasswordResetService.generate_reset_token()
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def verify_and_reset(
        db: AsyncSession, token: str, new_password: str
    ) -> tuple[bool, str]:
        """
        Verify reset token and update password.

        Returns:
            (success: bool, message: str)
        """
        # Find user with token
        result = await db.execute(
            select(User).where(User.password_reset_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "Invalid reset token"

        # Check if token expired
        if user.password_reset_expires < datetime.utcnow():
            return False, "Reset token has expired"

        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None

        db.add(user)
        await db.commit()

        return True, "Password reset successful"
```

#### 1.3 Add API Endpoints

```python
# backend/app/api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services.password_reset import PasswordResetService
from app.services.email import EmailService  # You'll need to create this

router = APIRouter()

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate password reset process.

    Generates reset token and sends email to user.
    Always returns success even if email not found (security).
    """
    user = await PasswordResetService.initiate_reset(db, request.email)

    if user:
        # Send email with reset link
        reset_url = f"https://yourapp.com/reset-password?token={user.password_reset_token}"

        # TODO: Implement email sending
        # await EmailService.send_password_reset_email(user.email, reset_url)

        # For development, log the token
        print(f"Password reset token for {user.email}: {user.password_reset_token}")

    # Always return success (don't reveal if email exists)
    return ForgotPasswordResponse(
        message="If that email exists, a password reset link has been sent",
        email=request.email,
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Complete password reset with token."""
    success, message = await PasswordResetService.verify_and_reset(
        db, request.token, request.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return ResetPasswordResponse(message=message)
```

#### 1.4 Email Service (Stub)

```python
# backend/app/services/email.py

class EmailService:
    """Email service for sending transactional emails."""

    @staticmethod
    async def send_password_reset_email(email: str, reset_url: str):
        """
        Send password reset email.

        TODO: Implement with SendGrid, AWS SES, or similar
        """
        print(f"Sending password reset email to {email}")
        print(f"Reset URL: {reset_url}")

        # Implementation would look like:
        # - Use email template
        # - Send via email provider
        # - Handle failures gracefully
```

### Frontend Integration

The frontend already has:
- ✅ ForgotPasswordForm component
- ✅ ResetPasswordForm component
- ✅ UI pages at /forgot-password and /reset-password

Just need to connect to new endpoints in `lib/api-client.ts`.

### Tests

```python
# backend/tests/test_password_reset.py

import pytest
from datetime import datetime, timedelta
from app.services.password_reset import PasswordResetService

@pytest.mark.asyncio
async def test_initiate_password_reset(db_session, test_user):
    """Test password reset initiation."""
    user = await PasswordResetService.initiate_reset(db_session, test_user.email)

    assert user is not None
    assert user.password_reset_token is not None
    assert user.password_reset_expires is not None

@pytest.mark.asyncio
async def test_reset_password_with_valid_token(db_session, test_user):
    """Test password reset with valid token."""
    # Initiate reset
    user = await PasswordResetService.initiate_reset(db_session, test_user.email)
    token = user.password_reset_token

    # Reset password
    success, message = await PasswordResetService.verify_and_reset(
        db_session, token, "NewPassword123!"
    )

    assert success is True
    assert "successful" in message.lower()

@pytest.mark.asyncio
async def test_reset_password_with_expired_token(db_session, test_user):
    """Test password reset with expired token."""
    # Initiate reset
    user = await PasswordResetService.initiate_reset(db_session, test_user.email)
    token = user.password_reset_token

    # Manually expire the token
    user.password_reset_expires = datetime.utcnow() - timedelta(hours=1)
    db_session.add(user)
    await db_session.commit()

    # Try to reset
    success, message = await PasswordResetService.verify_and_reset(
        db_session, token, "NewPassword123!"
    )

    assert success is False
    assert "expired" in message.lower()
```

---

## 2. Email Verification

### Database Changes (Already Applied)

```python
email_verified: bool = Field(default=False)
email_verification_token: str | None
email_verification_expires: datetime | None
```

### Implementation Steps

Very similar to password reset:

1. Create `EmailVerificationService`
2. Add endpoints:
   - POST `/api/auth/verify-email` - Verify with token
   - POST `/api/auth/resend-verification` - Resend email
3. Update registration to set `email_verified=False` and send verification email
4. Add tests

**Code structure identical to password reset above.**

---

## 3. Google OAuth

### Prerequisites

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### Environment Variables

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback/google
```

### Backend Implementation

#### 3.1 OAuth Service

```python
# backend/app/services/oauth.py

from google.oauth2 import id_token
from google.auth.transport import requests
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.core.config import settings

class OAuthService:
    """Service for OAuth operations."""

    @staticmethod
    async def verify_google_token(token: str) -> dict | None:
        """
        Verify Google ID token.

        Returns:
            User info dict or None if invalid
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return None

            return {
                'email': idinfo['email'],
                'name': idinfo.get('name'),
                'google_id': idinfo['sub'],
                'email_verified': idinfo.get('email_verified', False),
            }
        except ValueError:
            return None

    @staticmethod
    async def get_or_create_oauth_user(
        db: AsyncSession, user_info: dict
    ) -> User:
        """Get existing user or create new one from OAuth."""
        # Try to find existing user
        result = await db.execute(
            select(User).where(
                (User.email == user_info['email']) |
                (User.oauth_id == user_info['google_id'])
            )
        )
        user = result.scalar_one_or_none()

        if user:
            # Update OAuth info if needed
            if not user.oauth_id:
                user.oauth_provider = 'google'
                user.oauth_id = user_info['google_id']
                user.email_verified = user_info['email_verified']
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user

        # Create new user
        user = User(
            email=user_info['email'],
            full_name=user_info['name'],
            hashed_password='',  # No password for OAuth users
            oauth_provider='google',
            oauth_id=user_info['google_id'],
            email_verified=user_info['email_verified'],
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user
```

#### 3.2 OAuth Endpoints

```python
# backend/app/api/routes/auth.py

@router.get("/oauth/google/url")
async def get_google_oauth_url():
    """Get Google OAuth authorization URL."""
    # TODO: Generate proper OAuth URL
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
    }

    url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return {"url": url}

@router.post("/oauth/google")
async def google_oauth_callback(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Verify token and create/login user.
    """
    user_info = await OAuthService.verify_google_token(token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    user = await OAuthService.get_or_create_oauth_user(db, user_info)

    # Generate JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }
```

### Frontend Integration

The GoogleOAuthButton component already exists. Just needs to:
1. Call `/api/auth/oauth/google/url` to get OAuth URL
2. Redirect user to Google
3. Handle callback with token
4. Call `/api/auth/oauth/google` with token

---

## Testing Strategy

### Unit Tests
- Test each service method independently
- Mock database and external services
- Cover success and error cases

### Integration Tests
- Test full endpoint flows
- Use test database
- Verify database state changes

### E2E Tests
- Test through UI
- Verify email sending (use test email service)
- Test token expiration
- Test OAuth flow (can mock Google)

---

## Deployment Checklist

- [ ] Configure email service (SendGrid, AWS SES, etc.)
- [ ] Set up Google OAuth app and get credentials
- [ ] Add environment variables to production
- [ ] Test email delivery in staging
- [ ] Test OAuth flow in staging
- [ ] Monitor error rates after deploy

---

## Estimated Implementation Time

- **Password Reset:** 2-3 hours
- **Email Verification:** 1-2 hours
- **Google OAuth:** 2-3 hours
- **Testing:** 2 hours
- **Total:** 7-10 hours

---

## Priority Recommendation

**For MVP:** Password reset is most important. Email verification and OAuth are nice-to-have.

**Quick Win:** Implement password reset first (highest user value, simplest implementation).

