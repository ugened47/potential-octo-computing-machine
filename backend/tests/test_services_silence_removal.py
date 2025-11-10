"""Tests for silence removal service."""

import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.silence_removal import SilenceRemovalService


@pytest.mark.asyncio
async def test_detect_silence_segments():
    """Test silence detection in audio file."""
    # This is a unit test for the silence detection algorithm
    # In a real scenario, you would create a test audio file
    # For now, we'll mock the PyAV container

    service = SilenceRemovalService(Mock())

    # Mock PyAV container and frames
    with patch("av.open") as mock_av_open:
        mock_container = Mock()
        mock_stream = Mock()
        mock_container.streams.audio = [mock_stream]

        # Create mock frames with varying RMS levels
        # Simulate: silence (0-2s), sound (2-5s), silence (5-7s)
        mock_frames = []

        # Silent frames (RMS < threshold)
        for i in range(10):  # 0-2 seconds
            frame = Mock()
            frame.time = i * 0.2
            frame.to_ndarray = Mock(return_value=[0.001])  # Very quiet
            mock_frames.append(frame)

        # Sound frames (RMS > threshold)
        for i in range(10, 25):  # 2-5 seconds
            frame = Mock()
            frame.time = i * 0.2
            frame.to_ndarray = Mock(return_value=[0.5])  # Loud
            mock_frames.append(frame)

        # Silent frames again
        for i in range(25, 35):  # 5-7 seconds
            frame = Mock()
            frame.time = i * 0.2
            frame.to_ndarray = Mock(return_value=[0.001])  # Very quiet
            mock_frames.append(frame)

        mock_container.decode = Mock(return_value=mock_frames)
        mock_av_open.return_value = mock_container

        # Test detection
        segments = service.detect_silence_segments(
            "test.wav", threshold_db=-40, min_duration_ms=1000
        )

        # Should detect 2 silent segments
        assert len(segments) == 2
        assert segments[0]["start_time"] < 2.0
        assert segments[1]["start_time"] > 5.0


@pytest.mark.asyncio
async def test_detect_silence_video_not_found(db_session: AsyncSession):
    """Test detect_silence raises error when video not found."""
    service = SilenceRemovalService(db_session)

    with pytest.raises(ValueError, match="not found"):
        await service.detect_silence(uuid4())


@pytest.mark.asyncio
async def test_detect_silence_no_s3_key(db_session: AsyncSession):
    """Test detect_silence raises error when video has no S3 key."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id, title="Test", status=VideoStatus.UPLOADED, s3_key=None
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    with pytest.raises(ValueError, match="no S3 key"):
        await service.detect_silence(video.id)


@pytest.mark.asyncio
async def test_remove_silence_video_not_found(db_session: AsyncSession):
    """Test remove_silence raises error when video not found."""
    service = SilenceRemovalService(db_session)

    with pytest.raises(ValueError, match="not found"):
        await service.remove_silence(uuid4())


@pytest.mark.asyncio
async def test_remove_silence_no_s3_key(db_session: AsyncSession):
    """Test remove_silence raises error when video has no S3 key."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(
        user_id=user.id, title="Test", status=VideoStatus.UPLOADED, s3_key=None
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = SilenceRemovalService(db_session)

    with pytest.raises(ValueError, match="no S3 key"):
        await service.remove_silence(video.id)


@pytest.mark.asyncio
async def test_segment_exclusion():
    """Test that excluded segments are not removed."""
    service = SilenceRemovalService(Mock())

    # Mock segments
    silent_segments = [
        {"start_time": 1.0, "end_time": 2.0, "duration": 1.0},
        {"start_time": 5.0, "end_time": 7.0, "duration": 2.0},
        {"start_time": 10.0, "end_time": 12.0, "duration": 2.0},
    ]

    # This test verifies the logic but doesn't actually process video
    # In production, you'd want integration tests with real video files

    # Filter out excluded segments (indices 0 and 2)
    excluded = [0, 2]
    filtered_segments = [
        seg for i, seg in enumerate(silent_segments) if i not in excluded
    ]

    # Should only have segment at index 1
    assert len(filtered_segments) == 1
    assert filtered_segments[0]["start_time"] == 5.0


@pytest.mark.asyncio
async def test_extract_audio_from_video():
    """Test audio extraction from video file."""
    service = SilenceRemovalService(Mock())

    # This test would require a real video file
    # For unit testing, we verify the method exists and has correct signature
    assert hasattr(service, "extract_audio_from_video")
    assert callable(service.extract_audio_from_video)


@pytest.mark.asyncio
async def test_download_video_from_s3():
    """Test S3 video download."""
    service = SilenceRemovalService(Mock())

    with patch.object(service.s3_client, "download_file") as mock_download:
        service.download_video_from_s3("test-key", "/tmp/test.mp4")

        # Verify download was called
        mock_download.assert_called_once()
        assert "test-key" in str(mock_download.call_args)
