"""Tests for Notification Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import UserFactory, VideoFactory, CommentFactory


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


class TestShareNotification:
    """Tests for video share notifications."""

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_user_on_video_share(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test notification sent when video is shared with user."""
        mock_send_email.return_value = AsyncMock()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_video_shared(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            permission="viewer",
        )

        # Should have sent email notification
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert user.email in str(call_args)
        assert video.title in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_share_notification_includes_sharer_name(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test share notification includes sharer's name."""
        mock_send_email.return_value = AsyncMock()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_video_shared(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            permission="editor",
        )

        call_args = mock_send_email.call_args
        # Should mention the sharer's name
        assert video_owner.full_name in str(call_args) or video_owner.email in str(call_args)

    @pytest.mark.asyncio
    async def test_share_notification_creates_in_app_notification(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test share creates in-app notification."""
        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        notification = await service.notify_video_shared(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            permission="viewer",
        )

        assert notification is not None
        assert notification.user_id == user.id
        assert notification.type == "video_shared"
        assert notification.video_id == video.id


class TestMentionNotification:
    """Tests for comment mention notifications."""

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_user_on_mention(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test notification sent when user is mentioned in comment."""
        mock_send_email.return_value = AsyncMock()

        # Create comment with mention
        comment = CommentFactory(
            video_id=video.id,
            user_id=video_owner.id,
            content=f"Hey @{user.email}, check this out!",
            mentions=[str(user.id)],
        )
        db_session.add(comment)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_comment_mention(
            comment_id=comment.id,
            mentioned_user_ids=[str(user.id)],
        )

        # Should have sent email notification
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert user.email in str(call_args)

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_mention_notification_multiple_users(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test notification sent to multiple mentioned users."""
        mock_send_email.return_value = AsyncMock()

        # Create another user
        user2 = UserFactory(email="user2@example.com", verified=True)
        db_session.add(user2)
        db_session.commit()
        db_session.refresh(user2)

        # Create comment with multiple mentions
        comment = CommentFactory(
            video_id=video.id,
            user_id=video_owner.id,
            content=f"@{user.email} and @{user2.email}, thoughts?",
            mentions=[str(user.id), str(user2.id)],
        )
        db_session.add(comment)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_comment_mention(
            comment_id=comment.id,
            mentioned_user_ids=[str(user.id), str(user2.id)],
        )

        # Should have sent notifications to both users
        assert mock_send_email.call_count == 2

    @pytest.mark.asyncio
    async def test_mention_notification_not_sent_to_commenter(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test user doesn't get notified when mentioning themselves."""
        # Create comment where user mentions themselves
        comment = CommentFactory(
            video_id=video.id,
            user_id=video_owner.id,
            content=f"Reminder for @{video_owner.email}",
            mentions=[str(video_owner.id)],
        )
        db_session.add(comment)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        notifications = await service.notify_comment_mention(
            comment_id=comment.id,
            mentioned_user_ids=[str(video_owner.id)],
        )

        # Should not create notification for self-mention
        assert len(notifications) == 0


class TestCommentNotification:
    """Tests for comment notifications."""

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_video_owner_on_comment(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test video owner notified when someone comments."""
        mock_send_email.return_value = AsyncMock()

        # Create comment from different user
        comment = CommentFactory(
            video_id=video.id,
            user_id=user.id,
            content="Great video!",
        )
        db_session.add(comment)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_new_comment(
            comment_id=comment.id,
            video_owner_id=video_owner.id,
        )

        # Should have sent email to video owner
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert video_owner.email in str(call_args)

    @pytest.mark.asyncio
    async def test_owner_not_notified_on_own_comment(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test video owner not notified for their own comments."""
        # Create comment from video owner
        comment = CommentFactory(
            video_id=video.id,
            user_id=video_owner.id,
            content="Thanks everyone!",
        )
        db_session.add(comment)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        notification = await service.notify_new_comment(
            comment_id=comment.id,
            video_owner_id=video_owner.id,
        )

        # Should not create notification
        assert notification is None

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_parent_comment_author_on_reply(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test parent comment author notified on reply."""
        mock_send_email.return_value = AsyncMock()

        # Create parent comment
        parent_comment = CommentFactory(
            video_id=video.id,
            user_id=user.id,
            content="Question about this video",
        )
        db_session.add(parent_comment)
        db_session.commit()

        # Create reply
        reply = CommentFactory(
            video_id=video.id,
            user_id=video_owner.id,
            content="Here's the answer",
            parent_comment_id=parent_comment.id,
        )
        db_session.add(reply)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_comment_reply(
            reply_id=reply.id,
            parent_comment_author_id=user.id,
        )

        # Should have sent email to parent comment author
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert user.email in str(call_args)


class TestVersionNotification:
    """Tests for version control notifications."""

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_on_new_version(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test collaborators notified when new version is created."""
        mock_send_email.return_value = AsyncMock()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_new_version(
            video_id=video.id,
            version_number=2,
            created_by_user_id=video_owner.id,
            collaborator_ids=[str(user.id)],
        )

        # Should have sent notification to collaborator
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert user.email in str(call_args)

    @pytest.mark.asyncio
    async def test_version_creator_not_notified(
        self, db_session: AsyncSession, video_owner, video
    ):
        """Test version creator not notified about their own version."""
        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        notifications = await service.notify_new_version(
            video_id=video.id,
            version_number=2,
            created_by_user_id=video_owner.id,
            collaborator_ids=[str(video_owner.id)],  # Same as creator
        )

        # Should not create notification for creator
        assert len(notifications) == 0

    @pytest.mark.asyncio
    @patch("app.services.notification_service.send_email")
    async def test_notify_on_version_rollback(
        self, mock_send_email, db_session: AsyncSession, user, video_owner, video
    ):
        """Test collaborators notified when version is rolled back."""
        mock_send_email.return_value = AsyncMock()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        await service.notify_version_rollback(
            video_id=video.id,
            rolled_back_to_version=1,
            rolled_back_by_user_id=video_owner.id,
            collaborator_ids=[str(user.id)],
        )

        # Should have sent notification
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert user.email in str(call_args)
        assert "rolled back" in str(call_args).lower() or "rollback" in str(call_args).lower()


class TestNotificationPreferences:
    """Tests for notification preferences and filtering."""

    @pytest.mark.asyncio
    async def test_respect_email_notification_preferences(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test email notifications respect user preferences."""
        # Set user to disable email notifications
        user.notification_preferences = {"email_enabled": False}
        db_session.add(user)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)

        with patch("app.services.notification_service.send_email") as mock_send_email:
            mock_send_email.return_value = AsyncMock()

            await service.notify_video_shared(
                video_id=video.id,
                shared_by_user_id=video_owner.id,
                shared_with_user_id=user.id,
                permission="viewer",
            )

            # Should not have sent email
            mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_in_app_notification_still_created_when_email_disabled(
        self, db_session: AsyncSession, user, video_owner, video
    ):
        """Test in-app notification created even if email disabled."""
        # Set user to disable email notifications
        user.notification_preferences = {"email_enabled": False}
        db_session.add(user)
        db_session.commit()

        from app.services.notification_service import NotificationService

        service = NotificationService(db_session)
        notification = await service.notify_video_shared(
            video_id=video.id,
            shared_by_user_id=video_owner.id,
            shared_with_user_id=user.id,
            permission="viewer",
        )

        # Should still create in-app notification
        assert notification is not None
        assert notification.user_id == user.id
