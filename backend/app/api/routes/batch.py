"""Batch processing API endpoints."""

import asyncio
import json
from typing import Any, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import redis.asyncio as redis

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.batch import BatchJob, BatchJobStatus, BatchVideo
from app.models.user import User
from app.schemas.batch import (
    AddVideosRequest,
    BatchExportRequest,
    BatchExportResponse,
    BatchJobCreate,
    BatchJobCreateResponse,
    BatchJobListResponse,
    BatchJobResponse,
    BatchJobStartResponse,
    BatchProgressEvent,
    BatchVideoResponse,
)
from app.services.batch_export import BatchExportService
from app.services.batch_upload import BatchUploadService
from app.worker import enqueue_export_batch_job, enqueue_process_batch_job

router = APIRouter()


async def verify_batch_ownership(
    batch_job_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> BatchJob:
    """Verify user owns the batch job and return it.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJob: Batch job object

    Raises:
        HTTPException: If batch not found or user doesn't own it
    """
    result = await db.execute(select(BatchJob).where(BatchJob.id == batch_job_id))
    batch_job = result.scalar_one_or_none()

    if not batch_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    if batch_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this batch job",
        )

    return batch_job


@router.post("", response_model=BatchJobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_job(
    request: BatchJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new batch job and generate presigned URLs for video uploads.

    Args:
        request: Batch job creation request
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobCreateResponse: Created batch job and upload URLs
    """
    try:
        service = BatchUploadService(db)
        batch_job, upload_urls = await service.create_batch_upload(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            settings=request.settings.model_dump(),
            video_count=request.video_count,
        )

        return BatchJobCreateResponse(
            batch_job=BatchJobResponse.model_validate(batch_job),
            upload_urls=upload_urls,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{batch_job_id}/videos", response_model=BatchJobResponse)
async def add_videos_to_batch(
    batch_job_id: UUID,
    request: AddVideosRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add existing videos to a batch job.

    Args:
        batch_job_id: Batch job ID
        request: Add videos request
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Updated batch job
    """
    # Verify ownership
    await verify_batch_ownership(batch_job_id, current_user, db)

    try:
        service = BatchUploadService(db)
        batch_job = await service.add_videos_to_batch(
            batch_job_id=batch_job_id,
            video_ids=request.video_ids,
            user_id=current_user.id,
        )

        return BatchJobResponse.model_validate(batch_job)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{batch_job_id}/start", response_model=BatchJobStartResponse)
async def start_batch_processing(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Start processing a batch job.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobStartResponse: Job ID and updated batch job
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    # Check if already processing
    if batch_job.status not in [BatchJobStatus.PENDING, BatchJobStatus.PAUSED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch is already processing or completed",
        )

    # Validate all videos are uploaded
    service = BatchUploadService(db)
    is_valid, error_message = await service.validate_uploads_complete(
        batch_job_id=batch_job_id,
        user_id=current_user.id,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Enqueue processing job
    job = await enqueue_process_batch_job(str(batch_job_id))

    return BatchJobStartResponse(
        job_id=job.job_id,
        batch_job=BatchJobResponse.model_validate(batch_job),
    )


@router.get("", response_model=BatchJobListResponse)
async def list_batch_jobs(
    status_filter: BatchJobStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at", regex="^(created_at|priority|status)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all batch jobs for the current user.

    Args:
        status_filter: Filter by status (optional)
        limit: Number of results to return
        offset: Number of results to skip
        sort: Sort field
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobListResponse: List of batch jobs
    """
    # Build query
    query = select(BatchJob).where(BatchJob.user_id == current_user.id)

    if status_filter:
        query = query.where(BatchJob.status == status_filter)

    # Apply sorting
    if sort == "created_at":
        query = query.order_by(BatchJob.created_at.desc())
    elif sort == "priority":
        query = query.order_by(BatchJob.priority.desc(), BatchJob.created_at.desc())
    elif sort == "status":
        query = query.order_by(BatchJob.status, BatchJob.created_at.desc())

    # Count total
    count_query = select(BatchJob).where(BatchJob.user_id == current_user.id)
    if status_filter:
        count_query = count_query.where(BatchJob.status == status_filter)

    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = count_result.scalar_one()

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    batch_jobs = result.scalars().all()

    return BatchJobListResponse(
        batch_jobs=[BatchJobResponse.model_validate(bj) for bj in batch_jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{batch_job_id}", response_model=BatchJobResponse)
async def get_batch_job(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get batch job details with all videos.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Batch job details
    """
    # Verify ownership and get batch job
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    # Fetch batch videos
    batch_videos_result = await db.execute(
        select(BatchVideo)
        .where(BatchVideo.batch_job_id == batch_job_id)
        .order_by(BatchVideo.position)
    )
    batch_videos = batch_videos_result.scalars().all()

    # Convert to response model
    batch_job_dict = batch_job.model_dump()
    batch_job_dict["videos"] = [
        BatchVideoResponse.model_validate(bv) for bv in batch_videos
    ]

    return BatchJobResponse(**batch_job_dict)


@router.post("/{batch_job_id}/pause", response_model=BatchJobResponse)
async def pause_batch_job(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Pause batch processing.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Updated batch job
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    if batch_job.status != BatchJobStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only pause a processing batch",
        )

    # Set pause flag in Redis
    redis_client = await redis.from_url(settings.redis_url)
    await redis_client.set(f"batch_paused:{batch_job_id}", "true")

    # Update status
    batch_job.status = BatchJobStatus.PAUSED
    await db.commit()
    await db.refresh(batch_job)

    return BatchJobResponse.model_validate(batch_job)


@router.post("/{batch_job_id}/resume", response_model=BatchJobResponse)
async def resume_batch_job(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Resume batch processing.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Updated batch job
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    if batch_job.status != BatchJobStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resume a paused batch",
        )

    # Remove pause flag in Redis
    redis_client = await redis.from_url(settings.redis_url)
    await redis_client.delete(f"batch_paused:{batch_job_id}")

    # Update status
    batch_job.status = BatchJobStatus.PROCESSING
    await db.commit()
    await db.refresh(batch_job)

    # Re-enqueue processing job
    await enqueue_process_batch_job(str(batch_job_id))

    return BatchJobResponse.model_validate(batch_job)


@router.post("/{batch_job_id}/cancel", response_model=BatchJobResponse)
async def cancel_batch_job(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Cancel batch processing.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Updated batch job
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    if batch_job.status in [BatchJobStatus.COMPLETED, BatchJobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed or already cancelled batch",
        )

    # Set cancel flag in Redis
    redis_client = await redis.from_url(settings.redis_url)
    await redis_client.set(f"batch_cancelled:{batch_job_id}", "true")

    # Update status
    batch_job.status = BatchJobStatus.CANCELLED
    await db.commit()
    await db.refresh(batch_job)

    return BatchJobResponse.model_validate(batch_job)


@router.post("/{batch_job_id}/retry-failed", response_model=BatchJobResponse)
async def retry_failed_videos(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retry all failed videos in batch.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchJobResponse: Updated batch job
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    # Find failed videos
    from app.models.batch import BatchVideoStatus

    failed_videos_result = await db.execute(
        select(BatchVideo).where(
            BatchVideo.batch_job_id == batch_job_id,
            BatchVideo.status == BatchVideoStatus.FAILED,
        )
    )
    failed_videos = failed_videos_result.scalars().all()

    if not failed_videos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No failed videos to retry",
        )

    # Reset failed videos to pending
    for video in failed_videos:
        if video.retry_count < video.max_retries:
            video.status = BatchVideoStatus.PENDING
            video.retry_count += 1
            video.error_message = None

    # Update batch status
    batch_job.status = BatchJobStatus.PROCESSING
    batch_job.failed_videos = max(0, batch_job.failed_videos - len(failed_videos))

    await db.commit()
    await db.refresh(batch_job)

    # Re-enqueue processing
    await enqueue_process_batch_job(str(batch_job_id))

    return BatchJobResponse.model_validate(batch_job)


@router.delete("/{batch_job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_batch_job(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a batch job.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session
    """
    # Verify ownership
    batch_job = await verify_batch_ownership(batch_job_id, current_user, db)

    if batch_job.status not in [
        BatchJobStatus.COMPLETED,
        BatchJobStatus.FAILED,
        BatchJobStatus.CANCELLED,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete completed, failed, or cancelled batches",
        )

    # Delete batch (cascade will handle batch_videos)
    await db.delete(batch_job)
    await db.commit()


@router.get("/{batch_job_id}/progress")
async def stream_batch_progress(
    batch_job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream real-time progress updates via Server-Sent Events.

    Args:
        batch_job_id: Batch job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse: SSE stream
    """
    # Verify ownership
    await verify_batch_ownership(batch_job_id, current_user, db)

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from Redis pub/sub."""
        redis_client = await redis.from_url(settings.redis_url)
        pubsub = redis_client.pubsub()
        channel = f"batch_progress:{batch_job_id}"

        await pubsub.subscribe(channel)

        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to progress stream'})}\n\n"

            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"

                # Send heartbeat every 15 seconds
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await redis_client.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.post("/{batch_job_id}/export", response_model=BatchExportResponse)
async def export_batch(
    batch_job_id: UUID,
    request: BatchExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate export for batch job.

    Args:
        batch_job_id: Batch job ID
        request: Export request
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchExportResponse: Export details
    """
    # Verify ownership
    await verify_batch_ownership(batch_job_id, current_user, db)

    try:
        # For now, execute sync (could be made async with worker)
        service = BatchExportService(db)
        result = await service.export_batch(
            batch_job_id=batch_job_id,
            export_format=request.format,
            include_failed=request.include_failed,
            custom_naming=request.custom_naming,
        )

        return BatchExportResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{batch_job_id}/export/{export_id}", response_model=BatchExportResponse)
async def get_export_status(
    batch_job_id: UUID,
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get export status and download URL.

    Args:
        batch_job_id: Batch job ID
        export_id: Export ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        BatchExportResponse: Export details
    """
    # Verify ownership
    await verify_batch_ownership(batch_job_id, current_user, db)

    # For now, return placeholder
    # In production, this would check export status from cache/database
    return BatchExportResponse(
        export_job_id=export_id,
        status="completed",
        progress=100,
        download_url="https://example.com/download",
        file_size=0,
        expires_at=None,
    )
