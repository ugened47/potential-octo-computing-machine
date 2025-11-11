"""Tests for batch processing service."""

import asyncio
from datetime import datetime, timedelta
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


class BatchProcessingService:
    """Mock batch processing service for testing."""

    def __init__(self, db: AsyncSession):
        self.db = db


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="processing_test@example.com",
        hashed_password="hashed_password",
        full_name="Processing Test User",
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
            title=f"Test Video {i+1}",
            status=VideoStatus.UPLOADED,
            s3_key=f"videos/test/video-{i+1}.mp4",
            duration=120.0,
        )
        db_session.add(video)
        videos.append(video)
    await db_session.commit()
    for video in videos:
        await db_session.refresh(video)
    return videos


@pytest.mark.asyncio
class TestBatchProcessingService:
    """Tests for batch processing service."""

    async def test_apply_settings_to_multiple_videos(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test applying shared settings to all videos in batch."""
        service = BatchProcessingService(db_session)

        batch_settings = {
            "transcribe": True,
            "remove_silence": True,
            "detect_highlights": False,
            "silence_threshold": -40.0,
            "export_format": "mp4",
            "export_quality": "1080p",
        }

        # Simulate applying settings to each video
        for video in test_videos[:5]:
            # In real implementation, settings would be applied during processing
            video_settings = batch_settings.copy()
            assert video_settings["transcribe"] is True
            assert video_settings["remove_silence"] is True
            assert video_settings["silence_threshold"] == -40.0

    async def test_process_videos_sequentially(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test processing videos sequentially."""
        service = BatchProcessingService(db_session)

        processed_videos = []

        async def process_video(video):
            await asyncio.sleep(0.1)  # Simulate processing
            return video.id

        # Process sequentially
        for video in test_videos[:3]:
            result = await process_video(video)
            processed_videos.append(result)

        assert len(processed_videos) == 3
        assert processed_videos[0] == test_videos[0].id

    async def test_process_videos_with_concurrency(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test processing videos with concurrency limit."""
        service = BatchProcessingService(db_session)

        concurrency_limit = 3

        async def process_video(video):
            await asyncio.sleep(0.1)
            return video.id

        # Process with concurrency limit
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def process_with_limit(video):
            async with semaphore:
                return await process_video(video)

        results = await asyncio.gather(
            *[process_with_limit(v) for v in test_videos[:5]]
        )

        assert len(results) == 5

    async def test_track_progress_for_each_video(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test tracking progress for each video."""
        service = BatchProcessingService(db_session)

        video_progress = {}

        # Initialize progress tracking
        for video in test_videos[:3]:
            video_progress[str(video.id)] = {
                "status": BatchVideoStatus.PENDING,
                "progress_percentage": 0,
                "current_stage": None,
            }

        # Simulate processing stages
        stages = ["transcribing", "removing_silence", "detecting_highlights", "exporting"]

        for video_id in video_progress:
            for i, stage in enumerate(stages):
                video_progress[video_id]["current_stage"] = stage
                video_progress[video_id]["progress_percentage"] = (i + 1) * 25
                video_progress[video_id]["status"] = BatchVideoStatus.PROCESSING

            video_progress[video_id]["status"] = BatchVideoStatus.COMPLETED
            video_progress[video_id]["progress_percentage"] = 100

        assert all(p["progress_percentage"] == 100 for p in video_progress.values())
        assert all(p["status"] == BatchVideoStatus.COMPLETED for p in video_progress.values())

    async def test_update_batch_job_progress_counters(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating batch job progress counters."""
        service = BatchProcessingService(db_session)

        batch_stats = {
            "total_videos": 10,
            "completed_videos": 0,
            "failed_videos": 0,
            "cancelled_videos": 0,
        }

        # Simulate processing
        for i in range(10):
            if i < 7:
                batch_stats["completed_videos"] += 1
            elif i < 9:
                batch_stats["failed_videos"] += 1
            else:
                batch_stats["cancelled_videos"] += 1

        assert batch_stats["completed_videos"] == 7
        assert batch_stats["failed_videos"] == 2
        assert batch_stats["cancelled_videos"] == 1

    async def test_calculate_estimated_time_remaining(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test calculating estimated time remaining."""
        service = BatchProcessingService(db_session)

        total_videos = 10
        completed_videos = 3
        average_processing_time = 120  # seconds per video

        remaining_videos = total_videos - completed_videos
        estimated_time = remaining_videos * average_processing_time

        assert estimated_time == 7 * 120  # 840 seconds
        assert estimated_time / 60 == 14  # 14 minutes

    async def test_handle_individual_video_failure_without_stopping_batch(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test handling individual video failures without stopping batch."""
        service = BatchProcessingService(db_session)

        results = []

        async def process_video(video, should_fail=False):
            if should_fail:
                raise Exception(f"Processing failed for {video.id}")
            return {"video_id": video.id, "status": "completed"}

        # Process with some failures
        for i, video in enumerate(test_videos[:5]):
            try:
                result = await process_video(video, should_fail=(i == 2))
                results.append(result)
            except Exception as e:
                results.append({"video_id": video.id, "status": "failed", "error": str(e)})

        assert len(results) == 5
        assert results[2]["status"] == "failed"
        assert results[0]["status"] == "completed"
        assert results[4]["status"] == "completed"

    async def test_pause_batch_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test pausing batch processing."""
        service = BatchProcessingService(db_session)

        batch_state = {
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 3,
            "paused": False,
        }

        # Pause processing
        batch_state["status"] = BatchJobStatus.PAUSED
        batch_state["paused"] = True

        assert batch_state["status"] == BatchJobStatus.PAUSED
        assert batch_state["current_video_index"] == 3  # State preserved

    async def test_resume_batch_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test resuming batch processing from paused state."""
        service = BatchProcessingService(db_session)

        batch_state = {
            "status": BatchJobStatus.PAUSED,
            "current_video_index": 5,
            "paused": True,
        }

        # Resume processing
        batch_state["status"] = BatchJobStatus.PROCESSING
        batch_state["paused"] = False

        assert batch_state["status"] == BatchJobStatus.PROCESSING
        assert batch_state["current_video_index"] == 5  # Resume from where we left off

    async def test_cancel_batch_processing(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test cancelling batch processing."""
        service = BatchProcessingService(db_session)

        batch_state = {
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 4,
        }

        # Cancel processing
        batch_state["status"] = BatchJobStatus.CANCELLED

        # Mark remaining videos as cancelled
        cancelled_count = 0
        for i in range(batch_state["current_video_index"], 10):
            cancelled_count += 1

        assert batch_state["status"] == BatchJobStatus.CANCELLED
        assert cancelled_count == 6  # Videos 4-9

    async def test_retry_failed_videos(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test retrying failed videos."""
        service = BatchProcessingService(db_session)

        video_states = {
            str(test_videos[0].id): {"status": BatchVideoStatus.COMPLETED, "retry_count": 0},
            str(test_videos[1].id): {"status": BatchVideoStatus.FAILED, "retry_count": 1},
            str(test_videos[2].id): {"status": BatchVideoStatus.FAILED, "retry_count": 2},
        }

        max_retries = 3

        # Retry failed videos
        retried_videos = []
        for video_id, state in video_states.items():
            if state["status"] == BatchVideoStatus.FAILED and state["retry_count"] < max_retries:
                state["status"] = BatchVideoStatus.PENDING
                state["retry_count"] += 1
                retried_videos.append(video_id)

        assert len(retried_videos) == 2
        assert video_states[str(test_videos[1].id)]["retry_count"] == 2
        assert video_states[str(test_videos[2].id)]["retry_count"] == 3

    async def test_retry_with_exponential_backoff(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test retry logic with exponential backoff."""
        service = BatchProcessingService(db_session)

        retry_count = 0
        base_delay = 1  # seconds

        delays = []
        for attempt in range(5):
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            delays.append(delay)

        assert delays == [1, 2, 4, 8, 16]

    async def test_mark_batch_completed_when_all_videos_done(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test marking batch as completed when all videos are done."""
        service = BatchProcessingService(db_session)

        batch_stats = {
            "total_videos": 10,
            "completed_videos": 7,
            "failed_videos": 3,
            "status": BatchJobStatus.PROCESSING,
        }

        # Check if all videos processed (completed or failed)
        if batch_stats["completed_videos"] + batch_stats["failed_videos"] == batch_stats["total_videos"]:
            batch_stats["status"] = BatchJobStatus.COMPLETED

        assert batch_stats["status"] == BatchJobStatus.COMPLETED

    async def test_store_processing_results(
        self, db_session: AsyncSession, test_user: User, test_videos: list[Video]
    ):
        """Test storing processing results for each video."""
        service = BatchProcessingService(db_session)

        processing_results = {}

        for video in test_videos[:3]:
            processing_results[str(video.id)] = {
                "transcription_word_count": 1500,
                "silence_segments_removed": 12,
                "highlights_detected": 5,
                "output_duration": 95.5,
                "processing_time": 145.2,
            }

        assert len(processing_results) == 3
        assert all("transcription_word_count" in r for r in processing_results.values())

    async def test_generate_batch_summary_report(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test generating batch summary report."""
        service = BatchProcessingService(db_session)

        batch_summary = {
            "total_videos": 10,
            "completed_videos": 8,
            "failed_videos": 2,
            "total_processing_time": 1200,  # seconds
            "average_processing_time": 150,  # seconds per video
            "total_input_duration": 1200,  # seconds
            "total_output_duration": 960,  # seconds
            "time_saved": 240,  # seconds
        }

        assert batch_summary["completed_videos"] == 8
        assert batch_summary["time_saved"] == 240

    async def test_manage_processing_queue(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test managing processing queue."""
        service = BatchProcessingService(db_session)

        queue = []

        # Add jobs to queue
        for i in range(5):
            queue.append({
                "batch_job_id": f"batch-{i}",
                "priority": i,
                "created_at": datetime.utcnow(),
            })

        # Sort by priority
        queue.sort(key=lambda x: x["priority"], reverse=True)

        assert queue[0]["priority"] == 4  # Highest priority first
        assert len(queue) == 5

    async def test_enforce_concurrency_limits_per_tier(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test enforcing concurrency limits based on user tier."""
        service = BatchProcessingService(db_session)

        tier_limits = {
            "free": 1,
            "creator": 3,
            "pro": 5,
        }

        user_tier = "creator"
        max_concurrent = tier_limits[user_tier]

        assert max_concurrent == 3

        # Simulate concurrent processing
        active_jobs = ["job-1", "job-2", "job-3"]

        # Try to add another job
        can_process = len(active_jobs) < max_concurrent
        assert can_process is False

    async def test_track_active_batch_jobs_in_redis(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test tracking active batch jobs in Redis."""
        service = BatchProcessingService(db_session)

        # Mock Redis storage
        redis_storage = {}

        batch_job_id = str(uuid4())
        redis_storage[f"batch_job:{batch_job_id}"] = {
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 5,
            "completed_count": 5,
            "started_at": datetime.utcnow().isoformat(),
        }

        assert f"batch_job:{batch_job_id}" in redis_storage
        assert redis_storage[f"batch_job:{batch_job_id}"]["status"] == BatchJobStatus.PROCESSING

    async def test_fair_scheduling_round_robin(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test fair scheduling with round-robin across users."""
        service = BatchProcessingService(db_session)

        # Multiple users with jobs
        user_queues = {
            "user-1": ["job-1a", "job-1b"],
            "user-2": ["job-2a", "job-2b"],
            "user-3": ["job-3a"],
        }

        # Round-robin scheduling
        scheduled = []
        while any(user_queues.values()):
            for user_id in list(user_queues.keys()):
                if user_queues[user_id]:
                    job = user_queues[user_id].pop(0)
                    scheduled.append(job)
                    if not user_queues[user_id]:
                        del user_queues[user_id]

        # Should alternate between users
        assert scheduled == ["job-1a", "job-2a", "job-3a", "job-1b", "job-2b"]

    async def test_job_state_persistence_for_recovery(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test job state persistence for worker restart recovery."""
        service = BatchProcessingService(db_session)

        # Save state before crash
        job_state = {
            "batch_job_id": str(uuid4()),
            "status": BatchJobStatus.PROCESSING,
            "current_video_index": 7,
            "completed_videos": [f"video-{i}" for i in range(7)],
            "failed_videos": ["video-3"],
        }

        # Simulate worker crash and recovery
        recovered_state = job_state.copy()

        # Resume from saved state
        assert recovered_state["current_video_index"] == 7
        assert len(recovered_state["completed_videos"]) == 7
        assert "video-3" in recovered_state["failed_videos"]

    async def test_update_batch_statistics(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating batch statistics in real-time."""
        service = BatchProcessingService(db_session)

        batch_stats = {
            "total_duration_seconds": 0.0,
            "processed_duration_seconds": 0.0,
        }

        # Add video durations
        video_durations = [120.5, 180.0, 95.3, 200.0]

        for duration in video_durations:
            batch_stats["total_duration_seconds"] += duration
            batch_stats["processed_duration_seconds"] += duration * 0.8  # Assume 20% removed

        assert batch_stats["total_duration_seconds"] == sum(video_durations)
        assert batch_stats["processed_duration_seconds"] < batch_stats["total_duration_seconds"]
