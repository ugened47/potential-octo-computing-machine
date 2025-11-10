"""Tests for timeline API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.video import Video, VideoStatus


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    from app.main import app

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
async def test_video(db_session: AsyncSession, test_user: User) -> Video:
    """Create a test video."""
    await db_session.commit()
    await db_session.refresh(test_user)

    video = Video(
        user_id=test_user.id,
        title="Test Video",
        s3_key="videos/test/test-video.mp4",
        duration=60.0,
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video


@pytest.mark.asyncio
async def test_get_waveform_not_found(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test GET /api/videos/{id}/timeline/waveform returns 404 when waveform doesn't exist."""
    with patch("app.api.routes.timeline.WaveformService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_waveform_data.side_effect = ValueError("Waveform not found")

        response = client.get(
            f"/api/videos/{test_video.id}/timeline/waveform",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_waveform_success(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test GET /api/videos/{id}/timeline/waveform returns waveform data."""
    with patch("app.api.routes.timeline.WaveformService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_waveform_data.return_value = {
            "peaks": [0.1, 0.5, 0.8, 0.3],
            "duration": 60.0,
            "sample_rate": 44100,
        }

        response = client.get(
            f"/api/videos/{test_video.id}/timeline/waveform",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "peaks" in data
        assert "duration" in data
        assert "sample_rate" in data
        assert data["duration"] == 60.0
        assert data["sample_rate"] == 44100
        assert len(data["peaks"]) == 4


@pytest.mark.asyncio
async def test_generate_waveform_already_exists(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test POST /api/videos/{id}/timeline/waveform returns completed when waveform exists."""
    with patch("app.api.routes.timeline.WaveformService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_waveform_data.return_value = {
            "peaks": [0.1, 0.5],
            "duration": 60.0,
            "sample_rate": 44100,
        }

        response = client.post(
            f"/api/videos/{test_video.id}/timeline/waveform",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100


@pytest.mark.asyncio
async def test_get_waveform_status_completed(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test GET /api/videos/{id}/timeline/waveform/status returns completed when waveform exists."""
    with patch("app.api.routes.timeline.WaveformService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_waveform_data.return_value = {
            "peaks": [0.1, 0.5],
            "duration": 60.0,
            "sample_rate": 44100,
        }

        response = client.get(
            f"/api/videos/{test_video.id}/timeline/waveform/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100


@pytest.mark.asyncio
async def test_get_waveform_status_processing(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test GET /api/videos/{id}/timeline/waveform/status returns processing when waveform doesn't exist."""
    with patch("app.api.routes.timeline.WaveformService") as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_waveform_data.side_effect = ValueError("Not found")

        response = client.get(
            f"/api/videos/{test_video.id}/timeline/waveform/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 0


@pytest.mark.asyncio
async def test_save_segments(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test POST /api/videos/{id}/timeline/segments saves segments."""
    segments = [
        {
            "id": "seg1",
            "start_time": 10.0,
            "end_time": 20.0,
            "selected": True,
        },
        {
            "id": "seg2",
            "start_time": 30.0,
            "end_time": 40.0,
            "selected": False,
        },
    ]

    response = client.post(
        f"/api/videos/{test_video.id}/timeline/segments",
        json=segments,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "seg1"
    assert data[0]["start_time"] == 10.0
    assert data[0]["end_time"] == 20.0
    assert data[0]["selected"] is True


@pytest.mark.asyncio
async def test_save_segments_invalid_time_range(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test POST /api/videos/{id}/timeline/segments validates time ranges."""
    segments = [
        {
            "id": "seg1",
            "start_time": 20.0,
            "end_time": 10.0,  # Invalid: end < start
            "selected": True,
        },
    ]

    response = client.post(
        f"/api/videos/{test_video.id}/timeline/segments",
        json=segments,
        headers=auth_headers,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_segments(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test GET /api/videos/{id}/timeline/segments returns empty list (MVP implementation)."""
    response = client.get(
        f"/api/videos/{test_video.id}/timeline/segments",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # MVP returns empty list


@pytest.mark.asyncio
async def test_delete_segments(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test DELETE /api/videos/{id}/timeline/segments clears segments."""
    response = client.delete(
        f"/api/videos/{test_video.id}/timeline/segments",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_timeline_endpoints_require_auth(
    client: TestClient, test_video: Video, db_session: AsyncSession
):
    """Test timeline endpoints require authentication."""
    from app.main import app

    # Clear any overrides
    app.dependency_overrides.clear()

    endpoints = [
        ("GET", f"/api/videos/{test_video.id}/timeline/waveform"),
        ("POST", f"/api/videos/{test_video.id}/timeline/waveform"),
        ("GET", f"/api/videos/{test_video.id}/timeline/waveform/status"),
        ("POST", f"/api/videos/{test_video.id}/timeline/segments"),
        ("GET", f"/api/videos/{test_video.id}/timeline/segments"),
        ("DELETE", f"/api/videos/{test_video.id}/timeline/segments"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=[])
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_timeline_endpoints_verify_ownership(
    client: TestClient,
    test_user: User,
    test_video: Video,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test timeline endpoints verify video ownership."""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        full_name="Other User",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    # Create video owned by other user
    other_video = Video(
        user_id=other_user.id,
        title="Other Video",
        s3_key="videos/other/other-video.mp4",
        duration=60.0,
        status=VideoStatus.COMPLETED,
    )
    db_session.add(other_video)
    await db_session.commit()
    await db_session.refresh(other_video)

    # Try to access other user's video
    response = client.get(
        f"/api/videos/{other_video.id}/timeline/waveform",
        headers=auth_headers,
    )

    assert response.status_code == 403
