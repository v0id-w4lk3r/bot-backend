from redis.asyncio import Redis
from settings.config import settings

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_redis() -> bool:
    """Check Redis health connection."""
    return await redis_client.ping()


async def close_redis() -> None:
    """Close Redis client pool."""
    await redis_client.aclose()