"""Tests for Permission Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    UserFactory,
    VideoFactory,
    OrganizationFactory,
    TeamMemberFactory,
    VideoShareFactory,
)


@pytest.fixture
def user(db_session: AsyncSession):
    """Create a test user."""
    user = UserFactory(email="user@example.com", verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def video_owner(db_session: AsyncSession):
    """Create a video owner user."""
    owner = UserFactory(email="owner@example.com", verified=True)
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)
    return owner


@pytest.fixture
def video(db_session: AsyncSession, video_owner):
    """Create a test video."""
    video = VideoFactory(user_id=video_owner.id, title="Test Video")
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def redis_mock():
    """Mock Redis client."""
    return MagicMock()


class TestCanViewVideo:
    """Tests for can_view_video permission checks."""

    @pytest.mark.asyncio
    async def test_owner_can_view(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test video owner can always view their video."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_view_video(video.id, video_owner.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_non_owner_cannot_view_private_video(
        self, db_session: AsyncSession, user, video
    ):
        """Test non-owner cannot view private video without share."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_view_video(video.id, user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_user_with_direct_share_can_view(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test user with direct share can view video."""
        # Create share
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_view_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_org_admin_can_view_org_video(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test organization admin can view videos owned by org members."""
        # Create organization
        org = OrganizationFactory(owner_id=user.id, name="Test Org")
        db_session.add(org)

        # Add video owner as org member
        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=video_owner.id,
            role="editor",
        )
        db_session.add(member)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_view_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_org_member_can_view_shared_org_video(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test org member can view video shared with organization."""
        # Create organization
        org = OrganizationFactory(owner_id=video_owner.id, name="Test Org")
        db_session.add(org)

        # Add user as org member
        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=user.id,
            role="viewer",
        )
        db_session.add(member)

        # Share video with organization
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_organization_id=org.id,
            share_type="team",
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_view_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_public_link_allows_view(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test public link allows anyone to view."""
        # Create public share link
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            share_type="public_link",
            is_public=True,
            public_token=str(uuid4()),
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        # Pass public token instead of user ID
        result = await service.can_view_video_by_token(video.id, share.public_token)

        assert result is True


class TestCanEditVideo:
    """Tests for can_edit_video permission checks."""

    @pytest.mark.asyncio
    async def test_owner_can_edit(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test video owner can edit their video."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, video_owner.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_viewer_cannot_edit(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test user with viewer permission cannot edit."""
        # Create viewer share
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_editor_can_edit(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test user with editor permission can edit."""
        # Create editor share
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="editor",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_org_admin_can_edit_org_video(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test org admin can edit videos from org members."""
        # Create organization with user as admin
        org = OrganizationFactory(owner_id=user.id, name="Test Org")
        db_session.add(org)

        # Add video owner as org member
        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=video_owner.id,
            role="editor",
        )
        db_session.add(member)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_non_editor_cannot_edit(
        self, db_session: AsyncSession, user, video
    ):
        """Test user without any permission cannot edit."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, user.id)

        assert result is False


class TestCanDeleteVideo:
    """Tests for can_delete_video permission checks."""

    @pytest.mark.asyncio
    async def test_owner_can_delete(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test video owner can delete their video."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_delete_video(video.id, video_owner.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_editor_cannot_delete(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test editor cannot delete video (only owner can)."""
        # Create editor share
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="editor",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_delete_video(video.id, user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_org_owner_can_delete_org_video(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test org owner can delete videos from org members."""
        # Create organization with user as owner
        org = OrganizationFactory(owner_id=user.id, name="Test Org")
        db_session.add(org)

        # Add video owner as org member
        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=video_owner.id,
            role="editor",
        )
        db_session.add(member)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_delete_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete(
        self, db_session: AsyncSession, user, video
    ):
        """Test non-owner cannot delete video."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_delete_video(video.id, user.id)

        assert result is False


class TestCanShareVideo:
    """Tests for can_share_video permission checks."""

    @pytest.mark.asyncio
    async def test_owner_can_share(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test video owner can share their video."""
        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_share_video(video.id, video_owner.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_editor_can_share_if_enabled(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test editor can share if settings allow."""
        # Create editor share with share permission
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="editor",
            settings={"allow_reshare": True},
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_share_video(video.id, user.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_viewer_cannot_share(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test viewer cannot share video."""
        # Create viewer share
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_share_video(video.id, user.id)

        assert result is False


class TestPermissionResolutionPriority:
    """Tests for permission resolution priority."""

    @pytest.mark.asyncio
    async def test_owner_permission_highest_priority(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test owner permission overrides all other permissions."""
        # Even if owner is also a viewer in an org, they can still edit
        org = OrganizationFactory(owner_id=str(uuid4()), name="Test Org")
        db_session.add(org)

        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=video_owner.id,
            role="viewer",  # Limited role
        )
        db_session.add(member)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, video_owner.id)

        assert result is True

    @pytest.mark.asyncio
    async def test_direct_share_overrides_org_permission(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test direct share permission overrides org permission."""
        # Create org with viewer permission
        org = OrganizationFactory(owner_id=video_owner.id, name="Test Org")
        db_session.add(org)

        member = TeamMemberFactory(
            organization_id=org.id,
            user_id=user.id,
            role="viewer",
        )
        db_session.add(member)

        org_share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_organization_id=org.id,
            share_type="team",
            permission="viewer",
        )
        db_session.add(org_share)

        # Create direct share with editor permission
        direct_share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="editor",
        )
        db_session.add(direct_share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        result = await service.can_edit_video(video.id, user.id)

        # Should have editor permission from direct share
        assert result is True


class TestPermissionCaching:
    """Tests for Redis permission caching."""

    @pytest.mark.asyncio
    @patch("app.services.permission_service.redis_client")
    async def test_cache_hit_returns_cached_permission(
        self, mock_redis, db_session: AsyncSession, video_owner, video
    ):
        """Test cached permission is returned on cache hit."""
        # Setup mock Redis to return cached value
        mock_redis.get = AsyncMock(return_value=b"true")

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session, redis=mock_redis)
        result = await service.can_view_video(video.id, video_owner.id)

        assert result is True
        # Should have called Redis get
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.permission_service.redis_client")
    async def test_cache_miss_queries_db_and_caches(
        self, mock_redis, db_session: AsyncSession, video_owner, video
    ):
        """Test cache miss queries database and stores result."""
        # Setup mock Redis to return None (cache miss)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session, redis=mock_redis)
        result = await service.can_view_video(video.id, video_owner.id)

        assert result is True
        # Should have tried to get from cache
        mock_redis.get.assert_called_once()
        # Should have stored result in cache
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.permission_service.redis_client")
    async def test_cache_invalidated_on_permission_change(
        self, mock_redis, db_session: AsyncSession, user, video_owner, video
    ):
        """Test cache is invalidated when permissions change."""
        mock_redis.delete = AsyncMock()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session, redis=mock_redis)

        # Add new share (permission change)
        share = VideoShareFactory(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="editor",
        )
        db_session.add(share)
        db_session.commit()

        # Invalidate cache
        await service.invalidate_video_permissions_cache(video.id)

        # Should have deleted cache keys
        mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_permission_check_without_redis(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test permission checks work without Redis (fallback)."""
        from app.services.permission_service import PermissionService

        # Create service without Redis
        service = PermissionService(db_session, redis=None)
        result = await service.can_view_video(video.id, video_owner.id)

        # Should still work by querying database
        assert result is True


class TestBulkPermissionChecks:
    """Tests for checking permissions on multiple videos."""

    @pytest.mark.asyncio
    async def test_can_view_multiple_videos(
        self, db_session: AsyncSession, video_owner
    ):
        """Test checking view permissions for multiple videos."""
        # Create multiple videos
        videos = []
        for i in range(3):
            video = VideoFactory(user_id=video_owner.id, title=f"Video {i}")
            db_session.add(video)
            videos.append(video)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        video_ids = [v.id for v in videos]
        results = await service.can_view_videos_bulk(video_ids, video_owner.id)

        # Should have permission for all owned videos
        assert len(results) == 3
        assert all(results.values())

    @pytest.mark.asyncio
    async def test_bulk_check_mixed_permissions(
        self, db_session: AsyncSession, user, video_owner
    ):
        """Test bulk check with mixed permissions."""
        # Create videos with different permissions
        video1 = VideoFactory(user_id=video_owner.id, title="Video 1")
        video2 = VideoFactory(user_id=video_owner.id, title="Video 2")
        db_session.add(video1)
        db_session.add(video2)

        # Share only video1 with user
        share = VideoShareFactory(
            video_id=video1.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            share_type="user",
            permission="viewer",
        )
        db_session.add(share)
        db_session.commit()

        from app.services.permission_service import PermissionService

        service = PermissionService(db_session)
        results = await service.can_view_videos_bulk(
            [video1.id, video2.id], user.id
        )

        # Should have permission for video1, but not video2
        assert results[video1.id] is True
        assert results[video2.id] is False
