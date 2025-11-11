"""Tests for Collaboration WebSocket endpoints."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import WebSocket
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.factories import UserFactory, VideoFactory


@pytest.fixture
def user(db_session: AsyncSession):
    """Create a test user."""
    user = UserFactory(email="user@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_token(user) -> str:
    """Create auth token for user."""
    return create_access_token({"sub": str(user.id)})


@pytest.fixture
def second_user(db_session: AsyncSession):
    """Create a second test user."""
    user = UserFactory(email="user2@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user_token(second_user) -> str:
    """Create auth token for second user."""
    return create_access_token({"sub": str(second_user.id)})


@pytest.fixture
def video(db_session: AsyncSession, user):
    """Create a test video."""
    video = VideoFactory(user_id=user.id, title="Test Video")
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    @pytest.mark.asyncio
    async def test_connect_with_valid_token(
        self, client: TestClient, user_token: str, video
    ):
        """Test successful WebSocket connection with valid token."""
        with patch("app.api.websocket.collaboration.ConnectionManager") as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.connect = AsyncMock()

            # Simulate WebSocket connection
            ws_url = f"/ws/videos/{video.id}?token={user_token}"

            # Note: TestClient doesn't support WebSocket directly,
            # so we test the connection manager instead
            from app.api.websocket.collaboration import ConnectionManager

            manager = ConnectionManager()
            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            await manager.connect(mock_ws, str(video.id), str(user_token))

            # Should have accepted connection
            mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_without_token_fails(
        self, mock_websocket, video
    ):
        """Test WebSocket connection without token fails."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        with pytest.raises(Exception):  # Should raise authentication error
            await manager.connect(mock_websocket, str(video.id), None)

    @pytest.mark.asyncio
    async def test_connect_with_invalid_token_fails(
        self, mock_websocket, video
    ):
        """Test WebSocket connection with invalid token fails."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()
        invalid_token = "invalid.jwt.token"

        with pytest.raises(Exception):  # Should raise authentication error
            await manager.connect(mock_websocket, str(video.id), invalid_token)

    @pytest.mark.asyncio
    async def test_connect_without_video_permission_fails(
        self, mock_websocket, user_token, second_user
    ):
        """Test connecting to video without permission fails."""
        # Create video owned by different user
        video = VideoFactory(user_id=str(uuid4()), title="Private Video")

        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        with pytest.raises(Exception):  # Should raise permission error
            await manager.connect(mock_websocket, str(video.id), user_token)


class TestCommentBroadcast:
    """Tests for broadcasting comments via WebSocket."""

    @pytest.mark.asyncio
    async def test_broadcast_new_comment(
        self, mock_websocket, user_token, video, user
    ):
        """Test broadcasting new comment to all connected clients."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect first user
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Broadcast comment
        comment_data = {
            "id": str(uuid4()),
            "content": "New comment",
            "user_id": str(user.id),
            "video_id": str(video.id),
            "timestamp": 45.5,
        }

        await manager.broadcast_comment(str(video.id), comment_data)

        # Should have sent message to connected client
        mock_websocket.send_json.assert_called()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "comment"
        assert sent_data["data"] == comment_data

    @pytest.mark.asyncio
    async def test_broadcast_comment_to_multiple_clients(
        self, user_token, second_user_token, video
    ):
        """Test comment broadcast reaches multiple connected clients."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Create mock WebSockets for two users
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        # Connect both users
        await manager.connect(ws1, str(video.id), user_token)
        await manager.connect(ws2, str(video.id), second_user_token)

        # Broadcast comment
        comment_data = {"id": str(uuid4()), "content": "Test comment"}
        await manager.broadcast_comment(str(video.id), comment_data)

        # Both clients should receive the message
        ws1.send_json.assert_called()
        ws2.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_comment_only_to_video_viewers(
        self, user_token, second_user_token, video
    ):
        """Test comment only broadcast to users viewing the same video."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Create another video
        other_video = VideoFactory(user_id=str(uuid4()), title="Other Video")

        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        # Connect user1 to video1, user2 to video2
        await manager.connect(ws1, str(video.id), user_token)
        await manager.connect(ws2, str(other_video.id), second_user_token)

        # Broadcast comment to video1
        comment_data = {"id": str(uuid4()), "content": "Test comment"}
        await manager.broadcast_comment(str(video.id), comment_data)

        # Only ws1 should receive the message
        ws1.send_json.assert_called()
        ws2.send_json.assert_not_called()


class TestActiveUsersTracking:
    """Tests for tracking active users on video."""

    @pytest.mark.asyncio
    async def test_track_active_users(
        self, mock_websocket, user_token, video, user
    ):
        """Test active users are tracked when they connect."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect user
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Get active users
        active_users = await manager.get_active_users(str(video.id))

        assert len(active_users) == 1
        assert active_users[0]["user_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_remove_user_on_disconnect(
        self, mock_websocket, user_token, video
    ):
        """Test user removed from active list on disconnect."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect user
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Disconnect
        await manager.disconnect(mock_websocket, str(video.id))

        # Get active users
        active_users = await manager.get_active_users(str(video.id))

        assert len(active_users) == 0

    @pytest.mark.asyncio
    async def test_broadcast_user_joined(
        self, user_token, second_user_token, video
    ):
        """Test broadcast when user joins video."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect first user
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        # Connect second user (should trigger broadcast)
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        # First user should be notified about second user joining
        # Check if any call was about user presence
        calls = ws1.send_json.call_args_list
        user_joined_calls = [
            call for call in calls
            if call[0][0].get("type") == "user_joined"
        ]
        assert len(user_joined_calls) > 0

    @pytest.mark.asyncio
    async def test_broadcast_user_left(
        self, user_token, second_user_token, video
    ):
        """Test broadcast when user leaves video."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect both users
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        # Reset call history
        ws1.send_json.reset_mock()

        # Disconnect second user
        await manager.disconnect(ws2, str(video.id))

        # First user should be notified
        calls = ws1.send_json.call_args_list
        user_left_calls = [
            call for call in calls
            if call[0][0].get("type") == "user_left"
        ]
        assert len(user_left_calls) > 0


class TestPresenceUpdates:
    """Tests for user presence and cursor position updates."""

    @pytest.mark.asyncio
    async def test_broadcast_cursor_position(
        self, user_token, second_user_token, video
    ):
        """Test broadcasting cursor/playhead position."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect both users
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        # User1 updates their position
        position_data = {"timestamp": 45.5, "is_playing": True}
        await manager.broadcast_presence(str(video.id), str(user_token), position_data)

        # User2 should receive the update
        ws2.send_json.assert_called()
        sent_data = ws2.send_json.call_args[0][0]
        assert sent_data["type"] == "presence_update"
        assert sent_data["data"]["timestamp"] == 45.5

    @pytest.mark.asyncio
    async def test_presence_update_not_sent_to_self(
        self, mock_websocket, user_token, video
    ):
        """Test presence update not sent back to originating user."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        await manager.connect(mock_websocket, str(video.id), user_token)

        # Reset mock to clear connection messages
        mock_websocket.send_json.reset_mock()

        # Update presence
        position_data = {"timestamp": 45.5}
        await manager.broadcast_presence(
            str(video.id), str(user_token), position_data, exclude_sender=True
        )

        # Should not have sent to self
        mock_websocket.send_json.assert_not_called()


class TestTypingIndicators:
    """Tests for typing indicators in comments."""

    @pytest.mark.asyncio
    async def test_broadcast_typing_indicator(
        self, user_token, second_user_token, video, user
    ):
        """Test broadcasting typing indicator."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect both users
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        # User1 starts typing
        await manager.broadcast_typing(str(video.id), str(user.id), is_typing=True)

        # User2 should receive the indicator
        ws2.send_json.assert_called()
        sent_data = ws2.send_json.call_args[0][0]
        assert sent_data["type"] == "typing"
        assert sent_data["data"]["user_id"] == str(user.id)
        assert sent_data["data"]["is_typing"] is True

    @pytest.mark.asyncio
    async def test_stop_typing_indicator(
        self, user_token, second_user_token, video, user
    ):
        """Test stopping typing indicator."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect both users
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        # User1 stops typing
        await manager.broadcast_typing(str(video.id), str(user.id), is_typing=False)

        # User2 should receive the update
        ws2.send_json.assert_called()
        sent_data = ws2.send_json.call_args[0][0]
        assert sent_data["data"]["is_typing"] is False


class TestConnectionLimits:
    """Tests for connection limits and management."""

    @pytest.mark.asyncio
    async def test_enforce_max_connections_per_video(
        self, video
    ):
        """Test maximum concurrent connections per video."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager(max_connections_per_video=2)

        # Connect two users (should succeed)
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        token1 = create_access_token({"sub": str(uuid4())})
        await manager.connect(ws1, str(video.id), token1)

        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        token2 = create_access_token({"sub": str(uuid4())})
        await manager.connect(ws2, str(video.id), token2)

        # Try to connect third user (should fail)
        ws3 = MagicMock(spec=WebSocket)
        ws3.accept = AsyncMock()
        ws3.close = AsyncMock()
        token3 = create_access_token({"sub": str(uuid4())})

        with pytest.raises(Exception):  # Should raise connection limit error
            await manager.connect(ws3, str(video.id), token3)

    @pytest.mark.asyncio
    async def test_connection_count_per_video(
        self, user_token, second_user_token, video
    ):
        """Test tracking connection count per video."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Initial count should be 0
        count = await manager.get_connection_count(str(video.id))
        assert count == 0

        # Connect first user
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        await manager.connect(ws1, str(video.id), user_token)

        count = await manager.get_connection_count(str(video.id))
        assert count == 1

        # Connect second user
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        await manager.connect(ws2, str(video.id), second_user_token)

        count = await manager.get_connection_count(str(video.id))
        assert count == 2


class TestReconnectionHandling:
    """Tests for handling reconnections and disconnections."""

    @pytest.mark.asyncio
    async def test_handle_unexpected_disconnect(
        self, mock_websocket, user_token, video
    ):
        """Test handling unexpected WebSocket disconnection."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect user
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Simulate unexpected disconnect
        mock_websocket.close.side_effect = Exception("Connection lost")

        # Should handle gracefully
        try:
            await manager.disconnect(mock_websocket, str(video.id))
        except Exception:
            pytest.fail("Should handle disconnect gracefully")

        # User should be removed from active list
        active_users = await manager.get_active_users(str(video.id))
        assert len(active_users) == 0

    @pytest.mark.asyncio
    async def test_allow_reconnection_after_disconnect(
        self, mock_websocket, user_token, video
    ):
        """Test user can reconnect after disconnecting."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Disconnect
        await manager.disconnect(mock_websocket, str(video.id))

        # Reconnect (should succeed)
        await manager.connect(mock_websocket, str(video.id), user_token)

        active_users = await manager.get_active_users(str(video.id))
        assert len(active_users) == 1

    @pytest.mark.asyncio
    async def test_cleanup_on_multiple_disconnects(
        self, mock_websocket, user_token, video
    ):
        """Test cleanup works even if disconnect called multiple times."""
        from app.api.websocket.collaboration import ConnectionManager

        manager = ConnectionManager()

        # Connect
        await manager.connect(mock_websocket, str(video.id), user_token)

        # Disconnect multiple times (should not error)
        await manager.disconnect(mock_websocket, str(video.id))
        await manager.disconnect(mock_websocket, str(video.id))

        # Should still be cleaned up properly
        active_users = await manager.get_active_users(str(video.id))
        assert len(active_users) == 0
