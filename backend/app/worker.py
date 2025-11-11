"""ARQ worker for background tasks."""

import json
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings
from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.models.clip import Clip, ClipStatus
from app.models.project import Project, ProjectStatus
from app.models.transcript import Transcript, TranscriptStatus
from app.models.video import Video, VideoStatus
from app.services.clip_generation import ClipGenerationService
from app.services.silence_removal import SilenceRemovalService
from app.services.transcription import TranscriptionService
from app.services.video_metadata import VideoMetadataService
from app.services.video_rendering_service import VideoRenderingService


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


async def render_project(
    ctx: dict[str, Any],
    project_id: str,
    user_id: str,
    quality: str = "high",
    format: str = "mp4",
) -> dict[str, Any]:
    """
    Render a multi-track project to video.

    Args:
        ctx: ARQ context
        project_id: Project ID as string
        user_id: User ID as string
        quality: Quality preset ('low', 'medium', 'high', 'max')
        format: Output format ('mp4', 'mov', 'webm')

    Returns:
        dict: Result with project ID and rendered video URL
    """
    project_uuid = UUID(project_id)
    redis_client = await redis.from_url(settings.redis_url)

    async def update_progress(progress: int, stage: str) -> None:
        """Update render progress in Redis."""
        progress_key = f"render:progress:{project_id}"

        progress_data = {
            "progress": progress,
            "stage": stage,
            "status": "processing" if progress < 100 else "completed",
            "estimated_time_remaining": None,
        }
        await redis_client.setex(
            progress_key, 7200, json.dumps(progress_data)
        )  # Expire after 2 hours

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            # Get project
            result = await db.execute(select(Project).where(Project.id == project_uuid))
            project = result.scalar_one_or_none()

            if not project or str(project.user_id) != user_id:
                raise ValueError("Project not found or unauthorized")

            # Update project status to rendering
            project.status = ProjectStatus.RENDERING
            await db.commit()

            # Update progress
            await update_progress(0, "Validating project")

            # Initialize rendering service
            rendering_service = VideoRenderingService(db)

            # Create temp directory for rendering
            with tempfile.TemporaryDirectory() as temp_dir:
                output_filename = f"project_{project_id}.{format}"
                output_path = Path(temp_dir) / output_filename

                # Update progress
                await update_progress(10, "Downloading source files")

                # TODO: Download source files from S3 to temp directory
                # For now, assume files are already accessible

                # Update progress
                await update_progress(30, "Rendering video")

                # Render project
                rendered_path = await rendering_service.render_project(
                    project,
                    str(output_path),
                    quality=quality,
                )

                # Update progress
                await update_progress(80, "Uploading rendered video")

                # TODO: Upload rendered video to S3
                # For now, use a placeholder URL
                render_output_url = f"s3://bucket/rendered/{output_filename}"

                # Update project with render output
                project.status = ProjectStatus.COMPLETED
                project.render_output_url = render_output_url
                from datetime import datetime
                project.last_rendered_at = datetime.utcnow()
                await db.commit()

            # Update progress to complete
            await update_progress(100, "Complete")

            # Clean up progress key after short delay
            await redis_client.expire(f"render:progress:{project_id}", 300)

            return {
                "status": "success",
                "project_id": project_id,
                "render_output_url": render_output_url,
            }

    except Exception as e:
        # Update project status to error
        async with async_session_maker() as db:
            result = await db.execute(select(Project).where(Project.id == project_uuid))
            project = result.scalar_one_or_none()

            if project:
                project.status = ProjectStatus.ERROR
                await db.commit()

        # Update progress to show error
        progress_key = f"render:progress:{project_id}"
        error_data = {
            "progress": 0,
            "stage": "Error",
            "status": "error",
            "error": str(e),
            "estimated_time_remaining": None,
        }
        await redis_client.setex(progress_key, 3600, json.dumps(error_data))

        raise


async def generate_project_thumbnail(
    ctx: dict[str, Any],
    project_id: str,
    time: float = 0.0,
) -> dict[str, Any]:
    """
    Generate preview thumbnail for project.

    Args:
        ctx: ARQ context
        project_id: Project ID as string
        time: Time in seconds to capture thumbnail (default: 0.0 for first frame)

    Returns:
        dict: Result with project ID and thumbnail URL
    """
    project_uuid = UUID(project_id)

    try:
        # Create database session for worker
        async with async_session_maker() as db:
            # Get project
            result = await db.execute(select(Project).where(Project.id == project_uuid))
            project = result.scalar_one_or_none()

            if not project:
                raise ValueError("Project not found")

            # Initialize rendering service
            rendering_service = VideoRenderingService(db)

            # Create temp directory for thumbnail
            with tempfile.TemporaryDirectory() as temp_dir:
                thumbnail_filename = f"project_{project_id}_thumb.jpg"
                thumbnail_path = Path(temp_dir) / thumbnail_filename

                # If time not specified, use midpoint of project
                if time == 0.0:
                    time = project.duration_seconds / 2

                # Generate preview frame
                await rendering_service.generate_preview_frame(
                    project,
                    time,
                    str(thumbnail_path),
                )

                # TODO: Upload thumbnail to S3
                # For now, use a placeholder URL
                thumbnail_url = f"s3://bucket/thumbnails/{thumbnail_filename}"

                # Update project with thumbnail URL
                project.thumbnail_url = thumbnail_url
                await db.commit()

            return {
                "status": "success",
                "project_id": project_id,
                "thumbnail_url": thumbnail_url,
            }

    except Exception as e:
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
        render_project,
        generate_project_thumbnail,
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


async def enqueue_render_project(
    project_id: str,
    user_id: str,
    quality: str = "high",
    format: str = "mp4",
) -> Any:
    """
    Enqueue a project rendering job.

    Args:
        project_id: Project ID as string
        user_id: User ID as string
        quality: Quality preset ('low', 'medium', 'high', 'max')
        format: Output format ('mp4', 'mov', 'webm')

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "render_project",
        project_id,
        user_id,
        quality=quality,
        format=format,
    )
    return job


async def enqueue_generate_project_thumbnail(
    project_id: str,
    time: float = 0.0,
) -> Any:
    """
    Enqueue a project thumbnail generation job.

    Args:
        project_id: Project ID as string
        time: Time in seconds to capture thumbnail

    Returns:
        Job result
    """
    pool = await get_redis_pool()
    job = await pool.enqueue_job("generate_project_thumbnail", project_id, time=time)
    return job
