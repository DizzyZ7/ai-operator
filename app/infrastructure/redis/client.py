from __future__ import annotations

from redis.asyncio import Redis

from app.config.settings import RuntimeSettings


def create_redis_client(settings: RuntimeSettings) -> Redis:
    if settings.redis_url is None:
        raise ValueError("REDIS_URL is required for Redis infrastructure")

    return Redis.from_url(
        settings.redis_url.get_secret_value(),
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
    )
