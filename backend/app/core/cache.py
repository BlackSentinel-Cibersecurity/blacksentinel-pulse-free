import structlog

logger = structlog.get_logger()

redis_client = None
_redis_available = False

try:
    import redis.asyncio as redis
    from app.core.config import settings
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    _redis_available = True
except Exception as e:
    logger.warning("Redis not available, using in-memory fallback", error=str(e))


class InMemoryCache:
    """Fallback in-memory cache when Redis is unavailable."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl: int = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def increment(self, key: str) -> int:
        self._store[key] = str(int(self._store.get(key, "0")) + 1)
        return int(self._store[key])

    async def get_pattern(self, pattern: str) -> list[str]:
        import fnmatch
        return [k for k in self._store if fnmatch.fnmatch(k, pattern)]

    async def publish(self, channel: str, message: str) -> None:
        pass

    async def subscribe(self, channel: str):
        return None

    async def ping(self) -> bool:
        return True


class CacheService:
    """Cache service with Redis or in-memory fallback."""

    def __init__(self, client=None):
        self.client = client or redis_client
        self._fallback = InMemoryCache()

    async def get(self, key: str) -> str | None:
        if self.client:
            try:
                return await self.client.get(key)
            except Exception:
                pass
        return await self._fallback.get(key)

    async def set(self, key: str, value: str, ttl: int = None) -> None:
        if self.client:
            try:
                return await self.client.set(key, value, ex=ttl or 300)
            except Exception:
                pass
        await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        if self.client:
            try:
                return await self.client.delete(key)
            except Exception:
                pass
        await self._fallback.delete(key)

    async def exists(self, key: str) -> bool:
        if self.client:
            try:
                return await self.client.exists(key)
            except Exception:
                pass
        return await self._fallback.exists(key)

    async def increment(self, key: str) -> int:
        if self.client:
            try:
                return await self.client.incr(key)
            except Exception:
                pass
        return await self._fallback.increment(key)

    async def get_pattern(self, pattern: str) -> list[str]:
        if self.client:
            try:
                keys = []
                async for key in self.client.scan_iter(match=pattern):
                    keys.append(key)
                return keys
            except Exception:
                pass
        return await self._fallback.get_pattern(pattern)

    async def publish(self, channel: str, message: str) -> None:
        if self.client:
            try:
                return await self.client.publish(channel, message)
            except Exception:
                pass

    async def subscribe(self, channel: str):
        if self.client:
            try:
                pubsub = self.client.pubsub()
                await pubsub.subscribe(channel)
                return pubsub
            except Exception:
                pass
        return None

    async def ping(self) -> bool:
        if self.client:
            try:
                await self.client.ping()
                return True
            except Exception:
                return False
        return True


cache = CacheService()
