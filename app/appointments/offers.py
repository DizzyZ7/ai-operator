from __future__ import annotations

from app.appointments.models import AvailableSlot
from app.conversations.models import OfferedOption


def build_slot_options(slots: list[AvailableSlot], *, limit: int = 3) -> list[OfferedOption]:
    """Convert trusted scheduling slots into backend-owned conversation options."""
    return [
        OfferedOption(
            option_id=f"slot-option-{index + 1}",
            label=slot.starts_at.isoformat(),
            payload={
                "slot_id": slot.slot_id,
                "clinic_id": slot.clinic_id,
                "service_id": slot.service_id,
                "doctor_id": slot.doctor_id,
                "starts_at": slot.starts_at.isoformat(),
                "ends_at": slot.ends_at.isoformat(),
            },
        )
        for index, slot in enumerate(slots[:limit])
    ]
