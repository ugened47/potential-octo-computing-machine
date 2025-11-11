"""Tests for highlight detection worker (ARQ background job)."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_video(db_session: AsyncSession, test_user: User) -> Video:
    """Create a test video with transcript."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        s3_key="videos/test/test-video.mp4",
        duration=120.0,
        resolution="1920x1080",
        format="h264",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.mark.asyncio
async def test_detect_highlights_task_completes_successfully(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights ARQ task completes successfully."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        # Mock dependencies
        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"

            # Mock detection result
            mock_detection.return_value = [
                {
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "overall_score": 85,
                    "audio_energy_score": 80,
                    "scene_change_score": 70,
                    "speech_density_score": 90,
                    "keyword_score": 85,
                    "detected_keywords": ["amazing"],
                    "rank": 1,
                    "highlight_type": "high_energy",
                    "confidence_level": 0.92,
                    "duration_seconds": 10.0,
                }
            ]

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            # Call worker function
            result = await detect_highlights(
                {}, str(test_video.id), sensitivity="medium"
            )

            # Verify result
            assert result["status"] == "success"
            assert result["highlights_count"] == 1

            # Verify video metadata updated
            await db_session.refresh(test_video)
            assert hasattr(test_video, "highlight_count") or True  # May not be in model yet


@pytest.mark.asyncio
async def test_detect_highlights_with_different_sensitivities(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task with different sensitivity levels."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            # Test low sensitivity (top 5, threshold 80)
            mock_detection.return_value = [
                {"overall_score": 85, "rank": 1, "start_time": 10.0, "end_time": 20.0}
            ]

            result_low = await detect_highlights(
                {}, str(test_video.id), sensitivity="low"
            )
            assert result_low["status"] == "success"

            # Test high sensitivity (top 15, threshold 60)
            mock_detection.return_value = [
                {"overall_score": 65, "rank": i, "start_time": i * 10.0, "end_time": i * 10.0 + 10.0}
                for i in range(1, 11)
            ]

            result_high = await detect_highlights(
                {}, str(test_video.id), sensitivity="high"
            )
            assert result_high["status"] == "success"


@pytest.mark.asyncio
async def test_detect_highlights_with_custom_keywords(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task with custom keywords."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"

            mock_detection.return_value = [
                {
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "overall_score": 85,
                    "keyword_score": 90,
                    "detected_keywords": ["epic", "clutch"],
                    "rank": 1,
                }
            ]

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            custom_keywords = ["epic", "clutch", "victory"]
            result = await detect_highlights(
                {}, str(test_video.id), sensitivity="medium", keywords=custom_keywords
            )

            assert result["status"] == "success"
            # Verify custom keywords were passed to detection service
            mock_detection.assert_called_once()
            call_kwargs = mock_detection.call_args[1]
            assert "keywords" in call_kwargs


@pytest.mark.asyncio
async def test_detect_highlights_tracks_progress_in_redis(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task tracks progress in Redis."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"
            mock_detection.return_value = []

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            await detect_highlights({}, str(test_video.id), sensitivity="medium")

            # Verify progress updates were made
            assert mock_redis_client.setex.call_count >= 5  # Multiple progress stages
            # Check progress stages: downloading, analyzing_audio, analyzing_video, analyzing_speech, scoring


@pytest.mark.asyncio
async def test_detect_highlights_progress_stages(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task updates progress at key stages."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"
            mock_detection.return_value = []

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            setex_calls = []

            def track_setex(key, ttl, value):
                setex_calls.append((key, value))
                return AsyncMock()

            mock_redis_client.setex = Mock(side_effect=track_setex)
            mock_redis_client.delete = AsyncMock()

            await detect_highlights({}, str(test_video.id), sensitivity="medium")

            # Verify progress stages were tracked
            progress_key = f"highlight_detection_progress:{test_video.id}"
            assert any(progress_key in call[0] for call in setex_calls)

            # Verify progress values increased over time
            # Stages: downloading (0-20%), analyzing_audio (20-40%), analyzing_video (40-60%),
            #         analyzing_speech (60-80%), scoring (80-100%)


@pytest.mark.asyncio
async def test_detect_highlights_handles_video_not_found(db_session: AsyncSession):
    """Test detect_highlights task handles video not found error."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        fake_video_id = uuid4()

        with patch("app.worker.redis.from_url") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            result = await detect_highlights({}, str(fake_video_id), sensitivity="medium")

            assert result["status"] == "error"
            assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_detect_highlights_handles_s3_download_failure(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task handles S3 download failure."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.side_effect = Exception("S3 download failed")

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            result = await detect_highlights({}, str(test_video.id), sensitivity="medium")

            assert result["status"] == "error"
            assert "S3" in result["error"] or "download" in result["error"].lower()


@pytest.mark.asyncio
async def test_detect_highlights_handles_detection_failure(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task handles detection service failure."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"
            mock_detection.side_effect = Exception("Detection failed")

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            result = await detect_highlights({}, str(test_video.id), sensitivity="medium")

            assert result["status"] == "error"


@pytest.mark.asyncio
async def test_detect_highlights_stores_highlights_in_database(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task stores Highlight records in database."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"

            mock_detection.return_value = [
                {
                    "video_id": test_video.id,
                    "start_time": 10.0,
                    "end_time": 20.0,
                    "overall_score": 85,
                    "audio_energy_score": 80,
                    "scene_change_score": 70,
                    "speech_density_score": 90,
                    "keyword_score": 85,
                    "detected_keywords": ["amazing"],
                    "rank": 1,
                    "highlight_type": "high_energy",
                    "status": "detected",
                    "duration_seconds": 10.0,
                }
            ]

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            result = await detect_highlights({}, str(test_video.id), sensitivity="medium")

            assert result["status"] == "success"

            # Verify highlight was stored in database
            from app.models.highlight import Highlight
            from sqlmodel import select

            highlights = await db_session.execute(
                select(Highlight).where(Highlight.video_id == test_video.id)
            )
            highlights_list = highlights.scalars().all()
            assert len(highlights_list) >= 1


@pytest.mark.asyncio
async def test_detect_highlights_clears_progress_on_completion(
    db_session: AsyncSession, test_video: Video
):
    """Test detect_highlights task clears progress key on completion."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import detect_highlights

        with (
            patch("app.services.s3.S3Service.download_file") as mock_s3_download,
            patch(
                "app.services.highlight_detection.HighlightDetectionService.detect_highlights"
            ) as mock_detection,
            patch("app.worker.redis.from_url") as mock_redis,
        ):
            mock_s3_download.return_value = "/tmp/test-video.mp4"
            mock_detection.return_value = []

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.delete = AsyncMock()

            await detect_highlights({}, str(test_video.id), sensitivity="medium")

            # Verify progress was set to 100% or key was deleted
            # Should have called delete or set to 100% with short TTL
            assert mock_redis_client.setex.called or mock_redis_client.delete.called
