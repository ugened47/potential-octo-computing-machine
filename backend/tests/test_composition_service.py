"""Tests for CompositionService."""

import pytest
from sqlmodel import select

from app.models import Project, ProjectStatus, Track, TrackItem, TrackType
from app.services.composition_service import CompositionService


@pytest.mark.asyncio
async def test_create_project(db_session, test_user):
    """Test creating a new project."""
    service = CompositionService(db_session)

    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
        description="A test project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
    )

    assert project is not None
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.width == 1920
    assert project.height == 1080
    assert project.status == ProjectStatus.DRAFT
    assert project.user_id == test_user.id


@pytest.mark.asyncio
async def test_create_project_with_default_tracks(db_session, test_user):
    """Test that creating a project creates default tracks."""
    service = CompositionService(db_session)

    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Verify project has default tracks
    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    tracks = result.scalars().all()

    assert len(tracks) == 2  # 1 video track + 1 audio track
    assert any(t.track_type == TrackType.VIDEO for t in tracks)
    assert any(t.track_type == TrackType.AUDIO for t in tracks)


@pytest.mark.asyncio
async def test_get_project(db_session, test_user):
    """Test getting a project by ID."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Get the project
    retrieved = await service.get_project(project.id, test_user.id)

    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == project.name


@pytest.mark.asyncio
async def test_update_project(db_session, test_user):
    """Test updating a project."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Update the project
    updated = await service.update_project(
        project.id,
        test_user.id,
        {"name": "Updated Project", "width": 3840, "height": 2160},
    )

    assert updated is not None
    assert updated.name == "Updated Project"
    assert updated.width == 3840
    assert updated.height == 2160


@pytest.mark.asyncio
async def test_delete_project(db_session, test_user):
    """Test deleting a project."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    project_id = project.id

    # Delete the project
    deleted = await service.delete_project(project_id, test_user.id)

    assert deleted is True

    # Verify project is deleted
    result = await db_session.execute(select(Project).where(Project.id == project_id))
    found = result.scalar_one_or_none()
    assert found is None


@pytest.mark.asyncio
async def test_add_track(db_session, test_user):
    """Test adding a track to a project."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Add a track
    track = await service.add_track(
        project_id=project.id,
        user_id=test_user.id,
        track_type=TrackType.VIDEO,
        name="Video Track 2",
    )

    assert track is not None
    assert track.name == "Video Track 2"
    assert track.track_type == TrackType.VIDEO
    assert track.project_id == project.id


@pytest.mark.asyncio
async def test_add_track_item(db_session, test_user):
    """Test adding an item to a track."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Get the first track
    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    track = result.scalars().first()

    # Add an item
    item = await service.add_track_item(
        track_id=track.id,
        user_id=test_user.id,
        item_data={
            "item_type": "video_clip",
            "source_type": "video",
            "start_time": 0.0,
            "end_time": 10.0,
        },
    )

    assert item is not None
    assert item.start_time == 0.0
    assert item.end_time == 10.0
    assert item.duration == 10.0
    assert item.track_id == track.id


@pytest.mark.asyncio
async def test_validate_project_valid(db_session, test_user):
    """Test validating a valid project."""
    service = CompositionService(db_session)

    # Create a project with tracks and items
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Get the first track
    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    track = result.scalars().first()

    # Add a valid item
    await service.add_track_item(
        track_id=track.id,
        user_id=test_user.id,
        item_data={
            "item_type": "video_clip",
            "source_type": "video",
            "source_url": "s3://bucket/video.mp4",
            "start_time": 0.0,
            "end_time": 10.0,
        },
    )

    # Validate project
    validation = await service.validate_project(project.id, test_user.id)

    assert validation["valid"] is True
    assert len(validation["errors"]) == 0


@pytest.mark.asyncio
async def test_validate_project_invalid_time_range(db_session, test_user):
    """Test validating a project with invalid item time range."""
    service = CompositionService(db_session)

    # Create a project
    project = await service.create_project(
        user_id=test_user.id,
        name="Test Project",
    )

    # Get the first track
    result = await db_session.execute(
        select(Track).where(Track.project_id == project.id)
    )
    track = result.scalars().first()

    # Add an invalid item (start_time >= end_time)
    item = await service.add_track_item(
        track_id=track.id,
        user_id=test_user.id,
        item_data={
            "item_type": "video_clip",
            "source_type": "video",
            "source_url": "s3://bucket/video.mp4",
            "start_time": 10.0,
            "end_time": 10.0,
        },
    )

    # Manually set invalid time (since validation would normally prevent this)
    item.start_time = 10.0
    item.end_time = 5.0
    await db_session.commit()

    # Validate project
    validation = await service.validate_project(project.id, test_user.id)

    assert validation["valid"] is False
    assert len(validation["errors"]) > 0
    assert any("invalid time range" in error.lower() for error in validation["errors"])
