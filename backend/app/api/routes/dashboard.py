"""Dashboard API endpoints."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.core.cache import get_cache, set_cache
from app.models.user import User
from app.models.video import Video, VideoStatus

router = APIRouter()

# Cache TTL for dashboard stats (5 minutes)
CACHE_TTL = 300


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get dashboard statistics for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dashboard stats including total videos, storage used, processing time, and recent activity
    """
    # Check cache first
    cache_key = f"dashboard:stats:{current_user.id}"
    cached_stats = await get_cache(cache_key)
    if cached_stats:
        return cached_stats

    # Total videos count
    total_videos_result = await db.execute(
        select(func.count(Video.id)).where(Video.user_id == current_user.id)
    )
    total_videos = total_videos_result.scalar() or 0

    # Storage used (sum of file_size in GB)
    storage_result = await db.execute(
        select(func.coalesce(func.sum(Video.file_size), 0)).where(Video.user_id == current_user.id)
    )
    storage_bytes = storage_result.scalar() or 0
    storage_used_gb = storage_bytes / (1024 * 1024 * 1024)  # Convert to GB

    # Processing time (sum of duration in minutes)
    processing_time_result = await db.execute(
        select(func.coalesce(func.sum(Video.duration), 0)).where(
            Video.user_id == current_user.id,
            Video.status == VideoStatus.COMPLETED,
        )
    )
    processing_time_seconds = processing_time_result.scalar() or 0
    processing_time_minutes = processing_time_seconds / 60  # Convert to minutes

    # Recent activity (videos uploaded in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity_result = await db.execute(
        select(func.count(Video.id)).where(
            Video.user_id == current_user.id,
            Video.created_at >= seven_days_ago,
        )
    )
    recent_activity_count = recent_activity_result.scalar() or 0

    stats = {
        "total_videos": total_videos,
        "storage_used_gb": round(storage_used_gb, 2),
        "processing_time_minutes": round(processing_time_minutes, 2),
        "recent_activity_count": recent_activity_count,
    }

    # Cache the result
    await set_cache(cache_key, stats, ttl=CACHE_TTL)

    return stats
