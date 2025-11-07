"""Timeline API endpoints for waveform and segments."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.timeline import (
    Segment,
    SegmentCreate,
    WaveformData,
    WaveformStatus,
)
from app.services.waveform import WaveformService

router = APIRouter(prefix="/videos/{video_id}/timeline", tags=["timeline"])


@router.get("/waveform", response_model=WaveformData)
async def get_waveform(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get waveform data for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        WaveformData: Waveform data with peaks, duration, and sample_rate
    """
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

    # Check if waveform exists
    waveform_service = WaveformService(db)
    waveform_s3_key = f"waveforms/{video.user_id}/{video_id}/waveform.json"

    try:
        waveform_data = waveform_service.get_waveform_data(waveform_s3_key)
        return WaveformData(**waveform_data)
    except ValueError:
        # Waveform doesn't exist, return processing status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waveform not found. Please generate it first.",
        )


@router.post("/waveform", response_model=WaveformStatus)
async def generate_waveform(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger waveform generation for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        WaveformStatus: Status of waveform generation
    """
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

    # Check if waveform already exists
    waveform_service = WaveformService(db)
    waveform_s3_key = f"waveforms/{video.user_id}/{video_id}/waveform.json"

    try:
        waveform_data = waveform_service.get_waveform_data(waveform_s3_key)
        # Waveform already exists
        return WaveformStatus(status="completed", progress=100)
    except ValueError:
        # Waveform doesn't exist, generate it
        # In production, this would be enqueued as a background job
        # For MVP, we'll generate it synchronously
        try:
            waveform_data = await waveform_service.generate_waveform(video_id)
            return WaveformStatus(status="completed", progress=100)
        except Exception as e:
            return WaveformStatus(status="failed", progress=0)


@router.get("/waveform/status", response_model=WaveformStatus)
async def get_waveform_status(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get waveform generation status.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        WaveformStatus: Status of waveform generation
    """
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

    # Check if waveform exists
    waveform_service = WaveformService(db)
    waveform_s3_key = f"waveforms/{video.user_id}/{video_id}/waveform.json"

    try:
        waveform_service.get_waveform_data(waveform_s3_key)
        return WaveformStatus(status="completed", progress=100)
    except ValueError:
        return WaveformStatus(status="processing", progress=0)


@router.post("/segments", response_model=list[Segment])
async def save_segments(
    video_id: UUID,
    segments: list[SegmentCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Save segment selections for a video.

    Args:
        video_id: Video ID
        segments: List of segments to save
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of saved segments
    """
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

    # Validate segments
    for segment in segments:
        if segment.start_time >= segment.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Segment {segment.id}: start_time must be less than end_time",
            )
        if video.duration and segment.end_time > video.duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Segment {segment.id}: end_time exceeds video duration",
            )

    # For MVP, we'll store segments in memory or a simple storage
    # In production, this would be stored in database
    # For now, return the segments as-is
    return [
        Segment(
            id=seg.id,
            start_time=seg.start_time,
            end_time=seg.end_time,
            selected=seg.selected,
        )
        for seg in segments
    ]


@router.get("/segments", response_model=list[Segment])
async def get_segments(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get saved segment selections for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of segments
    """
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

    # For MVP, return empty list (segments stored in frontend state)
    # In production, this would fetch from database
    return []


@router.delete("/segments")
async def delete_segments(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Clear all segment selections for a video.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
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

    # For MVP, just return success
    return {"message": "Segments cleared"}

