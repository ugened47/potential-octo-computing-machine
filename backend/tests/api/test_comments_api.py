"""Tests for Comments API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.security import create_access_token
from tests.factories import UserFactory, VideoFactory


@pytest.fixture
def user(db_session: AsyncSession):
    """Create a test user."""
    user = UserFactory(email="commenter@example.com", verified=True)
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
    user = UserFactory(email="reviewer@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_user) -> str:
    """Create auth token for second user."""
    return create_access_token({"sub": str(second_user.id)})


class TestCreateComment:
    """Tests for creating comments."""

    def test_create_comment_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully creating a comment."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={
                "content": "This is a great video!",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a great video!"
        assert data["video_id"] == str(video.id)
        assert "id" in data
        assert "created_at" in data
        assert data["is_edited"] is False

    def test_create_timeline_comment(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating a comment at specific timeline position."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={
                "content": "Great moment here!",
                "timestamp": 45.5,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["timestamp"] == 45.5

    def test_create_comment_with_mentions(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test creating a comment with user mentions."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={
                "content": f"Hey @{second_user.email}, check this out!",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "mentions" in data
        assert str(second_user.id) in data["mentions"]

    def test_create_comment_empty_content(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test creating comment with empty content fails."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": ""},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_comment_without_auth(
        self, client: TestClient, video
    ):
        """Test creating comment without authentication fails."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Nice video!"},
        )

        assert response.status_code == 401

    def test_create_comment_on_nonexistent_video(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating comment on non-existent video fails."""
        fake_video_id = str(uuid4())
        response = client.post(
            f"/api/videos/{fake_video_id}/comments",
            json={"content": "Nice video!"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_create_comment_without_access_permission(
        self, client: TestClient, second_user_token: str, user
    ):
        """Test creating comment on video without access permission fails."""
        # Create private video as first user
        private_video = VideoFactory(user_id=user.id, title="Private Video")

        # Try to comment as second user (no access)
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.post(
            f"/api/videos/{private_video.id}/comments",
            json={"content": "Nice video!"},
            headers=headers,
        )

        assert response.status_code == 403


class TestListComments:
    """Tests for listing comments."""

    def test_list_comments_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test listing comments for a video."""
        # Create multiple comments
        for i in range(3):
            client.post(
                f"/api/videos/{video.id}/comments",
                json={"content": f"Comment {i}"},
                headers=auth_headers,
            )

        response = client.get(
            f"/api/videos/{video.id}/comments",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_comments_with_pagination(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test listing comments with pagination."""
        # Create 5 comments
        for i in range(5):
            client.post(
                f"/api/videos/{video.id}/comments",
                json={"content": f"Comment {i}"},
                headers=auth_headers,
            )

        response = client.get(
            f"/api/videos/{video.id}/comments?limit=2&offset=0",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_list_comments_sorted_by_timestamp(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test comments are sorted by creation timestamp."""
        # Create comments with different timestamps
        timestamps = [10.0, 5.0, 15.0]
        for ts in timestamps:
            client.post(
                f"/api/videos/{video.id}/comments",
                json={"content": f"Comment at {ts}", "timestamp": ts},
                headers=auth_headers,
            )

        response = client.get(
            f"/api/videos/{video.id}/comments?sort_by=timestamp",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should be sorted in ascending order
        assert data["items"][0]["timestamp"] == 5.0
        assert data["items"][1]["timestamp"] == 10.0
        assert data["items"][2]["timestamp"] == 15.0

    def test_list_comments_without_auth(
        self, client: TestClient, video
    ):
        """Test listing comments without authentication fails."""
        response = client.get(f"/api/videos/{video.id}/comments")
        assert response.status_code == 401


class TestUpdateComment:
    """Tests for updating comments."""

    def test_update_comment_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully updating a comment."""
        # Create comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Update comment
        response = client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Updated content"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["is_edited"] is True
        assert "edited_at" in data

    def test_update_comment_not_author(
        self, client: TestClient, auth_headers: dict, second_user_token: str, video
    ):
        """Test updating comment by non-author fails."""
        # Create comment as first user
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Try to update as second user
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Hacked content"},
            headers=headers,
        )

        assert response.status_code == 403

    def test_update_nonexistent_comment(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating non-existent comment fails."""
        fake_id = str(uuid4())
        response = client.patch(
            f"/api/comments/{fake_id}",
            json={"content": "Updated content"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestDeleteComment:
    """Tests for deleting comments."""

    def test_delete_comment_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully deleting a comment."""
        # Create comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "To be deleted"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Delete comment
        response = client.delete(
            f"/api/comments/{comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        list_response = client.get(
            f"/api/videos/{video.id}/comments",
            headers=auth_headers,
        )
        comments = list_response.json()["items"]
        assert all(c["id"] != comment_id for c in comments)

    def test_delete_comment_not_author(
        self, client: TestClient, auth_headers: dict, second_user_token: str, video
    ):
        """Test deleting comment by non-author fails."""
        # Create comment as first user
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Try to delete as second user
        headers = {"Authorization": f"Bearer {second_user_token}"}
        response = client.delete(
            f"/api/comments/{comment_id}",
            headers=headers,
        )

        assert response.status_code == 403

    def test_delete_comment_video_owner_can_delete(
        self, client: TestClient, auth_headers: dict, second_user_token: str, video
    ):
        """Test video owner can delete any comment on their video."""
        # Create comment as second user
        headers = {"Authorization": f"Bearer {second_user_token}"}
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Some comment"},
            headers=headers,
        )
        comment_id = create_response.json()["id"]

        # Delete as video owner (first user)
        response = client.delete(
            f"/api/comments/{comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204


class TestCommentReplies:
    """Tests for comment replies."""

    def test_create_reply_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully creating a reply to a comment."""
        # Create parent comment
        parent_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Parent comment"},
            headers=auth_headers,
        )
        parent_id = parent_response.json()["id"]

        # Create reply
        response = client.post(
            f"/api/comments/{parent_id}/replies",
            json={"content": "This is a reply"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a reply"
        assert data["parent_comment_id"] == parent_id

    def test_list_comment_replies(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test listing replies to a comment."""
        # Create parent comment
        parent_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Parent comment"},
            headers=auth_headers,
        )
        parent_id = parent_response.json()["id"]

        # Create multiple replies
        for i in range(3):
            client.post(
                f"/api/comments/{parent_id}/replies",
                json={"content": f"Reply {i}"},
                headers=auth_headers,
            )

        # List replies
        response = client.get(
            f"/api/comments/{parent_id}/replies",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

    def test_reply_to_nonexistent_comment(
        self, client: TestClient, auth_headers: dict
    ):
        """Test replying to non-existent comment fails."""
        fake_id = str(uuid4())
        response = client.post(
            f"/api/comments/{fake_id}/replies",
            json={"content": "Reply"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestCommentReactions:
    """Tests for comment reactions."""

    def test_add_reaction_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully adding a reaction to a comment."""
        # Create comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Great video!"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Add reaction
        response = client.post(
            f"/api/comments/{comment_id}/reactions",
            json={"reaction_type": "thumbs_up"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "thumbs_up" in data["reactions"]
        assert data["reactions"]["thumbs_up"] == 1

    def test_add_multiple_reactions(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test adding multiple different reactions."""
        # Create comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Great video!"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Add different reactions
        reactions = ["thumbs_up", "heart", "laugh"]
        for reaction in reactions:
            client.post(
                f"/api/comments/{comment_id}/reactions",
                json={"reaction_type": reaction},
                headers=auth_headers,
            )

        # Get comment
        response = client.get(
            f"/api/comments/{comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for reaction in reactions:
            assert reaction in data["reactions"]

    def test_remove_reaction(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test removing a reaction from a comment."""
        # Create comment and add reaction
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Great video!"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        client.post(
            f"/api/comments/{comment_id}/reactions",
            json={"reaction_type": "thumbs_up"},
            headers=auth_headers,
        )

        # Remove reaction
        response = client.delete(
            f"/api/comments/{comment_id}/reactions/thumbs_up",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reactions"].get("thumbs_up", 0) == 0


class TestCommentResolve:
    """Tests for resolving/unresolving comments."""

    def test_resolve_comment_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully resolving a comment."""
        # Create comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Please fix this issue"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        # Resolve comment
        response = client.post(
            f"/api/comments/{comment_id}/resolve",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True

    def test_unresolve_comment_success(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test successfully unresolving a comment."""
        # Create and resolve comment
        create_response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "Please fix this issue"},
            headers=auth_headers,
        )
        comment_id = create_response.json()["id"]

        client.post(
            f"/api/comments/{comment_id}/resolve",
            headers=auth_headers,
        )

        # Unresolve comment
        response = client.post(
            f"/api/comments/{comment_id}/unresolve",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is False

    def test_filter_resolved_comments(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test filtering resolved/unresolved comments."""
        # Create resolved and unresolved comments
        for i in range(2):
            response = client.post(
                f"/api/videos/{video.id}/comments",
                json={"content": f"Comment {i}"},
                headers=auth_headers,
            )
            if i == 0:
                comment_id = response.json()["id"]
                client.post(
                    f"/api/comments/{comment_id}/resolve",
                    headers=auth_headers,
                )

        # Filter for unresolved only
        response = client.get(
            f"/api/videos/{video.id}/comments?is_resolved=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert all(not c["is_resolved"] for c in data["items"])


class TestCommentMentions:
    """Tests for parsing and handling mentions."""

    def test_parse_mentions_from_content(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test mentions are automatically parsed from comment content."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": f"Hey @{second_user.email}, what do you think?"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert str(second_user.id) in data["mentions"]

    def test_multiple_mentions(
        self, client: TestClient, auth_headers: dict, video, second_user
    ):
        """Test parsing multiple mentions in one comment."""
        # Create third user
        third_user = UserFactory(email="third@example.com", verified=True)

        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={
                "content": f"@{second_user.email} and @{third_user.email}, check this!"
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["mentions"]) == 2

    def test_invalid_mention_ignored(
        self, client: TestClient, auth_headers: dict, video
    ):
        """Test invalid mentions are gracefully ignored."""
        response = client.post(
            f"/api/videos/{video.id}/comments",
            json={"content": "@nonexistent@example.com what do you think?"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["mentions"]) == 0
