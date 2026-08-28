from __future__ import annotations

from typing import Any, cast

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.idempotency.models import (
    IdempotencyClaim,
    IdempotencyRecord,
    IdempotencyStatus,
)
from app.idempotency.store import IdempotencyConflict
from app.infrastructure.database.models import IdempotencyRecordRow


class SqlAlchemyIdempotencyStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def claim(
        self,
        *,
        key: str,
        operation: str,
        request_fingerprint: str,
    ) -> IdempotencyClaim:
        async with self._sessions() as session:
            try:
                await session.execute(
                    insert(IdempotencyRecordRow).values(
                        key=key,
                        operation=operation,
                        request_fingerprint=request_fingerprint,
                        status=IdempotencyStatus.IN_PROGRESS.value,
                        result_json={},
                    )
                )
                await session.commit()
                return IdempotencyClaim(
                    created=True,
                    record=IdempotencyRecord(
                        key=key,
                        operation=operation,
                        request_fingerprint=request_fingerprint,
                        status=IdempotencyStatus.IN_PROGRESS,
                    ),
                )
            except IntegrityError:
                await session.rollback()

            row = await session.scalar(
                select(IdempotencyRecordRow).where(IdempotencyRecordRow.key == key)
            )
            if row is None:
                raise RuntimeError("Idempotency row disappeared after uniqueness conflict")

            if (
                row.operation != operation
                or row.request_fingerprint != request_fingerprint
            ):
                raise IdempotencyConflict(
                    "Idempotency key reused for a different operation or request"
                )

            return IdempotencyClaim(
                created=False,
                record=self._to_record(row),
            )

    async def complete(
        self,
        *,
        key: str,
        result: dict[str, Any],
    ) -> IdempotencyRecord:
        async with self._sessions() as session:
            execution = await session.execute(
                update(IdempotencyRecordRow)
                .where(IdempotencyRecordRow.key == key)
                .values(
                    status=IdempotencyStatus.COMPLETED.value,
                    result_json=result,
                )
            )
            rowcount = cast(Any, execution).rowcount
            if rowcount != 1:
                await session.rollback()
                raise KeyError("Cannot complete an idempotency key that was not claimed")
            await session.commit()

            row = await session.scalar(
                select(IdempotencyRecordRow).where(IdempotencyRecordRow.key == key)
            )

        if row is None:
            raise RuntimeError("Completed idempotency row could not be reloaded")
        return self._to_record(row)

    async def get(self, key: str) -> IdempotencyRecord | None:
        async with self._sessions() as session:
            row = await session.scalar(
                select(IdempotencyRecordRow).where(IdempotencyRecordRow.key == key)
            )
        return None if row is None else self._to_record(row)

    @staticmethod
    def _to_record(row: IdempotencyRecordRow) -> IdempotencyRecord:
        return IdempotencyRecord(
            key=row.key,
            operation=row.operation,
            request_fingerprint=row.request_fingerprint,
            status=IdempotencyStatus(row.status),
            result=dict(row.result_json),
        )
