"""Tests for video API endpoints."""

from unittest.mock import patch
from uuid import uuid4

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
async def other_user(db_session: AsyncSession) -> User:
    """Create another test user for authorization tests."""
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
def auth_headers(test_user: User) -> dict:
    """Create auth headers for test user."""
    from app.api.deps import get_current_user

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    return {"Authorization": "Bearer test-token"}


@pytest.mark.asyncio
async def test_post_presigned_url_generates_url_and_creates_video(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/upload/presigned-url generates valid URL and creates video record."""
    with patch("app.services.s3.S3Service.generate_presigned_url") as mock_s3:
        mock_s3.return_value = ("http://test-presigned-url", "videos/test/test-key.mp4")

        response = client.post(
            "/api/upload/presigned-url",
            json={
                "filename": "test-video.mp4",
                "file_size": 1024 * 1024,  # 1 MB
                "content_type": "video/mp4",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "presigned_url" in data
        assert "video_id" in data
        assert "s3_key" in data
        assert data["presigned_url"] == "http://test-presigned-url"

        # Verify video record was created (using db_session from fixture)
        from uuid import UUID

        from sqlmodel import select

        video_id = UUID(data["video_id"])
        result = await db_session.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        assert video is not None
        assert video.user_id == test_user.id
        assert video.status == VideoStatus.UPLOADED


@pytest.mark.asyncio
async def test_post_videos_creates_video_record(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/videos creates video record after upload."""
    # Create initial video record (as if presigned URL was generated)
    video_id = uuid4()
    video = Video(
        id=video_id,
        user_id=test_user.id,
        title="Initial Title",
        status=VideoStatus.UPLOADED,
        s3_key="videos/test/test-key.mp4",
    )
    db_session.add(video)
    await db_session.commit()

    response = client.post(
        "/api/videos",
        json={
            "video_id": str(video_id),
            "title": "Updated Video Title",
            "description": "Video description",
            "s3_key": "videos/test/test-key.mp4",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Updated Video Title"
    assert data["description"] == "Video description"
    assert data["status"] == VideoStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_get_videos_lists_user_videos_with_pagination(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos lists user's videos with pagination, filtering, sorting."""
    # Create multiple videos
    for i in range(5):
        video = Video(
            user_id=test_user.id,
            title=f"Video {i}",
            status=VideoStatus.COMPLETED if i % 2 == 0 else VideoStatus.PROCESSING,
        )
        db_session.add(video)
    await db_session.commit()

    # Test listing all videos
    response = client.get("/api/videos", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    # Test filtering by status
    response = client.get("/api/videos?status=completed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(v["status"] == VideoStatus.COMPLETED.value for v in data)

    # Test pagination
    response = client.get("/api/videos?limit=2&offset=0", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test sorting
    response = client.get("/api/videos?sort_by=title&sort_order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    titles = [v["title"] for v in data]
    assert titles == sorted(titles)


@pytest.mark.asyncio
async def test_get_video_returns_video_details(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/videos/{id} returns video details."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        description="Test description",
        status=VideoStatus.COMPLETED,
        duration=120.5,
        resolution="1920x1080",
        format="mp4",
        s3_key="videos/test/test-key.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    response = client.get(f"/api/videos/{video.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(video.id)
    assert data["title"] == "Test Video"
    assert data["duration"] == 120.5
    assert data["resolution"] == "1920x1080"


@pytest.mark.asyncio
async def test_patch_video_updates_title_description(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test PATCH /api/videos/{id} updates video title/description."""
    video = Video(
        user_id=test_user.id,
        title="Original Title",
        description="Original description",
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    response = client.patch(
        f"/api/videos/{video.id}",
        json={"title": "Updated Title", "description": "Updated description"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_video_deletes_video_and_s3_file(
    client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession
):
    """Test DELETE /api/videos/{id} deletes video and S3 file."""
    video = Video(
        user_id=test_user.id,
        title="Test Video",
        status=VideoStatus.COMPLETED,
        s3_key="videos/test/test-key.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    video_id = video.id

    with patch("app.services.s3.S3Service.delete_object") as mock_delete:
        response = client.delete(f"/api/videos/{video_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify S3 delete was called
        mock_delete.assert_called_once_with("videos/test/test-key.mp4")

        # Verify video was deleted from database
        from sqlmodel import select

        result = await db_session.execute(select(Video).where(Video.id == video_id))
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_authorization_users_can_only_access_own_videos(
    client: TestClient,
    test_user: User,
    other_user: User,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test authorization - users can only access their own videos."""
    # Create video for other user
    video = Video(
        user_id=other_user.id,
        title="Other User's Video",
        status=VideoStatus.COMPLETED,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    # Try to access other user's video
    response = client.get(f"/api/videos/{video.id}", headers=auth_headers)
    assert response.status_code == 403

    # Try to update other user's video
    response = client.patch(
        f"/api/videos/{video.id}",
        json={"title": "Hacked Title"},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # Try to delete other user's video
    response = client.delete(f"/api/videos/{video.id}", headers=auth_headers)
    assert response.status_code == 403
