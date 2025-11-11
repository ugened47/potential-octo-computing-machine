"""Tests for Video Sharing API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.security import create_access_token, get_password_hash
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
    user = UserFactory(email="viewer@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_user) -> str:
    """Create auth token for second user."""
    return create_access_token({"sub": str(second_user.id)})


class TestShareVideo:
    """Tests for sharing videos with users."""

    def test_share_video_with_user_success(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test successfully sharing a video with another user."""
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": second_user.email,
                "permission": "viewer",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["share_type"] == "user"
        assert data["permission"] == "viewer"
        assert data["shared_with_user_id"] == str(second_user.id)
        assert data["video_id"] == str(video.id)
        assert "id" in data

    def test_share_video_with_editor_permission(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test sharing video with editor permission."""
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": second_user.email,
                "permission": "editor",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["permission"] == "editor"

    def test_share_video_with_nonexistent_user(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test sharing video with non-existent user fails."""
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": "nonexistent@example.com",
                "permission": "viewer",
            },
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    def test_share_video_not_owner(
        self, client: TestClient, second_user_token: str, video
    ):
        """Test sharing video without ownership fails."""
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": "someone@example.com",
                "permission": "viewer",
            },
            headers=headers,
        )

        assert response.status_code == 403

    def test_share_video_with_self(
        self, client: TestClient, auth_headers: dict, video, user
    ):
        """Test sharing video with self fails."""
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": user.email,
                "permission": "viewer",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "cannot share with yourself" in response.json()["detail"].lower()

    def test_share_video_duplicate(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test sharing same video twice with same user updates existing share."""
        # First share
        client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": second_user.email,
                "permission": "viewer",
            },
            headers=auth_headers,
        )

        # Second share with different permission
        response = client.post(
            f"/api/videos/{video.id}/share",
            json={
                "user_email": second_user.email,
                "permission": "editor",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200  # Updated
        data = response.json()
        assert data["permission"] == "editor"


class TestShareLink:
    """Tests for creating shareable links."""

    def test_create_share_link_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating a shareable link."""
        response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={
                "permission": "viewer",
                "settings": {
                    "allow_download": False,
                    "allow_comments": True,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["share_type"] == "public_link"
        assert data["is_public"] is True
        assert "public_token" in data
        assert data["permission"] == "viewer"
        assert data["settings"]["allow_download"] is False

    def test_create_share_link_with_expiration(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating shareable link with expiration."""
        expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
        response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={
                "permission": "viewer",
                "expires_at": expires_at,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "expires_at" in data
        assert data["expires_at"] is not None

    def test_create_share_link_with_password(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating password-protected shareable link."""
        response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={
                "permission": "viewer",
                "password": "SecurePass123!",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["requires_password"] is True
        assert "password_hash" not in data  # Should not expose hash

    def test_create_share_link_with_view_limit(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating shareable link with view limit."""
        response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={
                "permission": "viewer",
                "max_views": 100,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["max_views"] == 100
        assert data["view_count"] == 0

    def test_create_share_link_not_owner(
        self, client: TestClient, second_user_token: str, video
    ):
        """Test creating share link without ownership fails."""
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer"},
            headers=headers,
        )

        assert response.status_code == 403


class TestAccessSharedVideo:
    """Tests for accessing shared videos."""

    def test_access_video_via_share_link(self, client: TestClient, video, user):
        """Test accessing video via public share link."""
        # Create share link as owner
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        create_response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer"},
            headers=owner_headers,
        )
        public_token = create_response.json()["public_token"]

        # Access via link without authentication
        response = client.get(f"/api/shares/link/{public_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["video"]["id"] == str(video.id)
        assert data["permission"] == "viewer"

    def test_access_expired_share_link(self, client: TestClient, video, user):
        """Test accessing expired share link fails."""
        # Create share link with past expiration
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        expired_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        create_response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer", "expires_at": expired_date},
            headers=owner_headers,
        )
        public_token = create_response.json()["public_token"]

        # Try to access
        response = client.get(f"/api/shares/link/{public_token}")

        assert response.status_code == 410  # Gone
        assert "expired" in response.json()["detail"].lower()

    def test_access_password_protected_link(self, client: TestClient, video, user):
        """Test accessing password-protected link."""
        # Create password-protected link
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        create_response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer", "password": "SecurePass123!"},
            headers=owner_headers,
        )
        public_token = create_response.json()["public_token"]

        # Try without password
        response = client.get(f"/api/shares/link/{public_token}")
        assert response.status_code == 401

        # Try with wrong password
        response = client.get(
            f"/api/shares/link/{public_token}?password=WrongPass"
        )
        assert response.status_code == 401

        # Try with correct password
        response = client.get(
            f"/api/shares/link/{public_token}?password=SecurePass123!"
        )
        assert response.status_code == 200

    def test_access_view_limit_exceeded(self, client: TestClient, video, user):
        """Test accessing link after view limit exceeded."""
        # Create link with view limit
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        create_response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer", "max_views": 1},
            headers=owner_headers,
        )
        public_token = create_response.json()["public_token"]

        # First access (should work)
        response = client.get(f"/api/shares/link/{public_token}")
        assert response.status_code == 200

        # Second access (should fail)
        response = client.get(f"/api/shares/link/{public_token}")
        assert response.status_code == 403
        assert "view limit exceeded" in response.json()["detail"].lower()


class TestListShares:
    """Tests for listing video shares."""

    def test_list_video_shares(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test listing all shares for a video."""
        # Create multiple shares
        client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "viewer"},
            headers=auth_headers,
        )
        client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer"},
            headers=auth_headers,
        )

        # List shares
        response = client.get(
            f"/api/videos/{video.id}/shares",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_shares_not_owner(
        self, client: TestClient, second_user_token: str, video
    ):
        """Test listing shares without ownership fails."""
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.get(
            f"/api/videos/{video.id}/shares",
            headers=headers,
        )

        assert response.status_code == 403


class TestRevokeShare:
    """Tests for revoking shares."""

    def test_revoke_user_share(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test revoking a user share."""
        # Create share
        create_response = client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "viewer"},
            headers=auth_headers,
        )
        share_id = create_response.json()["id"]

        # Revoke share
        response = client.delete(
            f"/api/shares/{share_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's revoked
        list_response = client.get(
            f"/api/videos/{video.id}/shares",
            headers=auth_headers,
        )
        shares = list_response.json()["items"]
        assert all(s["id"] != share_id for s in shares)

    def test_revoke_share_link(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test revoking a share link."""
        # Create share link
        create_response = client.post(
            f"/api/videos/{video.id}/share/link",
            json={"permission": "viewer"},
            headers=auth_headers,
        )
        share_id = create_response.json()["id"]
        public_token = create_response.json()["public_token"]

        # Revoke share
        response = client.delete(
            f"/api/shares/{share_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify link no longer works
        access_response = client.get(f"/api/shares/link/{public_token}")
        assert access_response.status_code == 404

    def test_revoke_share_not_owner(
        self, client: TestClient, auth_headers: dict, second_user_token: str,
        video, second_user
    ):
        """Test revoking share without ownership fails."""
        # Create share as owner
        create_response = client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "viewer"},
            headers=auth_headers,
        )
        share_id = create_response.json()["id"]

        # Try to revoke as non-owner
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.delete(
            f"/api/shares/{share_id}",
            headers=headers,
        )

        assert response.status_code == 403


class TestPermissionValidation:
    """Tests for share permission validation."""

    def test_shared_user_can_view_video(
        self, client: TestClient, video, second_user, user
    ):
        """Test user with viewer permission can access video."""
        # Share video with viewer permission
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "viewer"},
            headers=owner_headers,
        )

        # Access as shared user
        viewer_token = create_access_token({"sub": str(second_user.id)})
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        response = client.get(
            f"/api/videos/{video.id}",
            headers=viewer_headers,
        )

        assert response.status_code == 200

    def test_shared_user_cannot_edit_with_viewer_permission(
        self, client: TestClient, video, second_user, user
    ):
        """Test user with viewer permission cannot edit video."""
        # Share video with viewer permission
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "viewer"},
            headers=owner_headers,
        )

        # Try to edit as shared user
        viewer_token = create_access_token({"sub": str(second_user.id)})
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        response = client.patch(
            f"/api/videos/{video.id}",
            json={"title": "Hacked Title"},
            headers=viewer_headers,
        )

        assert response.status_code == 403

    def test_shared_user_can_edit_with_editor_permission(
        self, client: TestClient, video, second_user, user
    ):
        """Test user with editor permission can edit video."""
        # Share video with editor permission
        owner_token = create_access_token({"sub": str(user.id)})
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        client.post(
            f"/api/videos/{video.id}/share",
            json={"user_email": second_user.email, "permission": "editor"},
            headers=owner_headers,
        )

        # Edit as shared user
        editor_token = create_access_token({"sub": str(second_user.id)})
        editor_headers = {"Authorization": f"Bearer {editor_token}"}

        response = client.patch(
            f"/api/videos/{video.id}",
            json={"title": "Edited Title"},
            headers=editor_headers,
        )

        assert response.status_code == 200
