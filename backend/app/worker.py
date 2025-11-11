"""ARQ worker for background tasks."""

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings
from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.models.clip import Clip, ClipStatus
from app.models.export import Export, ExportStatus
from app.models.transcript import Transcript, TranscriptStatus
from app.models.video import Video, VideoStatus
from app.services.clip_generation import ClipGenerationService
from app.services.export import ExportService
from app.services.silence_removal import SilenceRemovalService
from app.services.transcription import TranscriptionService
from app.services.video_metadata import VideoMetadataService


async def transcribe_video(ctx: dict[str, Any], video_id: str) -> dict[str, Any]:
    """
    Transcribe a video using OpenAI Whisper API.

    Args:
        ctx: ARQ context
        video_id: Video ID as string

    Returns:
        dict: Result with transcript ID and status
    """
    video_uuid = UUID(video_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress(progress: int) -> None:
        """Update transcription progress in Redis."""
        progress_key = f"transcription:progress:{video_id}"
        status_messages = {
            10: "Downloading video...",
            30: "Extracting audio...",
            50: "Transcribing audio...",
            90: "Saving transcript...",
            100: "Complete",
        }
        status = status_messages.get(progress, "Processing...")

        progress_data = {
            "progress": progress,
            "status": status,
            "estimated_time_remaining": None,  # Can be calculated based on video duration
        }
        await redis_client.setex(
            progress_key, 3600, json.dumps(progress_data)
        )  # Expire after 1 hour

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            service = TranscriptionService(db)

            # Update progress: Starting
            await update_progress(0)

            # Transcribe video
            transcript = await service.transcribe_video(video_uuid, update_progress)

            # Clean up progress key after completion
            progress_key = f"transcription:progress:{video_id}"
            await redis_client.delete(progress_key)

            return {
                "status": "success",
                "transcript_id": str(transcript.id),
                "video_id": video_id,
            }

    except Exception as e:
        # Update transcript status to failed
        async with async_session_maker() as db:
            result = await db.execute(select(Transcript).where(Transcript.video_id == video_uuid))
            transcript = result.scalar_one_or_none()

            if transcript:
                transcript.status = TranscriptStatus.FAILED
                await db.commit()

        # Update progress to show error
        progress_key = f"transcription:progress:{video_id}"
        error_data = {
            "progress": 0,
            "status": f"Failed: {str(e)}",
            "estimated_time_remaining": None,
        }
        await redis_client.setex(progress_key, 3600, json.dumps(error_data))

        raise


async def extract_video_metadata(ctx: dict[str, Any], video_id: str) -> dict[str, Any]:
    """
    Extract metadata from a video file.

    Args:
        ctx: ARQ context
        video_id: Video ID as string

    Returns:
        dict: Result with video ID and status
    """
    video_uuid = UUID(video_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress_async(progress: int) -> None:
        """Update metadata extraction progress in Redis."""
        progress_key = f"metadata:progress:{video_id}"
        status_messages = {
            10: "Downloading video...",
            50: "Extracting metadata...",
            90: "Saving metadata...",
            100: "Complete",
        }
        status = status_messages.get(progress, "Processing...")

        progress_data = {
            "progress": progress,
            "status": status,
            "estimated_time_remaining": None,
        }
        await redis_client.setex(
            progress_key, 3600, json.dumps(progress_data)
        )  # Expire after 1 hour

    # Create sync wrapper that schedules async callback
    # Since we're in an async context, we can use create_task
    import asyncio

    def update_progress(progress: int) -> None:
        """Sync wrapper for async progress update - fire and forget."""
        # Schedule the async callback (fire and forget)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(update_progress_async(progress))
        except RuntimeError:
            # If no running loop, this shouldn't happen in ARQ context
            pass

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            service = VideoMetadataService(db)

            # Update progress: Starting
            await update_progress_async(0)

            # Update video status to processing
            result = await db.execute(select(Video).where(Video.id == video_uuid))
            video = result.scalar_one_or_none()
            if video:
                video.status = VideoStatus.PROCESSING
                await db.commit()

            # Extract metadata with sync callback wrapper
            video = await service.extract_video_metadata(video_uuid, update_progress)

            # Clean up progress key after completion
            progress_key = f"metadata:progress:{video_id}"
            await redis_client.delete(progress_key)

            return {
                "status": "success",
                "video_id": video_id,
                "duration": video.duration,
                "resolution": video.resolution,
                "format": video.format,
            }

    except Exception as e:
        # Update video status to failed
        async with async_session_maker() as db:
            result = await db.execute(select(Video).where(Video.id == video_uuid))
            video = result.scalar_one_or_none()

            if video:
                video.status = VideoStatus.FAILED
                await db.commit()

        # Update progress to show error
        progress_key = f"metadata:progress:{video_id}"
        error_data = {
            "progress": 0,
            "status": f"Failed: {str(e)}",
            "estimated_time_remaining": None,
        }
        await redis_client.setex(progress_key, 3600, json.dumps(error_data))

        raise


async def remove_silence(
    ctx: dict[str, Any],
    video_id: str,
    threshold_db: int = -40,
    min_duration_ms: int = 1000,
    excluded_segments: list[int] | None = None,
) -> dict[str, Any]:
    """
    Remove silent segments from a video.

    Args:
        ctx: ARQ context
        video_id: Video ID as string
        threshold_db: Silence threshold in dB
        min_duration_ms: Minimum silence duration in milliseconds
        excluded_segments: List of segment indices to exclude

    Returns:
        dict: Result with video ID and status
    """
    video_uuid = UUID(video_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress(progress: int) -> None:
        """Update silence removal progress in Redis."""
        progress_key = f"silence_removal:progress:{video_id}"
        status_messages = {
            10: "Downloading video...",
            20: "Detecting silence...",
            40: "Removing segments...",
            80: "Uploading processed video...",
            100: "Complete",
        }
        status = status_messages.get(progress, "Processing...")

        progress_data = {
            "progress": progress,
            "status": status,
            "estimated_time_remaining": None,
        }
        await redis_client.setex(
            progress_key, 3600, json.dumps(progress_data)
        )  # Expire after 1 hour

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            service = SilenceRemovalService(db)

            # Update progress: Starting
            await update_progress(0)

            # Remove silence with async progress wrapper
            import asyncio

            def update_progress_sync(progress: int) -> None:
                """Sync wrapper for async progress update."""
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(update_progress(progress))
                except RuntimeError:
                    pass

            video = await service.remove_silence(
                video_uuid,
                threshold_db=threshold_db,
                min_duration_ms=min_duration_ms,
                excluded_segments=excluded_segments,
                update_progress=update_progress_sync,
            )

            # Clean up progress key after completion
            progress_key = f"silence_removal:progress:{video_id}"
            await redis_client.delete(progress_key)

            return {
                "status": "success",
                "video_id": video_id,
                "duration": video.duration,
            }

    except Exception as e:
        # Update progress to show error
        progress_key = f"silence_removal:progress:{video_id}"
        error_data = {
            "progress": 0,
            "status": f"Failed: {str(e)}",
            "estimated_time_remaining": None,
        }
        await redis_client.setex(progress_key, 3600, json.dumps(error_data))

        raise


async def generate_clip(ctx: dict[str, Any], clip_id: str) -> dict[str, Any]:
    """
    Generate a video clip.

    Args:
        ctx: ARQ context
        clip_id: Clip ID as string

    Returns:
        dict: Result with clip ID and status
    """
    clip_uuid = UUID(clip_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress(progress: int) -> None:
        """Update clip generation progress in Redis."""
        progress_key = f"clip_generation:progress:{clip_id}"
        status_messages = {
            10: "Downloading video...",
            50: "Extracting clip...",
            80: "Uploading clip...",
            100: "Complete",
        }
        status = status_messages.get(progress, "Processing...")

        progress_data = {
            "progress": progress,
            "status": status,
            "estimated_time_remaining": None,
        }
        await redis_client.setex(
            progress_key, 3600, json.dumps(progress_data)
        )  # Expire after 1 hour

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            service = ClipGenerationService(db)

            # Update progress: Starting
            await update_progress(0)

            # Generate clip
            clip = await service.generate_clip(clip_uuid, update_progress)

            # Clean up progress key after completion
            progress_key = f"clip_generation:progress:{clip_id}"
            await redis_client.delete(progress_key)

            return {
                "status": "success",
                "clip_id": clip_id,
                "clip_url": clip.clip_url,
            }

    except Exception as e:
        # Update clip status to failed
        async with async_session_maker() as db:
            result = await db.execute(select(Clip).where(Clip.id == clip_uuid))
            clip = result.scalar_one_or_none()

            if clip:
                clip.status = ClipStatus.FAILED
                await db.commit()

        # Update progress to show error
        progress_key = f"clip_generation:progress:{clip_id}"
        error_data = {
            "progress": 0,
            "status": f"Failed: {str(e)}",
            "estimated_time_remaining": None,
        }
        await redis_client.setex(progress_key, 3600, json.dumps(error_data))

        raise


async def export_video(ctx: dict[str, Any], export_id: str) -> dict[str, Any]:
    """
    Process video export job.

    Args:
        ctx: ARQ context
        export_id: Export ID as string

    Returns:
        dict: Result with export ID and status
    """
    export_uuid = UUID(export_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress(progress: int, stage: str = "") -> None:
        """Update export progress in Redis."""
        progress_key = f"export_progress:{export_id}"

        progress_data = {
            "progress": str(progress),
            "stage": stage,
            "elapsed_time": "0",  # Could track elapsed time
            "estimated_time": "0",  # Could estimate time remaining
        }

        # Store in Redis hash
        await redis_client.hset(progress_key, mapping=progress_data)
        await redis_client.expire(progress_key, 3600)  # Expire after 1 hour

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            # Get export record
            result = await db.execute(select(Export).where(Export.id == export_uuid))
            export = result.scalar_one_or_none()

            if not export:
                raise ValueError(f"Export {export_id} not found")

            # Get video
            result = await db.execute(select(Video).where(Video.id == export.video_id))
            video = result.scalar_one_or_none()

            if not video:
                raise ValueError(f"Video {export.video_id} not found")

            # Update export status to processing
            export.status = ExportStatus.PROCESSING
            export.started_at = ctx.get("job_start_time") or None
            await db.commit()

            # Update progress: Starting
            await update_progress(0, "Initializing export")

            # Process export
            service = ExportService(db)

            def progress_callback(progress: int) -> None:
                """Sync progress callback for FFmpeg."""
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    stage_map = {
                        range(0, 20): "Downloading video",
                        range(20, 90): "Processing video",
                        range(90, 100): "Uploading to storage",
                    }
                    stage = "Processing"
                    for r, s in stage_map.items():
                        if progress in r:
                            stage = s
                            break
                    loop.create_task(update_progress(progress, stage))
                except RuntimeError:
                    pass

            # Check for cancellation
            cancel_key = f"export_cancel:{export_id}"
            if await redis_client.exists(cancel_key):
                export.status = ExportStatus.CANCELLED
                await db.commit()
                await redis_client.delete(cancel_key)
                return {
                    "status": "cancelled",
                    "export_id": export_id,
                }

            s3_key, cloudfront_url, file_size, total_duration = await service.process_export(
                export_id=export_uuid,
                video=video,
                segments=export.segment_selections or [],
                export_type=export.export_type,
                resolution=export.resolution,
                quality=export.quality_preset,
                format_type=export.format,
                progress_callback=progress_callback,
            )

            # Update export record with results
            export.output_s3_key = s3_key
            export.output_url = cloudfront_url
            export.file_size_bytes = file_size
            export.total_duration_seconds = total_duration
            export.status = ExportStatus.COMPLETED
            export.progress_percentage = 100
            from datetime import datetime
            export.completed_at = datetime.utcnow()

            await db.commit()

            # Clean up progress key after completion
            progress_key = f"export_progress:{export_id}"
            await redis_client.delete(progress_key)

            return {
                "status": "success",
                "export_id": export_id,
                "output_url": cloudfront_url,
                "file_size": file_size,
            }

    except Exception as e:
        # Update export status to failed
        async with async_session_maker() as db:
            result = await db.execute(select(Export).where(Export.id == export_uuid))
            export = result.scalar_one_or_none()

            if export:
                export.status = ExportStatus.FAILED
                export.error_message = str(e)
                await db.commit()

        # Update progress to show error
        progress_key = f"export_progress:{export_id}"
        error_data = {
            "progress": "0",
            "stage": f"Failed: {str(e)}",
            "elapsed_time": "0",
            "estimated_time": "0",
        }
        await redis_client.hset(progress_key, mapping=error_data)
        await redis_client.expire(progress_key, 3600)

        raise


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook."""
    print("Worker starting up...")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook."""
    print("Worker shutting down...")


class WorkerSettings:
    """ARQ worker settings."""

    functions = [
        transcribe_video,
        extract_video_metadata,
        remove_silence,
        generate_clip,
        export_video,
    ]

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 3600  # 1 hour
    keep_result = 3600  # Keep results for 1 hour


async def get_redis_pool() -> Any:
    """Get Redis pool for enqueueing jobs."""
    return await create_pool(WorkerSettings.redis_settings)


async def enqueue_transcribe_video(video_id: str) -> Any:
    """
    Enqueue a transcription job.

    Args:
        video_id: Video ID as string

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job("transcribe_video", video_id)
    return job


async def enqueue_extract_video_metadata(video_id: str) -> Any:
    """
    Enqueue a metadata extraction job.

    Args:
        video_id: Video ID as string

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job("extract_video_metadata", video_id)
    return job


async def enqueue_remove_silence(
    video_id: str,
    threshold_db: int = -40,
    min_duration_ms: int = 1000,
    excluded_segments: list[int] | None = None,
) -> Any:
    """
    Enqueue a silence removal job.

    Args:
        video_id: Video ID as string
        threshold_db: Silence threshold in dB
        min_duration_ms: Minimum silence duration in milliseconds
        excluded_segments: List of segment indices to exclude

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "remove_silence",
        video_id,
        threshold_db=threshold_db,
        min_duration_ms=min_duration_ms,
        excluded_segments=excluded_segments or [],
    )
    return job


async def enqueue_generate_clip(clip_id: str) -> Any:
    """
    Enqueue a clip generation job.

    Args:
        clip_id: Clip ID as string

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job("generate_clip", clip_id)
    return job


async def enqueue_export_video(export_id: str) -> Any:
    """
    Enqueue a video export job.

    Args:
        export_id: Export ID as string

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job("export_video", export_id)
    return job
