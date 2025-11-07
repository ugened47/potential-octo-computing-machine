"""Pydantic schemas for request/response validation."""

from .auth import (
    AuthResponse,
    MessageResponse,
    PasswordReset,
    PasswordResetRequest,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from .clip import (
    ClipCreate,
    ClipProgress,
    ClipRead,
    SearchRequest,
    SearchResult,
)
from .silence import (
    SilenceDetectionResponse,
    SilenceRemovalProgress,
    SilenceRemovalRequest,
    SilenceSegment,
)
from .timeline import (
    Segment,
    SegmentCreate,
    WaveformData,
    WaveformStatus,
)
from .transcript import (
    TranscriptExportRequest,
    TranscriptProgress,
    TranscriptRead,
    WordTimestamp,
)

__all__ = [
    "AuthResponse",
    "MessageResponse",
    "PasswordReset",
    "PasswordResetRequest",
    "TokenRefresh",
    "TokenResponse",
    "UserLogin",
    "UserRegister",
    "UserResponse",
    "TranscriptRead",
    "TranscriptProgress",
    "TranscriptExportRequest",
    "WordTimestamp",
    "ClipCreate",
    "ClipRead",
    "ClipProgress",
    "SearchRequest",
    "SearchResult",
    "SilenceRemovalRequest",
    "SilenceDetectionResponse",
    "SilenceRemovalProgress",
    "SilenceSegment",
    "WaveformData",
    "WaveformStatus",
    "Segment",
    "SegmentCreate",
]
