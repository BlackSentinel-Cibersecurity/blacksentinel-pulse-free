import redis.asyncio as redis

from app.core.config import settings


redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


class CacheService:
    """Redis-based caching service for Pulse."""

    def __init__(self, client: redis.Redis = None):
        self.client = client or redis_client

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = None) -> None:
        await self.client.set(key, value, ex=ttl or settings.REDIS_CACHE_TTL)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0

    async def increment(self, key: str) -> int:
        return await self.client.incr(key)

    async def get_pattern(self, pattern: str) -> list[str]:
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        return keys

    async def publish(self, channel: str, message: str) -> None:
        await self.client.publish(channel, message)

    async def subscribe(self, channel: str):
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


cache = CacheService()
