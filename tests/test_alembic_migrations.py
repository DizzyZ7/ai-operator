from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


def test_initial_migration_renders_in_offline_postgres_mode(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/ai_operator",
    )
    config = Config(str(Path("alembic.ini")))

    command.upgrade(config, "head", sql=True)

    rendered = capsys.readouterr().out
    assert "CREATE TABLE conversation_states" in rendered
    assert "CREATE TABLE idempotency_records" in rendered
    assert "CREATE TABLE audit_events" in rendered
