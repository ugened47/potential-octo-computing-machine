"""Social Media Template API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.deps import get_current_user, get_db
from app.models import PlatformType, SocialMediaTemplate
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateList,
    TemplateRead,
    TemplateUpdate,
)

router = APIRouter()


@router.get("", response_model=TemplateList)
async def list_templates(
    platform: PlatformType | None = None,
    is_system_preset: bool | None = None,
    is_active: bool = True,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all templates (system presets + user custom templates)."""
    # Build query
    query = select(SocialMediaTemplate).where(SocialMediaTemplate.is_active == is_active)

    # Filter by platform
    if platform:
        query = query.where(SocialMediaTemplate.platform == platform)

    # Filter by system preset
    if is_system_preset is not None:
        query = query.where(SocialMediaTemplate.is_system_preset == is_system_preset)
    else:
        # Include system presets and user's own templates
        query = query.where(
            (SocialMediaTemplate.is_system_preset == True)
            | (SocialMediaTemplate.user_id == current_user.id)
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(SocialMediaTemplate.created_at.desc()).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    templates = result.scalars().all()

    return TemplateList(templates=templates, total=total or 0)


@router.get("/presets", response_model=list[TemplateRead])
async def get_system_presets(
    platform: PlatformType | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all system preset templates."""
    query = select(SocialMediaTemplate).where(
        SocialMediaTemplate.is_system_preset == True,
        SocialMediaTemplate.is_active == True,
    )

    if platform:
        query = query.where(SocialMediaTemplate.platform == platform)

    query = query.order_by(SocialMediaTemplate.platform)

    result = await db.execute(query)
    templates = result.scalars().all()

    return templates


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get single template by ID."""
    result = await db.execute(
        select(SocialMediaTemplate).where(SocialMediaTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Check permissions - can view system presets or own templates
    if not template.is_system_preset and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this template",
        )

    return template


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_in: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a custom template."""
    # Create template
    template = SocialMediaTemplate(
        **template_in.model_dump(),
        user_id=current_user.id,
        is_system_preset=False,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: UUID,
    template_in: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update a custom template."""
    result = await db.execute(
        select(SocialMediaTemplate).where(SocialMediaTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Check permissions - cannot edit system presets
    if template.is_system_preset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit system preset templates",
        )

    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to edit this template",
        )

    # Update template
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (soft delete) a custom template."""
    result = await db.execute(
        select(SocialMediaTemplate).where(SocialMediaTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Check permissions - cannot delete system presets
    if template.is_system_preset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system preset templates",
        )

    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this template",
        )

    # Soft delete
    template.is_active = False
    db.add(template)
    await db.commit()
