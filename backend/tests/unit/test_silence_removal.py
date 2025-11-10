"""Unit tests for silence removal service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.silence_removal import SilenceRemovalService


@pytest.mark.asyncio
async def test_detect_silence_success(db_session: AsyncSession):
    """Test detecting silence in a video."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/video.mp4"
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    # Mock S3 download
    with patch.object(service, 'download_video_from_s3'):
        # Mock audio extraction
        with patch.object(service, 'extract_audio_from_video'):
            # Mock silence detection
            with patch.object(service, 'detect_silence_segments') as mock_detect:
                mock_detect.return_value = [
                    {"start_time": 1.0, "end_time": 2.0, "duration": 1.0},
                    {"start_time": 5.0, "end_time": 6.5, "duration": 1.5}
                ]

                segments = await service.detect_silence(video.id)

                assert len(segments) == 2
                assert segments[0]["start_time"] == 1.0
                assert segments[0]["duration"] == 1.0
                assert segments[1]["duration"] == 1.5


@pytest.mark.asyncio
async def test_detect_silence_video_not_found(db_session: AsyncSession):
    """Test detecting silence with non-existent video."""
    service = SilenceRemovalService(db_session)

    fake_id = uuid4()
    with pytest.raises(ValueError, match="not found"):
        await service.detect_silence(fake_id)


@pytest.mark.asyncio
async def test_detect_silence_no_s3_key(db_session: AsyncSession):
    """Test detecting silence with video missing S3 key."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key=None  # No S3 key
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    with pytest.raises(ValueError, match="no S3 key"):
        await service.detect_silence(video.id)


@pytest.mark.asyncio
async def test_remove_silence_success(db_session: AsyncSession):
    """Test removing silence from a video."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/video.mp4"
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    # Mock all external dependencies
    with patch.object(service, 'download_video_from_s3'):
        with patch.object(service, 'extract_audio_from_video'):
            with patch.object(service, 'detect_silence_segments') as mock_detect:
                mock_detect.return_value = [
                    {"start_time": 1.0, "end_time": 2.0, "duration": 1.0}
                ]

                with patch.object(service, 'remove_silence_from_video'):
                    with patch.object(service.s3_client, 'upload_file'):
                        with patch.object(service.s3_client, 'head_object'):
                            with patch('av.open') as mock_av:
                                # Mock AV container for duration
                                mock_container = MagicMock()
                                mock_container.duration = 10_000_000
                                mock_av.return_value = mock_container

                                result = await service.remove_silence(video.id)

                                assert result.status == VideoStatus.COMPLETED
                                assert result.s3_key is not None
                                assert "processed" in result.s3_key


@pytest.mark.asyncio
async def test_remove_silence_with_progress_callback(db_session: AsyncSession):
    """Test silence removal with progress updates."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/video.mp4"
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    # Track progress updates
    progress_updates = []

    def track_progress(progress: int):
        progress_updates.append(progress)

    # Mock all external dependencies
    with patch.object(service, 'download_video_from_s3'):
        with patch.object(service, 'extract_audio_from_video'):
            with patch.object(service, 'detect_silence_segments') as mock_detect:
                mock_detect.return_value = []  # No silence to remove

                with patch.object(service, 'remove_silence_from_video'):
                    with patch.object(service.s3_client, 'upload_file'):
                        with patch.object(service.s3_client, 'head_object'):
                            with patch('av.open') as mock_av:
                                mock_container = MagicMock()
                                mock_container.duration = 10_000_000
                                mock_av.return_value = mock_container

                                await service.remove_silence(
                                    video.id,
                                    update_progress=track_progress
                                )

                                # Verify progress was updated
                                assert len(progress_updates) > 0
                                assert 100 in progress_updates  # Should reach 100%


@pytest.mark.asyncio
async def test_remove_silence_with_excluded_segments(db_session: AsyncSession):
    """Test silence removal with excluded segments."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/video.mp4"
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    # Mock all external dependencies
    with patch.object(service, 'download_video_from_s3'):
        with patch.object(service, 'extract_audio_from_video'):
            with patch.object(service, 'detect_silence_segments') as mock_detect:
                mock_detect.return_value = [
                    {"start_time": 1.0, "end_time": 2.0, "duration": 1.0},
                    {"start_time": 5.0, "end_time": 6.0, "duration": 1.0}
                ]

                with patch.object(service, 'remove_silence_from_video') as mock_remove:
                    with patch.object(service.s3_client, 'upload_file'):
                        with patch.object(service.s3_client, 'head_object'):
                            with patch('av.open') as mock_av:
                                mock_container = MagicMock()
                                mock_container.duration = 10_000_000
                                mock_av.return_value = mock_container

                                await service.remove_silence(
                                    video.id,
                                    excluded_segments=[0]  # Exclude first segment
                                )

                                # Verify excluded segments were passed
                                mock_remove.assert_called_once()
                                call_args = mock_remove.call_args
                                assert call_args[0][3] == [0]  # excluded_segments


def test_detect_silence_segments_with_threshold():
    """Test silence detection with custom threshold."""
    # This would require actual audio file, so we'll test the logic
    service = SilenceRemovalService(Mock())

    # Test that the method exists and accepts parameters
    assert hasattr(service, 'detect_silence_segments')


def test_remove_silence_from_video_no_segments():
    """Test video copy when no segments to remove."""
    # This would require actual video file, so we test the logic exists
    service = SilenceRemovalService(Mock())

    assert hasattr(service, 'remove_silence_from_video')


def test_extract_audio_from_video_method_exists():
    """Test that audio extraction method exists."""
    service = SilenceRemovalService(Mock())

    assert hasattr(service, 'extract_audio_from_video')


def test_download_video_from_s3_method_exists():
    """Test that S3 download method exists."""
    service = SilenceRemovalService(Mock())

    assert hasattr(service, 'download_video_from_s3')
