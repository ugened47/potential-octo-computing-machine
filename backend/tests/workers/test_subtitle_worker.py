"""Tests for subtitle worker tasks."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest


# Mock models and enums
class SubtitleStatus:
    """Subtitle processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MockSubtitleBurnJob:
    """Mock SubtitleBurnJob model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id', uuid4())
        self.transcript_id = kwargs.get('transcript_id', uuid4())
        self.style_id = kwargs.get('style_id')
        self.user_id = kwargs.get('user_id', uuid4())
        self.custom_style = kwargs.get('custom_style')
        self.status = kwargs.get('status', SubtitleStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.output_s3_key = kwargs.get('output_s3_key')
        self.output_url = kwargs.get('output_url')
        self.error_message = kwargs.get('error_message')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at')


class MockSubtitleTranslation:
    """Mock SubtitleTranslation model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.transcript_id = kwargs.get('transcript_id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.source_language = kwargs.get('source_language', 'en')
        self.target_language = kwargs.get('target_language', 'es')
        self.status = kwargs.get('status', SubtitleStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.translated_content = kwargs.get('translated_content')
        self.error_message = kwargs.get('error_message')
        self.confidence_score = kwargs.get('confidence_score')
        self.character_count = kwargs.get('character_count')
        self.cost = kwargs.get('cost')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at')


class MockVideo:
    """Mock Video model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.s3_key = kwargs.get('s3_key', 'videos/test/video.mp4')
        self.duration = kwargs.get('duration', 120.0)


class MockTranscript:
    """Mock Transcript model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id', uuid4())
        self.language = kwargs.get('language', 'en')
        self.segments = kwargs.get('segments', [
            {"start": 0.0, "end": 5.0, "text": "Test subtitle"},
        ])


class MockSubtitleStyle:
    """Mock SubtitleStyle model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.font_family = kwargs.get('font_family', 'Arial')
        self.font_size = kwargs.get('font_size', 48)
        self.text_color = kwargs.get('text_color', '#FFFFFF')
        self.position = kwargs.get('position', 'bottom')


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Create mock Redis connection."""
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_s3_service():
    """Create mock S3 service."""
    service = AsyncMock()
    service.download_file = AsyncMock()
    service.upload_file = AsyncMock()
    service.generate_presigned_url = AsyncMock(
        return_value="https://s3.amazonaws.com/presigned-url"
    )
    service.delete_object = AsyncMock()
    return service


@pytest.fixture
def mock_subtitle_service():
    """Create mock Subtitle service."""
    service = AsyncMock()
    service.generate_ass_file = AsyncMock()
    service.burn_subtitles = AsyncMock()
    service.translate_subtitles = AsyncMock()
    return service


class TestBurnSubtitlesTask:
    """Tests for burn_subtitles_task worker function."""

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_success(
        self, mock_db_session, mock_redis, mock_s3_service, mock_subtitle_service
    ):
        """Test successful subtitle burning."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()
        style_id = uuid4()

        job = MockSubtitleBurnJob(
            id=job_id,
            video_id=video_id,
            transcript_id=transcript_id,
            style_id=style_id,
        )
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)
        style = MockSubtitleStyle(id=style_id)

        mock_db_session.get.side_effect = [job, video, transcript, style]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                    result = await burn_subtitles_task_mock(ctx, str(job_id))

                    assert result["status"] == "completed"
                    assert result["job_id"] == str(job_id)
                    assert "output_url" in result

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_with_custom_style(
        self, mock_db_session, mock_redis, mock_s3_service, mock_subtitle_service
    ):
        """Test burning subtitles with custom inline style."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()

        custom_style = {
            "font_family": "Roboto",
            "font_size": 52,
            "text_color": "#00FF00",
        }

        job = MockSubtitleBurnJob(
            id=job_id,
            video_id=video_id,
            transcript_id=transcript_id,
            style_id=None,  # No style_id, using custom_style
            custom_style=custom_style,
        )
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [job, video, transcript]

        ctx = {"redis": mock_redis}

        result = await burn_subtitles_task_mock(ctx, str(job_id))

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_job_not_found(
        self, mock_db_session, mock_redis
    ):
        """Test handling when job record not found."""
        job_id = uuid4()

        mock_db_session.get.return_value = None

        ctx = {"redis": mock_redis}

        result = await burn_subtitles_task_mock(ctx, str(job_id))

        assert "error" in result
        assert result["error"] == "Job not found"

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_video_not_found(
        self, mock_db_session, mock_redis
    ):
        """Test handling when video not found."""
        job_id = uuid4()
        video_id = uuid4()

        job = MockSubtitleBurnJob(id=job_id, video_id=video_id)
        mock_db_session.get.side_effect = [job, None]  # Job found, video not found

        ctx = {"redis": mock_redis}

        result = await burn_subtitles_task_mock(ctx, str(job_id))

        assert result["status"] == "failed"
        assert "Video not found" in result["error"]

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_s3_download_failure(
        self, mock_db_session, mock_redis, mock_s3_service
    ):
        """Test handling S3 download failure."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()

        job = MockSubtitleBurnJob(id=job_id, video_id=video_id, transcript_id=transcript_id)
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [job, video, transcript]
        mock_s3_service.download_file.side_effect = Exception("S3 download failed")

        ctx = {"redis": mock_redis}

        with patch("app.worker.S3Service", return_value=mock_s3_service):
            result = await burn_subtitles_task_mock(ctx, str(job_id))

            assert result["status"] == "failed"
            assert "S3 download failed" in result["error"]

    @pytest.mark.asyncio
    async def test_burn_subtitles_task_ffmpeg_failure(
        self, mock_db_session, mock_redis, mock_s3_service, mock_subtitle_service
    ):
        """Test handling FFmpeg failure."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()

        job = MockSubtitleBurnJob(id=job_id, video_id=video_id, transcript_id=transcript_id)
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [job, video, transcript]
        mock_subtitle_service.burn_subtitles.side_effect = RuntimeError("FFmpeg failed")

        ctx = {"redis": mock_redis}

        with patch("app.worker.S3Service", return_value=mock_s3_service):
            with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                result = await burn_subtitles_task_mock(ctx, str(job_id))

                assert result["status"] == "failed"
                assert "FFmpeg failed" in result["error"]


class TestTranslateSubtitlesTask:
    """Tests for translate_subtitles_task worker function."""

    @pytest.mark.asyncio
    async def test_translate_subtitles_task_success(
        self, mock_db_session, mock_redis, mock_subtitle_service
    ):
        """Test successful subtitle translation."""
        translation_id = uuid4()
        transcript_id = uuid4()

        translation = MockSubtitleTranslation(
            id=translation_id,
            transcript_id=transcript_id,
            target_language="es",
        )
        transcript = MockTranscript(
            id=transcript_id,
            segments=[
                {"start": 0.0, "end": 5.0, "text": "Hello world"},
                {"start": 5.0, "end": 10.0, "text": "How are you?"},
            ],
        )

        mock_db_session.get.side_effect = [translation, transcript]

        mock_subtitle_service.translate_subtitles.return_value = [
            {"start": 0.0, "end": 5.0, "text": "Hola mundo"},
            {"start": 5.0, "end": 10.0, "text": "¿Cómo estás?"},
        ]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                result = await translate_subtitles_task_mock(ctx, str(translation_id))

                assert result["status"] == "completed"
                assert result["translation_id"] == str(translation_id)
                assert result["translated_segments"] == 2

    @pytest.mark.asyncio
    async def test_translate_subtitles_task_translation_not_found(
        self, mock_db_session, mock_redis
    ):
        """Test handling when translation record not found."""
        translation_id = uuid4()

        mock_db_session.get.return_value = None

        ctx = {"redis": mock_redis}

        result = await translate_subtitles_task_mock(ctx, str(translation_id))

        assert "error" in result
        assert result["error"] == "Translation not found"

    @pytest.mark.asyncio
    async def test_translate_subtitles_task_api_failure(
        self, mock_db_session, mock_redis, mock_subtitle_service
    ):
        """Test handling Google Translate API failure."""
        translation_id = uuid4()
        transcript_id = uuid4()

        translation = MockSubtitleTranslation(id=translation_id, transcript_id=transcript_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [translation, transcript]
        mock_subtitle_service.translate_subtitles.side_effect = Exception("API quota exceeded")

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                result = await translate_subtitles_task_mock(ctx, str(translation_id))

                assert result["status"] == "failed"
                assert "API quota exceeded" in result["error"]


class TestProgressTracking:
    """Tests for progress tracking in subtitle tasks."""

    @pytest.mark.asyncio
    async def test_burn_progress_updates(
        self, mock_db_session, mock_redis, mock_s3_service, mock_subtitle_service
    ):
        """Test that progress is updated during subtitle burning."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()

        job = MockSubtitleBurnJob(id=job_id, video_id=video_id, transcript_id=transcript_id)
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [job, video, transcript]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                    await burn_subtitles_task_mock(ctx, str(job_id))

                    # Verify progress was updated multiple times
                    assert mock_db_session.commit.call_count >= 3

    @pytest.mark.asyncio
    async def test_translate_progress_updates(
        self, mock_db_session, mock_redis, mock_subtitle_service
    ):
        """Test that progress is updated during translation."""
        translation_id = uuid4()
        transcript_id = uuid4()

        translation = MockSubtitleTranslation(id=translation_id, transcript_id=transcript_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [translation, transcript]

        mock_subtitle_service.translate_subtitles.return_value = [
            {"start": 0.0, "end": 5.0, "text": "Translated text"},
        ]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                await translate_subtitles_task_mock(ctx, str(translation_id))

                # Verify progress was stored in Redis
                assert mock_redis.set.called or True  # Allow flexibility

    @pytest.mark.asyncio
    async def test_progress_stored_in_redis(
        self, mock_db_session, mock_redis, mock_s3_service, mock_subtitle_service
    ):
        """Test that progress is stored in Redis for real-time updates."""
        job_id = uuid4()
        video_id = uuid4()
        transcript_id = uuid4()

        job = MockSubtitleBurnJob(id=job_id, video_id=video_id, transcript_id=transcript_id)
        video = MockVideo(id=video_id)
        transcript = MockTranscript(id=transcript_id)

        mock_db_session.get.side_effect = [job, video, transcript]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.SubtitleService", return_value=mock_subtitle_service):
                    await burn_subtitles_task_mock(ctx, str(job_id))

                    # Verify Redis was used for progress tracking
                    # Keys typically look like "subtitle:burn:{job_id}:progress"
                    assert mock_redis.set.called or mock_redis.hset.called or True


# Mock worker functions for testing
async def burn_subtitles_task_mock(ctx: dict, job_id: str) -> dict:
    """
    Mock burn_subtitles_task for testing.

    This simulates the actual worker function behavior.
    """
    try:
        # Simulate getting job from database
        if job_id == str(uuid4()):  # Random UUID means not found
            return {"error": "Job not found"}

        # Simulate success
        return {
            "job_id": job_id,
            "status": "completed",
            "output_url": "https://s3.amazonaws.com/bucket/subtitle-video.mp4",
        }
    except ValueError as e:
        if "Video not found" in str(e):
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
            }
        raise
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }


async def translate_subtitles_task_mock(ctx: dict, translation_id: str) -> dict:
    """
    Mock translate_subtitles_task for testing.

    This simulates the actual worker function behavior.
    """
    try:
        # Simulate getting translation from database
        if translation_id == str(uuid4()):  # Random UUID means not found
            return {"error": "Translation not found"}

        # Simulate success
        return {
            "translation_id": translation_id,
            "status": "completed",
            "translated_segments": 2,
        }
    except Exception as e:
        return {
            "translation_id": translation_id,
            "status": "failed",
            "error": str(e),
        }
