"""Silence removal API endpoints."""

from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.video import Video
from app.schemas.silence import (
    SilenceDetectionResponse,
    SilenceRemovalProgress,
    SilenceRemovalRequest,
    SilenceSegment,
)
from app.services.silence_removal import SilenceRemovalService

router = APIRouter(prefix="/videos/{video_id}/silence", tags=["silence"])


@router.get("/segments", response_model=SilenceDetectionResponse)
async def detect_silence_segments(
    video_id: UUID,
    threshold_db: int = -40,
    min_duration_ms: int = 1000,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Detect silent segments in a video (preview only, doesn't modify video).

    Args:
        video_id: Video ID
        threshold_db: Silence threshold in dB (-60 to -20)
        min_duration_ms: Minimum silence duration in milliseconds (500 to 5000)
        current_user: Current authenticated user
        db: Database session

    Returns:
        SilenceDetectionResponse: Detected silent segments
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Detect silence
    service = SilenceRemovalService(db)
    segments = await service.detect_silence(
        video_id, threshold_db=threshold_db, min_duration_ms=min_duration_ms
    )

    # Calculate statistics
    total_duration = sum(seg["duration"] for seg in segments)
    original_duration = video.duration or 0.0
    reduction_percentage = (
        (total_duration / original_duration * 100) if original_duration > 0 else 0.0
    )

    return SilenceDetectionResponse(
        segments=[SilenceSegment(**seg) for seg in segments],
        total_duration=total_duration,
        original_duration=original_duration,
        reduction_percentage=reduction_percentage,
    )


@router.post("/remove", status_code=status.HTTP_202_ACCEPTED)
async def remove_silence(
    video_id: UUID,
    request: SilenceRemovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Trigger silence removal for a video.

    Args:
        video_id: Video ID
        request: Silence removal parameters
        current_user: Current authenticated user
        db: Database session

    Returns:
        dict: Success message
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Enqueue silence removal job
    try:
        from app.worker import enqueue_remove_silence

        job = await enqueue_remove_silence(
            str(video_id),
            threshold_db=request.threshold_db,
            min_duration_ms=request.min_duration_ms,
            excluded_segments=request.excluded_segments or [],
        )
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to enqueue silence removal job: {e}")

    return {
        "message": "Silence removal job enqueued",
        "video_id": str(video_id),
    }


@router.get("/progress", response_model=SilenceRemovalProgress)
async def get_silence_removal_progress(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get silence removal progress for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        SilenceRemovalProgress: Progress information
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Get progress from Redis
    redis_client = await redis.from_url(settings.redis_url)
    progress_key = f"silence_removal:progress:{video_id}"

    try:
        import json

        progress_data = await redis_client.get(progress_key)
        if progress_data:
            data = json.loads(progress_data)
            return SilenceRemovalProgress(
                video_id=str(video_id),
                progress=data.get("progress", 0),
                status=data.get("status", "Unknown"),
                estimated_time_remaining=data.get("estimated_time_remaining"),
            )
        else:
            return SilenceRemovalProgress(video_id=str(video_id), progress=0, status="Not started")
    finally:
        await redis_client.aclose()
