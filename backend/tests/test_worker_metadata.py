"""Tests for metadata extraction worker."""

from unittest.mock import AsyncMock, patch

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


@pytest.mark.asyncio
async def test_extract_video_metadata_extracts_duration_resolution_format(
    db_session, test_user: User
):
    """Test extract_video_metadata job extracts duration, resolution, format."""
    # Mock ARQ dependencies before importing worker
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import extract_video_metadata

        # Create video with S3 key
        video = Video(
            user_id=test_user.id,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            s3_key="videos/test/test-video.mp4",
        )
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        # Mock S3 download and metadata extraction
        with (
            patch("app.services.video_metadata.VideoMetadataService.download_video_from_s3"),
            patch(
                "app.services.video_metadata.VideoMetadataService.extract_metadata"
            ) as mock_extract,
        ):
            mock_extract.return_value = {
                "duration": 120.5,
                "resolution": "1920x1080",
                "format": "h264",
            }

            # Mock Redis
            with patch("app.worker.redis.from_url") as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                mock_redis_client.setex = AsyncMock()
                mock_redis_client.delete = AsyncMock()

                # Call worker function
                result = await extract_video_metadata({}, str(video.id))

                # Verify result
                assert result["status"] == "success"
                assert result["duration"] == 120.5
                assert result["resolution"] == "1920x1080"
                assert result["format"] == "h264"

                # Verify video was updated
                await db_session.refresh(video)
                assert video.duration == 120.5
                assert video.resolution == "1920x1080"
                assert video.format == "h264"
                assert video.status == VideoStatus.COMPLETED


@pytest.mark.asyncio
async def test_extract_video_metadata_status_updates_flow(db_session, test_user: User):
    """Test video status updates: 'uploaded' → 'processing' → 'completed'."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import extract_video_metadata

        video = Video(
            user_id=test_user.id,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            s3_key="videos/test/test-video.mp4",
        )
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        initial_status = video.status
        assert initial_status == VideoStatus.UPLOADED

        with (
            patch("app.services.video_metadata.VideoMetadataService.download_video_from_s3"),
            patch(
                "app.services.video_metadata.VideoMetadataService.extract_metadata"
            ) as mock_extract,
        ):
            mock_extract.return_value = {
                "duration": 60.0,
                "resolution": "1280x720",
                "format": "h264",
            }

            with patch("app.worker.redis.from_url") as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                mock_redis_client.setex = AsyncMock()
                mock_redis_client.delete = AsyncMock()

                # Call worker function
                await extract_video_metadata({}, str(video.id))

                # Verify status flow
                await db_session.refresh(video)
                assert video.status == VideoStatus.COMPLETED


@pytest.mark.asyncio
async def test_extract_video_metadata_error_handling_sets_failed_status(
    db_session, test_user: User
):
    """Test error handling sets status to 'failed'."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import extract_video_metadata

        video = Video(
            user_id=test_user.id,
            title="Test Video",
            status=VideoStatus.PROCESSING,
            s3_key="videos/test/test-video.mp4",
        )
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        # Mock S3 download to raise error
        with patch(
            "app.services.video_metadata.VideoMetadataService.download_video_from_s3"
        ) as mock_download:
            mock_download.side_effect = ValueError("Failed to download video")

            with patch("app.worker.redis.from_url") as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                mock_redis_client.setex = AsyncMock()

                # Call worker function - should raise exception but update status
                with pytest.raises(Exception):
                    await extract_video_metadata({}, str(video.id))

                # Verify video status was set to failed
                await db_session.refresh(video)
                assert video.status == VideoStatus.FAILED


@pytest.mark.asyncio
async def test_extract_video_metadata_redis_progress_tracking(db_session, test_user: User):
    """Test Redis progress tracking updates correctly."""
    with patch("arq.create_pool"), patch("arq.connections.RedisSettings"):
        from app.worker import extract_video_metadata

        video = Video(
            user_id=test_user.id,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            s3_key="videos/test/test-video.mp4",
        )
        db_session.add(video)
        await db_session.commit()
        await db_session.refresh(video)

        with (
            patch("app.services.video_metadata.VideoMetadataService.download_video_from_s3"),
            patch(
                "app.services.video_metadata.VideoMetadataService.extract_metadata"
            ) as mock_extract,
        ):
            mock_extract.return_value = {
                "duration": 60.0,
                "resolution": "1280x720",
                "format": "h264",
            }

            with patch("app.worker.redis.from_url") as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                mock_redis_client.setex = AsyncMock()
                mock_redis_client.delete = AsyncMock()

                # Call worker function
                await extract_video_metadata({}, str(video.id))

                # Verify Redis progress was updated
                assert mock_redis_client.setex.called
                # Verify progress key was deleted after completion
                assert mock_redis_client.delete.called
