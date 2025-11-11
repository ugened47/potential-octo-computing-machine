"""Permission service for role-based access control."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.cache import delete_cache, get_cache, invalidate_pattern, set_cache
from app.models import (
    MemberRole,
    MemberStatus,
    Organization,
    TeamMember,
    Video,
    VideoPermission,
    VideoShare,
)


class PermissionResult:
    """Result of a permission check."""

    def __init__(self, allowed: bool, reason: str = ""):
        self.allowed = allowed
        self.reason = reason

    def __bool__(self) -> bool:
        return self.allowed


class PermissionService:
    """Service for managing permissions and access control."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Cache TTL: 5 minutes
    CACHE_TTL = 300

    async def can_view_video(self, user_id: UUID, video_id: UUID) -> PermissionResult:
        """Check if user can view a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Check cache first
        cache_key = f"permission:{user_id}:{video_id}:view"
        cached = await get_cache(cache_key)
        if cached is not None:
            return PermissionResult(cached["allowed"], cached["reason"])

        # Check 1: User is video owner
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            return PermissionResult(False, "Video not found")

        if video.user_id == user_id:
            result = PermissionResult(True, "Owner")
            await set_cache(cache_key, {"allowed": True, "reason": "Owner"}, self.CACHE_TTL)
            return result

        # Check 2: Direct video permission
        perm_result = await self.db.execute(
            select(VideoPermission)
            .where(VideoPermission.video_id == video_id)
            .where(VideoPermission.user_id == user_id)
            .where(
                (VideoPermission.expires_at.is_(None))
                | (VideoPermission.expires_at > datetime.utcnow())
            )
        )
        permission = perm_result.scalar_one_or_none()
        if permission:
            result = PermissionResult(True, f"Direct permission: {permission.permission_level}")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": f"Direct permission: {permission.permission_level}"},
                self.CACHE_TTL,
            )
            return result

        # Check 3: Video shared with user
        share_result = await self.db.execute(
            select(VideoShare)
            .where(VideoShare.video_id == video_id)
            .where(VideoShare.shared_with_user_id == user_id)
            .where(VideoShare.is_active.is_(True))
            .where(
                (VideoShare.expires_at.is_(None)) | (VideoShare.expires_at > datetime.utcnow())
            )
        )
        share = share_result.scalar_one_or_none()
        if share:
            result = PermissionResult(True, f"Shared: {share.permission_level}")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": f"Shared: {share.permission_level}"},
                self.CACHE_TTL,
            )
            return result

        # Check 4: Video shared with user's organizations
        org_result = await self.db.execute(
            select(VideoShare)
            .join(TeamMember, TeamMember.organization_id == VideoShare.shared_with_organization_id)
            .where(VideoShare.video_id == video_id)
            .where(TeamMember.user_id == user_id)
            .where(TeamMember.status == MemberStatus.ACTIVE)
            .where(VideoShare.is_active.is_(True))
            .where(
                (VideoShare.expires_at.is_(None)) | (VideoShare.expires_at > datetime.utcnow())
            )
        )
        org_share = org_result.scalar_one_or_none()
        if org_share:
            result = PermissionResult(True, f"Organization share: {org_share.permission_level}")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": f"Organization share: {org_share.permission_level}"},
                self.CACHE_TTL,
            )
            return result

        # Check 5: Organization permission (video owned by organization member)
        org_perm_result = await self.db.execute(
            select(VideoPermission)
            .join(TeamMember, TeamMember.organization_id == VideoPermission.organization_id)
            .where(VideoPermission.video_id == video_id)
            .where(TeamMember.user_id == user_id)
            .where(TeamMember.status == MemberStatus.ACTIVE)
            .where(
                (VideoPermission.expires_at.is_(None))
                | (VideoPermission.expires_at > datetime.utcnow())
            )
        )
        org_permission = org_perm_result.scalar_one_or_none()
        if org_permission:
            result = PermissionResult(
                True, f"Organization permission: {org_permission.permission_level}"
            )
            await set_cache(
                cache_key,
                {
                    "allowed": True,
                    "reason": f"Organization permission: {org_permission.permission_level}",
                },
                self.CACHE_TTL,
            )
            return result

        # Default: deny access
        result = PermissionResult(False, "No access")
        await set_cache(cache_key, {"allowed": False, "reason": "No access"}, self.CACHE_TTL)
        return result

    async def can_edit_video(self, user_id: UUID, video_id: UUID) -> PermissionResult:
        """Check if user can edit a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Check cache first
        cache_key = f"permission:{user_id}:{video_id}:edit"
        cached = await get_cache(cache_key)
        if cached is not None:
            return PermissionResult(cached["allowed"], cached["reason"])

        # Check 1: User is video owner
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            return PermissionResult(False, "Video not found")

        if video.user_id == user_id:
            result = PermissionResult(True, "Owner")
            await set_cache(cache_key, {"allowed": True, "reason": "Owner"}, self.CACHE_TTL)
            return result

        # Check 2: Direct edit permission
        perm_result = await self.db.execute(
            select(VideoPermission)
            .where(VideoPermission.video_id == video_id)
            .where(VideoPermission.user_id == user_id)
            .where(VideoPermission.permission_level.in_(["edit", "admin"]))
            .where(
                (VideoPermission.expires_at.is_(None))
                | (VideoPermission.expires_at > datetime.utcnow())
            )
        )
        permission = perm_result.scalar_one_or_none()
        if permission:
            result = PermissionResult(True, f"Direct permission: {permission.permission_level}")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": f"Direct permission: {permission.permission_level}"},
                self.CACHE_TTL,
            )
            return result

        # Check 3: Shared with edit permission
        share_result = await self.db.execute(
            select(VideoShare)
            .where(VideoShare.video_id == video_id)
            .where(VideoShare.shared_with_user_id == user_id)
            .where(VideoShare.permission_level == "edit")
            .where(VideoShare.is_active.is_(True))
            .where(
                (VideoShare.expires_at.is_(None)) | (VideoShare.expires_at > datetime.utcnow())
            )
        )
        share = share_result.scalar_one_or_none()
        if share:
            result = PermissionResult(True, "Shared with edit permission")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": "Shared with edit permission"},
                self.CACHE_TTL,
            )
            return result

        # Check 4: Organization admin
        org_result = await self.db.execute(
            select(TeamMember)
            .join(VideoShare, VideoShare.shared_with_organization_id == TeamMember.organization_id)
            .where(VideoShare.video_id == video_id)
            .where(TeamMember.user_id == user_id)
            .where(TeamMember.role.in_([MemberRole.ADMIN, MemberRole.EDITOR]))
            .where(TeamMember.status == MemberStatus.ACTIVE)
        )
        member = org_result.scalar_one_or_none()
        if member:
            result = PermissionResult(True, f"Organization {member.role}")
            await set_cache(
                cache_key,
                {"allowed": True, "reason": f"Organization {member.role}"},
                self.CACHE_TTL,
            )
            return result

        # Default: deny access
        result = PermissionResult(False, "No edit access")
        await set_cache(cache_key, {"allowed": False, "reason": "No edit access"}, self.CACHE_TTL)
        return result

    async def can_delete_video(self, user_id: UUID, video_id: UUID) -> PermissionResult:
        """Check if user can delete a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Only owner or org admin can delete
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            return PermissionResult(False, "Video not found")

        if video.user_id == user_id:
            return PermissionResult(True, "Owner")

        # Check if user is admin in video owner's organization
        # (This assumes videos can be owned by organizations in future)
        return PermissionResult(False, "Only owner can delete")

    async def can_comment_on_video(self, user_id: UUID, video_id: UUID) -> PermissionResult:
        """Check if user can comment on a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Can comment if can view
        view_result = await self.can_view_video(user_id, video_id)
        if view_result.allowed:
            return PermissionResult(True, f"Can view: {view_result.reason}")
        return PermissionResult(False, "Cannot view video")

    async def can_share_video(self, user_id: UUID, video_id: UUID) -> PermissionResult:
        """Check if user can share a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Can share if can edit
        edit_result = await self.can_edit_video(user_id, video_id)
        if edit_result.allowed:
            return PermissionResult(True, f"Can edit: {edit_result.reason}")
        return PermissionResult(False, "Cannot edit video")

    async def can_manage_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> PermissionResult:
        """Check if user can manage an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            PermissionResult with allowed status and reason
        """
        # Check if user is organization owner
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            return PermissionResult(False, "Organization not found")

        if org.owner_id == user_id:
            return PermissionResult(True, "Owner")

        # Check if user is admin
        member_result = await self.db.execute(
            select(TeamMember)
            .where(TeamMember.organization_id == organization_id)
            .where(TeamMember.user_id == user_id)
            .where(TeamMember.role == MemberRole.ADMIN)
            .where(TeamMember.status == MemberStatus.ACTIVE)
        )
        member = member_result.scalar_one_or_none()
        if member:
            return PermissionResult(True, "Admin")

        return PermissionResult(False, "Not an admin")

    async def get_user_role(
        self, user_id: UUID, organization_id: UUID
    ) -> MemberRole | None:
        """Get user's role in an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            User's role or None if not a member
        """
        # Check cache first
        cache_key = f"role:{user_id}:{organization_id}"
        cached = await get_cache(cache_key)
        if cached is not None:
            return MemberRole(cached)

        result = await self.db.execute(
            select(TeamMember)
            .where(TeamMember.organization_id == organization_id)
            .where(TeamMember.user_id == user_id)
            .where(TeamMember.status == MemberStatus.ACTIVE)
        )
        member = result.scalar_one_or_none()

        if member:
            await set_cache(cache_key, member.role.value, self.CACHE_TTL)
            return member.role

        return None

    async def get_video_permissions(
        self, user_id: UUID, video_id: UUID
    ) -> dict[str, Any]:
        """Get all permissions for a video.

        Args:
            user_id: User ID
            video_id: Video ID

        Returns:
            Dictionary with permission details
        """
        return {
            "can_view": (await self.can_view_video(user_id, video_id)).allowed,
            "can_edit": (await self.can_edit_video(user_id, video_id)).allowed,
            "can_delete": (await self.can_delete_video(user_id, video_id)).allowed,
            "can_comment": (await self.can_comment_on_video(user_id, video_id)).allowed,
            "can_share": (await self.can_share_video(user_id, video_id)).allowed,
        }

    async def invalidate_permission_cache(
        self, user_id: UUID | None = None, video_id: UUID | None = None
    ) -> None:
        """Invalidate permission cache.

        Args:
            user_id: User ID to invalidate cache for (optional)
            video_id: Video ID to invalidate cache for (optional)
        """
        if user_id and video_id:
            await invalidate_pattern(f"permission:{user_id}:{video_id}:*")
        elif user_id:
            await invalidate_pattern(f"permission:{user_id}:*")
        elif video_id:
            await invalidate_pattern(f"permission:*:{video_id}:*")
        else:
            await invalidate_pattern("permission:*")

    async def invalidate_role_cache(
        self, user_id: UUID | None = None, organization_id: UUID | None = None
    ) -> None:
        """Invalidate role cache.

        Args:
            user_id: User ID to invalidate cache for (optional)
            organization_id: Organization ID to invalidate cache for (optional)
        """
        if user_id and organization_id:
            await delete_cache(f"role:{user_id}:{organization_id}")
        elif user_id:
            await invalidate_pattern(f"role:{user_id}:*")
        elif organization_id:
            await invalidate_pattern(f"role:*:{organization_id}")
        else:
            await invalidate_pattern("role:*")
