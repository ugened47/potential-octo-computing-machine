"""Main FastAPI application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.cache import close_redis
from app.core.config import settings
from app.core.db import close_db, init_db
from app.core.error_handler import (
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException
from app.core.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()
    await close_redis()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered video editing and clipping",
    version="0.1.0",
    lifespan=lifespan,
)

# Compression middleware (should be early in the stack)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.rate_limit_api_per_minute,
    period=60,
)

# Register exception handlers (order matters - most specific first)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(PydanticValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "AI Video Editor API", "version": "0.1.0"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Register routers
from app.api.routes import (
    auth,
    clip,
    dashboard,
    export,
    silence,
    timeline,
    transcript,
    video,
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(transcript.router, prefix="/api", tags=["transcripts"])
app.include_router(video.upload_router, prefix="/api/upload", tags=["upload"])
app.include_router(video.video_router, prefix="/api/videos", tags=["videos"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(silence.router, prefix="/api", tags=["silence"])
app.include_router(clip.router, prefix="/api", tags=["clips"])
app.include_router(clip.clip_router, prefix="/api", tags=["clips"])
app.include_router(timeline.router, prefix="/api", tags=["timeline"])
app.include_router(export.router, prefix="/api", tags=["exports"])
app.include_router(export.export_router, prefix="/api", tags=["exports"])
