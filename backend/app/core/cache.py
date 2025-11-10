"""Redis caching utilities."""

import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

# Global Redis client (lazy initialization)
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client.

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def get_cache(key: str) -> Any | None:
    """Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        # If Redis fails, return None (graceful degradation)
        return None


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Set value in cache with TTL.

    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl: Time to live in seconds (default: 5 minutes)
    """
    try:
        client = await get_redis_client()
        await client.setex(key, ttl, json.dumps(value))
    except Exception:
        # If Redis fails, silently continue (graceful degradation)
        pass


async def delete_cache(key: str) -> None:
    """Delete value from cache.

    Args:
        key: Cache key
    """
    try:
        client = await get_redis_client()
        await client.delete(key)
    except Exception:
        # If Redis fails, silently continue
        pass


async def invalidate_pattern(pattern: str) -> None:
    """Invalidate all cache keys matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "dashboard:stats:*")
    """
    try:
        client = await get_redis_client()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception:
        # If Redis fails, silently continue
        pass
