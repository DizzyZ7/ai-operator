from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import RuntimeSettings


def create_engine_from_settings(settings: RuntimeSettings) -> AsyncEngine:
    if settings.database_url is None:
        raise ValueError("DATABASE_URL is required for database infrastructure")

    url = settings.database_url.get_secret_value()
    if settings.app_env.value == "production" and not url.startswith(
        ("postgresql+asyncpg://", "postgresql://")
    ):
        raise ValueError("Production DATABASE_URL must use PostgreSQL")

    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")

    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )
