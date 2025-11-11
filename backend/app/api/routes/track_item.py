"""TrackItem API endpoints for Advanced Editor."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.models import Project, Track, TrackItem, User
from app.schemas.advanced_editor import (
    SplitItemRequest,
    SplitItemResponse,
    TrackItemCreate,
    TrackItemRead,
    TrackItemUpdate,
)
from app.services.composition_service import CompositionService

router = APIRouter()


@router.post("", response_model=TrackItemRead, status_code=status.HTTP_201_CREATED)
async def create_track_item(
    track_id: UUID,
    item_data: TrackItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Add item to track."""
    service = CompositionService(db)
    item = await service.add_track_item(
        track_id=track_id,
        user_id=current_user.id,
        item_data=item_data.model_dump(),
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    return item


@router.get("/{item_id}", response_model=TrackItemRead)
async def get_track_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get item details."""
    result = await db.execute(
        select(TrackItem)
        .join(Track)
        .join(Project)
        .where(TrackItem.id == item_id, Project.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return item


@router.patch("/{item_id}", response_model=TrackItemRead)
async def update_track_item(
    item_id: UUID,
    updates: TrackItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update item properties."""
    service = CompositionService(db)
    item = await service.update_track_item(
        item_id,
        current_user.id,
        updates.model_dump(exclude_unset=True),
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_track_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete item from track."""
    service = CompositionService(db)
    deleted = await service.delete_track_item(item_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )


@router.post("/{item_id}/split", response_model=SplitItemResponse)
async def split_track_item(
    item_id: UUID,
    split_request: SplitItemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Split item at specified time."""
    # Get original item
    result = await db.execute(
        select(TrackItem)
        .join(Track)
        .join(Project)
        .where(TrackItem.id == item_id, Project.user_id == current_user.id)
    )
    original_item = result.scalar_one_or_none()

    if not original_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    split_time = split_request.split_time

    # Validate split time is within item duration
    if split_time <= original_item.start_time or split_time >= original_item.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Split time must be within item time range",
        )

    # Update original item (first half)
    service = CompositionService(db)
    item1 = await service.update_track_item(
        item_id,
        current_user.id,
        {"end_time": split_time},
    )

    # Create new item (second half)
    item2_data = {
        "item_type": original_item.item_type,
        "source_type": original_item.source_type,
        "source_id": original_item.source_id,
        "source_url": original_item.source_url,
        "start_time": split_time,
        "end_time": original_item.end_time,
        "trim_start": original_item.trim_start + (split_time - original_item.start_time),
        "trim_end": original_item.trim_end,
        "position_x": original_item.position_x,
        "position_y": original_item.position_y,
        "scale_x": original_item.scale_x,
        "scale_y": original_item.scale_y,
        "rotation": original_item.rotation,
        "crop_settings": original_item.crop_settings,
        "transform_settings": original_item.transform_settings,
        "text_content": original_item.text_content,
        "text_style": original_item.text_style,
        "effects": original_item.effects,
    }

    item2 = await service.add_track_item(
        track_id=original_item.track_id,
        user_id=current_user.id,
        item_data=item2_data,
    )

    if not item1 or not item2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to split item",
        )

    return SplitItemResponse(item1=item1, item2=item2)
