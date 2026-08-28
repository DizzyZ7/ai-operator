from __future__ import annotations

from typing import Protocol

from app.appointments.models import (
    AppointmentOperationResult,
    AvailableSlot,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
    RescheduleAppointmentRequest,
    SlotQuery,
)


class SchedulingProvider(Protocol):
    async def get_available_slots(self, query: SlotQuery) -> list[AvailableSlot]: ...

    async def create_appointment(
        self,
        request: CreateAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult: ...

    async def reschedule_appointment(
        self,
        request: RescheduleAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult: ...

    async def cancel_appointment(
        self,
        request: CancelAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult: ...
