"""Sharing service for video collaboration."""

import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Organization,
    ShareAccessType,
    SharePermissionLevel,
    User,
    Video,
    VideoShare,
)


class SharingService:
    """Service for managing video shares."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_share_token(self) -> str:
        """Generate a cryptographically secure share token.

        Returns:
            32-character URL-safe token
        """
        return secrets.token_urlsafe(32)[:32]

    async def create_video_share(
        self,
        video_id: UUID,
        shared_by: UUID,
        permission_level: SharePermissionLevel,
        access_type: ShareAccessType,
        shared_with_user_id: UUID | None = None,
        shared_with_organization_id: UUID | None = None,
        expires_at: datetime | None = None,
        message: str | None = None,
    ) -> VideoShare:
        """Create a video share.

        Args:
            video_id: Video to share
            shared_by: User sharing the video
            permission_level: Permission level to grant
            access_type: Type of share (direct, link, organization)
            shared_with_user_id: User to share with (optional)
            shared_with_organization_id: Organization to share with (optional)
            expires_at: Expiration timestamp (optional)
            message: Optional message from sharer

        Returns:
            Created VideoShare

        Raises:
            ValueError: If validation fails
        """
        # Validate video exists
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Validate recipient
        if access_type == ShareAccessType.DIRECT and not shared_with_user_id:
            raise ValueError("Direct share requires shared_with_user_id")

        if access_type == ShareAccessType.ORGANIZATION and not shared_with_organization_id:
            raise ValueError("Organization share requires shared_with_organization_id")

        if shared_with_user_id:
            user_result = await self.db.execute(select(User).where(User.id == shared_with_user_id))
            if not user_result.scalar_one_or_none():
                raise ValueError("User not found")

        if shared_with_organization_id:
            org_result = await self.db.execute(
                select(Organization).where(Organization.id == shared_with_organization_id)
            )
            if not org_result.scalar_one_or_none():
                raise ValueError("Organization not found")

        # Generate unique token
        share_token = self.generate_share_token()

        # Ensure token is unique
        while True:
            existing = await self.db.execute(
                select(VideoShare).where(VideoShare.share_token == share_token)
            )
            if not existing.scalar_one_or_none():
                break
            share_token = self.generate_share_token()

        # Create share
        share = VideoShare(
            video_id=video_id,
            shared_by=shared_by,
            shared_with_user_id=shared_with_user_id,
            shared_with_organization_id=shared_with_organization_id,
            permission_level=permission_level,
            access_type=access_type,
            share_token=share_token,
            expires_at=expires_at,
            is_active=True,
            access_count=0,
            message=message,
        )

        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)

        return share

    async def get_video_shares(
        self, video_id: UUID, user_id: UUID
    ) -> list[VideoShare]:
        """Get all shares for a video.

        Args:
            video_id: Video ID
            user_id: User ID (must have permission to view shares)

        Returns:
            List of VideoShare objects
        """
        # Verify user has access to video
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Only owner can see all shares
        if video.user_id != user_id:
            raise ValueError("Only video owner can view shares")

        result = await self.db.execute(
            select(VideoShare)
            .where(VideoShare.video_id == video_id)
            .order_by(VideoShare.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_share_by_token(self, share_token: str) -> VideoShare | None:
        """Get a share by its token.

        Args:
            share_token: Share token

        Returns:
            VideoShare or None if not found
        """
        result = await self.db.execute(
            select(VideoShare).where(VideoShare.share_token == share_token)
        )
        return result.scalar_one_or_none()

    async def revoke_share(self, share_id: UUID, user_id: UUID) -> VideoShare:
        """Revoke a video share.

        Args:
            share_id: Share ID
            user_id: User revoking the share (must be owner or sharer)

        Returns:
            Revoked VideoShare

        Raises:
            ValueError: If share not found or user doesn't have permission
        """
        result = await self.db.execute(select(VideoShare).where(VideoShare.id == share_id))
        share = result.scalar_one_or_none()
        if not share:
            raise ValueError("Share not found")

        # Verify user has permission
        video_result = await self.db.execute(select(Video).where(Video.id == share.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        if video.user_id != user_id and share.shared_by != user_id:
            raise ValueError("Only video owner or sharer can revoke share")

        # Mark as inactive
        share.is_active = False
        share.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(share)

        return share

    async def access_shared_video(
        self, share_token: str, password: str | None = None
    ) -> tuple[VideoShare, Video]:
        """Access a video via share link.

        Args:
            share_token: Share token
            password: Optional password for password-protected shares

        Returns:
            Tuple of (VideoShare, Video)

        Raises:
            ValueError: If share is invalid, expired, or password incorrect
        """
        # Get share
        share = await self.get_share_by_token(share_token)
        if not share:
            raise ValueError("Invalid share link")

        # Check if active
        if not share.is_active:
            raise ValueError("This share has been revoked")

        # Check expiration
        if share.expires_at and share.expires_at < datetime.utcnow():
            raise ValueError("This share has expired")

        # Get video
        video_result = await self.db.execute(select(Video).where(Video.id == share.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Update access tracking
        share.access_count += 1
        share.last_accessed_at = datetime.utcnow()
        await self.db.commit()

        return share, video

    async def update_share(
        self,
        share_id: UUID,
        user_id: UUID,
        permission_level: SharePermissionLevel | None = None,
        expires_at: datetime | None = None,
        message: str | None = None,
    ) -> VideoShare:
        """Update a video share.

        Args:
            share_id: Share ID
            user_id: User updating the share (must be owner or sharer)
            permission_level: New permission level (optional)
            expires_at: New expiration (optional)
            message: New message (optional)

        Returns:
            Updated VideoShare

        Raises:
            ValueError: If share not found or user doesn't have permission
        """
        result = await self.db.execute(select(VideoShare).where(VideoShare.id == share_id))
        share = result.scalar_one_or_none()
        if not share:
            raise ValueError("Share not found")

        # Verify user has permission
        video_result = await self.db.execute(select(Video).where(Video.id == share.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        if video.user_id != user_id and share.shared_by != user_id:
            raise ValueError("Only video owner or sharer can update share")

        # Update fields
        if permission_level is not None:
            share.permission_level = permission_level
        if expires_at is not None:
            share.expires_at = expires_at
        if message is not None:
            share.message = message

        share.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(share)

        return share

    async def cleanup_expired_shares(self) -> int:
        """Mark expired shares as inactive.

        Returns:
            Number of shares marked as inactive
        """
        result = await self.db.execute(
            select(VideoShare)
            .where(VideoShare.is_active.is_(True))
            .where(VideoShare.expires_at < datetime.utcnow())
        )
        expired_shares = list(result.scalars().all())

        for share in expired_shares:
            share.is_active = False
            share.updated_at = datetime.utcnow()

        if expired_shares:
            await self.db.commit()

        return len(expired_shares)

    async def get_user_shares(self, user_id: UUID) -> list[VideoShare]:
        """Get all shares for a user (shared with them).

        Args:
            user_id: User ID

        Returns:
            List of VideoShare objects
        """
        result = await self.db.execute(
            select(VideoShare)
            .where(VideoShare.shared_with_user_id == user_id)
            .where(VideoShare.is_active.is_(True))
            .where(
                (VideoShare.expires_at.is_(None)) | (VideoShare.expires_at > datetime.utcnow())
            )
            .order_by(VideoShare.created_at.desc())
        )
        return list(result.scalars().all())
