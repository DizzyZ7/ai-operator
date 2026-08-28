import pytest
from pydantic import SecretStr, ValidationError

from app.config.settings import AppEnvironment, RuntimeSettings


def test_development_can_run_with_unconfigured_providers() -> None:
    settings = RuntimeSettings(app_env=AppEnvironment.DEVELOPMENT)

    assert settings.llm_provider == "unconfigured"
    assert settings.safe_summary()["database_configured"] is False


def test_production_rejects_unconfigured_critical_providers() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RuntimeSettings(
            app_env=AppEnvironment.PRODUCTION,
            database_url=SecretStr("postgresql://secret"),
        )

    message = str(exc_info.value)
    assert "llm_provider" in message
    assert "telephony_provider" in message
    assert "scheduling_provider" in message
    assert "postgresql://secret" not in message


def test_production_accepts_explicit_critical_provider_configuration() -> None:
    settings = RuntimeSettings(
        app_env=AppEnvironment.PRODUCTION,
        llm_provider="llm-adapter",
        stt_provider="stt-adapter",
        tts_provider="tts-adapter",
        telephony_provider="telephony-adapter",
        scheduling_provider="scheduling-adapter",
        database_url=SecretStr("postgresql://user:password@db/app"),
        redis_url=SecretStr("redis://:password@redis/0"),
    )

    assert settings.app_env is AppEnvironment.PRODUCTION


def test_safe_summary_never_contains_secret_urls() -> None:
    database_secret = "postgresql://user:password@db/app"
    redis_secret = "redis://:password@redis/0"
    settings = RuntimeSettings(
        database_url=SecretStr(database_secret),
        redis_url=SecretStr(redis_secret),
    )

    summary = settings.safe_summary()
    representation = repr(settings)

    assert database_secret not in str(summary)
    assert redis_secret not in str(summary)
    assert database_secret not in representation
    assert redis_secret not in representation
    assert summary["database_configured"] is True
    assert summary["redis_configured"] is True
