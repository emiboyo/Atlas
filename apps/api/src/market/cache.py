import json
from collections.abc import Awaitable, Callable
from hashlib import sha256
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from redis.asyncio import Redis

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


class MarketCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    @staticmethod
    def key(namespace: str, *parts: object) -> str:
        encoded_parts = json.dumps(
            [str(part) for part in parts],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
        digest = sha256(encoded_parts).hexdigest()
        return f"atlas:market:v1:{namespace}:{digest}"

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

    async def get_model(self, key: str, model: type[ModelT]) -> ModelT | None:
        cached = await self.get_json(key)
        if cached is None:
            return None
        try:
            return model.model_validate(cached)
        except ValidationError:
            return None

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
