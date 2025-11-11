"""Tests for track API endpoints."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create a test client with database session override."""
    from app.api.deps import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
async def other_user(db_session: AsyncSession):
    """Create another test user for authorization tests."""
    from app.models.user import User

    user = User(
        email="other@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


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
        volume=1.0,
        opacity=1.0,
    )
    db_session.add(track)
    await db_session.commit()
    await db_session.refresh(track)
    return track


@pytest.mark.asyncio
async def test_post_tracks_creates_track(
    client: TestClient, test_user, auth_headers: dict, test_project, db_session: AsyncSession
):
    """Test POST /api/projects/{project_id}/tracks creates new track."""
    response = client.post(
        f"/api/projects/{test_project.id}/tracks",
        json={
            "track_type": "audio",
            "name": "Background Music",
            "volume": 0.8,
            "opacity": 1.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["track_type"] == "audio"
    assert data["name"] == "Background Music"
    assert data["volume"] == 0.8
    assert data["project_id"] == str(test_project.id)
    assert "id" in data
    assert "z_index" in data


@pytest.mark.asyncio
async def test_post_tracks_sets_z_index_automatically(
    client: TestClient, test_user, auth_headers: dict, test_project, db_session: AsyncSession
):
    """Test POST /api/projects/{project_id}/tracks sets z_index automatically."""
    from app.models.project import Track

    # Create existing track with z_index 0
    existing_track = Track(
        project_id=test_project.id,
        track_type="video",
        name="Existing Track",
        z_index=0,
    )
    db_session.add(existing_track)
    await db_session.commit()

    # Create new track - should get z_index 1
    response = client.post(
        f"/api/projects/{test_project.id}/tracks",
        json={
            "track_type": "audio",
            "name": "New Track",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["z_index"] == 1  # Should be on top


@pytest.mark.asyncio
async def test_post_tracks_validation_errors(
    client: TestClient, auth_headers: dict, test_project
):
    """Test POST /api/projects/{project_id}/tracks with validation errors."""
    # Missing track_type
    response = client.post(
        f"/api/projects/{test_project.id}/tracks",
        json={"name": "Missing Type"},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid track_type
    response = client.post(
        f"/api/projects/{test_project.id}/tracks",
        json={
            "track_type": "invalid_type",
            "name": "Invalid Track",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_tracks_lists_project_tracks(
    client: TestClient, test_user, auth_headers: dict, test_project, db_session: AsyncSession
):
    """Test GET /api/projects/{project_id}/tracks lists all tracks."""
    from app.models.project import Track

    # Create multiple tracks
    for i in range(3):
        track = Track(
            project_id=test_project.id,
            track_type="video" if i % 2 == 0 else "audio",
            name=f"Track {i}",
            z_index=i,
        )
        db_session.add(track)
    await db_session.commit()

    response = client.get(f"/api/projects/{test_project.id}/tracks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_track_returns_track_details(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test GET /api/tracks/{id} returns track details with items."""
    response = client.get(f"/api/tracks/{test_track.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_track.id)
    assert data["name"] == "Test Video Track"
    assert data["track_type"] == "video"
    assert "items" in data


@pytest.mark.asyncio
async def test_get_track_not_found(client: TestClient, auth_headers: dict):
    """Test GET /api/tracks/{id} returns 404 for non-existent track."""
    fake_id = uuid4()
    response = client.get(f"/api/tracks/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_track_updates_track(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test PATCH /api/tracks/{id} updates track settings."""
    response = client.patch(
        f"/api/tracks/{test_track.id}",
        json={
            "name": "Updated Track Name",
            "volume": 0.5,
            "opacity": 0.8,
            "is_muted": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Track Name"
    assert data["volume"] == 0.5
    assert data["opacity"] == 0.8
    assert data["is_muted"] is True


@pytest.mark.asyncio
async def test_patch_track_update_z_index(
    client: TestClient, test_user, auth_headers: dict, test_track, db_session: AsyncSession
):
    """Test PATCH /api/tracks/{id} updates z_index and reorders tracks."""
    from app.models.project import Track

    # Create another track
    track2 = Track(
        project_id=test_track.project_id,
        track_type="audio",
        name="Track 2",
        z_index=1,
    )
    db_session.add(track2)
    await db_session.commit()

    # Update z_index of first track to move it on top
    response = client.patch(
        f"/api/tracks/{test_track.id}",
        json={"z_index": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["z_index"] == 2


@pytest.mark.asyncio
async def test_patch_track_toggle_visibility(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test PATCH /api/tracks/{id} toggles visibility."""
    response = client.patch(
        f"/api/tracks/{test_track.id}",
        json={"is_visible": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_visible"] is False


@pytest.mark.asyncio
async def test_patch_track_lock_track(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test PATCH /api/tracks/{id} locks track."""
    response = client.patch(
        f"/api/tracks/{test_track.id}",
        json={"is_locked": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_locked"] is True


@pytest.mark.asyncio
async def test_delete_track_deletes_track(
    client: TestClient, test_user, auth_headers: dict, test_track, db_session: AsyncSession
):
    """Test DELETE /api/tracks/{id} deletes track and items."""
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
    response = client.delete(f"/api/tracks/{track_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify track was deleted
    from sqlmodel import select
    from app.models.project import Track

    result = await db_session.execute(select(Track).where(Track.id == track_id))
    assert result.scalar_one_or_none() is None

    # Verify items were also deleted (cascade)
    result = await db_session.execute(select(TrackItem).where(TrackItem.track_id == track_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_track_adjusts_z_index(
    client: TestClient, test_user, auth_headers: dict, test_track, db_session: AsyncSession
):
    """Test DELETE /api/tracks/{id} adjusts z_index of remaining tracks."""
    from app.models.project import Track

    # Create tracks with z_index 0, 1, 2
    track2 = Track(
        project_id=test_track.project_id,
        track_type="audio",
        name="Track 2",
        z_index=1,
    )
    track3 = Track(
        project_id=test_track.project_id,
        track_type="image",
        name="Track 3",
        z_index=2,
    )
    db_session.add_all([track2, track3])
    await db_session.commit()

    # Delete middle track
    response = client.delete(f"/api/tracks/{track2.id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify z_index of track3 was adjusted
    await db_session.refresh(track3)
    assert track3.z_index == 1  # Should be decremented


@pytest.mark.asyncio
async def test_post_track_duplicate(
    client: TestClient, test_user, auth_headers: dict, test_track, db_session: AsyncSession
):
    """Test POST /api/tracks/{id}/duplicate creates a copy of track."""
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

    response = client.post(
        f"/api/tracks/{test_track.id}/duplicate",
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == f"{test_track.name} (Copy)"
    assert data["id"] != str(test_track.id)
    assert data["track_type"] == test_track.track_type
    assert len(data["items"]) >= 1  # Should include duplicated items


@pytest.mark.asyncio
async def test_post_track_reorder(
    client: TestClient, test_user, auth_headers: dict, test_track, db_session: AsyncSession
):
    """Test POST /api/tracks/{id}/reorder reorders track in list."""
    from app.models.project import Track

    # Create tracks with track_order 0, 1, 2
    test_track.track_order = 0
    track2 = Track(
        project_id=test_track.project_id,
        track_type="audio",
        name="Track 2",
        z_index=1,
        track_order=1,
    )
    track3 = Track(
        project_id=test_track.project_id,
        track_type="image",
        name="Track 3",
        z_index=2,
        track_order=2,
    )
    db_session.add_all([track2, track3])
    await db_session.commit()

    # Move track from position 0 to position 2
    response = client.post(
        f"/api/tracks/{test_track.id}/reorder",
        json={"new_order": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_patch_track_audio_specific_settings(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession, test_project
):
    """Test PATCH /api/tracks/{id} updates audio-specific settings."""
    from app.models.project import Track

    # Create audio track
    audio_track = Track(
        project_id=test_project.id,
        track_type="audio",
        name="Audio Track",
        z_index=0,
        volume=1.0,
    )
    db_session.add(audio_track)
    await db_session.commit()
    await db_session.refresh(audio_track)

    # Update audio settings
    response = client.patch(
        f"/api/tracks/{audio_track.id}",
        json={
            "volume": 0.5,
            "is_muted": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["volume"] == 0.5
    assert data["is_muted"] is True


@pytest.mark.asyncio
async def test_patch_track_video_specific_settings(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test PATCH /api/tracks/{id} updates video-specific settings."""
    response = client.patch(
        f"/api/tracks/{test_track.id}",
        json={
            "opacity": 0.7,
            "blend_mode": "multiply",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["opacity"] == 0.7
    assert data["blend_mode"] == "multiply"


@pytest.mark.asyncio
async def test_authorization_users_can_only_access_own_tracks(
    client: TestClient,
    test_user,
    other_user,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test authorization - users can only access tracks in their own projects."""
    from app.models.project import Project, Track

    # Create project and track for other user
    other_project = Project(
        user_id=other_user.id,
        name="Other User's Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
        status="draft",
    )
    db_session.add(other_project)
    await db_session.commit()

    other_track = Track(
        project_id=other_project.id,
        track_type="video",
        name="Other User's Track",
        z_index=0,
    )
    db_session.add(other_track)
    await db_session.commit()
    await db_session.refresh(other_track)

    # Try to access other user's track
    response = client.get(f"/api/tracks/{other_track.id}", headers=auth_headers)
    assert response.status_code == 403

    # Try to update other user's track
    response = client.patch(
        f"/api/tracks/{other_track.id}",
        json={"name": "Hacked Track"},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # Try to delete other user's track
    response = client.delete(f"/api/tracks/{other_track.id}", headers=auth_headers)
    assert response.status_code == 403
