"""Version control service for video edit history."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ChangeType, User, Version, Video


class VersionService:
    """Service for managing video version history."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self,
        video_id: UUID,
        created_by: UUID,
        change_type: ChangeType,
        change_summary: str,
        change_details: dict[str, Any] | None = None,
        file_url: str | None = None,
        file_size: int | None = None,
        duration: float | None = None,
        transcript_snapshot: dict[str, Any] | None = None,
        timeline_snapshot: dict[str, Any] | None = None,
    ) -> Version:
        """Create a new version.

        Args:
            video_id: Video ID
            created_by: User creating the version
            change_type: Type of change
            change_summary: Brief summary of changes
            change_details: Detailed change information (optional)
            file_url: S3 URL of video file (optional)
            file_size: File size in bytes (optional)
            duration: Video duration in seconds (optional)
            transcript_snapshot: Transcript state snapshot (optional)
            timeline_snapshot: Timeline state snapshot (optional)

        Returns:
            Created Version

        Raises:
            ValueError: If video not found
        """
        # Verify video exists
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Get current version number
        versions_result = await self.db.execute(
            select(Version)
            .where(Version.video_id == video_id)
            .order_by(Version.version_number.desc())
        )
        latest_version = versions_result.first()
        version_number = 1 if not latest_version else latest_version[0].version_number + 1

        # Mark all existing versions as not current
        if latest_version:
            existing_versions = await self.db.execute(
                select(Version)
                .where(Version.video_id == video_id)
                .where(Version.is_current.is_(True))
            )
            for existing_version_row in existing_versions:
                existing_version_row[0].is_current = False

        # Create video metadata snapshot
        video_metadata_snapshot = {
            "title": video.title,
            "description": video.description,
            "file_size": video.file_size,
            "format": video.format,
            "duration": video.duration,
            "resolution": video.resolution,
            "status": video.status,
            "s3_key": video.s3_key,
            "cloudfront_url": video.cloudfront_url,
        }

        # Create version
        version = Version(
            video_id=video_id,
            version_number=version_number,
            created_by=created_by,
            change_type=change_type,
            change_summary=change_summary,
            change_details=change_details or {},
            video_metadata_snapshot=video_metadata_snapshot,
            file_url=file_url or video.cloudfront_url,
            file_size=file_size or video.file_size,
            duration=duration or video.duration,
            transcript_snapshot=transcript_snapshot,
            timeline_snapshot=timeline_snapshot,
            is_current=True,
        )

        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)

        return version

    async def get_video_versions(
        self, video_id: UUID, limit: int = 30
    ) -> list[Version]:
        """Get version history for a video.

        Args:
            video_id: Video ID
            limit: Maximum number of versions to return (default: 30)

        Returns:
            List of versions, ordered by version number descending
        """
        result = await self.db.execute(
            select(Version)
            .where(Version.video_id == video_id)
            .order_by(Version.version_number.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_version(self, version_id: UUID) -> Version | None:
        """Get a specific version.

        Args:
            version_id: Version ID

        Returns:
            Version or None if not found
        """
        result = await self.db.execute(select(Version).where(Version.id == version_id))
        return result.scalar_one_or_none()

    async def get_version_by_number(
        self, video_id: UUID, version_number: int
    ) -> Version | None:
        """Get a version by its number.

        Args:
            video_id: Video ID
            version_number: Version number

        Returns:
            Version or None if not found
        """
        result = await self.db.execute(
            select(Version)
            .where(Version.video_id == video_id)
            .where(Version.version_number == version_number)
        )
        return result.scalar_one_or_none()

    async def get_current_version(self, video_id: UUID) -> Version | None:
        """Get the current version of a video.

        Args:
            video_id: Video ID

        Returns:
            Current Version or None if no versions exist
        """
        result = await self.db.execute(
            select(Version)
            .where(Version.video_id == video_id)
            .where(Version.is_current.is_(True))
        )
        return result.scalar_one_or_none()

    async def rollback_to_version(
        self, video_id: UUID, version_id: UUID, user_id: UUID
    ) -> Version:
        """Rollback video to a previous version.

        This creates a new version that references the rolled-back version as its parent.

        Args:
            video_id: Video ID
            version_id: Version ID to rollback to
            user_id: User performing the rollback

        Returns:
            New Version representing the rollback

        Raises:
            ValueError: If video or version not found
        """
        # Get the target version
        target_version = await self.get_version(version_id)
        if not target_version:
            raise ValueError("Version not found")

        if target_version.video_id != video_id:
            raise ValueError("Version doesn't belong to this video")

        # Verify video exists
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        # Restore video metadata from snapshot
        video.title = target_version.video_metadata_snapshot.get("title", video.title)
        video.description = target_version.video_metadata_snapshot.get(
            "description", video.description
        )
        video.file_size = target_version.file_size
        video.duration = target_version.duration
        video.cloudfront_url = target_version.file_url
        video.updated_at = datetime.utcnow()

        # Create new version for the rollback
        new_version = await self.create_version(
            video_id=video_id,
            created_by=user_id,
            change_type=ChangeType.ROLLBACK,
            change_summary=f"Rolled back to version {target_version.version_number}",
            change_details={
                "rollback_target_version_id": str(version_id),
                "rollback_target_version_number": target_version.version_number,
                "previous_version_number": (await self.get_current_version(video_id)).version_number
                if await self.get_current_version(video_id)
                else None,
            },
            file_url=target_version.file_url,
            file_size=target_version.file_size,
            duration=target_version.duration,
            transcript_snapshot=target_version.transcript_snapshot,
            timeline_snapshot=target_version.timeline_snapshot,
        )

        # Set parent_version_id to reference the rolled-back version
        new_version.parent_version_id = version_id
        await self.db.commit()
        await self.db.refresh(new_version)

        return new_version

    async def compare_versions(
        self, version_id_1: UUID, version_id_2: UUID
    ) -> dict[str, Any]:
        """Compare two versions and return differences.

        Args:
            version_id_1: First version ID
            version_id_2: Second version ID

        Returns:
            Dictionary with comparison details

        Raises:
            ValueError: If either version not found
        """
        version_1 = await self.get_version(version_id_1)
        version_2 = await self.get_version(version_id_2)

        if not version_1 or not version_2:
            raise ValueError("One or both versions not found")

        if version_1.video_id != version_2.video_id:
            raise ValueError("Versions belong to different videos")

        # Compare metadata
        metadata_diff = {}
        for key in version_1.video_metadata_snapshot:
            val_1 = version_1.video_metadata_snapshot.get(key)
            val_2 = version_2.video_metadata_snapshot.get(key)
            if val_1 != val_2:
                metadata_diff[key] = {"v1": val_1, "v2": val_2}

        return {
            "video_id": str(version_1.video_id),
            "version_1": {
                "id": str(version_1.id),
                "version_number": version_1.version_number,
                "change_type": version_1.change_type,
                "change_summary": version_1.change_summary,
                "created_at": version_1.created_at.isoformat(),
            },
            "version_2": {
                "id": str(version_2.id),
                "version_number": version_2.version_number,
                "change_type": version_2.change_type,
                "change_summary": version_2.change_summary,
                "created_at": version_2.created_at.isoformat(),
            },
            "metadata_differences": metadata_diff,
            "duration_change": (version_2.duration or 0) - (version_1.duration or 0),
            "file_size_change": (version_2.file_size or 0) - (version_1.file_size or 0),
        }

    async def delete_old_versions(
        self, video_id: UUID, keep_count: int = 30
    ) -> int:
        """Delete old versions beyond the keep count.

        Args:
            video_id: Video ID
            keep_count: Number of recent versions to keep

        Returns:
            Number of versions deleted
        """
        # Get all versions ordered by version number descending
        result = await self.db.execute(
            select(Version)
            .where(Version.video_id == video_id)
            .order_by(Version.version_number.desc())
        )
        versions = list(result.scalars().all())

        # Keep the most recent versions, delete the rest
        versions_to_delete = versions[keep_count:]

        for version in versions_to_delete:
            # Don't delete if it's referenced by another version as parent
            referencing_result = await self.db.execute(
                select(Version).where(Version.parent_version_id == version.id)
            )
            if not referencing_result.first():
                await self.db.delete(version)

        if versions_to_delete:
            await self.db.commit()

        return len(versions_to_delete)

    async def get_version_count(self, video_id: UUID) -> int:
        """Get total number of versions for a video.

        Args:
            video_id: Video ID

        Returns:
            Version count
        """
        result = await self.db.execute(
            select(Version).where(Version.video_id == video_id)
        )
        versions = list(result.scalars().all())
        return len(versions)
