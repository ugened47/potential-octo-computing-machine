"""Track API endpoints for Advanced Editor."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.routes.project import verify_project_ownership
from app.models import User
from app.schemas.advanced_editor import TrackCreate, TrackRead, TrackUpdate
from app.services.composition_service import CompositionService

router = APIRouter()


@router.post("", response_model=TrackRead, status_code=status.HTTP_201_CREATED)
async def create_track(
    project_id: UUID,
    track_data: TrackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Add track to project."""
    await verify_project_ownership(project_id, current_user, db)

    service = CompositionService(db)
    track = await service.add_track(
        project_id=project_id,
        user_id=current_user.id,
        track_type=track_data.track_type,
        name=track_data.name,
        z_index=track_data.z_index,
        volume=track_data.volume,
        opacity=track_data.opacity,
    )

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return track


@router.patch("/{track_id}", response_model=TrackRead)
async def update_track(
    track_id: UUID,
    updates: TrackUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update track settings."""
    service = CompositionService(db)
    track = await service.update_track(
        track_id,
        current_user.id,
        updates.model_dump(exclude_unset=True),
    )

    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    return track


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track(
    track_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete track and all items."""
    service = CompositionService(db)
    deleted = await service.delete_track(track_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
