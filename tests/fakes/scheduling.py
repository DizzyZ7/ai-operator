from __future__ import annotations

from app.appointments.models import (
    AppointmentOperationResult,
    AppointmentOperationStatus,
    AvailableSlot,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
    RescheduleAppointmentRequest,
    SlotQuery,
)


class FakeSchedulingProvider:
    def __init__(
        self,
        *,
        slots: list[AvailableSlot] | None = None,
        timeout_on_create: bool = False,
    ) -> None:
        self.slots = slots or []
        self.timeout_on_create = timeout_on_create
        self.create_calls = 0

    async def get_available_slots(self, query: SlotQuery) -> list[AvailableSlot]:
        return [
            slot
            for slot in self.slots
            if slot.service_id == query.service_id
            and (query.clinic_id is None or slot.clinic_id == query.clinic_id)
            and (query.doctor_id is None or slot.doctor_id == query.doctor_id)
            and query.starts_after <= slot.starts_at < query.ends_before
        ][: query.limit]

    async def create_appointment(
        self,
        request: CreateAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult:
        del idempotency_key
        self.create_calls += 1
        if self.timeout_on_create:
            raise TimeoutError

        if not any(slot.slot_id == request.slot_id for slot in self.slots):
            return AppointmentOperationResult(status=AppointmentOperationStatus.CONFLICT)

        return AppointmentOperationResult(
            status=AppointmentOperationStatus.SUCCEEDED,
            appointment_id="appointment-test-1",
            external_reference="external-test-1",
        )

    async def reschedule_appointment(
        self,
        request: RescheduleAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult:
        del request, idempotency_key
        return AppointmentOperationResult(status=AppointmentOperationStatus.REJECTED)

    async def cancel_appointment(
        self,
        request: CancelAppointmentRequest,
        *,
        idempotency_key: str,
    ) -> AppointmentOperationResult:
        del request, idempotency_key
        return AppointmentOperationResult(status=AppointmentOperationStatus.REJECTED)
