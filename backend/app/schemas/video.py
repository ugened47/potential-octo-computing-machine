"""Video schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class PresignedUrlRequest(BaseModel):
    """Request schema for presigned URL generation."""

    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")


class PresignedUrlResponse(BaseModel):
    """Response schema for presigned URL generation."""

    presigned_url: str = Field(..., description="Presigned URL for direct upload")
    video_id: UUID = Field(..., description="Video ID created for this upload")
    s3_key: str = Field(..., description="S3 key where the file will be stored")


class VideoCreate(BaseModel):
    """Request schema for creating a video record after upload."""

    video_id: UUID = Field(..., description="Video ID from presigned URL response")
    title: str = Field(..., max_length=255, description="Video title")
    description: str | None = Field(None, description="Video description")
    s3_key: str = Field(..., description="S3 key where the file was uploaded")


class VideoUpdate(BaseModel):
    """Request schema for updating video metadata."""

    title: str | None = Field(None, max_length=255, description="Video title")
    description: str | None = Field(None, description="Video description")


# Response schemas
class VideoRead(BaseModel):
    """Response schema for video data."""

    id: UUID
    user_id: UUID
    title: str
    description: str | None
    file_size: int | None
    format: str | None
    duration: float | None
    resolution: str | None
    s3_key: str | None
    cloudfront_url: str | None
    thumbnail_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
