"""Video Export API endpoints."""

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.deps import get_current_user, get_db
from app.models import ExportStatus, SocialMediaTemplate, Video, VideoExport
from app.models.user import User
from app.schemas.export import (
    ExportCreate,
    ExportList,
    ExportProgress,
    ExportRead,
    ExportResponse,
)

router = APIRouter()


@router.post("/videos/{video_id}/export", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def create_export(
    video_id: UUID,
    export_in: ExportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a video export with template."""
    # Verify video exists and user owns it
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export this video",
        )

    # Verify template exists
    template_result = await db.execute(
        select(SocialMediaTemplate).where(SocialMediaTemplate.id == export_in.template_id)
    )
    template = template_result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Create export record
    export = VideoExport(
        video_id=video_id,
        template_id=export_in.template_id,
        segment_start_time=export_in.segment_start_time,
        segment_end_time=export_in.segment_end_time,
        crop_strategy=export_in.crop_strategy,
        status=ExportStatus.PROCESSING,
    )

    db.add(export)
    await db.commit()
    await db.refresh(export)

    # TODO: Enqueue ARQ background job here
    job_id = f"export_{export.id}"

    return ExportResponse(
        export_id=export.id,
        job_id=job_id,
        message="Export started successfully",
    )


@router.get("/videos/{video_id}/exports", response_model=ExportList)
async def list_video_exports(
    video_id: UUID,
    status: ExportStatus | None = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all exports for a video."""
    # Verify video exists and user owns it
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this video",
        )

    # Build query
    query = select(VideoExport).where(VideoExport.video_id == video_id)

    if status:
        query = query.where(VideoExport.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(VideoExport.created_at.desc()).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    exports = result.scalars().all()

    return ExportList(exports=exports, total=total or 0)


@router.get("/exports/{export_id}", response_model=ExportRead)
async def get_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get single export by ID."""
    result = await db.execute(select(VideoExport).where(VideoExport.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    # Verify user owns the video
    video_result = await db.execute(select(Video).where(Video.id == export.video_id))
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this export",
        )

    return export


@router.delete("/exports/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an export."""
    result = await db.execute(select(VideoExport).where(VideoExport.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    # Verify user owns the video
    video_result = await db.execute(select(Video).where(Video.id == export.video_id))
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this export",
        )

    # TODO: Delete S3 file if exists

    # Delete export record
    await db.delete(export)
    await db.commit()


@router.get("/exports/{export_id}/progress", response_model=ExportProgress)
async def get_export_progress(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get export progress."""
    result = await db.execute(select(VideoExport).where(VideoExport.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    # Verify user owns the video
    video_result = await db.execute(select(Video).where(Video.id == export.video_id))
    video = video_result.scalar_one_or_none()

    if not video or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this export",
        )

    # TODO: Get progress from Redis
    # For now, return basic progress based on status
    if export.status == ExportStatus.COMPLETED:
        progress = 100
        stage = "completed"
    elif export.status == ExportStatus.FAILED:
        progress = 0
        stage = "failed"
    else:
        progress = 50
        stage = "processing"

    return ExportProgress(
        progress=progress,
        status=export.status,
        current_stage=stage,
        estimated_time_remaining=None,
    )
