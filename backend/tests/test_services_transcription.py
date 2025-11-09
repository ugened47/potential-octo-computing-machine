"""Tests for transcription service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from app.models.transcript import Transcript, TranscriptStatus
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.transcription import TranscriptionService


@pytest.mark.asyncio
async def test_get_transcript_existing(db_session: AsyncSession):
    """Test getting an existing transcript."""
    # Create user and video
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Create transcript
    transcript = Transcript(
        video_id=video.id,
        full_text="Test transcript",
        word_timestamps={},
        status=TranscriptStatus.COMPLETED,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    # Get transcript
    service = TranscriptionService(db_session)
    result = await service.get_transcript(video.id)

    assert result is not None
    assert result.id == transcript.id
    assert result.full_text == "Test transcript"


@pytest.mark.asyncio
async def test_get_transcript_not_found(db_session: AsyncSession):
    """Test getting transcript when it doesn't exist."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = TranscriptionService(db_session)
    result = await service.get_transcript(video.id)

    assert result is None


@pytest.mark.asyncio
async def test_create_transcript_record(db_session: AsyncSession):
    """Test creating a new transcript record."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    service = TranscriptionService(db_session)
    transcript = await service.create_transcript_record(video.id)

    assert transcript.id is not None
    assert transcript.video_id == video.id
    assert transcript.status == TranscriptStatus.PROCESSING
    assert transcript.full_text == ""


@pytest.mark.asyncio
async def test_update_transcript(db_session: AsyncSession):
    """Test updating transcript with transcription results."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="",
        word_timestamps={},
        status=TranscriptStatus.PROCESSING,
    )
    db_session.add(transcript)
    await db_session.commit()
    await db_session.refresh(transcript)

    word_timestamps = {
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95}
        ]
    }

    service = TranscriptionService(db_session)
    updated = await service.update_transcript(
        transcript.id,
        full_text="Hello",
        word_timestamps=word_timestamps,
        language="en",
        status=TranscriptStatus.COMPLETED,
    )

    assert updated.full_text == "Hello"
    assert updated.language == "en"
    assert updated.status == TranscriptStatus.COMPLETED
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_format_transcript_srt(db_session: AsyncSession):
    """Test formatting transcript as SRT."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="Hello world",
        word_timestamps={
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92},
            ]
        },
        status=TranscriptStatus.COMPLETED,
    )

    service = TranscriptionService(db_session)
    srt_content = service.format_transcript_srt(transcript)

    assert "1" in srt_content  # Sequence number
    assert "00:00:00" in srt_content  # Timestamp format
    assert "Hello world" in srt_content


@pytest.mark.asyncio
async def test_format_transcript_vtt(db_session: AsyncSession):
    """Test formatting transcript as VTT."""
    user = User(email="test@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    video = Video(user_id=user.id, title="Test", status=VideoStatus.UPLOADED)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    transcript = Transcript(
        video_id=video.id,
        full_text="Hello world",
        word_timestamps={
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92},
            ]
        },
        status=TranscriptStatus.COMPLETED,
    )

    service = TranscriptionService(db_session)
    vtt_content = service.format_transcript_vtt(transcript)

    assert "WEBVTT" in vtt_content
    assert "00:00:00" in vtt_content
    assert "Hello world" in vtt_content


@pytest.mark.asyncio
async def test_transcribe_video_missing_s3_key(db_session: AsyncSession):
    """Test transcribe_video raises error when video has no S3 key."""
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

    service = TranscriptionService(db_session)

    with pytest.raises(ValueError, match="no S3 key"):
        await service.transcribe_video(video.id)


@pytest.mark.asyncio
async def test_transcribe_audio_with_retry_success(db_session: AsyncSession):
    """Test transcribe_audio_with_retry succeeds on first attempt."""
    service = TranscriptionService(db_session)

    mock_response = Mock()
    mock_response.text = "Test transcription"
    mock_response.language = "en"
    mock_response.words = [
        Mock(word="Test", start=0.0, end=0.5, probability=0.95),
        Mock(word="transcription", start=0.5, end=1.5, probability=0.92),
    ]

    with patch.object(
        service.openai_client.audio.transcriptions, "create", return_value=mock_response
    ):
        with patch("builtins.open", create=True):
            result = await service.transcribe_audio_with_retry("/fake/path.mp3")

    assert result["text"] == "Test transcription"
    assert result["language"] == "en"
    assert len(result["word_timestamps"]["words"]) == 2


@pytest.mark.asyncio
async def test_transcribe_audio_with_retry_failure_then_success(db_session: AsyncSession):
    """Test transcribe_audio_with_retry succeeds after retry."""
    from openai import APIError

    service = TranscriptionService(db_session)

    mock_response = Mock()
    mock_response.text = "Test transcription"
    mock_response.language = "en"
    mock_response.words = [
        Mock(word="Test", start=0.0, end=0.5, probability=0.95),
    ]

    # First call fails, second succeeds
    with patch.object(
        service.openai_client.audio.transcriptions,
        "create",
        side_effect=[
            APIError("Rate limit exceeded"),
            mock_response,
        ],
    ):
        with patch("builtins.open", create=True):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await service.transcribe_audio_with_retry("/fake/path.mp3")

    assert result["text"] == "Test transcription"


@pytest.mark.asyncio
async def test_transcribe_audio_with_retry_max_retries_exceeded(db_session: AsyncSession):
    """Test transcribe_audio_with_retry fails after max retries."""
    from openai import APIError

    service = TranscriptionService(db_session)

    with patch.object(
        service.openai_client.audio.transcriptions,
        "create",
        side_effect=APIError("Rate limit exceeded"),
    ):
        with patch("builtins.open", create=True):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(APIError):
                    await service.transcribe_audio_with_retry("/fake/path.mp3", max_retries=2)


@pytest.mark.asyncio
async def test_split_audio_into_chunks(db_session: AsyncSession):
    """Test splitting audio into chunks."""
    service = TranscriptionService(db_session)

    # Mock PyAV container and stream
    mock_container = Mock()
    mock_stream = Mock()
    mock_stream.time_base = 0.001  # 1ms time base

    # Create mock frames with timestamps
    mock_frames = []
    for i in range(0, 1200, 100):  # 12 frames spanning 1200 seconds
        frame = Mock()
        frame.pts = i * 1000  # Convert to ms
        frame.layout.nb_channels = 1
        mock_frames.append(frame)

    mock_container.streams.audio = [mock_stream]
    mock_container.decode.return_value = iter(mock_frames)

    with patch("av.open", return_value=mock_container):
        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.return_value.__enter__.return_value.name = "/fake/chunk.mp3"

            # Mock output containers
            mock_output = Mock()
            mock_output_stream = Mock()
            mock_output_stream.encode.return_value = []
            mock_output.add_stream.return_value = mock_output_stream

            with patch("av.open", return_value=mock_output):
                chunks = service._split_audio_into_chunks("/fake/audio.mp3", chunk_duration_seconds=600)

    # Should create 2 chunks (0-600s, 600-1200s)
    assert len(chunks) >= 2


@pytest.mark.asyncio
async def test_transcribe_audio_chunked(db_session: AsyncSession):
    """Test transcribing audio file with chunking."""
    service = TranscriptionService(db_session)

    # Mock chunk paths
    chunk_paths = ["/fake/chunk1.mp3", "/fake/chunk2.mp3"]

    # Mock transcription results for each chunk
    chunk1_result = {
        "text": "First chunk",
        "language": "en",
        "word_timestamps": {
            "words": [
                {"word": "First", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "chunk", "start": 0.5, "end": 1.0, "confidence": 0.92},
            ]
        },
    }

    chunk2_result = {
        "text": "Second chunk",
        "language": "en",
        "word_timestamps": {
            "words": [
                {"word": "Second", "start": 0.0, "end": 0.6, "confidence": 0.93},
                {"word": "chunk", "start": 0.6, "end": 1.2, "confidence": 0.91},
            ]
        },
    }

    with patch.object(
        service, "_split_audio_into_chunks", return_value=chunk_paths
    ):
        with patch.object(
            service,
            "transcribe_audio",
            side_effect=[chunk1_result, chunk2_result],
        ):
            with patch("os.path.exists", return_value=True):
                with patch("os.unlink"):
                    result = await service._transcribe_audio_chunked("/fake/audio.mp3")

    # Verify merged results
    assert result["text"] == "First chunk Second chunk"
    assert result["language"] == "en"
    assert len(result["word_timestamps"]["words"]) == 4

    # Verify timestamp offsets
    words = result["word_timestamps"]["words"]
    assert words[0]["word"] == "First"
    assert words[0]["start"] == 0.0
    assert words[2]["word"] == "Second"
    # Second chunk should be offset by last word end time from first chunk (1.0)
    assert words[2]["start"] == 1.0
    assert words[3]["start"] == 1.6  # 0.6 + 1.0 offset

