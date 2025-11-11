"""Composition service for Advanced Editor project management."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import (
    Project,
    ProjectStatus,
    Track,
    TrackItem,
    TrackType,
)


class CompositionService:
    """Service for managing multi-track compositions."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def create_project(
        self,
        user_id: UUID,
        name: str,
        width: int = 1920,
        height: int = 1080,
        frame_rate: float = 30.0,
        duration_seconds: float = 60.0,
        description: str | None = None,
        video_id: UUID | None = None,
        background_color: str = "#000000",
    ) -> Project:
        """Create new multi-track project with default tracks.

        Args:
            user_id: User ID creating the project
            name: Project name
            width: Output width in pixels
            height: Output height in pixels
            frame_rate: Output frame rate
            duration_seconds: Project duration in seconds
            description: Optional project description
            video_id: Optional base video ID
            background_color: Background color (hex)

        Returns:
            Created Project object with default tracks
        """
        # Create project
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            video_id=video_id,
            width=width,
            height=height,
            frame_rate=frame_rate,
            duration_seconds=duration_seconds,
            background_color=background_color,
            status=ProjectStatus.DRAFT,
        )
        self.db.add(project)
        await self.db.flush()  # Flush to get project ID

        # Create default tracks (1 video track, 1 audio track)
        video_track = Track(
            project_id=project.id,
            track_type=TrackType.VIDEO,
            name="Video Track 1",
            z_index=1,
            track_order=0,
        )
        audio_track = Track(
            project_id=project.id,
            track_type=TrackType.AUDIO,
            name="Audio Track 1",
            z_index=0,
            track_order=1,
        )

        self.db.add_all([video_track, audio_track])
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def get_project(self, project_id: UUID, user_id: UUID) -> Project | None:
        """Fetch project with all tracks and items.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification

        Returns:
            Project object or None if not found/unauthorized
        """
        stmt = select(Project).where(
            Project.id == project_id, Project.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_project(
        self, project_id: UUID, user_id: UUID, updates: dict[str, Any]
    ) -> Project | None:
        """Update project settings.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update

        Returns:
            Updated Project or None if not found/unauthorized
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        # Update allowed fields
        allowed_fields = {
            "name",
            "description",
            "width",
            "height",
            "frame_rate",
            "duration_seconds",
            "background_color",
            "canvas_settings",
            "export_settings",
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: UUID, user_id: UUID) -> bool:
        """Delete project and all associated data.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification

        Returns:
            True if deleted, False if not found/unauthorized
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.commit()
        return True

    async def add_track(
        self,
        project_id: UUID,
        user_id: UUID,
        track_type: TrackType,
        name: str,
        z_index: int | None = None,
        volume: float = 1.0,
        opacity: float = 1.0,
    ) -> Track | None:
        """Add new track to project.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification
            track_type: Type of track
            name: Track name
            z_index: Stacking order (auto-assigned if None)
            volume: Track volume (0.0 to 1.0)
            opacity: Track opacity (0.0 to 1.0)

        Returns:
            Created Track or None if project not found
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return None

        # Auto-assign z_index if not provided
        if z_index is None:
            # Get max z_index from existing tracks
            stmt = select(Track).where(Track.project_id == project_id)
            result = await self.db.execute(stmt)
            tracks = result.scalars().all()
            z_index = max((t.z_index for t in tracks), default=0) + 1

        # Get max track_order for UI positioning
        stmt = select(Track).where(Track.project_id == project_id)
        result = await self.db.execute(stmt)
        tracks = result.scalars().all()
        track_order = max((t.track_order for t in tracks), default=-1) + 1

        track = Track(
            project_id=project_id,
            track_type=track_type,
            name=name,
            z_index=z_index,
            volume=volume,
            opacity=opacity,
            track_order=track_order,
        )

        self.db.add(track)
        await self.db.commit()
        await self.db.refresh(track)
        return track

    async def update_track(
        self, track_id: UUID, user_id: UUID, updates: dict[str, Any]
    ) -> Track | None:
        """Update track settings.

        Args:
            track_id: Track ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update

        Returns:
            Updated Track or None if not found/unauthorized
        """
        stmt = (
            select(Track)
            .join(Project)
            .where(Track.id == track_id, Project.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        track = result.scalar_one_or_none()

        if not track:
            return None

        # Update allowed fields
        allowed_fields = {
            "name",
            "z_index",
            "is_locked",
            "is_visible",
            "is_muted",
            "volume",
            "opacity",
            "blend_mode",
            "track_order",
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(track, field, value)

        await self.db.commit()
        await self.db.refresh(track)
        return track

    async def delete_track(self, track_id: UUID, user_id: UUID) -> bool:
        """Delete track and all items.

        Args:
            track_id: Track ID
            user_id: User ID for ownership verification

        Returns:
            True if deleted, False if not found/unauthorized
        """
        stmt = (
            select(Track)
            .join(Project)
            .where(Track.id == track_id, Project.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        track = result.scalar_one_or_none()

        if not track:
            return False

        await self.db.delete(track)
        await self.db.commit()
        return True

    async def add_track_item(
        self,
        track_id: UUID,
        user_id: UUID,
        item_data: dict[str, Any],
    ) -> TrackItem | None:
        """Add item to track.

        Args:
            track_id: Track ID
            user_id: User ID for ownership verification
            item_data: Item configuration

        Returns:
            Created TrackItem or None if track not found
        """
        stmt = (
            select(Track)
            .join(Project)
            .where(Track.id == track_id, Project.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        track = result.scalar_one_or_none()

        if not track:
            return None

        # Calculate duration
        start_time = item_data.get("start_time", 0.0)
        end_time = item_data.get("end_time", 0.0)
        duration = end_time - start_time

        item = TrackItem(
            track_id=track_id,
            duration=duration,
            **item_data,
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_track_item(
        self, item_id: UUID, user_id: UUID, updates: dict[str, Any]
    ) -> TrackItem | None:
        """Update track item properties.

        Args:
            item_id: Item ID
            user_id: User ID for ownership verification
            updates: Dictionary of fields to update

        Returns:
            Updated TrackItem or None if not found/unauthorized
        """
        stmt = (
            select(TrackItem)
            .join(Track)
            .join(Project)
            .where(TrackItem.id == item_id, Project.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return None

        # Update duration if start_time or end_time changed
        if "start_time" in updates or "end_time" in updates:
            start_time = updates.get("start_time", item.start_time)
            end_time = updates.get("end_time", item.end_time)
            updates["duration"] = end_time - start_time

        for field, value in updates.items():
            setattr(item, field, value)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_track_item(self, item_id: UUID, user_id: UUID) -> bool:
        """Delete track item.

        Args:
            item_id: Item ID
            user_id: User ID for ownership verification

        Returns:
            True if deleted, False if not found/unauthorized
        """
        stmt = (
            select(TrackItem)
            .join(Track)
            .join(Project)
            .where(TrackItem.id == item_id, Project.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return False

        await self.db.delete(item)
        await self.db.commit()
        return True

    async def get_project_preview_data(
        self, project_id: UUID, time: float, user_id: UUID
    ) -> dict[str, Any]:
        """Get all visible items at specific time for preview.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification
            time: Time in seconds

        Returns:
            Dictionary with layered data for preview rendering
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return {"error": "Project not found"}

        # Get all tracks for the project
        stmt = select(Track).where(Track.project_id == project_id).order_by(Track.z_index)
        result = await self.db.execute(stmt)
        tracks = result.scalars().all()

        layers = []
        for track in tracks:
            if not track.is_visible:
                continue

            # Get items that are active at the specified time
            stmt = select(TrackItem).where(
                TrackItem.track_id == track.id,
                TrackItem.start_time <= time,
                TrackItem.end_time >= time,
            )
            result = await self.db.execute(stmt)
            items = result.scalars().all()

            for item in items:
                layers.append(
                    {
                        "track_id": str(track.id),
                        "track_type": track.track_type,
                        "z_index": track.z_index,
                        "item_id": str(item.id),
                        "item_type": item.item_type,
                        "source_url": item.source_url,
                        "position_x": item.position_x,
                        "position_y": item.position_y,
                        "scale_x": item.scale_x,
                        "scale_y": item.scale_y,
                        "rotation": item.rotation,
                        "opacity": track.opacity,
                        "blend_mode": track.blend_mode,
                        "text_content": item.text_content,
                        "text_style": item.text_style,
                    }
                )

        return {
            "project_id": str(project_id),
            "time": time,
            "width": project.width,
            "height": project.height,
            "background_color": project.background_color,
            "layers": layers,
        }

    async def validate_project(
        self, project_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """Validate project before rendering.

        Args:
            project_id: Project ID
            user_id: User ID for ownership verification

        Returns:
            Validation report with errors and warnings
        """
        project = await self.get_project(project_id, user_id)
        if not project:
            return {
                "valid": False,
                "errors": ["Project not found"],
                "warnings": [],
            }

        errors = []
        warnings = []

        # Get all tracks
        stmt = select(Track).where(Track.project_id == project_id)
        result = await self.db.execute(stmt)
        tracks = result.scalars().all()

        if not tracks:
            errors.append("Project has no tracks")

        # Check each track
        for track in tracks:
            stmt = select(TrackItem).where(TrackItem.track_id == track.id)
            result = await self.db.execute(stmt)
            items = result.scalars().all()

            if not items:
                warnings.append(f"Track '{track.name}' has no items")

            # Validate items
            for item in items:
                if item.start_time >= item.end_time:
                    errors.append(
                        f"Item {item.id} has invalid time range: start >= end"
                    )

                if item.end_time > project.duration_seconds:
                    warnings.append(
                        f"Item {item.id} extends beyond project duration"
                    )

                if not item.source_url and not item.source_id:
                    if item.item_type not in ["text", "shape"]:
                        errors.append(f"Item {item.id} has no source")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
