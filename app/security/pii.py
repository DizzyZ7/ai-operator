from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = frozenset(
    {
        "phone",
        "email",
        "patient_name",
        "full_name",
        "first_name",
        "last_name",
        "middle_name",
        "date_of_birth",
        "dob",
        "passport",
        "snils",
        "insurance_number",
        "medical_record",
    }
)

_EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s()\-]{7,}\d)(?!\w)")


def sanitize_text(value: str) -> str:
    value = _EMAIL_RE.sub(_REDACTED, value)
    return _PHONE_RE.sub(_REDACTED, value)


def sanitize_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and key.lower() in _SENSITIVE_KEYS:
        return _REDACTED

    if isinstance(value, str):
        return sanitize_text(value)

    if isinstance(value, Mapping):
        return {
            str(nested_key): sanitize_value(nested_value, key=str(nested_key))
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_value(item) for item in value]

    return value


def sanitize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): sanitize_value(nested_value, key=str(key))
        for key, nested_value in value.items()
    }
