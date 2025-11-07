"""ARQ worker for background tasks."""

from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings


async def sample_task(ctx: dict[str, Any], name: str) -> str:
    """Sample background task."""
    return f"Hello {name}!"


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook."""
    print("Worker starting up...")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook."""
    print("Worker shutting down...")


class WorkerSettings:
    """ARQ worker settings."""

    functions = [sample_task]

    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = 10
    job_timeout = 3600  # 1 hour
    keep_result = 3600  # Keep results for 1 hour


async def get_redis_pool() -> Any:
    """Get Redis pool for enqueueing jobs."""
    return await create_pool(WorkerSettings.redis_settings)
