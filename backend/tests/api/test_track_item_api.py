"""Tests for track item API endpoints."""

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
async def test_track_item(db_session: AsyncSession, test_track, test_video):
    """Create a test track item."""
    from app.models.project import TrackItem

    item = TrackItem(
        track_id=test_track.id,
        item_type="video_clip",
        source_type="video",
        source_id=test_video.id,
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
        position_x=0.5,
        position_y=0.5,
        scale_x=1.0,
        scale_y=1.0,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_post_track_items_creates_video_item(
    client: TestClient, test_user, auth_headers: dict, test_track, test_video
):
    """Test POST /api/tracks/{track_id}/items creates video clip item."""
    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "video_clip",
            "source_type": "video",
            "source_id": str(test_video.id),
            "start_time": 0.0,
            "end_time": 15.0,
            "position_x": 0.5,
            "position_y": 0.5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_type"] == "video_clip"
    assert data["source_type"] == "video"
    assert data["source_id"] == str(test_video.id)
    assert data["start_time"] == 0.0
    assert data["end_time"] == 15.0
    assert data["duration"] == 15.0
    assert "id" in data


@pytest.mark.asyncio
async def test_post_track_items_creates_image_item(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test POST /api/tracks/{track_id}/items creates image item."""
    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "image",
            "source_type": "asset",
            "source_url": "https://s3.amazonaws.com/bucket/image.png",
            "start_time": 5.0,
            "end_time": 15.0,
            "position_x": 0.8,
            "position_y": 0.2,
            "scale_x": 0.5,
            "scale_y": 0.5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_type"] == "image"
    assert data["source_url"] == "https://s3.amazonaws.com/bucket/image.png"
    assert data["start_time"] == 5.0
    assert data["end_time"] == 15.0


@pytest.mark.asyncio
async def test_post_track_items_creates_text_item(
    client: TestClient, test_user, auth_headers: dict, test_track
):
    """Test POST /api/tracks/{track_id}/items creates text item."""
    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "text",
            "source_type": "text",
            "start_time": 2.0,
            "end_time": 8.0,
            "text_content": "Hello World",
            "text_style": {
                "font_family": "Arial",
                "font_size": 48,
                "color": "#FFFFFF",
                "alignment": "center",
            },
            "position_x": 0.5,
            "position_y": 0.9,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["item_type"] == "text"
    assert data["text_content"] == "Hello World"
    assert data["text_style"]["font_family"] == "Arial"


@pytest.mark.asyncio
async def test_post_track_items_with_transitions(
    client: TestClient, test_user, auth_headers: dict, test_track, test_video
):
    """Test POST /api/tracks/{track_id}/items creates item with transitions."""
    transition_id = uuid4()

    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "video_clip",
            "source_type": "video",
            "source_id": str(test_video.id),
            "start_time": 0.0,
            "end_time": 10.0,
            "transition_in": str(transition_id),
            "transition_out": str(transition_id),
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["transition_in"] == str(transition_id)
    assert data["transition_out"] == str(transition_id)


@pytest.mark.asyncio
async def test_post_track_items_validation_errors(
    client: TestClient, auth_headers: dict, test_track
):
    """Test POST /api/tracks/{track_id}/items with validation errors."""
    # End time before start time
    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "video_clip",
            "source_type": "video",
            "start_time": 10.0,
            "end_time": 5.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Missing required fields
    response = client.post(
        f"/api/tracks/{test_track.id}/items",
        json={
            "item_type": "video_clip",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_track_items_lists_items(
    client: TestClient, test_user, auth_headers: dict, test_track, test_video, db_session: AsyncSession
):
    """Test GET /api/tracks/{track_id}/items lists all items in track."""
    from app.models.project import TrackItem

    # Create multiple items
    for i in range(3):
        item = TrackItem(
            track_id=test_track.id,
            item_type="video_clip",
            source_type="video",
            source_id=test_video.id,
            start_time=i * 10.0,
            end_time=(i + 1) * 10.0,
            duration=10.0,
        )
        db_session.add(item)
    await db_session.commit()

    response = client.get(f"/api/tracks/{test_track.id}/items", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_item_returns_item_details(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test GET /api/items/{id} returns item details."""
    response = client.get(f"/api/items/{test_track_item.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_track_item.id)
    assert data["item_type"] == "video_clip"
    assert data["start_time"] == 0.0
    assert data["end_time"] == 10.0


@pytest.mark.asyncio
async def test_get_item_not_found(client: TestClient, auth_headers: dict):
    """Test GET /api/items/{id} returns 404 for non-existent item."""
    fake_id = uuid4()
    response = client.get(f"/api/items/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_item_updates_position(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates item position."""
    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={
            "position_x": 0.3,
            "position_y": 0.7,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["position_x"] == 0.3
    assert data["position_y"] == 0.7


@pytest.mark.asyncio
async def test_patch_item_updates_scale(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates item scale."""
    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={
            "scale_x": 1.5,
            "scale_y": 1.5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scale_x"] == 1.5
    assert data["scale_y"] == 1.5


@pytest.mark.asyncio
async def test_patch_item_updates_rotation(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates item rotation."""
    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={"rotation": 45.0},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rotation"] == 45.0


@pytest.mark.asyncio
async def test_patch_item_updates_timing(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates item timing."""
    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={
            "start_time": 5.0,
            "end_time": 20.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["start_time"] == 5.0
    assert data["end_time"] == 20.0
    assert data["duration"] == 15.0  # Auto-calculated


@pytest.mark.asyncio
async def test_patch_item_updates_effects(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates item effects."""
    effects = [
        {"effect_type": "blur", "parameters": {"radius": 5}},
        {"effect_type": "color", "parameters": {"brightness": 1.2}},
    ]

    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={"effects": effects},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["effects"]) == 2
    assert data["effects"][0]["effect_type"] == "blur"


@pytest.mark.asyncio
async def test_patch_item_updates_crop_settings(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test PATCH /api/items/{id} updates crop settings."""
    crop_settings = {
        "top": 10,
        "bottom": 10,
        "left": 20,
        "right": 20,
    }

    response = client.patch(
        f"/api/items/{test_track_item.id}",
        json={"crop_settings": crop_settings},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["crop_settings"]["top"] == 10


@pytest.mark.asyncio
async def test_delete_item_deletes_item(
    client: TestClient, test_user, auth_headers: dict, test_track_item, db_session: AsyncSession
):
    """Test DELETE /api/items/{id} deletes item."""
    item_id = test_track_item.id

    response = client.delete(f"/api/items/{item_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify item was deleted
    from sqlmodel import select
    from app.models.project import TrackItem

    result = await db_session.execute(select(TrackItem).where(TrackItem.id == item_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_post_item_split(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test POST /api/items/{id}/split splits item at specified time."""
    response = client.post(
        f"/api/items/{test_track_item.id}/split",
        json={"split_time": 5.0},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "item1" in data
    assert "item2" in data

    # First item: 0.0 to 5.0
    assert data["item1"]["start_time"] == 0.0
    assert data["item1"]["end_time"] == 5.0
    assert data["item1"]["duration"] == 5.0

    # Second item: 5.0 to 10.0
    assert data["item2"]["start_time"] == 5.0
    assert data["item2"]["end_time"] == 10.0
    assert data["item2"]["duration"] == 5.0


@pytest.mark.asyncio
async def test_post_item_split_validation(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test POST /api/items/{id}/split with invalid split time."""
    # Split time outside item bounds
    response = client.post(
        f"/api/items/{test_track_item.id}/split",
        json={"split_time": 15.0},  # Item ends at 10.0
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_item_duplicate(
    client: TestClient, test_user, auth_headers: dict, test_track_item
):
    """Test POST /api/items/{id}/duplicate creates a copy of item."""
    response = client.post(
        f"/api/items/{test_track_item.id}/duplicate",
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] != str(test_track_item.id)
    assert data["item_type"] == test_track_item.item_type
    assert data["track_id"] == str(test_track_item.track_id)
    # Duplicated item should start after the original
    assert data["start_time"] >= test_track_item.end_time


@pytest.mark.asyncio
async def test_authorization_users_can_only_access_own_items(
    client: TestClient,
    test_user,
    other_user,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test authorization - users can only access items in their own projects."""
    from app.models.project import Project, Track, TrackItem

    # Create project, track, and item for other user
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

    other_item = TrackItem(
        track_id=other_track.id,
        item_type="video_clip",
        source_type="video",
        start_time=0.0,
        end_time=10.0,
        duration=10.0,
    )
    db_session.add(other_item)
    await db_session.commit()
    await db_session.refresh(other_item)

    # Try to access other user's item
    response = client.get(f"/api/items/{other_item.id}", headers=auth_headers)
    assert response.status_code == 403

    # Try to update other user's item
    response = client.patch(
        f"/api/items/{other_item.id}",
        json={"position_x": 0.5},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # Try to delete other user's item
    response = client.delete(f"/api/items/{other_item.id}", headers=auth_headers)
    assert response.status_code == 403
