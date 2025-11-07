"""Tests for video metadata extraction service."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.video_metadata import VideoMetadataService


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
async def test_extract_metadata_extracts_duration_resolution_format(
    db_session: AsyncSession, test_user: User
):
    """Test extract_metadata extracts duration, resolution, format."""
    service = VideoMetadataService(db_session)

    # Mock PyAV container
    with patch("av.open") as mock_open:
        # Create mock container that works as context manager
        mock_container = Mock()
        mock_container.__enter__ = Mock(return_value=mock_container)
        mock_container.__exit__ = Mock(return_value=None)
        mock_open.return_value = mock_container
        
        # Mock video stream
        mock_stream = Mock()
        mock_stream.width = 1920
        mock_stream.height = 1080
        mock_codec = Mock()
        mock_codec.name = "h264"
        mock_stream.codec = mock_codec
        mock_stream.duration = None
        mock_stream.time_base = None
        
        # Mock streams
        mock_streams = Mock()
        mock_streams.video = [mock_stream]
        mock_container.streams = mock_streams
        
        # Mock container properties
        mock_container.duration = 120500000  # microseconds (120.5 seconds)
        mock_format = Mock()
        mock_format.name = "mp4"
        mock_container.format = mock_format

        metadata = service.extract_metadata("/tmp/test-video.mp4")

        assert metadata["duration"] == 120.5
        assert metadata["resolution"] == "1920x1080"
        assert metadata["format"] == "h264"


@pytest.mark.asyncio
async def test_extract_video_metadata_updates_video_status_flow(
    db_session: AsyncSession, test_user: User
):
    """Test extract_video_metadata updates video status: uploaded → processing → completed."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/test-video.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = VideoMetadataService(db_session)

    # Mock S3 download and metadata extraction
    with patch.object(service, "download_video_from_s3"), \
         patch.object(service, "extract_metadata") as mock_extract:
        
        mock_extract.return_value = {
            "duration": 60.0,
            "resolution": "1280x720",
            "format": "h264",
        }

        # Call service
        updated_video = await service.extract_video_metadata(video.id)

        # Verify status was updated to completed
        assert updated_video.status == VideoStatus.COMPLETED
        assert updated_video.duration == 60.0
        assert updated_video.resolution == "1280x720"
        assert updated_video.format == "h264"


@pytest.mark.asyncio
async def test_extract_video_metadata_error_handling(
    db_session: AsyncSession, test_user: User
):
    """Test error handling in extract_video_metadata."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.PROCESSING,
        s3_key="videos/test/test-video.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = VideoMetadataService(db_session)

    # Mock S3 download to raise error
    with patch.object(service, "download_video_from_s3") as mock_download:
        mock_download.side_effect = ValueError("Failed to download video")

        # Should raise exception
        with pytest.raises(ValueError, match="Failed to download video"):
            await service.extract_video_metadata(video.id)


@pytest.mark.asyncio
async def test_extract_video_metadata_progress_callback(
    db_session: AsyncSession, test_user: User
):
    """Test progress callback is called during metadata extraction."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/test-video.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = VideoMetadataService(db_session)
    progress_updates = []

    def update_progress(progress: int) -> None:
        progress_updates.append(progress)

    # Mock S3 download and metadata extraction
    with patch.object(service, "download_video_from_s3"), \
         patch.object(service, "extract_metadata") as mock_extract:
        
        mock_extract.return_value = {
            "duration": 60.0,
            "resolution": "1280x720",
            "format": "h264",
        }

        await service.extract_video_metadata(video.id, update_progress)

        # Verify progress was updated
        assert len(progress_updates) > 0
        assert 100 in progress_updates  # Should reach 100%

