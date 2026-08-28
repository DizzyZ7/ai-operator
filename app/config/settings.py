from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    log_level: str = "INFO"

    llm_provider: str = "unconfigured"
    stt_provider: str = "unconfigured"
    tts_provider: str = "unconfigured"
    telephony_provider: str = "unconfigured"
    crm_provider: str = "unconfigured"
    medical_system_provider: str = "unconfigured"
    scheduling_provider: str = "unconfigured"
    notification_provider: str = "unconfigured"
    knowledge_provider: str = "unconfigured"

    database_url: SecretStr | None = None
    redis_url: SecretStr | None = None

    @model_validator(mode="after")
    def validate_production_configuration(self) -> RuntimeSettings:
        if self.app_env is not AppEnvironment.PRODUCTION:
            return self

        critical_providers = {
            "llm_provider": self.llm_provider,
            "stt_provider": self.stt_provider,
            "tts_provider": self.tts_provider,
            "telephony_provider": self.telephony_provider,
            "scheduling_provider": self.scheduling_provider,
        }
        missing = sorted(
            name
            for name, provider in critical_providers.items()
            if not provider.strip() or provider == "unconfigured"
        )
        if self.database_url is None:
            missing.append("database_url")

        if missing:
            raise ValueError(
                "Production configuration is incomplete: " + ", ".join(missing)
            )

        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "app_env": self.app_env.value,
            "providers": {
                "llm": self.llm_provider,
                "stt": self.stt_provider,
                "tts": self.tts_provider,
                "telephony": self.telephony_provider,
                "crm": self.crm_provider,
                "medical_system": self.medical_system_provider,
                "scheduling": self.scheduling_provider,
                "notification": self.notification_provider,
                "knowledge": self.knowledge_provider,
            },
            "database_configured": self.database_url is not None,
            "redis_configured": self.redis_url is not None,
        }
