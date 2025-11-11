"""Project API endpoints for Advanced Editor."""

from typing import Any
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models import Project, ProjectStatus, User
from app.schemas.advanced_editor import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    RenderConfig,
    RenderProgress,
    ValidationResult,
)
from app.services.composition_service import CompositionService
from app.worker import enqueue_generate_project_thumbnail, enqueue_render_project

router = APIRouter()


async def verify_project_ownership(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Verify user owns the project and return it."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this project",
        )

    return project


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create new multi-track project."""
    service = CompositionService(db)

    project = await service.create_project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        video_id=project_data.video_id,
        width=project_data.width,
        height=project_data.height,
        frame_rate=project_data.frame_rate,
        duration_seconds=project_data.duration_seconds,
        background_color=project_data.background_color,
    )

    # Enqueue thumbnail generation (fire and forget)
    try:
        await enqueue_generate_project_thumbnail(str(project.id))
    except Exception:
        pass  # Don't fail project creation if thumbnail generation fails

    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("created_at", pattern="^(created_at|updated_at|name)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List user's projects with pagination and filtering."""
    query = select(Project).where(Project.user_id == current_user.id)

    if status_filter:
        query = query.where(Project.status == status_filter)

    # Apply sorting
    if sort == "created_at":
        query = query.order_by(desc(Project.created_at))
    elif sort == "updated_at":
        query = query.order_by(desc(Project.updated_at))
    elif sort == "name":
        query = query.order_by(Project.name)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    projects = result.scalars().all()

    return projects


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get project details with all tracks and items."""
    project = await verify_project_ownership(project_id, current_user, db)
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    updates: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update project settings."""
    await verify_project_ownership(project_id, current_user, db)

    service = CompositionService(db)
    project = await service.update_project(
        project_id,
        current_user.id,
        updates.model_dump(exclude_unset=True),
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete project and all associated data."""
    await verify_project_ownership(project_id, current_user, db)

    service = CompositionService(db)
    deleted = await service.delete_project(project_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


@router.post("/{project_id}/duplicate", response_model=ProjectRead)
async def duplicate_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Duplicate project with all tracks and items."""
    project = await verify_project_ownership(project_id, current_user, db)

    # Create new project with same settings
    service = CompositionService(db)
    new_project = await service.create_project(
        user_id=current_user.id,
        name=f"{project.name} (Copy)",
        description=project.description,
        video_id=project.video_id,
        width=project.width,
        height=project.height,
        frame_rate=project.frame_rate,
        duration_seconds=project.duration_seconds,
        background_color=project.background_color,
    )

    # TODO: Copy all tracks and items to new project
    # This would require iterating through all tracks and items and creating copies

    return new_project


@router.post("/{project_id}/render")
async def trigger_project_render(
    project_id: UUID,
    render_config: RenderConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger project rendering job."""
    project = await verify_project_ownership(project_id, current_user, db)

    # Validate project first
    service = CompositionService(db)
    validation = await service.validate_project(project_id, current_user.id)

    if not validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project validation failed: {', '.join(validation['errors'])}",
        )

    # Enqueue render job
    job = await enqueue_render_project(
        str(project_id),
        str(current_user.id),
        quality=render_config.quality,
        format=render_config.format,
    )

    # Estimate render time
    from app.services.video_rendering_service import VideoRenderingService

    rendering_service = VideoRenderingService(db)
    estimated_time = rendering_service.estimate_render_time(project)

    return {
        "job_id": str(job.job_id) if hasattr(job, "job_id") else "unknown",
        "estimated_time": estimated_time,
    }


@router.get("/{project_id}/render/progress", response_model=RenderProgress)
async def get_render_progress(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get render progress for project."""
    await verify_project_ownership(project_id, current_user, db)

    # Get progress from Redis
    redis_client = await redis.from_url(settings.redis_url)
    progress_key = f"render:progress:{project_id}"
    progress_data = await redis_client.get(progress_key)

    if not progress_data:
        # Check project status
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if project and project.status == ProjectStatus.COMPLETED:
            return RenderProgress(
                progress=100,
                stage="Complete",
                status="completed",
            )

        return RenderProgress(
            progress=0,
            stage="Not started",
            status="idle",
        )

    import json

    progress_dict = json.loads(progress_data)
    return RenderProgress(**progress_dict)


@router.post("/{project_id}/render/cancel")
async def cancel_project_render(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Cancel ongoing render job."""
    project = await verify_project_ownership(project_id, current_user, db)

    if project.status != ProjectStatus.RENDERING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not currently rendering",
        )

    # TODO: Cancel ARQ job
    # For now, just update project status
    project.status = ProjectStatus.DRAFT
    await db.commit()

    return {"message": "Render cancelled"}


@router.get("/{project_id}/preview")
async def get_project_preview(
    project_id: UUID,
    time: float = Query(..., ge=0.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get preview frame at specified time."""
    await verify_project_ownership(project_id, current_user, db)

    service = CompositionService(db)
    preview_data = await service.get_project_preview_data(
        project_id,
        time,
        current_user.id,
    )

    return preview_data


@router.get("/{project_id}/validate", response_model=ValidationResult)
async def validate_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Validate project before rendering."""
    await verify_project_ownership(project_id, current_user, db)

    service = CompositionService(db)
    validation = await service.validate_project(project_id, current_user.id)

    return validation
