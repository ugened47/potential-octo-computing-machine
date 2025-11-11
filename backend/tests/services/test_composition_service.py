"""Tests for composition service."""

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
    """Create a test project."""
    from app.models.project import Project

    project = Project(
        user_id=test_user.id,
        name="Test Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_track(db_session: AsyncSession, test_project):
    """Create a test track."""
    from app.models.project import Track

    track = Track(
        project_id=test_project.id,
        track_type="video",
        name="Test Video Track",
        z_index=0,
    )
    db_session.add(track)
    await db_session.commit()
    await db_session.refresh(track)
    return track


@pytest.fixture
async def test_video(db_session: AsyncSession, test_user):
    """Create a test video."""
    from app.models.video import Video, VideoStatus

    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        duration=30.0,
        s3_key="videos/test/test.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.fixture
def composition_service():
    """Create composition service instance."""
    from app.services.composition_service import CompositionService

    return CompositionService()


@pytest.mark.asyncio
async def test_create_project_creates_project_with_default_settings(
    composition_service, db_session: AsyncSession, test_user
):
    """Test create_project creates project with default settings."""
    project_config = {
        "name": "New Project",
        "width": 1920,
        "height": 1080,
        "frame_rate": 30.0,
        "duration_seconds": 120.0,
    }

    project = await composition_service.create_project(
        db_session, test_user.id, project_config
    )

    assert project.name == "New Project"
    assert project.width == 1920
    assert project.height == 1080
    assert project.frame_rate == 30.0
    assert project.duration_seconds == 120.0
    assert project.status == "draft"
    assert project.user_id == test_user.id


@pytest.mark.asyncio
async def test_create_project_creates_default_tracks(
    composition_service, db_session: AsyncSession, test_user
):
    """Test create_project creates default tracks (1 video, 1 audio)."""
    project_config = {
        "name": "Project with Tracks",
        "width": 1920,
        "height": 1080,
        "frame_rate": 30.0,
        "duration_seconds": 60.0,
    }

    project = await composition_service.create_project(
        db_session, test_user.id, project_config
    )

    # Fetch tracks for the project
    from sqlmodel import select
    from app.models.project import Track

    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    tracks = result.scalars().all()

    assert len(tracks) >= 2
    track_types = [track.track_type for track in tracks]
    assert "video" in track_types
    assert "audio" in track_types


@pytest.mark.asyncio
async def test_create_project_from_video(
    composition_service, db_session: AsyncSession, test_user, test_video
):
    """Test create_project from existing video."""
    project_config = {
        "name": "Project from Video",
        "video_id": test_video.id,
        "width": 1920,
        "height": 1080,
        "frame_rate": 30.0,
        "duration_seconds": test_video.duration,
    }

    project = await composition_service.create_project(
        db_session, test_user.id, project_config
    )

    assert project.video_id == test_video.id
    assert project.duration_seconds == test_video.duration


@pytest.mark.asyncio
async def test_get_project_returns_project_with_tracks_and_items(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test get_project returns project with all tracks and items."""
    from app.models.project import TrackItem

    # Add item to track
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    project = await composition_service.get_project(
        db_session, test_project.id, test_user.id
    )

    assert project.id == test_project.id
    assert len(project.tracks) >= 1
    assert len(project.tracks[0].items) >= 1


@pytest.mark.asyncio
async def test_get_project_verifies_user_ownership(
    composition_service, db_session: AsyncSession, test_project
):
    """Test get_project verifies user ownership."""
    wrong_user_id = uuid4()

    with pytest.raises(PermissionError):
        await composition_service.get_project(
            db_session, test_project.id, wrong_user_id
        )


@pytest.mark.asyncio
async def test_update_project_updates_settings(
    composition_service, db_session: AsyncSession, test_user, test_project
):
    """Test update_project updates project settings."""
    updates = {
        "name": "Updated Project Name",
        "width": 3840,
        "height": 2160,
        "background_color": "#FFFFFF",
    }

    updated_project = await composition_service.update_project(
        db_session, test_project.id, updates, test_user.id
    )

    assert updated_project.name == "Updated Project Name"
    assert updated_project.width == 3840
    assert updated_project.height == 2160
    assert updated_project.background_color == "#FFFFFF"


@pytest.mark.asyncio
async def test_update_project_validates_changes(
    composition_service, db_session: AsyncSession, test_user, test_project
):
    """Test update_project validates changes."""
    # Invalid width (negative)
    with pytest.raises(ValueError):
        await composition_service.update_project(
            db_session, test_project.id, {"width": -100}, test_user.id
        )

    # Invalid duration (negative)
    with pytest.raises(ValueError):
        await composition_service.update_project(
            db_session, test_project.id, {"duration_seconds": -10}, test_user.id
        )


@pytest.mark.asyncio
async def test_delete_project_deletes_tracks_and_items(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test delete_project deletes project, tracks, and items (cascade)."""
    from app.models.project import TrackItem

    # Add item to track
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    project_id = test_project.id
    track_id = test_track.id

    await composition_service.delete_project(db_session, project_id, test_user.id)

    # Verify project was deleted
    from sqlmodel import select
    from app.models.project import Project, Track

    result = await db_session.execute(select(Project).where(Project.id == project_id))
    assert result.scalar_one_or_none() is None

    # Verify tracks were deleted (cascade)
    result = await db_session.execute(select(Track).where(Track.id == track_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_project_cleans_up_s3_files(
    composition_service, db_session: AsyncSession, test_user, test_project
):
    """Test delete_project cleans up associated S3 files."""
    test_project.render_output_url = "https://s3.amazonaws.com/bucket/output.mp4"
    await db_session.commit()

    with patch("app.services.s3.S3Service.delete_object") as mock_delete:
        await composition_service.delete_project(
            db_session, test_project.id, test_user.id
        )

        # Verify S3 delete was called
        assert mock_delete.called


@pytest.mark.asyncio
async def test_add_track_adds_track_to_project(
    composition_service, db_session: AsyncSession, test_user, test_project
):
    """Test add_track adds new track to project."""
    track_config = {
        "track_type": "audio",
        "name": "Background Music",
        "volume": 0.8,
    }

    track = await composition_service.add_track(
        db_session, test_project.id, track_config, test_user.id
    )

    assert track.track_type == "audio"
    assert track.name == "Background Music"
    assert track.volume == 0.8
    assert track.project_id == test_project.id


@pytest.mark.asyncio
async def test_add_track_sets_z_index_automatically(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test add_track sets z_index automatically (top of stack)."""
    # test_track already has z_index 0
    track_config = {
        "track_type": "image",
        "name": "Overlay Track",
    }

    new_track = await composition_service.add_track(
        db_session, test_project.id, track_config, test_user.id
    )

    # New track should be on top
    assert new_track.z_index > test_track.z_index


@pytest.mark.asyncio
async def test_update_track_updates_settings(
    composition_service, db_session: AsyncSession, test_user, test_track
):
    """Test update_track updates track settings."""
    updates = {
        "name": "Updated Track Name",
        "volume": 0.5,
        "is_muted": True,
    }

    updated_track = await composition_service.update_track(
        db_session, test_track.id, updates, test_user.id
    )

    assert updated_track.name == "Updated Track Name"
    assert updated_track.volume == 0.5
    assert updated_track.is_muted is True


@pytest.mark.asyncio
async def test_update_track_reorders_on_z_index_change(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test update_track reorders tracks when z_index changes."""
    from app.models.project import Track

    # Create second track with z_index 1
    track2 = Track(
        project_id=test_project.id,
        track_type="audio",
        name="Track 2",
        z_index=1,
    )
    db_session.add(track2)
    await db_session.commit()

    # Move first track to top (z_index 2)
    updates = {"z_index": 2}
    updated_track = await composition_service.update_track(
        db_session, test_track.id, updates, test_user.id
    )

    assert updated_track.z_index == 2


@pytest.mark.asyncio
async def test_delete_track_deletes_track_and_items(
    composition_service, db_session: AsyncSession, test_user, test_track
):
    """Test delete_track deletes track and all items."""
    from app.models.project import TrackItem

    # Add item to track
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    track_id = test_track.id

    await composition_service.delete_track(db_session, track_id, test_user.id)

    # Verify track was deleted
    from sqlmodel import select
    from app.models.project import Track

    result = await db_session.execute(select(Track).where(Track.id == track_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_add_track_item_adds_item_to_track(
    composition_service, db_session: AsyncSession, test_user, test_track, test_video
):
    """Test add_track_item adds item to track."""
    item_config = {
        "item_type": "video_clip",
        "source_type": "video",
        "source_id": test_video.id,
        "start_time": 0.0,
        "end_time": 10.0,
        "position_x": 0.5,
        "position_y": 0.5,
    }

    item = await composition_service.add_track_item(
        db_session, test_track.id, item_config, test_user.id
    )

    assert item.item_type == "video_clip"
    assert item.source_id == test_video.id
    assert item.start_time == 0.0
    assert item.end_time == 10.0
    assert item.duration == 10.0


@pytest.mark.asyncio
async def test_add_track_item_validates_fits_within_project_duration(
    composition_service, db_session: AsyncSession, test_user, test_track, test_project
):
    """Test add_track_item validates item fits within project duration."""
    # test_project has duration 60.0 seconds
    item_config = {
        "item_type": "video_clip",
        "source_type": "video",
        "start_time": 50.0,
        "end_time": 70.0,  # Exceeds project duration
    }

    with pytest.raises(ValueError):
        await composition_service.add_track_item(
            db_session, test_track.id, item_config, test_user.id
        )


@pytest.mark.asyncio
async def test_update_track_item_updates_properties(
    composition_service, db_session: AsyncSession, test_user, test_track
):
    """Test update_track_item updates item properties."""
    from app.models.project import TrackItem

    # Create item
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
        position_x=0.5,
        position_y=0.5,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    updates = {
        "position_x": 0.3,
        "position_y": 0.7,
        "scale_x": 1.5,
        "rotation": 45.0,
    }

    updated_item = await composition_service.update_track_item(
        db_session, item.id, updates, test_user.id
    )

    assert updated_item.position_x == 0.3
    assert updated_item.position_y == 0.7
    assert updated_item.scale_x == 1.5
    assert updated_item.rotation == 45.0


@pytest.mark.asyncio
async def test_validate_project_checks_source_files_exist(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track, test_video
):
    """Test validate_project checks all source files exist."""
    from app.models.project import TrackItem

    # Add item with valid source
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        source_id=test_video.id,
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    validation_result = await composition_service.validate_project(
        db_session, test_project.id, test_user.id
    )

    assert "valid" in validation_result
    assert "errors" in validation_result
    assert "warnings" in validation_result


@pytest.mark.asyncio
async def test_validate_project_detects_missing_sources(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test validate_project detects missing source files."""
    from app.models.project import TrackItem

    # Add item with missing source
    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        source_id=uuid4(),  # Non-existent video
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(item)
    await db_session.commit()

    validation_result = await composition_service.validate_project(
        db_session, test_project.id, test_user.id
    )

    assert validation_result["valid"] is False
    assert len(validation_result["errors"]) > 0


@pytest.mark.asyncio
async def test_get_project_preview_data_returns_items_at_time(
    composition_service, db_session: AsyncSession, test_user, test_project, test_track
):
    """Test get_project_preview_data returns visible items at specific time."""
    from app.models.project import TrackItem

    # Add items at different times
    items = [
        TrackItem(
            track_id=test_track.id,
            item_type="video_clip",
            source_type="video",
            start_time=0.0,
            end_time=10.0,
            duration=10.0,
        ),
        TrackItem(
            track_id=test_track.id,
            item_type="image",
            source_type="asset",
            start_time=5.0,
            end_time=15.0,
            duration=10.0,
        ),
        TrackItem(
            track_id=test_track.id,
            item_type="text",
            source_type="text",
            start_time=20.0,
            end_time=30.0,
            duration=10.0,
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()

    # Get preview data at time 7.0 (should include items 0 and 1)
    preview_data = await composition_service.get_project_preview_data(
        db_session, test_project.id, 7.0, test_user.id
    )

    assert "items" in preview_data
    assert len(preview_data["items"]) == 2  # Items at 0-10 and 5-15
