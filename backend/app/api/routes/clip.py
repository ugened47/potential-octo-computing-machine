"""Clip API endpoints."""

from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.clip import Clip, ClipStatus
from app.models.user import User
from app.models.video import Video
from app.schemas.clip import (
    ClipCreate,
    ClipProgress,
    ClipRead,
    SearchRequest,
    SearchResult,
)
from app.services.clip_generation import ClipGenerationService
from app.services.search import SearchService

router = APIRouter(prefix="/videos/{video_id}/clips", tags=["clips"])
clip_router = APIRouter(prefix="/clips", tags=["clips"])


@router.post("/search", response_model=list[SearchResult])
async def search_transcript(
    video_id: UUID,
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Search transcript for keywords.

    Args:
        video_id: Video ID
        request: Search request with keywords
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of matching segments
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Search transcript
    service = SearchService(db)
    results = await service.search_transcript(
        video_id, request.keywords, request.padding_seconds
    )

    return [SearchResult(**result) for result in results]


@router.post("", response_model=ClipRead, status_code=status.HTTP_201_CREATED)
async def create_clip(
    video_id: UUID,
    clip_data: ClipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a clip from a video.

    Args:
        video_id: Video ID
        clip_data: Clip creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ClipRead: Created clip record
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Validate time range
    if clip_data.start_time >= clip_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be less than end time",
        )

    if video.duration and clip_data.end_time > video.duration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time exceeds video duration",
        )

    # Create clip record
    clip = Clip(
        video_id=video_id,
        title=clip_data.title,
        description=clip_data.description,
        keywords=clip_data.keywords,
        start_time=clip_data.start_time,
        end_time=clip_data.end_time,
        duration=clip_data.end_time - clip_data.start_time,
        status=ClipStatus.PROCESSING,
    )

    db.add(clip)
    await db.commit()
    await db.refresh(clip)

    # Enqueue clip generation job
    try:
        from app.worker import enqueue_generate_clip

        job = await enqueue_generate_clip(str(clip.id))
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to enqueue clip generation job: {e}")

    return ClipRead.model_validate(clip)


@router.get("", response_model=list[ClipRead])
async def list_clips(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all clips for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of clips
    """
    from sqlmodel import select

    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Get clips
    result = await db.execute(select(Clip).where(Clip.video_id == video_id))
    clips = result.scalars().all()

    return [ClipRead.model_validate(clip) for clip in clips]


@clip_router.get("/{clip_id}", response_model=ClipRead)
async def get_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get clip details.

    Args:
        clip_id: Clip ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ClipRead: Clip details
    """
    from sqlmodel import select

    # Get clip
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Verify video belongs to user
    result = await db.execute(select(Video).where(Video.id == clip.video_id))
    video = result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this clip",
        )

    return ClipRead.model_validate(clip)


@clip_router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clip(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a clip.

    Args:
        clip_id: Clip ID
        current_user: Current authenticated user
        db: Database session
    """
    from sqlmodel import select

    # Get clip
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Verify video belongs to user
    result = await db.execute(select(Video).where(Video.id == clip.video_id))
    video = result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this clip",
        )

    # Delete clip file from S3 if exists
    if clip.clip_url:
        try:
            from app.services.s3 import S3Service

            s3_service = S3Service()
            s3_service.delete_object(clip.clip_url)
        except Exception:
            # Log but don't fail if S3 deletion fails
            pass

    # Delete clip record
    await db.delete(clip)
    await db.commit()


@clip_router.get("/{clip_id}/progress", response_model=ClipProgress)
async def get_clip_progress(
    clip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get clip generation progress.

    Args:
        clip_id: Clip ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ClipProgress: Progress information
    """
    from sqlmodel import select

    # Get clip
    result = await db.execute(select(Clip).where(Clip.id == clip_id))
    clip = result.scalar_one_or_none()

    if not clip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found"
        )

    # Verify video belongs to user
    result = await db.execute(select(Video).where(Video.id == clip.video_id))
    video = result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this clip",
        )

    # Get progress from Redis
    redis_client = await redis.from_url(settings.redis_url)
    progress_key = f"clip_generation:progress:{clip_id}"

    try:
        import json

        progress_data = await redis_client.get(progress_key)
        if progress_data:
            data = json.loads(progress_data)
            return ClipProgress(
                clip_id=clip_id,
                progress=data.get("progress", 0),
                status=data.get("status", "Unknown"),
                estimated_time_remaining=data.get("estimated_time_remaining"),
            )
        else:
            # Check clip status
            if clip.status == ClipStatus.COMPLETED:
                return ClipProgress(clip_id=clip_id, progress=100, status="Completed")
            elif clip.status == ClipStatus.FAILED:
                return ClipProgress(clip_id=clip_id, progress=0, status="Failed")
            else:
                return ClipProgress(clip_id=clip_id, progress=0, status="Processing")
    finally:
        await redis_client.aclose()

