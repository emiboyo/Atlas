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

    @staticmethod
    def stale_key(key: str) -> str:
        return f"{key}:stale"

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

    async def set_model_with_stale_fallback(
        self,
        key: str,
        value: BaseModel,
        *,
        fresh_ttl_seconds: int,
        stale_ttl_seconds: int,
    ) -> None:
        payload = value.model_dump(mode="json")
        await self.set_json(key, payload, fresh_ttl_seconds)
        await self.set_json(self.stale_key(key), payload, stale_ttl_seconds)

    async def get_stale_model(self, key: str, model: type[ModelT]) -> ModelT | None:
        return await self.get_model(self.stale_key(key), model)

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
