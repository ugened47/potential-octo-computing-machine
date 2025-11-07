"""Video API endpoints."""

from typing import Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    VideoCreate,
    VideoRead,
    VideoUpdate,
)
from app.services.s3 import S3Service
from app.services.video_validation import VideoValidationService

# Upload router for presigned URL generation
upload_router = APIRouter()

# Video router for CRUD operations
video_router = APIRouter()


async def verify_video_ownership(
    video_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Video:
    """Verify user owns the video and return it.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Video: Video object

    Raises:
        HTTPException: If video not found or user doesn't own it
    """
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
            detail="Not enough permissions to access this video",
        )

    return video


@upload_router.post("/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(
    request: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate presigned URL for direct video upload to S3/MinIO.

    Args:
        request: File metadata (filename, size, content_type)
        current_user: Current authenticated user
        db: Database session

    Returns:
        PresignedUrlResponse: Presigned URL and video ID
    """
    # Validate upload request
    extension = VideoValidationService.validate_upload_request(
        filename=request.filename,
        file_size=request.file_size,
        content_type=request.content_type,
    )

    # Generate S3 key path
    video_id = uuid4()
    s3_service = S3Service()
    presigned_url, s3_key = s3_service.generate_presigned_url(
        user_id=current_user.id,
        video_id=video_id,
        filename=request.filename,
        content_type=request.content_type,
    )

    # Create video record with "uploaded" status
    video = Video(
        id=video_id,
        user_id=current_user.id,
        title=request.filename.rsplit(".", 1)[0],  # Use filename without extension as title
        status=VideoStatus.UPLOADED,
        s3_key=s3_key,
        file_size=request.file_size,
        format=extension,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    return PresignedUrlResponse(
        presigned_url=presigned_url,
        video_id=video_id,
        s3_key=s3_key,
    )


@video_router.post("", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def create_video(
    video_data: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create video record after upload completes.

    Args:
        video_data: Video creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        VideoRead: Created video record
    """
    # Get existing video record
    result = await db.execute(select(Video).where(Video.id == video_data.video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )

    # Verify ownership
    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Update video with provided data
    video.title = video_data.title
    video.description = video_data.description
    video.s3_key = video_data.s3_key
    video.status = VideoStatus.PROCESSING  # Ready for metadata extraction

    await db.commit()
    await db.refresh(video)

    # Enqueue metadata extraction job
    try:
        # Lazy import to avoid circular dependency
        from app.worker import enqueue_extract_video_metadata
        await enqueue_extract_video_metadata(str(video.id))
    except Exception as e:
        # Log error but don't fail the request
        # In production, you might want to log this to a monitoring service
        # For now, we'll let the job retry mechanism handle it
        pass

    return VideoRead.model_validate(video)


@video_router.get("", response_model=List[VideoRead])
async def list_videos(
    status_filter: Optional[VideoStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by title"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, title, duration"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List user's videos with pagination, filtering, and sorting.

    Args:
        status_filter: Filter by video status
        search: Search videos by title
        sort_by: Field to sort by (created_at, title, duration)
        sort_order: Sort order (asc or desc)
        limit: Number of results per page
        offset: Number of results to skip
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[VideoRead]: List of videos
    """
    query = select(Video).where(Video.user_id == current_user.id)

    # Apply status filter
    if status_filter:
        query = query.where(Video.status == status_filter)

    # Apply search filter
    if search:
        query = query.where(Video.title.ilike(f"%{search}%"))

    # Apply sorting
    if sort_by == "title":
        sort_column = Video.title
    elif sort_by == "duration":
        sort_column = Video.duration
    else:  # default to created_at
        sort_column = Video.created_at

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    videos = result.scalars().all()

    return [VideoRead.model_validate(video) for video in videos]


@video_router.get("/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get video details.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        VideoRead: Video details
    """
    video = await verify_video_ownership(video_id, current_user, db)
    return VideoRead.model_validate(video)


@video_router.patch("/{video_id}", response_model=VideoRead)
async def update_video(
    video_id: UUID,
    video_data: VideoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update video title and description.

    Args:
        video_id: Video ID
        video_data: Video update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        VideoRead: Updated video
    """
    video = await verify_video_ownership(video_id, current_user, db)

    # Update fields if provided
    if video_data.title is not None:
        video.title = video_data.title
    if video_data.description is not None:
        video.description = video_data.description

    await db.commit()
    await db.refresh(video)

    return VideoRead.model_validate(video)


@video_router.get("/{video_id}/playback-url", response_model=dict[str, str])
async def get_video_playback_url(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get presigned URL for video playback.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dictionary with playback_url
    """
    video = await verify_video_ownership(video_id, current_user, db)

    if not video.s3_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found",
        )

    # Use CloudFront URL if available, otherwise generate presigned URL
    if video.cloudfront_url:
        return {"playback_url": video.cloudfront_url}

    s3_service = S3Service()
    try:
        import boto3
        from botocore.exceptions import ClientError

        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }

        endpoint_url = settings.s3_endpoint_url
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client(**client_kwargs)

        playback_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": video.s3_key},
            ExpiresIn=3600,  # 1 hour
        )

        return {"playback_url": playback_url}
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate playback URL: {str(e)}",
        )


@video_router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete video record and S3 file.

    Args:
        video_id: Video ID
        current_user: Current authenticated user
        db: Database session
    """
    video = await verify_video_ownership(video_id, current_user, db)

    # Delete S3 file if s3_key exists
    if video.s3_key:
        try:
            s3_service = S3Service()
            s3_service.delete_object(video.s3_key)
        except Exception:
            # Log error but continue with database deletion
            # In production, you might want to log this to a monitoring service
            pass

    # Delete video record (cascade will handle related records)
    await db.delete(video)
    await db.commit()

