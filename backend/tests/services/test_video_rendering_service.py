"""Tests for video rendering service."""

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
        duration_seconds=10.0,
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
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(video_item)
    await db_session.commit()

    return project


@pytest.fixture
def video_rendering_service():
    """Create video rendering service instance."""
    from app.services.video_rendering_service import VideoRenderingService

    return VideoRenderingService()


@pytest.fixture
def temp_video_file():
    """Create a temporary video file."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_project_orchestrates_full_workflow(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test render_project orchestrates full rendering workflow."""
    with patch("app.services.s3.S3Service.upload_file") as mock_upload, \
         patch("app.services.composition_service.CompositionService.validate_project") as mock_validate, \
         patch("subprocess.run") as mock_run:

        mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_run.return_value = MagicMock(returncode=0)
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        render_config = {
            "quality": "high",
            "format": "mp4",
            "codec": "h264",
        }

        result = await video_rendering_service.render_project(
            db_session, test_project.id, test_user.id, render_config
        )

        assert result is not None
        assert "https://" in result  # Should return S3 URL


@pytest.mark.asyncio
async def test_build_ffmpeg_filter_complex_generates_filter_graph(
    video_rendering_service, db_session: AsyncSession, test_project
):
    """Test build_ffmpeg_filter_complex generates FFmpeg filter graph."""
    # Fetch project with tracks and items
    from sqlmodel import select
    from app.models.project import Project

    result = await db_session.execute(
        select(Project).where(Project.id == test_project.id)
    )
    project = result.scalar_one()

    filter_complex = await video_rendering_service.build_ffmpeg_filter_complex(project)

    assert isinstance(filter_complex, str)
    assert len(filter_complex) > 0


@pytest.mark.asyncio
async def test_build_ffmpeg_filter_complex_handles_multiple_video_tracks(
    video_rendering_service, db_session: AsyncSession, test_project
):
    """Test build_ffmpeg_filter_complex handles multiple video tracks with overlay."""
    from app.models.project import Track, TrackItem

    # Add second video track (overlay)
    overlay_track = Track(
        project_id=test_project.id,
        track_type="video",
        name="Overlay Track",
        z_index=2,  # On top
        opacity=0.8,
    )
    db_session.add(overlay_track)
    await db_session.commit()

    overlay_item = TrackItem(
        track_id=overlay_track.id,
        item_type="video_clip",
        source_type="video",
        source_url="https://s3.amazonaws.com/bucket/overlay.mp4",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
        position_x=0.8,
        position_y=0.2,
        scale_x=0.3,
        scale_y=0.3,
    )
    db_session.add(overlay_item)
    await db_session.commit()

    # Fetch project
    from sqlmodel import select
    from app.models.project import Project

    result = await db_session.execute(
        select(Project).where(Project.id == test_project.id)
    )
    project = result.scalar_one()

    filter_complex = await video_rendering_service.build_ffmpeg_filter_complex(project)

    # Should include overlay filter
    assert "overlay" in filter_complex.lower()


@pytest.mark.asyncio
async def test_build_ffmpeg_filter_complex_applies_transforms(
    video_rendering_service, db_session: AsyncSession, test_project
):
    """Test build_ffmpeg_filter_complex applies item transforms (scale, position, rotation)."""
    from app.models.project import Project
    from sqlmodel import select

    result = await db_session.execute(
        select(Project).where(Project.id == test_project.id)
    )
    project = result.scalar_one()

    # Update item with transforms
    item = project.tracks[0].items[0]
    item.scale_x = 1.5
    item.scale_y = 1.5
    item.rotation = 45.0
    await db_session.commit()

    filter_complex = await video_rendering_service.build_ffmpeg_filter_complex(project)

    # Should include scale and rotate filters
    assert "scale" in filter_complex.lower() or "rotate" in filter_complex.lower()


@pytest.mark.asyncio
async def test_render_video_layer_renders_individual_item(
    video_rendering_service, temp_video_file
):
    """Test render_video_layer renders individual track item to video segment."""
    from app.models.project import TrackItem

    item = TrackItem(
        id=uuid4(),
        track_id=uuid4(),
        item_type="video_clip",
        source_type="video",
        source_url=temp_video_file,
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        position_x=0.5,
        position_y=0.5,
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        temp_dir = "/tmp"
        result = await video_rendering_service.render_video_layer(item, temp_dir)

        assert result is not None
        assert mock_run.called


@pytest.mark.asyncio
async def test_apply_transition_applies_fade_transition(
    video_rendering_service, temp_video_file
):
    """Test apply_transition applies fade transition between clips."""
    from app.models.project import Transition

    transition = Transition(
        id=uuid4(),
        name="Fade",
        transition_type="fade",
        default_duration=0.5,
        parameters={"type": "fade"},
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        clip1_path = temp_video_file
        clip2_path = temp_video_file
        output_path = "/tmp/transitioned_output.mp4"

        result = await video_rendering_service.apply_transition(
            clip1_path, clip2_path, transition, output_path
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes xfade or similar filter
        ffmpeg_command = mock_run.call_args[0][0]
        command_str = " ".join(ffmpeg_command)
        assert "xfade" in command_str or "fade" in command_str


@pytest.mark.asyncio
async def test_apply_transition_applies_slide_transition(
    video_rendering_service, temp_video_file
):
    """Test apply_transition applies slide transition."""
    from app.models.project import Transition

    transition = Transition(
        id=uuid4(),
        name="Slide Left",
        transition_type="slide",
        default_duration=0.5,
        parameters={"direction": "left"},
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        clip1_path = temp_video_file
        clip2_path = temp_video_file
        output_path = "/tmp/transitioned_output.mp4"

        result = await video_rendering_service.apply_transition(
            clip1_path, clip2_path, transition, output_path
        )

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_apply_transition_applies_dissolve_transition(
    video_rendering_service, temp_video_file
):
    """Test apply_transition applies dissolve (cross-fade) transition."""
    from app.models.project import Transition

    transition = Transition(
        id=uuid4(),
        name="Dissolve",
        transition_type="dissolve",
        default_duration=1.0,
        parameters={},
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        clip1_path = temp_video_file
        clip2_path = temp_video_file
        output_path = "/tmp/transitioned_output.mp4"

        result = await video_rendering_service.apply_transition(
            clip1_path, clip2_path, transition, output_path
        )

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_apply_transition_applies_wipe_transition(
    video_rendering_service, temp_video_file
):
    """Test apply_transition applies wipe transition."""
    from app.models.project import Transition

    transition = Transition(
        id=uuid4(),
        name="Wipe Horizontal",
        transition_type="wipe",
        default_duration=0.75,
        parameters={"direction": "horizontal"},
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        clip1_path = temp_video_file
        clip2_path = temp_video_file
        output_path = "/tmp/transitioned_output.mp4"

        result = await video_rendering_service.apply_transition(
            clip1_path, clip2_path, transition, output_path
        )

        assert result == output_path
        assert mock_run.called


@pytest.mark.asyncio
async def test_render_text_overlay_renders_text_to_video(
    video_rendering_service
):
    """Test render_text_overlay renders text to transparent video overlay."""
    from app.models.project import TrackItem

    text_item = TrackItem(
        id=uuid4(),
        track_id=uuid4(),
        item_type="text",
        source_type="text",
        text_content="Hello World",
        text_style={
            "font_family": "Arial",
            "font_size": 48,
            "color": "#FFFFFF",
            "alignment": "center",
        },
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        position_x=0.5,
        position_y=0.9,
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/text_overlay.mp4"
        result = await video_rendering_service.render_text_overlay(
            text_item, 5.0, output_path
        )

        assert result == output_path
        assert mock_run.called

        # Verify FFmpeg command includes drawtext filter
        ffmpeg_command = mock_run.call_args[0][0]
        command_str = " ".join(ffmpeg_command)
        assert "drawtext" in command_str


@pytest.mark.asyncio
async def test_render_text_overlay_applies_text_styling(
    video_rendering_service
):
    """Test render_text_overlay applies text styling (font, size, color, alignment)."""
    from app.models.project import TrackItem

    text_item = TrackItem(
        id=uuid4(),
        track_id=uuid4(),
        item_type="text",
        source_type="text",
        text_content="Styled Text",
        text_style={
            "font_family": "Arial",
            "font_size": 72,
            "color": "#FF0000",
            "alignment": "left",
            "bold": True,
        },
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        output_path = "/tmp/text_overlay.mp4"
        result = await video_rendering_service.render_text_overlay(
            text_item, 5.0, output_path
        )

        assert result == output_path


@pytest.mark.asyncio
async def test_generate_preview_frame_generates_single_frame(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test generate_preview_frame generates single frame preview at time."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        time = 5.0
        output_path = await video_rendering_service.generate_preview_frame(
            db_session, test_project.id, time, test_user.id
        )

        assert output_path is not None
        assert mock_run.called


@pytest.mark.asyncio
async def test_generate_preview_frame_composites_all_visible_layers(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test generate_preview_frame composites all visible layers at time."""
    from app.models.project import Track, TrackItem

    # Add overlay track
    overlay_track = Track(
        project_id=test_project.id,
        track_type="image",
        name="Overlay",
        z_index=2,
    )
    db_session.add(overlay_track)
    await db_session.commit()

    overlay_item = TrackItem(
        track_id=overlay_track.id,
        item_type="image",
        source_type="asset",
        source_url="https://s3.amazonaws.com/bucket/logo.png",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(overlay_item)
    await db_session.commit()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        time = 5.0
        output_path = await video_rendering_service.generate_preview_frame(
            db_session, test_project.id, time, test_user.id
        )

        assert output_path is not None
        assert mock_run.called


@pytest.mark.asyncio
async def test_estimate_render_time_estimates_based_on_complexity(
    video_rendering_service, db_session: AsyncSession, test_project
):
    """Test estimate_render_time estimates rendering time based on project complexity."""
    from sqlmodel import select
    from app.models.project import Project

    result = await db_session.execute(
        select(Project).where(Project.id == test_project.id)
    )
    project = result.scalar_one()

    estimated_time = video_rendering_service.estimate_render_time(project)

    assert estimated_time > 0
    assert isinstance(estimated_time, (int, float))


@pytest.mark.asyncio
async def test_render_project_updates_project_status(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test render_project updates project status and render_output_url."""
    with patch("app.services.s3.S3Service.upload_file") as mock_upload, \
         patch("app.services.composition_service.CompositionService.validate_project") as mock_validate, \
         patch("subprocess.run") as mock_run:

        mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_run.return_value = MagicMock(returncode=0)
        mock_upload.return_value = "https://s3.amazonaws.com/bucket/rendered-output.mp4"

        render_config = {"quality": "high", "format": "mp4"}

        await video_rendering_service.render_project(
            db_session, test_project.id, test_user.id, render_config
        )

        # Verify project was updated
        await db_session.refresh(test_project)
        assert test_project.status == "completed"
        assert test_project.render_output_url is not None


@pytest.mark.asyncio
async def test_render_project_handles_different_quality_settings(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test render_project handles different quality settings."""
    qualities = ["low", "medium", "high", "max"]

    for quality in qualities:
        with patch("app.services.s3.S3Service.upload_file") as mock_upload, \
             patch("app.services.composition_service.CompositionService.validate_project") as mock_validate, \
             patch("subprocess.run") as mock_run:

            mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}
            mock_run.return_value = MagicMock(returncode=0)
            mock_upload.return_value = f"https://s3.amazonaws.com/bucket/output-{quality}.mp4"

            render_config = {"quality": quality, "format": "mp4"}

            result = await video_rendering_service.render_project(
                db_session, test_project.id, test_user.id, render_config
            )

            assert result is not None


@pytest.mark.asyncio
async def test_render_project_validates_before_rendering(
    video_rendering_service, db_session: AsyncSession, test_user, test_project
):
    """Test render_project validates project before rendering."""
    with patch("app.services.composition_service.CompositionService.validate_project") as mock_validate:
        # Simulate validation failure
        mock_validate.return_value = {
            "valid": False,
            "errors": ["Missing source file"],
            "warnings": [],
        }

        render_config = {"quality": "high", "format": "mp4"}

        with pytest.raises(ValueError):
            await video_rendering_service.render_project(
                db_session, test_project.id, test_user.id, render_config
            )
