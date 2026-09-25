"""Cliente Redis asíncrono para la lista negra de tokens (sesiones revocadas)."""

import logging

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _blacklist_key(token: str) -> str:
    return f"blacklist:{token}"


async def blacklist_token(token: str, ttl: int) -> None:
    """Marca un token como revocado durante `ttl` segundos."""
    if ttl <= 0:
        return
    await redis_client.set(_blacklist_key(token), "1", ex=ttl)


async def is_blacklisted(token: str) -> bool:
    """Indica si el token está revocado.

    Si Redis no está disponible, degrada de forma segura: registra un warning y
    asume que el token NO está revocado (evita un 500 por infraestructura).
    """
    try:
        return bool(await redis_client.exists(_blacklist_key(token)))
    except Exception:  # noqa: BLE001 - degradación intencional ante caída de Redis
        logger.warning("Redis no disponible para blacklist; asumiendo token no revocado")
        return False
