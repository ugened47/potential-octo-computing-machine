"""Export API endpoints."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models import Export, ExportStatus, Video
from app.models.user import User
from app.schemas.export import (
    ExportCreateRequest,
    ExportDownloadResponse,
    ExportListResponse,
    ExportProgressResponse,
    ExportRead,
)

router = APIRouter(prefix="/videos/{video_id}/exports", tags=["exports"])
export_router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
async def create_export(
    video_id: UUID,
    export_data: ExportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new export job for a video.

    Args:
        video_id: Video ID
        export_data: Export configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created export record
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

    # Validate video is completed
    if video.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video must be in completed status to export",
        )

    # Validate segments
    video_duration = video.duration or 0
    for segment in export_data.segments:
        if segment.start_time < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Segment start time must be >= 0",
            )
        if segment.end_time > video_duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Segment end time {segment.end_time}s exceeds video duration {video_duration}s",
            )
        if segment.start_time >= segment.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Segment start time must be less than end time",
            )

    # Check rate limiting (10 exports per hour per user)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(Export).where(
            Export.user_id == current_user.id,
            Export.created_at >= one_hour_ago,
        )
    )
    recent_exports = result.scalars().all()
    if len(recent_exports) >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Export rate limit exceeded. Maximum 10 exports per hour.",
        )

    # Create export record
    export = Export(
        video_id=video_id,
        user_id=current_user.id,
        export_type=export_data.export_type,
        resolution=export_data.resolution,
        format=export_data.format,
        quality_preset=export_data.quality_preset,
        segment_selections=[
            {
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "clip_id": str(seg.clip_id) if seg.clip_id else None,
            }
            for seg in export_data.segments
        ],
        status=ExportStatus.PENDING,
        progress_percentage=0,
    )

    db.add(export)
    await db.commit()
    await db.refresh(export)

    # Enqueue export job
    try:
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.enqueue_job(
            "export_video",
            str(export.id),
        )
        await redis_client.aclose()
    except Exception as e:
        # If job enqueue fails, mark export as failed
        export.status = ExportStatus.FAILED
        export.error_message = f"Failed to enqueue export job: {str(e)}"
        await db.commit()
        await db.refresh(export)

    return export


@router.get("", response_model=ExportListResponse)
async def list_exports(
    video_id: UUID,
    page: int = 1,
    limit: int = 10,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all exports for a video.

    Args:
        video_id: Video ID
        page: Page number (default: 1)
        limit: Items per page (default: 10)
        status_filter: Optional status filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of exports
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

    # Build query
    query = select(Export).where(Export.video_id == video_id)

    if status_filter:
        query = query.where(Export.status == status_filter)

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.order_by(Export.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    exports = result.scalars().all()

    return ExportListResponse(
        exports=exports,
        total=total,
        page=page,
        limit=limit,
        has_more=total > page * limit,
    )


@export_router.get("/{export_id}", response_model=ExportRead)
async def get_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get export details.

    Args:
        export_id: Export ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Export record
    """
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export not found"
        )

    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this export",
        )

    return export


@export_router.get("/{export_id}/progress", response_model=ExportProgressResponse)
async def get_export_progress(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get real-time export progress.

    Args:
        export_id: Export ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Export progress data
    """
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export not found"
        )

    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this export",
        )

    # Get progress from Redis
    redis_client = redis.from_url(settings.redis_url)
    try:
        progress_data = await redis_client.hgetall(f"export_progress:{export_id}")
        await redis_client.aclose()

        current_stage = None
        estimated_time_remaining = None
        elapsed_time = None

        if progress_data:
            current_stage = progress_data.get(b"stage", b"").decode()
            if b"estimated_time" in progress_data:
                estimated_time_remaining = int(
                    progress_data[b"estimated_time"].decode()
                )
            if b"elapsed_time" in progress_data:
                elapsed_time = int(progress_data[b"elapsed_time"].decode())
    except Exception:
        current_stage = None
        estimated_time_remaining = None
        elapsed_time = None
        await redis_client.aclose()

    return ExportProgressResponse(
        export_id=export.id,
        status=export.status,
        progress_percentage=export.progress_percentage,
        current_stage=current_stage,
        estimated_time_remaining=estimated_time_remaining,
        elapsed_time=elapsed_time,
    )


@export_router.get("/{export_id}/download", response_model=ExportDownloadResponse)
async def get_export_download_url(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate download URL for completed export.

    Args:
        export_id: Export ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Presigned download URL
    """
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export not found"
        )

    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this export",
        )

    if export.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not completed yet. Current status: {export.status}",
        )

    if not export.output_s3_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export output file not found",
        )

    # Generate presigned URL (1 hour expiration)
    import boto3

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
    )

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": export.output_s3_key,
        },
        ExpiresIn=3600,  # 1 hour
    )

    expires_at = datetime.utcnow() + timedelta(hours=1)

    return ExportDownloadResponse(
        url=presigned_url,
        expires_at=expires_at,
        file_size_bytes=export.file_size_bytes,
    )


@export_router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Cancel or delete an export.

    Args:
        export_id: Export ID
        current_user: Current authenticated user
        db: Database session
    """
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export not found"
        )

    if export.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this export",
        )

    # If processing, mark as cancelled
    if export.status == ExportStatus.PROCESSING:
        export.status = ExportStatus.CANCELLED
        await db.commit()

        # Set cancellation flag in Redis
        try:
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.set(f"export_cancel:{export_id}", "1", ex=3600)
            await redis_client.aclose()
        except Exception:
            pass

    # Delete S3 files if they exist
    if export.output_s3_key:
        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            )
            s3_client.delete_object(
                Bucket=settings.s3_bucket, Key=export.output_s3_key
            )
        except Exception:
            pass  # Best effort deletion

    # Delete export record
    await db.delete(export)
    await db.commit()
