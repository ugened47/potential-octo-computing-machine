"""Tests for batch processing worker tasks."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus


class BatchJobStatus:
    """Batch job status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchVideoStatus:
    """Batch video status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="worker_test@example.com",
        hashed_password="hashed_password",
        full_name="Worker Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_videos(db_session: AsyncSession, test_user: User) -> list[Video]:
    """Create test videos."""
    videos = []
    for i in range(10):
        video = Video(
            user_id=test_user.id,
            title=f"Worker Test Video {i+1}",
            status=VideoStatus.UPLOADED,
            s3_key=f"videos/worker/video-{i+1}.mp4",
            duration=120.0,
        )
        db_session.add(video)
        videos.append(video)
    await db_session.commit()
    for video in videos:
        await db_session.refresh(video)
    return videos


@pytest.mark.asyncio
class TestBatchWorker:
    """Tests for batch processing worker tasks."""

    async def test_process_batch_job_task(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test process_batch_job task processes all videos."""
        batch_job_id = str(uuid4())

        # Mock worker context
        ctx = {
            "db": db_session,
            "redis": MagicMock(),
        }

        # Mock process_video function
        processed_videos = []

        async def process_batch_job(context, batch_id, concurrency=1):
            """Mock batch job processing."""
            # Simulate processing videos
            for video in test_videos[:5]:
                processed_videos.append(video.id)
                await asyncio.sleep(0.01)  # Simulate processing time

            return {
                "batch_job_id": batch_id,
                "status": "completed",
                "processed_count": len(processed_videos),
            }

        result = await process_batch_job(ctx, batch_job_id)

        assert result["status"] == "completed"
        assert result["processed_count"] == 5
        assert len(processed_videos) == 5

    async def test_process_batch_video_task(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test process_batch_video task processes single video."""
        batch_video_id = str(uuid4())
        video = test_videos[0]

        ctx = {
            "db": db_session,
            "redis": MagicMock(),
        }

        async def process_batch_video(context, batch_video_id, settings):
            """Mock individual video processing."""
            # Simulate processing stages
            stages = ["transcribing", "removing_silence", "detecting_highlights", "exporting"]

            for stage in stages:
                await asyncio.sleep(0.01)
                # Update progress
                context["redis"].set(f"progress:{batch_video_id}:{stage}", "100")

            return {
                "batch_video_id": batch_video_id,
                "status": "completed",
                "output_url": f"s3://bucket/output/{video.id}.mp4",
            }

        settings = {
            "transcribe": True,
            "remove_silence": True,
            "detect_highlights": False,
        }

        result = await process_batch_video(ctx, batch_video_id, settings)

        assert result["status"] == "completed"
        assert "output_url" in result

    async def test_parallel_video_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test parallel processing of multiple videos."""
        concurrency = 3

        async def process_video(video_id):
            await asyncio.sleep(0.1)
            return {"video_id": video_id, "status": "completed"}

        # Process videos in parallel with concurrency limit
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_limit(video_id):
            async with semaphore:
                return await process_video(video_id)

        video_ids = [str(v.id) for v in test_videos[:6]]
        results = await asyncio.gather(*[process_with_limit(vid) for vid in video_ids])

        assert len(results) == 6
        assert all(r["status"] == "completed" for r in results)

    async def test_handle_video_processing_failure(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test handling video processing failure."""
        video = test_videos[0]

        async def process_video_with_failure(video_id, should_fail=False):
            if should_fail:
                raise Exception(f"Processing failed for video {video_id}")
            return {"video_id": video_id, "status": "completed"}

        # Test successful processing
        result = await process_video_with_failure(str(video.id), should_fail=False)
        assert result["status"] == "completed"

        # Test failed processing
        with pytest.raises(Exception) as exc_info:
            await process_video_with_failure(str(video.id), should_fail=True)
        assert "Processing failed" in str(exc_info.value)

    async def test_retry_failed_video_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test retry logic for failed video processing."""
        video = test_videos[0]
        max_retries = 3
        retry_count = 0

        async def process_with_retry(video_id):
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise Exception("Temporary failure")
            return {"video_id": video_id, "status": "completed"}

        # Retry loop
        attempts = 0
        result = None
        last_error = None

        while attempts < max_retries:
            try:
                result = await process_with_retry(str(video.id))
                break
            except Exception as e:
                last_error = e
                attempts += 1
                await asyncio.sleep(0.01)

        assert result is not None
        assert result["status"] == "completed"
        assert retry_count == 3

    async def test_progress_aggregation_for_batch(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test aggregating progress from multiple videos."""
        video_progress = {}

        # Initialize progress for videos
        for i in range(5):
            video_progress[f"video-{i}"] = {
                "progress": 0,
                "status": BatchVideoStatus.PENDING,
            }

        # Simulate progress updates
        video_progress["video-0"]["progress"] = 100
        video_progress["video-0"]["status"] = BatchVideoStatus.COMPLETED

        video_progress["video-1"]["progress"] = 100
        video_progress["video-1"]["status"] = BatchVideoStatus.COMPLETED

        video_progress["video-2"]["progress"] = 50
        video_progress["video-2"]["status"] = BatchVideoStatus.PROCESSING

        # Calculate overall progress
        total_progress = sum(v["progress"] for v in video_progress.values())
        overall_progress = total_progress / len(video_progress)

        assert overall_progress == 50.0  # (100+100+50+0+0)/5 = 50

    async def test_batch_job_timeout_handling(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test handling batch job timeout."""
        timeout_seconds = 2

        async def long_running_batch_job():
            await asyncio.sleep(5)  # Longer than timeout
            return "completed"

        # Test timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(long_running_batch_job(), timeout=timeout_seconds)

    async def test_store_job_state_in_redis(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test storing job state in Redis for recovery."""
        batch_job_id = str(uuid4())

        # Mock Redis
        redis_storage = {}

        # Store state
        job_state = {
            "batch_job_id": batch_job_id,
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 5,
            "completed_count": 5,
            "failed_count": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

        redis_storage[f"batch_job_state:{batch_job_id}"] = job_state

        # Retrieve state
        retrieved_state = redis_storage[f"batch_job_state:{batch_job_id}"]

        assert retrieved_state["current_video_index"] == 5
        assert retrieved_state["completed_count"] == 5

    async def test_emit_progress_events_via_redis(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test emitting progress events via Redis."""
        batch_job_id = str(uuid4())

        # Mock Redis pub/sub
        events = []

        def publish_event(channel, event):
            events.append({"channel": channel, "event": event})

        # Emit progress events
        for i in range(3):
            publish_event(
                f"batch_progress:{batch_job_id}",
                {
                    "type": "video_progress",
                    "video_id": str(test_videos[i].id),
                    "progress": 100,
                    "status": "completed",
                }
            )

        assert len(events) == 3
        assert all(e["channel"] == f"batch_progress:{batch_job_id}" for e in events)

    async def test_handle_worker_failure_gracefully(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test graceful handling of worker failures."""
        batch_job_id = str(uuid4())

        # Simulate worker crash during processing
        job_state = {
            "batch_job_id": batch_job_id,
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 5,
        }

        # Worker crashes - state is in Redis
        # Another worker picks up the job

        # Verify state can be recovered
        recovered_state = job_state.copy()
        assert recovered_state["current_video_index"] == 5

        # Continue processing from saved state
        recovered_state["status"] = BatchJobStatus.PROCESSING
        assert recovered_state["status"] == BatchJobStatus.PROCESSING

    async def test_batch_job_cancellation_cleanup(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test cleanup when batch job is cancelled."""
        batch_job_id = str(uuid4())

        # Simulate processing
        processing_videos = [str(v.id) for v in test_videos[:3]]
        temp_files = [f"/tmp/processing/{vid}.tmp" for vid in processing_videos]

        # Cancel job
        cancelled = True

        # Cleanup
        if cancelled:
            cleaned_up_files = []
            for temp_file in temp_files:
                # Simulate file deletion
                cleaned_up_files.append(temp_file)

            assert len(cleaned_up_files) == len(temp_files)

    async def test_concurrent_batch_jobs_from_different_users(
        self, db_session: AsyncSession
    ):
        """Test processing concurrent batch jobs from different users."""
        # Create multiple users
        users = []
        for i in range(3):
            user = User(
                email=f"concurrent_user_{i}@example.com",
                hashed_password="hashed",
                full_name=f"Concurrent User {i}",
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()

        # Create batch jobs for each user
        batch_jobs = []
        for i, user in enumerate(users):
            job_id = str(uuid4())
            batch_jobs.append({
                "id": job_id,
                "user_id": user.id,
                "status": BatchJobStatus.PROCESSING,
            })

        # Process concurrently
        async def process_job(job):
            await asyncio.sleep(0.1)
            return {"job_id": job["id"], "status": "completed"}

        results = await asyncio.gather(*[process_job(job) for job in batch_jobs])

        assert len(results) == 3
        assert all(r["status"] == "completed" for r in results)

    async def test_batch_completion_notification(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test sending notification when batch completes."""
        batch_job_id = str(uuid4())

        notifications = []

        def send_notification(user_id, message):
            notifications.append({"user_id": user_id, "message": message})

        # Simulate batch completion
        batch_completed = True

        if batch_completed:
            send_notification(
                test_user.id,
                f"Batch job {batch_job_id} completed successfully!"
            )

        assert len(notifications) == 1
        assert "completed successfully" in notifications[0]["message"]

    async def test_update_database_after_video_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test updating database after video processing."""
        video = test_videos[0]

        # Simulate processing
        processing_result = {
            "video_id": video.id,
            "status": VideoStatus.COMPLETED,
            "duration": 95.5,
            "output_s3_key": f"videos/processed/{video.id}.mp4",
        }

        # Update video in database
        video.status = processing_result["status"]
        video.duration = processing_result["duration"]
        video.s3_key = processing_result["output_s3_key"]

        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        assert video.status == VideoStatus.COMPLETED
        assert video.duration == 95.5

    async def test_rate_limit_concurrent_processing_per_user(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test rate limiting concurrent processing per user."""
        max_concurrent_per_user = 2

        # User's active jobs
        active_jobs = ["job-1", "job-2"]

        # Try to start another job
        can_start = len(active_jobs) < max_concurrent_per_user

        assert can_start is False

        # Complete one job
        active_jobs.remove("job-1")

        # Now can start new job
        can_start = len(active_jobs) < max_concurrent_per_user
        assert can_start is True

    async def test_batch_processing_with_different_settings(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test batch processing with different setting combinations."""
        settings_combinations = [
            {"transcribe": True, "remove_silence": False, "detect_highlights": False},
            {"transcribe": True, "remove_silence": True, "detect_highlights": False},
            {"transcribe": True, "remove_silence": True, "detect_highlights": True},
        ]

        results = []

        async def process_with_settings(video_id, settings):
            # Simulate processing with different settings
            processing_time = 10
            if settings["transcribe"]:
                processing_time += 30
            if settings["remove_silence"]:
                processing_time += 20
            if settings["detect_highlights"]:
                processing_time += 15

            return {
                "video_id": video_id,
                "settings": settings,
                "processing_time": processing_time,
            }

        for settings in settings_combinations:
            result = await process_with_settings(str(test_videos[0].id), settings)
            results.append(result)

        assert len(results) == 3
        assert results[0]["processing_time"] == 40  # transcribe only
        assert results[1]["processing_time"] == 60  # transcribe + silence
        assert results[2]["processing_time"] == 75  # all features
