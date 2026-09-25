"""Utilidades de seguridad: hashing de passwords, JWT y dependencia de usuario actual."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import is_blacklisted
from app.models.usuario import Usuario

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en claro contra su hash Argon2."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash Argon2 de una contraseña en claro."""
    return pwd_context.hash(password)


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    """Emite un JWT de acceso."""
    return _create_token(subject, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str) -> str:
    """Emite un JWT de refresco."""
    return _create_token(
        subject, "refresh", timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Lanza 401 si es inválido o expiró."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def token_remaining_ttl(token: str) -> int:
    """Segundos restantes de vida de un token (0 si expirado/inválido). No lanza."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return 0
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        return 0
    now = datetime.now(UTC).timestamp()
    return max(0, int(exp - now))


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Dependencia que resuelve el usuario autenticado a partir del Bearer token."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise credentials_exc
    username = payload.get("sub")
    if username is None:
        raise credentials_exc
    if await is_blacklisted(token):
        raise credentials_exc
    user = await db.scalar(select(Usuario).where(Usuario.username == username))
    if user is None or not user.activo:
        raise credentials_exc
    return user
