"""Tests for project API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
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
        description="Test project description",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
        background_color="#000000",
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_post_projects_creates_project(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/projects creates a new project."""
    response = client.post(
        "/api/projects",
        json={
            "name": "My New Project",
            "description": "A test project",
            "width": 1920,
            "height": 1080,
            "frame_rate": 30.0,
            "duration_seconds": 120.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My New Project"
    assert data["description"] == "A test project"
    assert data["width"] == 1920
    assert data["height"] == 1080
    assert data["frame_rate"] == 30.0
    assert data["duration_seconds"] == 120.0
    assert data["status"] == "draft"
    assert "id" in data
    assert data["user_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_post_projects_with_video_id(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/projects with existing video creates project from video."""
    from app.models.video import Video, VideoStatus

    # Create a video
    video = Video(
        user_id=test_user.id,
        title="Base Video",
        status=VideoStatus.COMPLETED,
        duration=60.5,
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)

    response = client.post(
        "/api/projects",
        json={
            "name": "Project from Video",
            "video_id": str(video.id),
            "width": 1920,
            "height": 1080,
            "frame_rate": 30.0,
            "duration_seconds": 60.5,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Project from Video"
    assert data["video_id"] == str(video.id)


@pytest.mark.asyncio
async def test_post_projects_creates_default_tracks(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test POST /api/projects creates default tracks."""
    response = client.post(
        "/api/projects",
        json={
            "name": "Project with Tracks",
            "width": 1920,
            "height": 1080,
            "frame_rate": 30.0,
            "duration_seconds": 60.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()

    # Verify default tracks are created (1 video track, 1 audio track)
    assert "tracks" in data
    assert len(data["tracks"]) >= 2

    track_types = [track["track_type"] for track in data["tracks"]]
    assert "video" in track_types
    assert "audio" in track_types


@pytest.mark.asyncio
async def test_post_projects_validation_errors(
    client: TestClient, auth_headers: dict
):
    """Test POST /api/projects with validation errors."""
    # Missing required fields
    response = client.post(
        "/api/projects",
        json={"name": "Missing Fields"},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid dimensions
    response = client.post(
        "/api/projects",
        json={
            "name": "Invalid Dimensions",
            "width": -100,
            "height": 1080,
            "frame_rate": 30.0,
            "duration_seconds": 60.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Invalid frame rate
    response = client.post(
        "/api/projects",
        json={
            "name": "Invalid Frame Rate",
            "width": 1920,
            "height": 1080,
            "frame_rate": 0,
            "duration_seconds": 60.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_projects_lists_user_projects(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/projects lists user's projects."""
    from app.models.project import Project

    # Create multiple projects
    for i in range(5):
        project = Project(
            user_id=test_user.id,
            name=f"Project {i}",
            width=1920,
            height=1080,
            frame_rate=30.0,
            duration_seconds=60.0,
            status="draft" if i % 2 == 0 else "completed",
        )
        db_session.add(project)
    await db_session.commit()

    response = client.get("/api/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert len(data["projects"]) == 5
    assert "total" in data
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_get_projects_with_filters(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/projects with status filter."""
    from app.models.project import Project

    # Create projects with different statuses
    for status in ["draft", "rendering", "completed"]:
        for i in range(2):
            project = Project(
                user_id=test_user.id,
                name=f"Project {status} {i}",
                width=1920,
                height=1080,
                frame_rate=30.0,
                duration_seconds=60.0,
                status=status,
            )
            db_session.add(project)
    await db_session.commit()

    # Filter by status
    response = client.get("/api/projects?status=completed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
    assert all(p["status"] == "completed" for p in data["projects"])


@pytest.mark.asyncio
async def test_get_projects_with_pagination(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/projects with pagination."""
    from app.models.project import Project

    # Create 10 projects
    for i in range(10):
        project = Project(
            user_id=test_user.id,
            name=f"Project {i}",
            width=1920,
            height=1080,
            frame_rate=30.0,
            duration_seconds=60.0,
            status="draft",
        )
        db_session.add(project)
    await db_session.commit()

    # Test pagination
    response = client.get("/api/projects?limit=5&offset=0", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 5

    response = client.get("/api/projects?limit=5&offset=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 5


@pytest.mark.asyncio
async def test_get_projects_with_sorting(
    client: TestClient, test_user, auth_headers: dict, db_session: AsyncSession
):
    """Test GET /api/projects with sorting."""
    from app.models.project import Project

    # Create projects with different names
    for name in ["Zebra", "Alpha", "Beta"]:
        project = Project(
            user_id=test_user.id,
            name=name,
            width=1920,
            height=1080,
            frame_rate=30.0,
            duration_seconds=60.0,
            status="draft",
        )
        db_session.add(project)
    await db_session.commit()

    # Sort by name ascending
    response = client.get("/api/projects?sort_by=name&sort_order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data["projects"]]
    assert names == ["Alpha", "Beta", "Zebra"]


@pytest.mark.asyncio
async def test_get_project_returns_project_details(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test GET /api/projects/{id} returns project details with tracks and items."""
    response = client.get(f"/api/projects/{test_project.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_project.id)
    assert data["name"] == "Test Project"
    assert data["width"] == 1920
    assert data["height"] == 1080
    assert "tracks" in data


@pytest.mark.asyncio
async def test_get_project_not_found(client: TestClient, auth_headers: dict):
    """Test GET /api/projects/{id} returns 404 for non-existent project."""
    fake_id = uuid4()
    response = client.get(f"/api/projects/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_project_updates_project(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test PATCH /api/projects/{id} updates project settings."""
    response = client.patch(
        f"/api/projects/{test_project.id}",
        json={
            "name": "Updated Project Name",
            "description": "Updated description",
            "width": 3840,
            "height": 2160,
            "background_color": "#FFFFFF",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project Name"
    assert data["description"] == "Updated description"
    assert data["width"] == 3840
    assert data["height"] == 2160
    assert data["background_color"] == "#FFFFFF"


@pytest.mark.asyncio
async def test_patch_project_partial_update(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test PATCH /api/projects/{id} with partial update."""
    original_width = test_project.width

    response = client.patch(
        f"/api/projects/{test_project.id}",
        json={"name": "Only Name Changed"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Only Name Changed"
    assert data["width"] == original_width  # Unchanged


@pytest.mark.asyncio
async def test_delete_project_deletes_project(
    client: TestClient, test_user, auth_headers: dict, test_project, db_session: AsyncSession
):
    """Test DELETE /api/projects/{id} deletes project."""
    project_id = test_project.id

    response = client.delete(f"/api/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify project was deleted
    from sqlmodel import select
    from app.models.project import Project

    result = await db_session.execute(select(Project).where(Project.id == project_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_project_deletes_s3_files(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test DELETE /api/projects/{id} deletes associated S3 files."""
    # Set render output URL to simulate rendered project
    test_project.render_output_url = "https://s3.amazonaws.com/bucket/output.mp4"

    with patch("app.services.s3.S3Service.delete_object") as mock_delete:
        response = client.delete(f"/api/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify S3 delete was called
        assert mock_delete.called


@pytest.mark.asyncio
async def test_post_project_duplicate(
    client: TestClient, test_user, auth_headers: dict, test_project, db_session: AsyncSession
):
    """Test POST /api/projects/{id}/duplicate creates a copy of project."""
    from app.models.project import Track

    # Add a track to the original project
    track = Track(
        project_id=test_project.id,
        track_type="video",
        name="Test Track",
        z_index=0,
    )
    db_session.add(track)
    await db_session.commit()

    response = client.post(
        f"/api/projects/{test_project.id}/duplicate",
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == f"{test_project.name} (Copy)"
    assert data["id"] != str(test_project.id)
    assert data["user_id"] == str(test_user.id)
    assert len(data["tracks"]) >= 1  # Should include duplicated tracks


@pytest.mark.asyncio
async def test_post_project_render(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test POST /api/projects/{id}/render triggers project rendering."""
    with patch("app.worker.enqueue_job") as mock_enqueue:
        mock_enqueue.return_value = "job-123"

        response = client.post(
            f"/api/projects/{test_project.id}/render",
            json={
                "quality": "high",
                "format": "mp4",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "estimated_time" in data
        assert mock_enqueue.called


@pytest.mark.asyncio
async def test_get_render_progress(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test GET /api/projects/{id}/render/progress returns render progress."""
    with patch("app.services.redis.get") as mock_redis:
        mock_redis.return_value = {
            "progress": 50,
            "stage": "Rendering video",
            "status": "processing",
            "estimated_remaining": 120,
        }

        response = client.get(
            f"/api/projects/{test_project.id}/render/progress",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 50
        assert data["stage"] == "Rendering video"
        assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_post_project_preview(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test POST /api/projects/{id}/preview generates preview frame."""
    with patch("app.services.video_rendering_service.VideoRenderingService.generate_preview_frame") as mock_preview:
        mock_preview.return_value = "/tmp/preview.jpg"

        response = client.post(
            f"/api/projects/{test_project.id}/preview",
            json={"time": 5.0},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
        assert mock_preview.called


@pytest.mark.asyncio
async def test_get_project_validate(
    client: TestClient, test_user, auth_headers: dict, test_project
):
    """Test GET /api/projects/{id}/validate validates project before render."""
    with patch("app.services.composition_service.CompositionService.validate_project") as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "warnings": ["Track 2 has no items"],
        }

        response = client.get(
            f"/api/projects/{test_project.id}/validate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "errors" in data
        assert "warnings" in data


@pytest.mark.asyncio
async def test_authorization_users_can_only_access_own_projects(
    client: TestClient,
    test_user,
    other_user,
    auth_headers: dict,
    db_session: AsyncSession,
):
    """Test authorization - users can only access their own projects."""
    from app.models.project import Project

    # Create project for other user
    project = Project(
        user_id=other_user.id,
        name="Other User's Project",
        width=1920,
        height=1080,
        frame_rate=30.0,
        duration_seconds=60.0,
        status="draft",
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Try to access other user's project
    response = client.get(f"/api/projects/{project.id}", headers=auth_headers)
    assert response.status_code == 403

    # Try to update other user's project
    response = client.patch(
        f"/api/projects/{project.id}",
        json={"name": "Hacked Project"},
        headers=auth_headers,
    )
    assert response.status_code == 403

    # Try to delete other user's project
    response = client.delete(f"/api/projects/{project.id}", headers=auth_headers)
    assert response.status_code == 403
