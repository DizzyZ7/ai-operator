from __future__ import annotations

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit.models import AuditEvent
from app.infrastructure.database.models import AuditEventRow


class SqlAlchemyAuditSink:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def emit(self, event: AuditEvent) -> None:
        async with self._sessions() as session:
            await session.execute(
                insert(AuditEventRow).values(
                    event_type=event.event_type.value,
                    call_id=event.call_id,
                    conversation_id=event.conversation_id,
                    correlation_id=event.correlation_id,
                    occurred_at=event.occurred_at,
                    metadata_json=event.metadata,
                )
            )
            await session.commit()
