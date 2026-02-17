import json
from typing import Any, Protocol

from redis.asyncio import Redis

from app.core.config import settings


class CacheServiceProtocol(Protocol):
    async def get_json(self, key: str) -> dict[str, Any] | list[dict[str, Any]] | None: ...

    async def set_json(self, key: str, payload: dict[str, Any] | list[dict[str, Any]], ttl: int) -> None: ...

    async def invalidate_prefix(self, prefix: str) -> None: ...


class RedisClientProvider:
    _client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            cls._client = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is None:
            return
        await cls._client.aclose()
        cls._client = None


class CacheService:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def get_json(self, key: str) -> dict[str, Any] | list[dict[str, Any]] | None:
        cached_value = await self.redis_client.get(key)
        if cached_value is None:
            return None
        return json.loads(cached_value)

    async def set_json(self, key: str, payload: dict[str, Any] | list[dict[str, Any]], ttl: int) -> None:
        encoded = json.dumps(payload)
        await self.redis_client.set(key, encoded, ex=ttl)

    async def invalidate_prefix(self, prefix: str) -> None:
        keys: list[str] = []
        async for key in self.redis_client.scan_iter(match=f"{prefix}*"):
            keys.append(key)
        if keys:
            await self.redis_client.delete(*keys)
