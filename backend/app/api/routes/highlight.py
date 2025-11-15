"""Highlight detection API endpoints."""

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.highlight import Highlight, HighlightStatus as HighlightStatusModel
from app.models.user import User
from app.models.video import Video
from app.schemas.highlight import (
    HighlightDetectionJob,
    HighlightDetectionRequest,
    HighlightListResponse,
    HighlightProgress,
    HighlightResponse,
    HighlightStatus,
    HighlightUpdateRequest,
)
from app.worker import enqueue_detect_highlights

router = APIRouter(prefix="/videos/{video_id}/highlights", tags=["highlights"])
highlight_router = APIRouter(prefix="/highlights", tags=["highlights"])


@router.post("/detect", response_model=HighlightDetectionJob)
async def trigger_highlight_detection(
    video_id: UUID,
    request: HighlightDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Trigger highlight detection for a video.

    Args:
        video_id: Video ID
        request: Detection configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        Job information with job_id
    """
    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Check if detection is already in progress
    redis_client = await redis.from_url(settings.redis_url)
    progress_key = f"highlight_detection:progress:{video_id}"
    existing_progress = await redis_client.get(progress_key)

    if existing_progress:
        progress_data = json.loads(existing_progress)
        if progress_data.get("progress", 0) < 100:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Highlight detection already in progress for this video",
            )

    # Enqueue detection job
    score_weights = None
    if request.score_weights:
        score_weights = {
            "audio_energy": request.score_weights.audio_energy,
            "scene_change": request.score_weights.scene_change,
            "speech_density": request.score_weights.speech_density,
            "keyword": request.score_weights.keyword,
        }

    job = await enqueue_detect_highlights(
        video_id=str(video_id),
        sensitivity=request.sensitivity.value,
        custom_keywords=request.keywords if request.keywords else None,
        score_weights=score_weights,
    )

    await redis_client.close()

    return HighlightDetectionJob(
        job_id=job.job_id,
        message=f"Highlight detection started for video {video_id}",
    )


@router.get("", response_model=HighlightListResponse)
async def list_highlights(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: HighlightStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by status",
    ),
    min_score: int | None = Query(
        default=None,
        ge=0,
        le=100,
        description="Minimum overall score",
    ),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    sort: str = Query(default="rank", description="Sort by: rank, score, time"),
) -> Any:
    """
    List all highlights for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session
        status_filter: Optional status filter
        min_score: Optional minimum score filter
        limit: Maximum results to return
        offset: Results offset for pagination
        sort: Sort field

    Returns:
        List of highlights with total count
    """
    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Build query
    query = select(Highlight).where(Highlight.video_id == video_id)

    # Apply filters
    if status_filter:
        query = query.where(Highlight.status == status_filter.value)

    if min_score is not None:
        query = query.where(Highlight.overall_score >= min_score)

    # Apply sorting
    if sort == "rank":
        query = query.order_by(Highlight.rank)
    elif sort == "score":
        query = query.order_by(Highlight.overall_score.desc())
    elif sort == "time":
        query = query.order_by(Highlight.start_time)

    # Get total count
    count_result = await db.execute(
        select(Highlight).where(Highlight.video_id == video_id)
    )
    total = len(count_result.scalars().all())

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    highlights = result.scalars().all()

    return HighlightListResponse(
        highlights=[HighlightResponse.model_validate(h) for h in highlights],
        total=total,
    )


@router.get("/progress", response_model=HighlightProgress)
async def get_detection_progress(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get highlight detection progress for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Progress information
    """
    # Verify video exists and belongs to user
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this video",
        )

    # Get progress from Redis
    redis_client = await redis.from_url(settings.redis_url)
    progress_key = f"highlight_detection:progress:{video_id}"
    progress_data = await redis_client.get(progress_key)
    await redis_client.close()

    if not progress_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No detection in progress for this video",
        )

    progress_dict = json.loads(progress_data)

    return HighlightProgress(**progress_dict)


@highlight_router.get("/{highlight_id}", response_model=HighlightResponse)
async def get_highlight(
    highlight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single highlight by ID.

    Args:
        highlight_id: Highlight ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Highlight details
    """
    # Get highlight
    result = await db.execute(select(Highlight).where(Highlight.id == highlight_id))
    highlight = result.scalar_one_or_none()

    if not highlight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Highlight not found",
        )

    # Verify video belongs to user
    video_result = await db.execute(
        select(Video).where(Video.id == highlight.video_id)
    )
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this highlight",
        )

    return HighlightResponse.model_validate(highlight)


@highlight_router.patch("/{highlight_id}", response_model=HighlightResponse)
async def update_highlight(
    highlight_id: UUID,
    update_data: HighlightUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a highlight.

    Args:
        highlight_id: Highlight ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated highlight
    """
    # Get highlight
    result = await db.execute(select(Highlight).where(Highlight.id == highlight_id))
    highlight = result.scalar_one_or_none()

    if not highlight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Highlight not found",
        )

    # Verify video belongs to user
    video_result = await db.execute(
        select(Video).where(Video.id == highlight.video_id)
    )
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this highlight",
        )

    # Update fields
    if update_data.rank is not None:
        highlight.rank = update_data.rank

    if update_data.status is not None:
        highlight.status = HighlightStatusModel(update_data.status.value)

    if update_data.start_time is not None:
        highlight.start_time = update_data.start_time

    if update_data.end_time is not None:
        highlight.end_time = update_data.end_time
        # Recalculate duration
        highlight.duration_seconds = highlight.end_time - highlight.start_time

    await db.commit()
    await db.refresh(highlight)

    return HighlightResponse.model_validate(highlight)


@highlight_router.delete("/{highlight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_highlight(
    highlight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    hard_delete: bool = Query(default=False, description="Permanently delete"),
) -> None:
    """
    Delete a highlight.

    Args:
        highlight_id: Highlight ID
        current_user: Current authenticated user
        db: Database session
        hard_delete: If True, permanently delete; if False, mark as rejected
    """
    # Get highlight
    result = await db.execute(select(Highlight).where(Highlight.id == highlight_id))
    highlight = result.scalar_one_or_none()

    if not highlight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Highlight not found",
        )

    # Verify video belongs to user
    video_result = await db.execute(
        select(Video).where(Video.id == highlight.video_id)
    )
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this highlight",
        )

    if hard_delete:
        # Permanently delete
        await db.delete(highlight)
    else:
        # Soft delete (mark as rejected)
        highlight.status = HighlightStatusModel.REJECTED

    await db.commit()
