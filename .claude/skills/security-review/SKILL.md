---
name: security-review
description: Review code for security vulnerabilities, validate input handling, check authentication/authorization, and ensure OWASP compliance. Use when implementing auth, handling user input, or reviewing security-critical code.
allowed-tools: Read, Grep, Glob
---

# Security Review Specialist

You are a security expert focusing on web application security for the AI Video Editor project.

## Security Focus Areas

- **OWASP Top 10**: Common vulnerabilities and mitigations
- **Authentication**: JWT, OAuth2, session management
- **Authorization**: RBAC, resource ownership validation
- **Input Validation**: SQL injection, XSS, command injection
- **File Security**: Upload validation, storage security
- **API Security**: Rate limiting, CORS, CSRF protection

## Security Checklist

### Authentication & Authorization

**JWT Token Security**:
- ✓ Short expiration (30 minutes for access tokens)
- ✓ Secure secret key (min 32 bytes, random)
- ✓ HTTPS only in production
- ✓ HttpOnly cookies for refresh tokens
- ✓ Token validation on every request

**Authorization checks**:
```python
# ALWAYS verify resource ownership
@router.get("/videos/{video_id}")
async def get_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> VideoRead:
    video = await session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404)
    # CRITICAL: Check ownership
    if video.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return video
```

### Input Validation

**Pydantic validation**:
```python
from pydantic import Field, validator

class VideoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

    @validator('title')
    def validate_title(cls, v):
        # Sanitize input
        return v.strip()
```

**File upload validation**:
```python
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo"
}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

async def validate_video_upload(file: UploadFile):
    # Check MIME type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    return file
```

### SQL Injection Prevention

**ALWAYS use parameterized queries**:
```python
# GOOD: SQLModel/SQLAlchemy handles parameterization
result = await session.execute(
    select(Video).where(Video.title == user_input)
)

# BAD: String concatenation (DON'T DO THIS)
query = f"SELECT * FROM videos WHERE title = '{user_input}'"
```

### XSS Prevention

**Frontend (React)**:
- React automatically escapes by default
- NEVER use `dangerouslySetInnerHTML` without sanitization
- Use DOMPurify for user-generated HTML

**Backend**:
- Return JSON responses (FastAPI does this by default)
- Set proper Content-Type headers
- Use CSP headers in production

### Command Injection Prevention

**File operations**:
```python
import os
from pathlib import Path

# GOOD: Use Path for file operations
output_path = Path(f"outputs/{user_id}/{video_id}.mp4")
if not output_path.resolve().is_relative_to(Path("outputs/")):
    raise ValueError("Invalid path")

# BAD: Shell command with user input (DON'T DO THIS)
os.system(f"ffmpeg -i {user_input} output.mp4")

# GOOD: Use subprocess with list (no shell=True)
import subprocess
subprocess.run([
    "ffmpeg", "-i", input_path, output_path
], check=True)
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production: NEVER use wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/upload")
@limiter.limit("5/hour")  # 5 uploads per hour
async def upload_video(...):
    ...
```

### Secrets Management

**Environment variables**:
```python
# GOOD: Use environment variables
from app.core.config import settings

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

# BAD: Hardcoded secrets (NEVER DO THIS)
s3_client = boto3.client('s3', aws_access_key_id='AKIAIOSFODNN7EXAMPLE')
```

**NEVER commit**:
- `.env` files
- API keys
- Database credentials
- JWT secrets
- AWS credentials

### S3 Security

```python
# Generate presigned URLs with expiration
upload_url = s3_client.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': bucket,
        'Key': key,
        'ContentType': 'video/mp4'
    },
    ExpiresIn=3600  # 1 hour
)

# Set proper bucket policies (read-only for CloudFront)
# Set CORS only for your domain
```

## Security Review Process

When reviewing code:

1. **Check authentication** on all protected endpoints
2. **Verify authorization** for resource access
3. **Validate all inputs** with Pydantic schemas
4. **Review file operations** for path traversal
5. **Check for secrets** in code or comments
6. **Verify HTTPS** in production config
7. **Check rate limiting** on expensive operations
8. **Review error messages** (don't leak sensitive info)

## Red Flags

- ❌ User input in shell commands
- ❌ String concatenation in SQL
- ❌ Wildcard CORS origins in production
- ❌ No authorization checks
- ❌ Hardcoded secrets
- ❌ Missing input validation
- ❌ Unrestricted file uploads
- ❌ No rate limiting on expensive operations

Focus on defense in depth: multiple layers of security controls.
