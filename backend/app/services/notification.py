"""Notification service for in-app notifications."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Comment,
    Notification,
    NotificationType,
    User,
    Video,
    VideoShare,
)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        related_entity_type: str,
        related_entity_id: UUID,
        title: str,
        message: str,
        action_url: str | None = None,
    ) -> Notification:
        """Create a notification.

        Args:
            user_id: User to notify
            notification_type: Type of notification
            related_entity_type: Entity type (e.g., "video_share", "comment")
            related_entity_id: Entity ID
            title: Notification title
            message: Notification message
            action_url: URL to navigate to (optional)

        Returns:
            Created Notification
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            title=title,
            message=message,
            action_url=action_url,
            is_read=False,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def create_share_notification(
        self, share_id: UUID
    ) -> list[Notification]:
        """Create notifications for a video share.

        Args:
            share_id: VideoShare ID

        Returns:
            List of created notifications
        """
        # Get share details
        result = await self.db.execute(select(VideoShare).where(VideoShare.id == share_id))
        share = result.scalar_one_or_none()
        if not share:
            raise ValueError("Share not found")

        # Get video details
        video_result = await self.db.execute(select(Video).where(Video.id == share.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Get sharer details
        sharer_result = await self.db.execute(select(User).where(User.id == share.shared_by))
        sharer = sharer_result.scalar_one_or_none()

        sharer_name = sharer.full_name if sharer and sharer.full_name else "Someone"

        notifications = []

        # Create notification for shared user
        if share.shared_with_user_id:
            notification = await self.create_notification(
                user_id=share.shared_with_user_id,
                notification_type=NotificationType.SHARE,
                related_entity_type="video_share",
                related_entity_id=share_id,
                title=f"{sharer_name} shared a video with you",
                message=f'"{video.title}" has been shared with you ({share.permission_level} access)',
                action_url=f"/videos/{video.id}",
            )
            notifications.append(notification)

        # Create notifications for organization members
        if share.shared_with_organization_id:
            # Get all active members of the organization (except the sharer)
            from app.models import TeamMember, MemberStatus

            members_result = await self.db.execute(
                select(TeamMember)
                .where(TeamMember.organization_id == share.shared_with_organization_id)
                .where(TeamMember.status == MemberStatus.ACTIVE)
                .where(TeamMember.user_id != share.shared_by)
            )
            members = list(members_result.scalars().all())

            for member in members:
                notification = await self.create_notification(
                    user_id=member.user_id,
                    notification_type=NotificationType.SHARE,
                    related_entity_type="video_share",
                    related_entity_id=share_id,
                    title=f"{sharer_name} shared a video with your team",
                    message=f'"{video.title}" has been shared with your organization ({share.permission_level} access)',
                    action_url=f"/videos/{video.id}",
                )
                notifications.append(notification)

        return notifications

    async def create_comment_notification(
        self, comment_id: UUID
    ) -> list[Notification]:
        """Create notifications for a comment.

        Args:
            comment_id: Comment ID

        Returns:
            List of created notifications
        """
        # Get comment details
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Get video details
        video_result = await self.db.execute(select(Video).where(Video.id == comment.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Get commenter details
        commenter_result = await self.db.execute(select(User).where(User.id == comment.user_id))
        commenter = commenter_result.scalar_one_or_none()

        commenter_name = commenter.full_name if commenter and commenter.full_name else "Someone"

        notifications = []

        # Notify video owner (if not the commenter)
        if video.user_id != comment.user_id:
            notification = await self.create_notification(
                user_id=video.user_id,
                notification_type=NotificationType.COMMENT,
                related_entity_type="comment",
                related_entity_id=comment_id,
                title=f"{commenter_name} commented on your video",
                message=f'New comment on "{video.title}"',
                action_url=f"/videos/{video.id}?comment={comment_id}",
            )
            notifications.append(notification)

        # If it's a reply, notify parent comment author
        if comment.parent_comment_id:
            parent_result = await self.db.execute(
                select(Comment).where(Comment.id == comment.parent_comment_id)
            )
            parent_comment = parent_result.scalar_one_or_none()

            if parent_comment and parent_comment.user_id != comment.user_id:
                notification = await self.create_notification(
                    user_id=parent_comment.user_id,
                    notification_type=NotificationType.COMMENT,
                    related_entity_type="comment",
                    related_entity_id=comment_id,
                    title=f"{commenter_name} replied to your comment",
                    message=f'Reply on "{video.title}"',
                    action_url=f"/videos/{video.id}?comment={comment_id}",
                )
                notifications.append(notification)

        return notifications

    async def create_mention_notifications(
        self, comment_id: UUID, mentioned_user_ids: list[UUID]
    ) -> list[Notification]:
        """Create notifications for mentioned users.

        Args:
            comment_id: Comment ID
            mentioned_user_ids: List of user IDs mentioned

        Returns:
            List of created notifications
        """
        # Get comment details
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Get video details
        video_result = await self.db.execute(select(Video).where(Video.id == comment.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Get commenter details
        commenter_result = await self.db.execute(select(User).where(User.id == comment.user_id))
        commenter = commenter_result.scalar_one_or_none()

        commenter_name = commenter.full_name if commenter and commenter.full_name else "Someone"

        notifications = []

        for mentioned_user_id in mentioned_user_ids:
            # Don't notify the commenter if they mentioned themselves
            if mentioned_user_id == comment.user_id:
                continue

            notification = await self.create_notification(
                user_id=mentioned_user_id,
                notification_type=NotificationType.MENTION,
                related_entity_type="comment",
                related_entity_id=comment_id,
                title=f"{commenter_name} mentioned you in a comment",
                message=f'You were mentioned in a comment on "{video.title}"',
                action_url=f"/videos/{video.id}?comment={comment_id}",
            )
            notifications.append(notification)

        return notifications

    async def create_version_notification(
        self, version_id: UUID, affected_user_ids: list[UUID]
    ) -> list[Notification]:
        """Create notifications for a new version.

        Args:
            version_id: Version ID
            affected_user_ids: List of user IDs to notify

        Returns:
            List of created notifications
        """
        from app.models import Version

        # Get version details
        result = await self.db.execute(select(Version).where(Version.id == version_id))
        version = result.scalar_one_or_none()
        if not version:
            raise ValueError("Version not found")

        # Get video details
        video_result = await self.db.execute(select(Video).where(Video.id == version.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Get creator details
        creator_result = await self.db.execute(select(User).where(User.id == version.created_by))
        creator = creator_result.scalar_one_or_none()

        creator_name = creator.full_name if creator and creator.full_name else "Someone"

        notifications = []

        for user_id in affected_user_ids:
            # Don't notify the creator
            if user_id == version.created_by:
                continue

            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.VERSION,
                related_entity_type="version",
                related_entity_id=version_id,
                title=f"{creator_name} created a new version",
                message=f'New version (v{version.version_number}) of "{video.title}": {version.change_summary}',
                action_url=f"/videos/{video.id}/versions/{version_id}",
            )
            notifications.append(notification)

        return notifications

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """Get notifications for a user.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            Tuple of (notifications, total_count)
        """
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        # Get total count
        count_result = await self.db.execute(query)
        total_count = len(list(count_result.scalars().all()))

        # Get paginated results
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total_count

    async def mark_notification_read(
        self, notification_id: UUID, user_id: UUID
    ) -> Notification:
        """Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (must own the notification)

        Returns:
            Updated Notification

        Raises:
            ValueError: If notification not found or doesn't belong to user
        """
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise ValueError("Notification not found")

        if notification.user_id != user_id:
            raise ValueError("Notification doesn't belong to user")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_all_notifications_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
        )
        notifications = list(result.scalars().all())

        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()

        if notifications:
            await self.db.commit()

        return len(notifications)

    async def delete_notification(
        self, notification_id: UUID, user_id: UUID
    ) -> None:
        """Delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (must own the notification)

        Raises:
            ValueError: If notification not found or doesn't belong to user
        """
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise ValueError("Notification not found")

        if notification.user_id != user_id:
            raise ValueError("Notification doesn't belong to user")

        await self.db.delete(notification)
        await self.db.commit()

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
        )
        notifications = list(result.scalars().all())
        return len(notifications)
