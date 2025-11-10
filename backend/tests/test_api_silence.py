"""Tests for silence removal API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.video import Video, VideoStatus


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
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
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
async def test_video(db_session: AsyncSession, test_user: User) -> Video:
    """Create a test video."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.UPLOADED,
        s3_key="test-video.mp4",
        duration=120.0,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.mark.asyncio
async def test_detect_silence_segments_unauthorized(
    client: TestClient, test_video: Video
):
    """Test detecting silence without authentication."""
    response = client.get(f"/api/videos/{test_video.id}/silence/segments")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_detect_silence_segments_wrong_user(
    client: TestClient, db_session: AsyncSession, test_video: Video
):
    """Test detecting silence for video owned by different user."""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(other_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/silence/segments", headers=headers
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_detect_silence_segments_video_not_found(
    client: TestClient, test_user: User
):
    """Test detecting silence when video doesn't exist."""
    from uuid import uuid4

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_video_id = uuid4()
    response = client.get(
        f"/api/videos/{fake_video_id}/silence/segments", headers=headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_silence_unauthorized(client: TestClient, test_video: Video):
    """Test removing silence without authentication."""
    response = client.post(
        f"/api/videos/{test_video.id}/silence/remove",
        json={"threshold_db": -40, "min_duration_ms": 1000},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_silence_wrong_user(
    client: TestClient, db_session: AsyncSession, test_video: Video
):
    """Test removing silence for video owned by different user."""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    from app.core.security import create_access_token

    token = create_access_token({"sub": str(other_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/api/videos/{test_video.id}/silence/remove",
        headers=headers,
        json={"threshold_db": -40, "min_duration_ms": 1000},
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_silence_success(
    client: TestClient, test_user: User, test_video: Video
):
    """Test removing silence successfully."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Test that the endpoint accepts the request and returns 202
    # The actual enqueueing may fail in test environment
    response = client.post(
        f"/api/videos/{test_video.id}/silence/remove",
        headers=headers,
        json={
            "threshold_db": -40,
            "min_duration_ms": 1000,
            "excluded_segments": [0],
        },
    )

    # Endpoint should return 202 (accepted) even if enqueue fails
    assert response.status_code == 202
    data = response.json()
    assert "message" in data
    assert str(test_video.id) in data["video_id"]


@pytest.mark.asyncio
async def test_remove_silence_invalid_threshold(
    client: TestClient, test_user: User, test_video: Video
):
    """Test removing silence with invalid threshold."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Threshold too low
    response = client.post(
        f"/api/videos/{test_video.id}/silence/remove",
        headers=headers,
        json={"threshold_db": -100, "min_duration_ms": 1000},
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_remove_silence_invalid_duration(
    client: TestClient, test_user: User, test_video: Video
):
    """Test removing silence with invalid minimum duration."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Duration too short
    response = client.post(
        f"/api/videos/{test_video.id}/silence/remove",
        headers=headers,
        json={"threshold_db": -40, "min_duration_ms": 100},  # Min is 500
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_silence_removal_progress_not_started(
    client: TestClient, test_user: User, test_video: Video
):
    """Test getting progress when not started."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/videos/{test_video.id}/silence/progress", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == str(test_video.id)
    assert data["progress"] == 0
    assert data["status"] == "Not started"


@pytest.mark.asyncio
async def test_get_silence_removal_progress_unauthorized(
    client: TestClient, test_video: Video
):
    """Test getting progress without authentication."""
    response = client.get(f"/api/videos/{test_video.id}/silence/progress")

    assert response.status_code == 403
