"""Tests for Version Control API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.security import create_access_token
from tests.factories import UserFactory, VideoFactory


@pytest.fixture
def user(db_session: AsyncSession):
    """Create a test user."""
    user = UserFactory(email="owner@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(user) -> str:
    """Create auth token for user."""
    return create_access_token({"sub": str(user.id)})


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def video(db_session: AsyncSession, user):
    """Create a test video."""
    video = VideoFactory(user_id=user.id, title="Test Video")
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def second_user(db_session: AsyncSession):
    """Create a second test user."""
    user = UserFactory(email="editor@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_user) -> str:
    """Create auth token for second user."""
    return create_access_token({"sub": str(second_user.id)})


class TestListVersions:
    """Tests for listing video versions."""

    def test_list_versions_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully listing all versions of a video."""
        # Create some versions by updating video
        for i in range(3):
            client.post(
                f"/api/videos/{video.id}/versions",
                json={
                    "name": f"Version {i+1}",
                    "description": f"Changes in version {i+1}",
                    "snapshot_data": {
                        "segments": [{"start": 0, "end": 100}],
                        "settings": {"silence_removed": True},
                    },
                },
                headers=auth_headers,
            )

        response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 3
        # Versions should be sorted by version number (descending)
        version_numbers = [v["version_number"] for v in data["items"]]
        assert version_numbers == sorted(version_numbers, reverse=True)

    def test_list_versions_with_pagination(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test listing versions with pagination."""
        # Create 5 versions
        for i in range(5):
            client.post(
                f"/api/videos/{video.id}/versions",
                json={"name": f"Version {i+1}"},
                headers=auth_headers,
            )

        response = client.get(
            f"/api/videos/{video.id}/versions?limit=2&offset=0",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5

    def test_list_versions_without_access(
        self, client: TestClient, second_user_token: str, video
    ):
        """Test listing versions without access permission fails."""
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=headers,
        )

        assert response.status_code == 403

    def test_list_versions_shows_current_flag(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test listing versions shows which is current."""
        # Create a version
        client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )

        response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # One version should be marked as current
        current_versions = [v for v in data["items"] if v["is_current"]]
        assert len(current_versions) == 1


class TestGetVersion:
    """Tests for retrieving specific version details."""

    def test_get_version_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully retrieving version details."""
        # Create a version
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={
                "name": "Test Version",
                "description": "A test version",
                "snapshot_data": {
                    "segments": [{"start": 0, "end": 100}],
                    "settings": {"silence_removed": True},
                },
            },
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Get version details
        response = client.get(
            f"/api/versions/{version_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == version_id
        assert data["name"] == "Test Version"
        assert data["description"] == "A test version"
        assert "snapshot_data" in data
        assert "created_at" in data

    def test_get_version_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting non-existent version fails."""
        fake_id = str(uuid4())
        response = client.get(
            f"/api/versions/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_version_without_access(
        self, client: TestClient, auth_headers: dict, second_user_token: str, video
    ):
        """Test getting version without access permission fails."""
        # Create version as owner
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Test Version"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Try to get as non-owner
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.get(
            f"/api/versions/{version_id}",
            headers=headers,
        )

        assert response.status_code == 403


class TestRollbackVersion:
    """Tests for rolling back to previous versions."""

    def test_rollback_to_version_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully rolling back to a previous version."""
        # Create a few versions
        version_ids = []
        for i in range(3):
            response = client.post(
                f"/api/videos/{video.id}/versions",
                json={
                    "name": f"Version {i+1}",
                    "snapshot_data": {"version_num": i+1},
                },
                headers=auth_headers,
            )
            version_ids.append(response.json()["id"])

        # Rollback to first version
        response = client.post(
            f"/api/versions/{version_ids[0]}/rollback",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_current"] is True
        # Should create a new version based on the old one
        assert data["name"].startswith("Version 1")

    def test_rollback_creates_new_version(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test rollback creates a new version instead of modifying."""
        # Create initial version
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Get initial version count
        list_response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=auth_headers,
        )
        initial_count = list_response.json()["total"]

        # Rollback
        client.post(
            f"/api/versions/{version_id}/rollback",
            headers=auth_headers,
        )

        # Check version count increased
        list_response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=auth_headers,
        )
        new_count = list_response.json()["total"]
        assert new_count == initial_count + 1

    def test_rollback_without_edit_permission(
        self, client: TestClient, second_user_token: str, video, auth_headers: dict
    ):
        """Test rolling back without edit permission fails."""
        # Create version as owner
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Try to rollback as non-editor
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.post(
            f"/api/versions/{version_id}/rollback",
            headers=headers,
        )

        assert response.status_code == 403

    def test_rollback_to_current_version(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test rolling back to current version is allowed (creates copy)."""
        # Create version (becomes current)
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Current Version"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Rollback to same version
        response = client.post(
            f"/api/versions/{version_id}/rollback",
            headers=auth_headers,
        )

        # Should succeed and create a new version
        assert response.status_code == 200


class TestVersionDiff:
    """Tests for comparing versions."""

    def test_get_version_diff_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully getting diff between versions."""
        # Create two versions with different data
        response1 = client.post(
            f"/api/videos/{video.id}/versions",
            json={
                "name": "Version 1",
                "snapshot_data": {
                    "segments": [{"start": 0, "end": 100}],
                    "settings": {"silence_removed": False},
                },
            },
            headers=auth_headers,
        )
        version1_id = response1.json()["id"]

        response2 = client.post(
            f"/api/videos/{video.id}/versions",
            json={
                "name": "Version 2",
                "snapshot_data": {
                    "segments": [{"start": 0, "end": 100}, {"start": 200, "end": 300}],
                    "settings": {"silence_removed": True},
                },
            },
            headers=auth_headers,
        )
        version2_id = response2.json()["id"]

        # Get diff
        response = client.get(
            f"/api/versions/{version2_id}/diff?compare_to={version1_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "diff" in data
        assert "from_version" in data
        assert "to_version" in data
        assert data["from_version"]["id"] == version1_id
        assert data["to_version"]["id"] == version2_id

    def test_diff_with_nonexistent_version(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test diff with non-existent comparison version fails."""
        # Create one version
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        fake_id = str(uuid4())
        response = client.get(
            f"/api/versions/{version_id}/diff?compare_to={fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_diff_without_compare_to_uses_previous(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test diff without compare_to parameter uses previous version."""
        # Create two versions
        response1 = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )

        response2 = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 2"},
            headers=auth_headers,
        )
        version2_id = response2.json()["id"]

        # Get diff without specifying compare_to
        response = client.get(
            f"/api/versions/{version2_id}/diff",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should automatically compare with previous version
        assert "diff" in data


class TestDeleteVersion:
    """Tests for deleting versions."""

    def test_delete_old_version_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully deleting an old (non-current) version."""
        # Create multiple versions
        version_ids = []
        for i in range(3):
            response = client.post(
                f"/api/videos/{video.id}/versions",
                json={"name": f"Version {i+1}"},
                headers=auth_headers,
            )
            version_ids.append(response.json()["id"])

        # Delete the first version (not current)
        response = client.delete(
            f"/api/versions/{version_ids[0]}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        list_response = client.get(
            f"/api/videos/{video.id}/versions",
            headers=auth_headers,
        )
        versions = list_response.json()["items"]
        assert all(v["id"] != version_ids[0] for v in versions)

    def test_delete_current_version_fails(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test deleting current version fails."""
        # Create version (becomes current)
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Current Version"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Try to delete current version
        response = client.delete(
            f"/api/versions/{version_id}",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "cannot delete current version" in response.json()["detail"].lower()

    def test_delete_version_without_permission(
        self, client: TestClient, auth_headers: dict, second_user_token: str, video
    ):
        """Test deleting version without permission fails."""
        # Create version as owner
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 1"},
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Try to delete as non-owner
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.delete(
            f"/api/versions/{version_id}",
            headers=headers,
        )

        assert response.status_code == 403

    def test_delete_version_cascades_properly(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test deleting a version cleans up associated resources."""
        # Create version
        create_response = client.post(
            f"/api/videos/{video.id}/versions",
            json={
                "name": "Version 1",
                "snapshot_data": {"test": "data"},
            },
            headers=auth_headers,
        )
        version_id = create_response.json()["id"]

        # Create another version to make first one non-current
        client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Version 2"},
            headers=auth_headers,
        )

        # Delete first version
        response = client.delete(
            f"/api/versions/{version_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Try to get deleted version
        get_response = client.get(
            f"/api/versions/{version_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


class TestAutoSaveVersions:
    """Tests for auto-save functionality."""

    def test_create_auto_save_version(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating an auto-save version."""
        response = client.post(
            f"/api/videos/{video.id}/versions",
            json={
                "name": "Auto-save",
                "description": "Automatically saved",
                "is_auto_save": True,
                "snapshot_data": {"segments": []},
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "auto" in data["name"].lower() or "auto" in data["description"].lower()

    def test_list_versions_filter_auto_saves(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test filtering out auto-save versions from list."""
        # Create regular version
        client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Manual Version"},
            headers=auth_headers,
        )

        # Create auto-save version
        client.post(
            f"/api/videos/{video.id}/versions",
            json={"name": "Auto-save", "is_auto_save": True},
            headers=auth_headers,
        )

        # List without auto-saves
        response = client.get(
            f"/api/videos/{video.id}/versions?include_auto_save=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only include manual versions
        assert all("auto" not in v["name"].lower() for v in data["items"])
