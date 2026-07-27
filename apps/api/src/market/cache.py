import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

from redis.asyncio import Redis

T = TypeVar("T")


class MarketCache:
    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self.redis = redis

    @staticmethod
    def key(namespace: str, *parts: object) -> str:
        safe_parts = [str(part).replace(":", "_")[:160] for part in parts]
        return "atlas:market:v1:" + namespace + ":" + ":".join(safe_parts)

    async def get_json(self, key: str) -> object | None:
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:  # noqa: BLE001 -- cache failure must degrade safely
            return None

    async def set_json(self, key: str, value: object, ttl_seconds: int) -> None:
        try:
            await self.redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except Exception:  # noqa: BLE001 -- the database/provider remains authoritative
            return

    async def remember(
        self,
        key: str,
        ttl_seconds: int,
        loader: Callable[[], Awaitable[T]],
    ) -> tuple[T, bool]:
        cached = await self.get_json(key)
        if cached is not None:
            return cached, True  # type: ignore[return-value]
        value = await loader()
        await self.set_json(key, value, ttl_seconds)
        return value, False
