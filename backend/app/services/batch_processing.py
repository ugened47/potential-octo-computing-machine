"""Batch processing service for orchestrating multi-video processing."""

import asyncio
import json
from datetime import datetime
from typing import Callable
from uuid import UUID

import redis.asyncio as redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.batch import (
    BatchJob,
    BatchJobStatus,
    BatchVideo,
    BatchVideoStatus,
    ProcessingStage,
)
from app.models.video import Video
from app.services.clip_generation import ClipGenerationService
from app.services.silence_removal import SilenceRemovalService
from app.services.transcription import TranscriptionService


class BatchProcessingService:
    """Service for orchestrating batch video processing."""

    def __init__(self, db: AsyncSession):
        """Initialize batch processing service.

        Args:
            db: Database session
        """
        self.db = db
        self.redis_client: redis.Redis | None = None

    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for progress tracking."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(settings.redis_url)
        return self.redis_client

    async def _publish_progress_event(
        self,
        batch_job_id: UUID,
        event_type: str,
        video_id: UUID | None = None,
        progress: int = 0,
        current_stage: ProcessingStage | None = None,
        message: str | None = None,
    ) -> None:
        """Publish progress event via Redis pub/sub.

        Args:
            batch_job_id: Batch job ID
            event_type: Event type (progress, video_started, video_completed, etc.)
            video_id: Video ID (optional)
            progress: Progress percentage
            current_stage: Current processing stage
            message: Event message
        """
        redis_client = await self._get_redis_client()
        channel = f"batch_progress:{batch_job_id}"

        event_data = {
            "type": event_type,
            "batch_job_id": str(batch_job_id),
            "video_id": str(video_id) if video_id else None,
            "progress": progress,
            "current_stage": current_stage.value if current_stage else None,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await redis_client.publish(channel, json.dumps(event_data))

    async def process_batch(
        self,
        batch_job_id: UUID,
        concurrency: int = 1,
    ) -> dict:
        """Process all videos in a batch job.

        Args:
            batch_job_id: Batch job ID
            concurrency: Number of videos to process concurrently

        Returns:
            Processing result dictionary

        Raises:
            ValueError: If batch not found or invalid state
        """
        redis_client = await self._get_redis_client()

        # Fetch batch job
        batch_result = await self.db.execute(
            select(BatchJob).where(BatchJob.id == batch_job_id)
        )
        batch_job = batch_result.scalar_one_or_none()
        if not batch_job:
            raise ValueError("Batch job not found")

        # Update batch status to processing
        batch_job.status = BatchJobStatus.PROCESSING
        batch_job.started_at = datetime.utcnow()
        await self.db.commit()

        # Publish batch started event
        await self._publish_progress_event(
            batch_job_id=batch_job_id,
            event_type="batch_started",
            message=f"Starting batch processing of {batch_job.total_videos} videos",
        )

        # Fetch all batch videos ordered by position
        batch_videos_result = await self.db.execute(
            select(BatchVideo)
            .where(BatchVideo.batch_job_id == batch_job_id)
            .order_by(BatchVideo.position)
        )
        batch_videos = batch_videos_result.scalars().all()

        # Process videos (currently sequential, can be made concurrent)
        start_time = datetime.utcnow()
        completed_count = 0
        failed_count = 0

        for batch_video in batch_videos:
            # Check for pause/cancel flags
            pause_flag = await redis_client.get(f"batch_paused:{batch_job_id}")
            cancel_flag = await redis_client.get(f"batch_cancelled:{batch_job_id}")

            if cancel_flag:
                batch_job.status = BatchJobStatus.CANCELLED
                await self.db.commit()
                break

            if pause_flag:
                batch_job.status = BatchJobStatus.PAUSED
                await self.db.commit()
                break

            # Skip if video already completed or cancelled
            if batch_video.status in [
                BatchVideoStatus.COMPLETED,
                BatchVideoStatus.CANCELLED,
            ]:
                completed_count += 1
                continue

            try:
                await self._process_single_video(
                    batch_job=batch_job,
                    batch_video=batch_video,
                    settings=batch_job.settings,
                )
                completed_count += 1
                batch_job.completed_videos = completed_count
            except Exception as e:
                failed_count += 1
                batch_job.failed_videos = failed_count
                batch_video.status = BatchVideoStatus.FAILED
                batch_video.error_message = str(e)
                batch_video.completed_at = datetime.utcnow()

                # Publish video failed event
                await self._publish_progress_event(
                    batch_job_id=batch_job_id,
                    event_type="video_failed",
                    video_id=batch_video.video_id,
                    message=f"Video processing failed: {str(e)}",
                )

            # Update batch progress
            total_processed = completed_count + failed_count
            progress = int((total_processed / batch_job.total_videos) * 100)

            # Calculate estimated time remaining
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            if total_processed > 0:
                avg_time_per_video = elapsed_time / total_processed
                remaining_videos = batch_job.total_videos - total_processed
                batch_job.estimated_time_remaining = int(avg_time_per_video * remaining_videos)

            await self.db.commit()

            # Publish batch progress event
            await self._publish_progress_event(
                batch_job_id=batch_job_id,
                event_type="progress",
                progress=progress,
                message=f"Processed {total_processed}/{batch_job.total_videos} videos",
            )

        # Mark batch as completed if all videos processed
        if completed_count + failed_count == batch_job.total_videos:
            if failed_count == batch_job.total_videos:
                batch_job.status = BatchJobStatus.FAILED
            else:
                batch_job.status = BatchJobStatus.COMPLETED
            batch_job.completed_at = datetime.utcnow()
            await self.db.commit()

            # Publish batch completed event
            await self._publish_progress_event(
                batch_job_id=batch_job_id,
                event_type="batch_completed",
                progress=100,
                message=f"Batch processing completed: {completed_count} succeeded, {failed_count} failed",
            )

        return {
            "status": batch_job.status.value,
            "completed": completed_count,
            "failed": failed_count,
            "total": batch_job.total_videos,
        }

    async def _process_single_video(
        self,
        batch_job: BatchJob,
        batch_video: BatchVideo,
        settings: dict,
    ) -> None:
        """Process a single video according to batch settings.

        Args:
            batch_job: Batch job
            batch_video: Batch video to process
            settings: Processing settings

        Raises:
            Exception: If processing fails
        """
        # Update batch video status
        batch_video.status = BatchVideoStatus.PROCESSING
        batch_video.started_at = datetime.utcnow()
        await self.db.commit()

        # Publish video started event
        await self._publish_progress_event(
            batch_job_id=batch_job.id,
            event_type="video_started",
            video_id=batch_video.video_id,
            message=f"Starting processing for video at position {batch_video.position + 1}",
        )

        processing_result = {}

        # Step 1: Transcription (if enabled)
        if settings.get("transcribe", False):
            batch_video.current_stage = ProcessingStage.TRANSCRIBING
            batch_video.progress_percentage = 10
            await self.db.commit()

            await self._publish_progress_event(
                batch_job_id=batch_job.id,
                event_type="video_progress",
                video_id=batch_video.video_id,
                progress=10,
                current_stage=ProcessingStage.TRANSCRIBING,
                message="Transcribing video...",
            )

            transcription_service = TranscriptionService(self.db)
            transcript = await transcription_service.transcribe_video(
                video_id=batch_video.video_id
            )
            processing_result["transcript_id"] = str(transcript.id)

        # Step 2: Silence removal (if enabled)
        if settings.get("remove_silence", False):
            batch_video.current_stage = ProcessingStage.REMOVING_SILENCE
            batch_video.progress_percentage = 40
            await self.db.commit()

            await self._publish_progress_event(
                batch_job_id=batch_job.id,
                event_type="video_progress",
                video_id=batch_video.video_id,
                progress=40,
                current_stage=ProcessingStage.REMOVING_SILENCE,
                message="Removing silence...",
            )

            silence_service = SilenceRemovalService(self.db)
            threshold = settings.get("silence_threshold", -40)
            video = await silence_service.remove_silence(
                video_id=batch_video.video_id,
                threshold_db=int(threshold),
                min_duration_ms=1000,
            )
            processing_result["silence_removed"] = True

        # Step 3: Highlight detection (if enabled)
        if settings.get("detect_highlights", False):
            batch_video.current_stage = ProcessingStage.DETECTING_HIGHLIGHTS
            batch_video.progress_percentage = 70
            await self.db.commit()

            await self._publish_progress_event(
                batch_job_id=batch_job.id,
                event_type="video_progress",
                video_id=batch_video.video_id,
                progress=70,
                current_stage=ProcessingStage.DETECTING_HIGHLIGHTS,
                message="Detecting highlights...",
            )

            # Placeholder for highlight detection
            processing_result["highlights_detected"] = True

        # Step 4: Export (if needed)
        batch_video.current_stage = ProcessingStage.EXPORTING
        batch_video.progress_percentage = 90
        await self.db.commit()

        # Mark video as completed
        batch_video.status = BatchVideoStatus.COMPLETED
        batch_video.progress_percentage = 100
        batch_video.processing_result = processing_result
        batch_video.completed_at = datetime.utcnow()
        await self.db.commit()

        # Publish video completed event
        await self._publish_progress_event(
            batch_job_id=batch_job.id,
            event_type="video_completed",
            video_id=batch_video.video_id,
            progress=100,
            message=f"Video at position {batch_video.position + 1} completed",
        )
