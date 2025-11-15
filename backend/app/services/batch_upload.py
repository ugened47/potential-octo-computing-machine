"""Batch upload service for handling multi-video uploads."""

from typing import Callable
from uuid import UUID, uuid4

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.batch import BatchJob, BatchJobStatus, BatchVideo, BatchVideoStatus
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.s3 import S3Service


class BatchUploadService:
    """Service for handling batch video uploads."""

    def __init__(self, db: AsyncSession):
        """Initialize batch upload service.

        Args:
            db: Database session
        """
        self.db = db
        self.s3_service = S3Service()

    async def create_batch_upload(
        self,
        user_id: UUID,
        name: str,
        description: str | None,
        settings: dict,
        video_count: int,
    ) -> tuple[BatchJob, list[str]]:
        """Create a batch job and generate presigned URLs for uploads.

        Args:
            user_id: User ID
            name: Batch job name
            description: Batch job description
            settings: Processing settings for all videos
            video_count: Number of videos in batch

        Returns:
            Tuple of (BatchJob, list of presigned URLs)

        Raises:
            ValueError: If quota exceeded or invalid parameters
        """
        # Validate user tier and quota
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Check quota limits (simplified - should check user tier)
        max_batch_size = 50  # Default to pro tier
        if video_count > max_batch_size:
            raise ValueError(f"Batch size exceeds maximum of {max_batch_size} videos")

        if video_count < 1:
            raise ValueError("Batch must contain at least 1 video")

        # Create batch job
        batch_job = BatchJob(
            user_id=user_id,
            name=name,
            description=description,
            settings=settings,
            status=BatchJobStatus.PENDING,
            total_videos=video_count,
        )
        self.db.add(batch_job)
        await self.db.flush()  # Get the batch job ID

        # Create placeholder video records and generate presigned URLs
        upload_urls = []
        for position in range(video_count):
            video_id = uuid4()

            # Create video record
            video = Video(
                id=video_id,
                user_id=user_id,
                title=f"{name} - Video {position + 1}",
                status=VideoStatus.UPLOADED,  # Will be updated after upload
            )
            self.db.add(video)
            await self.db.flush()

            # Create batch video record
            batch_video = BatchVideo(
                batch_job_id=batch_job.id,
                video_id=video.id,
                position=position,
                status=BatchVideoStatus.PENDING,
            )
            self.db.add(batch_video)

            # Generate presigned URL for upload
            presigned_url, s3_key = self.s3_service.generate_presigned_url(
                user_id=user_id,
                video_id=video_id,
                filename=f"video_{position + 1}.mp4",
                content_type="video/mp4",
                expires_in=900,  # 15 minutes
            )

            # Update video with S3 key
            video.s3_key = s3_key
            upload_urls.append(presigned_url)

        await self.db.commit()
        await self.db.refresh(batch_job)

        return batch_job, upload_urls

    async def add_videos_to_batch(
        self,
        batch_job_id: UUID,
        video_ids: list[UUID],
        user_id: UUID,
    ) -> BatchJob:
        """Add existing videos to a batch job.

        Args:
            batch_job_id: Batch job ID
            video_ids: List of video IDs to add
            user_id: User ID for authorization

        Returns:
            Updated BatchJob

        Raises:
            ValueError: If batch not found, already started, or videos invalid
        """
        # Fetch batch job
        batch_result = await self.db.execute(
            select(BatchJob).where(
                BatchJob.id == batch_job_id,
                BatchJob.user_id == user_id,
            )
        )
        batch_job = batch_result.scalar_one_or_none()
        if not batch_job:
            raise ValueError("Batch job not found")

        # Check if batch is still pending
        if batch_job.status != BatchJobStatus.PENDING:
            raise ValueError("Cannot add videos to a batch that has already started")

        # Verify all videos exist and belong to user
        for video_id in video_ids:
            video_result = await self.db.execute(
                select(Video).where(
                    Video.id == video_id,
                    Video.user_id == user_id,
                )
            )
            video = video_result.scalar_one_or_none()
            if not video:
                raise ValueError(f"Video {video_id} not found or access denied")

            # Check if video is already in this batch
            existing_result = await self.db.execute(
                select(BatchVideo).where(
                    BatchVideo.batch_job_id == batch_job_id,
                    BatchVideo.video_id == video_id,
                )
            )
            if existing_result.scalar_one_or_none():
                continue  # Skip duplicates

            # Add video to batch
            position = batch_job.total_videos
            batch_video = BatchVideo(
                batch_job_id=batch_job_id,
                video_id=video_id,
                position=position,
                status=BatchVideoStatus.PENDING,
            )
            self.db.add(batch_video)
            batch_job.total_videos += 1

        await self.db.commit()
        await self.db.refresh(batch_job)

        return batch_job

    async def validate_uploads_complete(
        self,
        batch_job_id: UUID,
        user_id: UUID,
    ) -> tuple[bool, str]:
        """Validate that all videos in batch have been uploaded.

        Args:
            batch_job_id: Batch job ID
            user_id: User ID for authorization

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Fetch batch videos
        batch_videos_result = await self.db.execute(
            select(BatchVideo).where(BatchVideo.batch_job_id == batch_job_id)
        )
        batch_videos = batch_videos_result.scalars().all()

        if not batch_videos:
            return False, "Batch has no videos"

        # Check each video
        pending_count = 0
        for batch_video in batch_videos:
            video_result = await self.db.execute(
                select(Video).where(Video.id == batch_video.video_id)
            )
            video = video_result.scalar_one_or_none()

            if not video:
                return False, f"Video {batch_video.video_id} not found"

            # Check if video has been uploaded (has file_size and s3_key)
            if not video.file_size or not video.s3_key:
                pending_count += 1

        if pending_count > 0:
            return False, f"{pending_count} videos have not been uploaded yet"

        return True, "All videos uploaded successfully"
