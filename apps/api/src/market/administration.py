from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.src.market.fixtures import seed_development_data
from apps.api.src.market.metrics import INGESTION_RESULTS
from packages.database.atlas_database.models.identity import IdentityAuditEvent


class MarketAdministrationService:
    async def record(
        self,
        session: AsyncSession,
        *,
        operation_id: UUID,
        event_type: str,
        provider: str,
        command: str,
        metadata: dict[str, object],
    ) -> bool:
        if await session.get(IdentityAuditEvent, operation_id) is not None:
            return False
        session.add(
            IdentityAuditEvent(
                id=operation_id,
                event_type=event_type,
                actor_user_id=None,
                tenant_id=None,
                target_type="market_data_operation",
                target_id=operation_id,
                request_id=str(operation_id),
                event_metadata={
                    "provider": provider,
                    "command": command,
                    "completed_at": datetime.now(UTC).isoformat(),
                    **metadata,
                },
            )
        )
        return True

    async def seed(
        self,
        session: AsyncSession,
        *,
        operation_id: UUID,
        provider: str,
    ) -> dict[str, int]:
        existing = await session.get(IdentityAuditEvent, operation_id)
        if existing is not None:
            counts = existing.event_metadata.get("counts", {})
            return {str(key): int(value) for key, value in counts.items()}
        try:
            counts = await seed_development_data(session, commit=False)
            await self.record(
                session,
                operation_id=operation_id,
                event_type="market_data.development_seeded",
                provider=provider,
                command="seed-development-data",
                metadata={"counts": counts},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            INGESTION_RESULTS.labels(operation="seed", outcome="failure").inc()
            raise
        INGESTION_RESULTS.labels(operation="seed", outcome="success").inc()
        return counts
