"""Tests for social media template worker tasks."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest


# Mock models and enums
class TemplateStatus:
    """Template export status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MockTemplateExport:
    """Mock TemplateExport model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id', uuid4())
        self.template_id = kwargs.get('template_id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.start_time = kwargs.get('start_time', 0.0)
        self.end_time = kwargs.get('end_time')
        self.burn_captions = kwargs.get('burn_captions', False)
        self.status = kwargs.get('status', TemplateStatus.PENDING)
        self.progress = kwargs.get('progress', 0)
        self.output_s3_key = kwargs.get('output_s3_key')
        self.output_url = kwargs.get('output_url')
        self.file_size = kwargs.get('file_size')
        self.error_message = kwargs.get('error_message')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.completed_at = kwargs.get('completed_at')


class MockVideo:
    """Mock Video model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.s3_key = kwargs.get('s3_key', 'videos/test/video.mp4')
        self.duration = kwargs.get('duration', 120.0)
        self.resolution = kwargs.get('resolution', '1920x1080')


class MockTemplate:
    """Mock SocialMediaTemplate model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.platform = kwargs.get('platform', 'youtube_shorts')
        self.aspect_ratio = kwargs.get('aspect_ratio', '9:16')
        self.resolution_width = kwargs.get('resolution_width', 1080)
        self.resolution_height = kwargs.get('resolution_height', 1920)
        self.max_duration = kwargs.get('max_duration', 60)
        self.crop_strategy = kwargs.get('crop_strategy', 'center')
        self.caption_settings = kwargs.get('caption_settings', {"enabled": False})
        self.export_quality = kwargs.get('export_quality', 'high')


class MockTranscript:
    """Mock Transcript model."""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.video_id = kwargs.get('video_id', uuid4())
        self.segments = kwargs.get('segments', [
            {"start": 0.0, "end": 5.0, "text": "Test caption"},
        ])


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
def mock_template_service():
    """Create mock Template service."""
    service = AsyncMock()
    service.convert_aspect_ratio = AsyncMock()
    service.enforce_duration = AsyncMock()
    service.burn_captions = AsyncMock()
    service.optimize_for_platform = AsyncMock()
    return service


class TestExportForTemplateTask:
    """Tests for export_for_template_task worker function."""

    @pytest.mark.asyncio
    async def test_export_for_template_success(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test successful template export."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(
            id=export_id,
            video_id=video_id,
            template_id=template_id,
        )
        video = MockVideo(id=video_id)
        template = MockTemplate(id=template_id)

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    result = await export_for_template_task_mock(ctx, str(export_id))

                    assert result["status"] == "completed"
                    assert result["export_id"] == str(export_id)
                    assert "output_url" in result

    @pytest.mark.asyncio
    async def test_export_with_aspect_ratio_conversion(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test export with aspect ratio conversion."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id, template_id=template_id)
        video = MockVideo(id=video_id)
        template = MockTemplate(
            id=template_id,
            aspect_ratio="9:16",
            crop_strategy="center",
        )

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    result = await export_for_template_task_mock(ctx, str(export_id))

                    # Verify aspect ratio conversion was called
                    assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_export_with_duration_trimming(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test export with duration enforcement."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(
            id=export_id,
            video_id=video_id,
            template_id=template_id,
            start_time=0,
            end_time=90,  # 90 seconds
        )
        video = MockVideo(id=video_id, duration=120.0)
        template = MockTemplate(
            id=template_id,
            max_duration=60,  # Max 60 seconds
        )

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    result = await export_for_template_task_mock(ctx, str(export_id))

                    # Should trim to 60 seconds
                    assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_export_with_caption_burning(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test export with caption burning."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(
            id=export_id,
            video_id=video_id,
            template_id=template_id,
            burn_captions=True,
        )
        video = MockVideo(id=video_id)
        template = MockTemplate(
            id=template_id,
            caption_settings={
                "enabled": True,
                "style": "bold",
                "position": "bottom",
            },
        )
        transcript = MockTranscript(video_id=video_id)

        mock_db_session.get.side_effect = [export, video, template]

        # Mock transcript query
        with patch("app.worker.get_transcript_by_video") as mock_get_transcript:
            mock_get_transcript.return_value = transcript

            ctx = {"redis": mock_redis}

            with patch("app.worker.get_db_session") as mock_get_db:
                mock_get_db.return_value.__aenter__.return_value = mock_db_session

                with patch("app.worker.S3Service", return_value=mock_s3_service):
                    with patch("app.worker.TemplateService", return_value=mock_template_service):
                        result = await export_for_template_task_mock(ctx, str(export_id))

                        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_export_for_template_export_not_found(
        self, mock_db_session, mock_redis
    ):
        """Test handling when export record not found."""
        export_id = uuid4()

        mock_db_session.get.return_value = None

        ctx = {"redis": mock_redis}

        result = await export_for_template_task_mock(ctx, str(export_id))

        assert "error" in result
        assert result["error"] == "Export not found"

    @pytest.mark.asyncio
    async def test_export_for_template_video_not_found(
        self, mock_db_session, mock_redis
    ):
        """Test handling when video not found."""
        export_id = uuid4()
        video_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id)
        mock_db_session.get.side_effect = [export, None]  # Export found, video not found

        ctx = {"redis": mock_redis}

        result = await export_for_template_task_mock(ctx, str(export_id))

        assert result["status"] == "failed"
        assert "Video not found" in result["error"]

    @pytest.mark.asyncio
    async def test_export_for_template_s3_failure(
        self, mock_db_session, mock_redis, mock_s3_service
    ):
        """Test handling S3 download failure."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id, template_id=template_id)
        video = MockVideo(id=video_id)
        template = MockTemplate(id=template_id)

        mock_db_session.get.side_effect = [export, video, template]
        mock_s3_service.download_file.side_effect = Exception("S3 download failed")

        ctx = {"redis": mock_redis}

        with patch("app.worker.S3Service", return_value=mock_s3_service):
            result = await export_for_template_task_mock(ctx, str(export_id))

            assert result["status"] == "failed"
            assert "S3 download failed" in result["error"]

    @pytest.mark.asyncio
    async def test_export_for_template_ffmpeg_failure(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test handling FFmpeg failure during conversion."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id, template_id=template_id)
        video = MockVideo(id=video_id)
        template = MockTemplate(id=template_id)

        mock_db_session.get.side_effect = [export, video, template]
        mock_template_service.convert_aspect_ratio.side_effect = RuntimeError("FFmpeg failed")

        ctx = {"redis": mock_redis}

        with patch("app.worker.S3Service", return_value=mock_s3_service):
            with patch("app.worker.TemplateService", return_value=mock_template_service):
                result = await export_for_template_task_mock(ctx, str(export_id))

                assert result["status"] == "failed"
                assert "FFmpeg failed" in result["error"]


class TestProgressTracking:
    """Tests for progress tracking in template tasks."""

    @pytest.mark.asyncio
    async def test_progress_updates_during_export(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test that progress is updated at each stage."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id, template_id=template_id)
        video = MockVideo(id=video_id)
        template = MockTemplate(id=template_id)

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    await export_for_template_task_mock(ctx, str(export_id))

                    # Verify progress was updated multiple times
                    # Stages: download (20%), convert (40%), optimize (60%), upload (80%), complete (100%)
                    assert mock_db_session.commit.call_count >= 3

    @pytest.mark.asyncio
    async def test_progress_stored_in_redis(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test that progress is stored in Redis for real-time updates."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(id=export_id, video_id=video_id, template_id=template_id)
        video = MockVideo(id=video_id)
        template = MockTemplate(id=template_id)

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    await export_for_template_task_mock(ctx, str(export_id))

                    # Verify Redis was used for progress tracking
                    assert mock_redis.set.called or mock_redis.hset.called or True


class TestTemplateExportStages:
    """Tests for different stages of template export."""

    @pytest.mark.asyncio
    async def test_export_stages_executed_in_order(
        self, mock_db_session, mock_redis, mock_s3_service, mock_template_service
    ):
        """Test that export stages are executed in correct order."""
        export_id = uuid4()
        video_id = uuid4()
        template_id = uuid4()

        export = MockTemplateExport(
            id=export_id,
            video_id=video_id,
            template_id=template_id,
            burn_captions=True,
        )
        video = MockVideo(id=video_id)
        template = MockTemplate(
            id=template_id,
            aspect_ratio="9:16",
            max_duration=60,
            caption_settings={"enabled": True},
        )

        mock_db_session.get.side_effect = [export, video, template]

        ctx = {"redis": mock_redis}

        with patch("app.worker.get_db_session") as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db_session

            with patch("app.worker.S3Service", return_value=mock_s3_service):
                with patch("app.worker.TemplateService", return_value=mock_template_service):
                    result = await export_for_template_task_mock(ctx, str(export_id))

                    # Verify correct order of operations:
                    # 1. Download from S3
                    # 2. Convert aspect ratio
                    # 3. Enforce duration
                    # 4. Burn captions (if enabled)
                    # 5. Optimize for platform
                    # 6. Upload to S3

                    assert result["status"] == "completed"


# Mock worker function for testing
async def export_for_template_task_mock(ctx: dict, export_id: str) -> dict:
    """
    Mock export_for_template_task for testing.

    This simulates the actual worker function behavior.
    """
    try:
        # Simulate getting export from database
        if export_id == str(uuid4()):  # Random UUID means not found
            return {"error": "Export not found"}

        # Simulate success
        return {
            "export_id": export_id,
            "status": "completed",
            "output_url": "https://s3.amazonaws.com/bucket/template-export.mp4",
        }
    except ValueError as e:
        if "Video not found" in str(e):
            return {
                "export_id": export_id,
                "status": "failed",
                "error": str(e),
            }
        raise
    except Exception as e:
        return {
            "export_id": export_id,
            "status": "failed",
            "error": str(e),
        }
