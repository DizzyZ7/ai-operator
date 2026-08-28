import pytest

from app.audit.memory import MemoryAuditSink
from app.audit.models import AuditEvent, AuditEventType
from app.audit.safe import SafeAuditSink
from app.security.pii import sanitize_mapping, sanitize_text


def test_text_sanitizer_masks_email_and_phone() -> None:
    text = "Почта user@example.com, телефон +7 999 123-45-67"
    sanitized = sanitize_text(text)

    assert "user@example.com" not in sanitized
    assert "+7 999 123-45-67" not in sanitized
    assert sanitized.count("[REDACTED]") == 2


def test_mapping_sanitizer_redacts_sensitive_keys_recursively() -> None:
    value = {
        "patient": {
            "full_name": "Иванов Иван Иванович",
            "phone": "+79991234567",
        },
        "safe": "clinic-1",
    }

    sanitized = sanitize_mapping(value)

    assert sanitized["patient"]["full_name"] == "[REDACTED]"
    assert sanitized["patient"]["phone"] == "[REDACTED]"
    assert sanitized["safe"] == "clinic-1"


@pytest.mark.asyncio
async def test_safe_audit_sink_never_persists_raw_pii_metadata() -> None:
    memory = MemoryAuditSink()
    sink = SafeAuditSink(memory)

    await sink.emit(
        AuditEvent(
            event_type=AuditEventType.TOOL_REQUESTED,
            call_id="call-1",
            conversation_id="conv-1",
            correlation_id="corr-1",
            metadata={
                "phone": "+79991234567",
                "message": "write to person@example.com",
            },
        )
    )

    events = await memory.events()
    assert events[0].metadata["phone"] == "[REDACTED]"
    assert "person@example.com" not in events[0].metadata["message"]
