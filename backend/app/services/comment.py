"""Comment service for video discussions."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Comment, CommentReaction, ReactionType, User, Video


class CommentService:
    """Service for managing comments and reactions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def parse_mentions(self, content: str) -> list[str]:
        """Parse @mentions from comment content.

        Args:
            content: Comment content

        Returns:
            List of mentioned usernames
        """
        # Match @username (alphanumeric, underscore, hyphen)
        pattern = r"@([a-zA-Z0-9_-]+)"
        mentions = re.findall(pattern, content)
        return mentions

    async def resolve_mention_user_ids(
        self, mentions: list[str]
    ) -> list[UUID]:
        """Resolve usernames to user IDs.

        Args:
            mentions: List of usernames

        Returns:
            List of user IDs
        """
        if not mentions:
            return []

        # Query users by email (assuming username is email)
        # In a real system, you'd have a username field
        result = await self.db.execute(
            select(User).where(User.email.in_(mentions))
        )
        users = list(result.scalars().all())

        return [user.id for user in users]

    async def create_comment(
        self,
        video_id: UUID,
        user_id: UUID,
        content: str,
        timestamp: float,
        timestamp_end: float | None = None,
        parent_comment_id: UUID | None = None,
        attachments: list[dict] | None = None,
    ) -> Comment:
        """Create a comment.

        Args:
            video_id: Video ID
            user_id: User creating the comment
            content: Comment content
            timestamp: Video timestamp in seconds
            timestamp_end: End timestamp for range comments (optional)
            parent_comment_id: Parent comment ID for replies (optional)
            attachments: List of attachments (optional)

        Returns:
            Created Comment

        Raises:
            ValueError: If validation fails
        """
        # Verify video exists
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Verify parent comment exists if specified
        if parent_comment_id:
            parent_result = await self.db.execute(
                select(Comment).where(Comment.id == parent_comment_id)
            )
            parent_comment = parent_result.scalar_one_or_none()
            if not parent_comment:
                raise ValueError("Parent comment not found")

            if parent_comment.video_id != video_id:
                raise ValueError("Parent comment belongs to different video")

            # Check nesting depth (max 3 levels)
            depth = await self._get_comment_depth(parent_comment_id)
            if depth >= 3:
                raise ValueError("Maximum comment nesting depth (3) exceeded")

        # Parse mentions
        mention_usernames = self.parse_mentions(content)
        mention_user_ids = await self.resolve_mention_user_ids(mention_usernames)

        # Create comment
        comment = Comment(
            video_id=video_id,
            user_id=user_id,
            content=content,
            timestamp=timestamp,
            timestamp_end=timestamp_end,
            parent_comment_id=parent_comment_id,
            mentions=mention_user_ids,
            attachments=attachments or [],
            is_resolved=False,
            is_edited=False,
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def _get_comment_depth(self, comment_id: UUID, current_depth: int = 1) -> int:
        """Get nesting depth of a comment.

        Args:
            comment_id: Comment ID
            current_depth: Current recursion depth

        Returns:
            Nesting depth
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()

        if not comment or not comment.parent_comment_id:
            return current_depth

        return await self._get_comment_depth(comment.parent_comment_id, current_depth + 1)

    async def get_video_comments(
        self,
        video_id: UUID,
        parent_comment_id: UUID | None = None,
        include_resolved: bool = True,
    ) -> list[Comment]:
        """Get comments for a video.

        Args:
            video_id: Video ID
            parent_comment_id: Parent comment ID (for replies, None for top-level)
            include_resolved: Include resolved comments

        Returns:
            List of comments
        """
        query = select(Comment).where(Comment.video_id == video_id)

        if parent_comment_id is not None:
            query = query.where(Comment.parent_comment_id == parent_comment_id)
        else:
            query = query.where(Comment.parent_comment_id.is_(None))

        if not include_resolved:
            query = query.where(Comment.is_resolved.is_(False))

        query = query.order_by(Comment.created_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_comments_at_timestamp(
        self, video_id: UUID, timestamp: float, tolerance: float = 1.0
    ) -> list[Comment]:
        """Get comments at or near a specific timestamp.

        Args:
            video_id: Video ID
            timestamp: Timestamp in seconds
            tolerance: Tolerance in seconds (default: 1.0)

        Returns:
            List of comments
        """
        result = await self.db.execute(
            select(Comment)
            .where(Comment.video_id == video_id)
            .where(Comment.timestamp >= timestamp - tolerance)
            .where(Comment.timestamp <= timestamp + tolerance)
            .order_by(Comment.timestamp.asc())
        )
        return list(result.scalars().all())

    async def update_comment(
        self, comment_id: UUID, user_id: UUID, content: str
    ) -> Comment:
        """Update a comment.

        Args:
            comment_id: Comment ID
            user_id: User updating the comment (must be owner)
            content: New content

        Returns:
            Updated Comment

        Raises:
            ValueError: If comment not found or user doesn't have permission
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        if comment.user_id != user_id:
            raise ValueError("Only comment owner can update comment")

        # Parse new mentions
        mention_usernames = self.parse_mentions(content)
        mention_user_ids = await self.resolve_mention_user_ids(mention_usernames)

        comment.content = content
        comment.mentions = mention_user_ids
        comment.is_edited = True
        comment.edited_at = datetime.utcnow()
        comment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> None:
        """Delete a comment.

        Args:
            comment_id: Comment ID
            user_id: User deleting the comment (must be owner or video owner)

        Raises:
            ValueError: If comment not found or user doesn't have permission
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Check if user is comment owner or video owner
        video_result = await self.db.execute(select(Video).where(Video.id == comment.video_id))
        video = video_result.scalar_one_or_none()

        if comment.user_id != user_id and (not video or video.user_id != user_id):
            raise ValueError("Only comment owner or video owner can delete comment")

        await self.db.delete(comment)
        await self.db.commit()

    async def resolve_comment(
        self, comment_id: UUID, user_id: UUID
    ) -> Comment:
        """Mark a comment as resolved.

        Args:
            comment_id: Comment ID
            user_id: User resolving the comment

        Returns:
            Updated Comment

        Raises:
            ValueError: If comment not found
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        comment.is_resolved = True
        comment.resolved_by = user_id
        comment.resolved_at = datetime.utcnow()
        comment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def unresolve_comment(self, comment_id: UUID) -> Comment:
        """Mark a comment as unresolved.

        Args:
            comment_id: Comment ID

        Returns:
            Updated Comment

        Raises:
            ValueError: If comment not found
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        comment.is_resolved = False
        comment.resolved_by = None
        comment.resolved_at = None
        comment.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def add_reaction(
        self, comment_id: UUID, user_id: UUID, reaction_type: ReactionType
    ) -> CommentReaction:
        """Add a reaction to a comment.

        Args:
            comment_id: Comment ID
            user_id: User adding the reaction
            reaction_type: Type of reaction

        Returns:
            Created or updated CommentReaction

        Raises:
            ValueError: If comment not found
        """
        # Verify comment exists
        comment_result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = comment_result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Check if user already reacted
        reaction_result = await self.db.execute(
            select(CommentReaction)
            .where(CommentReaction.comment_id == comment_id)
            .where(CommentReaction.user_id == user_id)
        )
        existing_reaction = reaction_result.scalar_one_or_none()

        if existing_reaction:
            # Update existing reaction
            existing_reaction.reaction_type = reaction_type
            await self.db.commit()
            await self.db.refresh(existing_reaction)
            return existing_reaction

        # Create new reaction
        reaction = CommentReaction(
            comment_id=comment_id,
            user_id=user_id,
            reaction_type=reaction_type,
        )

        self.db.add(reaction)
        await self.db.commit()
        await self.db.refresh(reaction)

        return reaction

    async def remove_reaction(
        self, comment_id: UUID, user_id: UUID
    ) -> None:
        """Remove a reaction from a comment.

        Args:
            comment_id: Comment ID
            user_id: User removing the reaction

        Raises:
            ValueError: If reaction not found
        """
        result = await self.db.execute(
            select(CommentReaction)
            .where(CommentReaction.comment_id == comment_id)
            .where(CommentReaction.user_id == user_id)
        )
        reaction = result.scalar_one_or_none()
        if not reaction:
            raise ValueError("Reaction not found")

        await self.db.delete(reaction)
        await self.db.commit()

    async def get_comment_reactions(
        self, comment_id: UUID
    ) -> dict[str, list[UUID]]:
        """Get all reactions for a comment, grouped by type.

        Args:
            comment_id: Comment ID

        Returns:
            Dictionary mapping reaction type to list of user IDs
        """
        result = await self.db.execute(
            select(CommentReaction).where(CommentReaction.comment_id == comment_id)
        )
        reactions = list(result.scalars().all())

        grouped: dict[str, list[UUID]] = {}
        for reaction in reactions:
            reaction_type = reaction.reaction_type.value
            if reaction_type not in grouped:
                grouped[reaction_type] = []
            grouped[reaction_type].append(reaction.user_id)

        return grouped

    async def get_comment_with_details(
        self, comment_id: UUID
    ) -> dict[str, Any]:
        """Get comment with full details including reactions and replies count.

        Args:
            comment_id: Comment ID

        Returns:
            Dictionary with comment details

        Raises:
            ValueError: If comment not found
        """
        result = await self.db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Get reactions
        reactions = await self.get_comment_reactions(comment_id)

        # Get replies count
        replies_result = await self.db.execute(
            select(Comment).where(Comment.parent_comment_id == comment_id)
        )
        replies_count = len(list(replies_result.scalars().all()))

        return {
            "id": str(comment.id),
            "video_id": str(comment.video_id),
            "user_id": str(comment.user_id),
            "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
            "timestamp": comment.timestamp,
            "timestamp_end": comment.timestamp_end,
            "content": comment.content,
            "mentions": [str(uid) for uid in comment.mentions],
            "attachments": comment.attachments,
            "is_resolved": comment.is_resolved,
            "resolved_by": str(comment.resolved_by) if comment.resolved_by else None,
            "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
            "is_edited": comment.is_edited,
            "edited_at": comment.edited_at.isoformat() if comment.edited_at else None,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
            "reactions": reactions,
            "replies_count": replies_count,
        }
