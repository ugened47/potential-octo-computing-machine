"""Asset API endpoints for Advanced Editor."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, or_, select

from app.api.deps import get_current_user, get_db
from app.models import Asset, AssetType, User
from app.schemas.advanced_editor import AssetRead, AssetUpdate

router = APIRouter()


@router.get("", response_model=list[AssetRead])
async def list_assets(
    asset_type: AssetType | None = Query(None),
    tags: list[str] | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List user's assets with filtering and pagination."""
    query = select(Asset).where(
        or_(Asset.user_id == current_user.id, Asset.is_public == True)
    )

    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    if tags:
        # Filter by tags (any match)
        for tag in tags:
            query = query.where(Asset.tags.contains([tag]))

    if search:
        query = query.where(Asset.name.ilike(f"%{search}%"))

    query = query.order_by(desc(Asset.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    assets = result.scalars().all()

    return assets


@router.get("/{asset_id}", response_model=AssetRead)
async def get_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get asset details."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Check permissions
    if asset.user_id != current_user.id and not asset.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this asset",
        )

    return asset


@router.patch("/{asset_id}", response_model=AssetRead)
async def update_asset(
    asset_id: UUID,
    updates: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update asset metadata."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to modify this asset",
        )

    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)

    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete asset."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this asset",
        )

    # TODO: Check if asset is used in any projects
    # For now, just delete it

    await db.delete(asset)
    await db.commit()


@router.get("/search", response_model=list[AssetRead])
async def search_assets(
    q: str = Query(..., min_length=1),
    asset_type: AssetType | None = Query(None),
    tags: list[str] | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Search assets by query string."""
    query = select(Asset).where(
        or_(Asset.user_id == current_user.id, Asset.is_public == True),
        Asset.name.ilike(f"%{q}%"),
    )

    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    if tags:
        for tag in tags:
            query = query.where(Asset.tags.contains([tag]))

    query = query.order_by(desc(Asset.usage_count), desc(Asset.created_at)).limit(
        limit
    )

    result = await db.execute(query)
    assets = result.scalars().all()

    return assets
