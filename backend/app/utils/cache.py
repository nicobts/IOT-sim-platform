"""
Redis caching utilities.
"""

import json
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance.

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.redis_url_str,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
        logger.info("redis_client_initialized")

    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_connection_closed")


async def get_cached(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    if not settings.ENABLE_CACHE:
        return None

    try:
        client = await get_redis()
        value = await client.get(key)

        if value:
            logger.debug("cache_hit", key=key)
            return json.loads(value)

        logger.debug("cache_miss", key=key)
        return None

    except Exception as e:
        logger.error("cache_get_error", key=key, error=str(e))
        return None


async def set_cached(
    key: str, value: Any, ttl: Optional[int] = None
) -> bool:
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (defaults to settings)

    Returns:
        True if successful, False otherwise
    """
    if not settings.ENABLE_CACHE:
        return False

    try:
        client = await get_redis()
        ttl = ttl or settings.CACHE_TTL_SECONDS

        serialized = json.dumps(value)
        await client.setex(key, ttl, serialized)

        logger.debug("cache_set", key=key, ttl=ttl)
        return True

    except Exception as e:
        logger.error("cache_set_error", key=key, error=str(e))
        return False


async def delete_cached(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    if not settings.ENABLE_CACHE:
        return False

    try:
        client = await get_redis()
        await client.delete(key)

        logger.debug("cache_delete", key=key)
        return True

    except Exception as e:
        logger.error("cache_delete_error", key=key, error=str(e))
        return False


async def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.

    Args:
        pattern: Key pattern (e.g., "sims:*")

    Returns:
        Number of keys deleted
    """
    if not settings.ENABLE_CACHE:
        return 0

    try:
        client = await get_redis()
        keys = []

        async for key in client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await client.delete(*keys)
            logger.debug("cache_pattern_delete", pattern=pattern, count=deleted)
            return deleted

        return 0

    except Exception as e:
        logger.error("cache_pattern_delete_error", pattern=pattern, error=str(e))
        return 0


def cache(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from args

    Example:
        @cache(key_prefix="user", ttl=300)
        async def get_user(user_id: int):
            return await db.query(User).filter(User.id == user_id).first()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.ENABLE_CACHE:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder: prefix + args + kwargs
                key_parts = [key_prefix]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in kwargs.items())
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await get_cached(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await set_cached(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
