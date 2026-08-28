from __future__ import annotations

from app.appointments.models import PatientAppointment


class FakeMedicalSystemProvider:
    def __init__(self, appointments: list[PatientAppointment]) -> None:
        self._appointments = appointments
        self.calls = 0

    async def get_patient_appointments(
        self,
        patient_id: str,
    ) -> list[PatientAppointment]:
        self.calls += 1
        return [
            appointment.model_copy(deep=True)
            for appointment in self._appointments
            if appointment.patient_id == patient_id
        ]
