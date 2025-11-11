"""Tests for Organization API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import uuid4

from app.core.security import create_access_token
from tests.factories import UserFactory


@pytest.fixture
def user_token(db_session: AsyncSession) -> str:
    """Create a test user and return auth token."""
    user = UserFactory(email="owner@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": str(user.id)})


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def second_user_token(db_session: AsyncSession) -> str:
    """Create a second test user and return auth token."""
    user = UserFactory(email="member@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    return create_access_token({"sub": str(user.id)})


class TestOrganizationCreate:
    """Tests for creating organizations."""

    def test_create_organization_success(self, client: TestClient, auth_headers: dict):
        """Test successful organization creation."""
        response = client.post(
            "/api/organizations",
            json={
                "name": "Test Organization",
                "slug": "test-org",
                "description": "A test organization",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Organization"
        assert data["slug"] == "test-org"
        assert data["description"] == "A test organization"
        assert data["plan"] == "free"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_organization_auto_generate_slug(self, client: TestClient, auth_headers: dict):
        """Test organization creation with auto-generated slug."""
        response = client.post(
            "/api/organizations",
            json={
                "name": "My Cool Company",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "my-cool-company"

    def test_create_organization_duplicate_slug(self, client: TestClient, auth_headers: dict):
        """Test creating organization with duplicate slug fails."""
        # Create first org
        client.post(
            "/api/organizations",
            json={"name": "First Org", "slug": "duplicate-slug"},
            headers=auth_headers,
        )

        # Try to create second org with same slug
        response = client.post(
            "/api/organizations",
            json={"name": "Second Org", "slug": "duplicate-slug"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "slug already exists" in response.json()["detail"].lower()

    def test_create_organization_without_auth(self, client: TestClient):
        """Test creating organization without authentication fails."""
        response = client.post(
            "/api/organizations",
            json={"name": "Test Organization"},
        )

        assert response.status_code == 401

    def test_create_organization_invalid_slug(self, client: TestClient, auth_headers: dict):
        """Test creating organization with invalid slug format."""
        response = client.post(
            "/api/organizations",
            json={"name": "Test Org", "slug": "Invalid Slug!"},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert "slug" in str(response.json()).lower()


class TestOrganizationList:
    """Tests for listing organizations."""

    def test_list_user_organizations(self, client: TestClient, auth_headers: dict):
        """Test listing organizations the user is a member of."""
        # Create multiple organizations
        for i in range(3):
            client.post(
                "/api/organizations",
                json={"name": f"Organization {i}"},
                headers=auth_headers,
            )

        response = client.get("/api/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_organizations_with_pagination(self, client: TestClient, auth_headers: dict):
        """Test listing organizations with pagination."""
        # Create 5 organizations
        for i in range(5):
            client.post(
                "/api/organizations",
                json={"name": f"Organization {i}"},
                headers=auth_headers,
            )

        response = client.get(
            "/api/organizations?limit=2&offset=0",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_list_organizations_without_auth(self, client: TestClient):
        """Test listing organizations without authentication fails."""
        response = client.get("/api/organizations")
        assert response.status_code == 401


class TestOrganizationRetrieve:
    """Tests for retrieving organization details."""

    def test_get_organization_success(self, client: TestClient, auth_headers: dict):
        """Test retrieving organization details."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Organization"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        response = client.get(
            f"/api/organizations/{org_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org_id
        assert data["name"] == "Test Organization"

    def test_get_organization_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieving non-existent organization."""
        fake_id = str(uuid4())
        response = client.get(
            f"/api/organizations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_organization_no_permission(
        self, client: TestClient, second_user_token: str
    ):
        """Test retrieving organization without permission."""
        # Create org as first user
        first_user_headers = {"Authorization": f"Bearer {second_user_token}"}
        create_response = client.post(
            "/api/organizations",
            json={"name": "Private Org"},
            headers=first_user_headers,
        )
        org_id = create_response.json()["id"]

        # Try to access as second user (who is not a member)
        second_user = UserFactory(email="outsider@example.com", verified=True)
        outsider_token = create_access_token({"sub": str(second_user.id)})
        outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

        response = client.get(
            f"/api/organizations/{org_id}",
            headers=outsider_headers,
        )

        assert response.status_code == 403


class TestOrganizationUpdate:
    """Tests for updating organizations."""

    def test_update_organization_success(self, client: TestClient, auth_headers: dict):
        """Test updating organization details."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Original Name"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Update organization
        response = client.patch(
            f"/api/organizations/{org_id}",
            json={"name": "Updated Name", "description": "New description"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    def test_update_organization_not_owner(
        self, client: TestClient, auth_headers: dict, second_user_token: str
    ):
        """Test updating organization without owner permission fails."""
        # Create org as first user
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Try to update as second user
        second_headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.patch(
            f"/api/organizations/{org_id}",
            json={"name": "Hacked Name"},
            headers=second_headers,
        )

        assert response.status_code == 403

    def test_update_organization_settings(self, client: TestClient, auth_headers: dict):
        """Test updating organization settings."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Update settings
        response = client.patch(
            f"/api/organizations/{org_id}",
            json={
                "settings": {
                    "default_permissions": "editor",
                    "allow_public_sharing": False,
                }
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["default_permissions"] == "editor"
        assert data["settings"]["allow_public_sharing"] is False


class TestOrganizationDelete:
    """Tests for deleting organizations."""

    def test_delete_organization_success(self, client: TestClient, auth_headers: dict):
        """Test deleting organization as owner."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "To Delete"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Delete organization
        response = client.delete(
            f"/api/organizations/{org_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/api/organizations/{org_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_organization_not_owner(
        self, client: TestClient, auth_headers: dict, second_user_token: str
    ):
        """Test deleting organization without owner permission fails."""
        # Create org as first user
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Try to delete as second user
        second_headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.delete(
            f"/api/organizations/{org_id}",
            headers=second_headers,
        )

        assert response.status_code == 403


class TestOrganizationMembers:
    """Tests for managing organization members."""

    def test_invite_member_success(self, client: TestClient, auth_headers: dict):
        """Test inviting a member to organization."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Invite member
        response = client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "newmember@example.com", "role": "editor"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newmember@example.com"
        assert data["role"] == "editor"
        assert data["status"] == "invited"
        assert "invitation_token" in data

    def test_invite_member_duplicate(self, client: TestClient, auth_headers: dict):
        """Test inviting same member twice fails."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Invite member
        client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "member@example.com", "role": "editor"},
            headers=auth_headers,
        )

        # Try to invite again
        response = client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "member@example.com", "role": "viewer"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_list_organization_members(self, client: TestClient, auth_headers: dict):
        """Test listing organization members."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Invite some members
        for i in range(3):
            client.post(
                f"/api/organizations/{org_id}/members/invite",
                json={"email": f"member{i}@example.com", "role": "viewer"},
                headers=auth_headers,
            )

        # List members
        response = client.get(
            f"/api/organizations/{org_id}/members",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should include owner + 3 invited members
        assert len(data["items"]) >= 3

    def test_update_member_role(self, client: TestClient, auth_headers: dict):
        """Test updating member role."""
        # Create organization and invite member
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        invite_response = client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "member@example.com", "role": "viewer"},
            headers=auth_headers,
        )
        member_id = invite_response.json()["user_id"]

        # Update role
        response = client.patch(
            f"/api/organizations/{org_id}/members/{member_id}",
            json={"role": "admin"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_remove_member(self, client: TestClient, auth_headers: dict):
        """Test removing member from organization."""
        # Create organization and invite member
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        invite_response = client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "member@example.com", "role": "viewer"},
            headers=auth_headers,
        )
        member_id = invite_response.json()["user_id"]

        # Remove member
        response = client.delete(
            f"/api/organizations/{org_id}/members/{member_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    def test_remove_member_not_admin(
        self, client: TestClient, auth_headers: dict, second_user_token: str
    ):
        """Test removing member without admin permission fails."""
        # Create organization
        create_response = client.post(
            "/api/organizations",
            json={"name": "Test Org"},
            headers=auth_headers,
        )
        org_id = create_response.json()["id"]

        # Invite first member
        invite_response = client.post(
            f"/api/organizations/{org_id}/members/invite",
            json={"email": "victim@example.com", "role": "viewer"},
            headers=auth_headers,
        )
        victim_id = invite_response.json()["user_id"]

        # Try to remove as non-admin member
        second_headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.delete(
            f"/api/organizations/{org_id}/members/{victim_id}",
            headers=second_headers,
        )

        assert response.status_code == 403
