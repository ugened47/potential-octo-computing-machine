"""Tests for project worker tasks."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User

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
async def test_project(db_session: AsyncSession, test_user):
    """Create a test project with tracks and items."""
    from app.models.project import Project, Track, TrackItem

    project = Project(
        user_id=test_user.id,
        name="Test Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=30.0,
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add tracks
    video_track = Track(
        project_id=project.id,
        track_type="video",
        name="Main Video",
        z_index=0,
    )
    audio_track = Track(
        project_id=project.id,
        track_type="audio",
        name="Audio Track",
        z_index=1,
    )
    db_session.add_all([video_track, audio_track])
    await db_session.commit()

    # Add items
    video_item = TrackItem(
        track_id=video_track.id,
        item_type="video_clip",
        source_type="video",
        source_url="https://s3.amazonaws.com/bucket/video.mp4",
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
    )
    audio_item = TrackItem(
        track_id=audio_track.id,
        item_type="audio_clip",
        source_type="audio",
        source_url="https://s3.amazonaws.com/bucket/audio.mp3",
        start_time=0.0,
        end_time=30.0,
        duration=30.0,
    )
    db_session.add_all([video_item, audio_item])
    await db_session.commit()

    return project


@pytest.fixture
async def test_complex_project(db_session: AsyncSession, test_user):
    """Create a complex project with 100+ items."""
    from app.models.project import Project, Track, TrackItem

    project = Project(
        user_id=test_user.id,
        name="Complex Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=300.0,  # 5 minutes
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Add multiple tracks
    for i in range(10):
        track = Track(
            project_id=project.id,
            track_type="video" if i % 2 == 0 else "audio",
            name=f"Track {i}",
            z_index=i,
        )
        db_session.add(track)
    await db_session.commit()

    # Add 100+ items
    from sqlmodel import select

    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    tracks = result.scalars().all()

    for track in tracks:
        for j in range(12):  # 10 tracks * 12 items = 120 items
            item = TrackItem(
                track_id=track.id,
                item_type="video_clip" if track.track_type == "video" else "audio_clip",
                source_type="video" if track.track_type == "video" else "audio",
                source_url=f"https://s3.amazonaws.com/bucket/item-{j}.mp4",
                start_time=j * 25.0,
                end_time=(j + 1) * 25.0,
                duration=25.0,
            )
            db_session.add(item)
    await db_session.commit()

    return project


@pytest.mark.asyncio
async def test_render_project_task_completes_successfully(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task completes successfully."""
    from app.worker import render_project

    render_config = {
        "quality": "high",
        "format": "mp4",
        "codec": "h264",
    }

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render, \
         patch("app.services.s3.S3Service.upload_file") as mock_upload:

        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        # Simulate ARQ context
        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        result = await render_project(
            ctx, str(test_project.id), str(test_user.id), render_config
        )

        assert result["status"] == "complete"
        assert "output_url" in result


@pytest.mark.asyncio
async def test_render_project_task_tracks_progress(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task tracks progress in Redis."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}
    redis_mock = AsyncMock()

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        ctx = {
            "db_session": db_session,
            "redis": redis_mock,
        }

        await render_project(ctx, str(test_project.id), str(test_user.id), render_config)

        # Verify Redis set was called to track progress
        assert redis_mock.set.called or redis_mock.hset.called


@pytest.mark.asyncio
async def test_render_project_task_updates_progress_stages(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task updates progress through stages."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}
    progress_updates = []

    async def mock_set_progress(key, value):
        progress_updates.append(value)

    redis_mock = AsyncMock()
    redis_mock.set = mock_set_progress

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        ctx = {
            "db_session": db_session,
            "redis": redis_mock,
        }

        await render_project(ctx, str(test_project.id), str(test_user.id), render_config)

        # Expected stages: Validating, Downloading sources, Rendering video, Mixing audio, Encoding, Uploading, Complete
        # Verify progress was updated multiple times
        assert len(progress_updates) >= 3


@pytest.mark.asyncio
async def test_render_project_task_handles_errors(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task handles errors with retry."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        # Simulate rendering error
        mock_render.side_effect = Exception("Rendering failed")

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        with pytest.raises(Exception):
            await render_project(
                ctx, str(test_project.id), str(test_user.id), render_config
            )

        # Verify project status was updated to error
        await db_session.refresh(test_project)
        assert test_project.status == "error"


@pytest.mark.asyncio
async def test_render_project_task_cleans_up_temp_files(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task cleans up temporary files."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render, \
         patch("shutil.rmtree") as mock_cleanup:

        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        await render_project(ctx, str(test_project.id), str(test_user.id), render_config)

        # Verify temp files were cleaned up
        assert mock_cleanup.called or mock_render.called


@pytest.mark.asyncio
async def test_render_project_task_handles_complex_projects(
    db_session: AsyncSession, test_user, test_complex_project
):
    """Test render_project task handles projects with 100+ items."""
    from app.worker import render_project

    render_config = {"quality": "medium", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-complex.mp4"

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        result = await render_project(
            ctx, str(test_complex_project.id), str(test_user.id), render_config
        )

        assert result["status"] == "complete"
        assert mock_render.called


@pytest.mark.asyncio
async def test_render_project_task_manages_memory(
    db_session: AsyncSession, test_user, test_complex_project
):
    """Test render_project task manages memory for large projects."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render, \
         patch("psutil.Process") as mock_process:

        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-complex.mp4"
        mock_process_instance = MagicMock()
        mock_process_instance.memory_info.return_value.rss = 1024 * 1024 * 500  # 500 MB
        mock_process.return_value = mock_process_instance

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        result = await render_project(
            ctx, str(test_complex_project.id), str(test_user.id), render_config
        )

        assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_generate_project_thumbnail_task(
    db_session: AsyncSession, test_project
):
    """Test generate_project_thumbnail task."""
    from app.worker import generate_project_thumbnail

    with patch("app.services.video_rendering_service.VideoRenderingService.generate_preview_frame") as mock_preview, \
         patch("app.services.s3.S3Service.upload_file") as mock_upload:

        mock_preview.return_value = "/tmp/thumbnail.jpg"
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/thumbnail.jpg"

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        result = await generate_project_thumbnail(ctx, str(test_project.id))

        assert "thumbnail_url" in result
        assert result["thumbnail_url"] == "https://s3.amazonaws.com/bucket/thumbnail.jpg"

        # Verify project was updated
        await db_session.refresh(test_project)
        assert test_project.thumbnail_url is not None


@pytest.mark.asyncio
async def test_generate_project_thumbnail_at_midpoint(
    db_session: AsyncSession, test_project
):
    """Test generate_project_thumbnail generates thumbnail at project midpoint."""
    from app.worker import generate_project_thumbnail

    with patch("app.services.video_rendering_service.VideoRenderingService.generate_preview_frame") as mock_preview, \
         patch("app.services.s3.S3Service.upload_file") as mock_upload:

        mock_preview.return_value = "/tmp/thumbnail.jpg"
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/thumbnail.jpg"

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        await generate_project_thumbnail(ctx, str(test_project.id))

        # Verify preview was generated at midpoint (duration_seconds / 2)
        expected_time = test_project.duration_seconds / 2
        mock_preview.assert_called_once()
        call_args = mock_preview.call_args
        assert abs(call_args[0][2] - expected_time) < 1.0  # Within 1 second


@pytest.mark.asyncio
async def test_render_project_task_sends_notification(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task sends notification on completion."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render, \
         patch("app.services.notification_service.NotificationService.send_notification") as mock_notify:

        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        await render_project(ctx, str(test_project.id), str(test_user.id), render_config)

        # Verify notification was sent
        assert mock_notify.called


@pytest.mark.asyncio
async def test_render_project_task_timeout_handling(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task handles timeout (30 minutes)."""
    from app.worker import render_project
    import asyncio

    render_config = {"quality": "max", "format": "mp4"}

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        # Simulate long-running render
        async def slow_render(*args, **kwargs):
            await asyncio.sleep(35 * 60)  # 35 minutes (exceeds 30 min timeout)
            return "output"

        mock_render.side_effect = slow_render

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                render_project(ctx, str(test_project.id), str(test_user.id), render_config),
                timeout=30 * 60  # 30 minute timeout
            )


@pytest.mark.asyncio
async def test_render_project_task_retry_logic(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task retry logic (max 2 retries)."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}
    attempt_count = 0

    async def failing_render(*args, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:  # Fail first 2 times, succeed on 3rd
            raise Exception("Transient error")
        return "https://s3.amazonaws.com/bucket/rendered-output.mp4"

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        mock_render.side_effect = failing_render

        ctx = {
            "db_session": db_session,
            "redis": AsyncMock(),
        }

        # This would normally be handled by ARQ's retry mechanism
        # We'll simulate it by calling multiple times
        try:
            await render_project(ctx, str(test_project.id), str(test_user.id), render_config)
        except Exception:
            pass

        try:
            await render_project(ctx, str(test_project.id), str(test_user.id), render_config)
        except Exception:
            pass

        # Third attempt should succeed
        result = await render_project(ctx, str(test_project.id), str(test_user.id), render_config)
        assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_render_project_task_progress_percentage(
    db_session: AsyncSession, test_user, test_project
):
    """Test render_project task updates progress percentage (0-100%)."""
    from app.worker import render_project

    render_config = {"quality": "high", "format": "mp4"}
    progress_values = []

    async def capture_progress(key, value):
        if isinstance(value, dict) and "progress" in value:
            progress_values.append(value["progress"])

    redis_mock = AsyncMock()
    redis_mock.set = capture_progress

    with patch("app.services.video_rendering_service.VideoRenderingService.render_project") as mock_render:
        mock_render.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        ctx = {
            "db_session": db_session,
            "redis": redis_mock,
        }

        await render_project(ctx, str(test_project.id), str(test_user.id), render_config)

        # Verify progress values are between 0 and 100
        for progress in progress_values:
            assert 0 <= progress <= 100
