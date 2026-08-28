from __future__ import annotations

from typing import Protocol

from app.appointments.models import PatientAppointment


class CRMProvider(Protocol):
    async def search_patient(self, phone: str) -> dict[str, object] | None: ...


class MedicalSystemProvider(Protocol):
    async def get_patient_appointments(self, patient_id: str) -> list[PatientAppointment]: ...


class NotificationProvider(Protocol):
    async def send(
        self,
        *,
        recipient_ref: str,
        template_id: str,
        variables: dict[str, str],
        idempotency_key: str,
    ) -> str: ...
