"""Seed de datos iniciales para desarrollo (usuario DOCENTE por defecto)."""

import asyncio
import os

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.usuario import RolEnum, Usuario

DEFAULT_ADMIN_USER = "docente"
DEFAULT_ADMIN_PASSWORD = "docente123"
DEFAULT_ADMIN_NOMBRE = "Usuario Docente"


async def seed_users() -> None:
    """Upsert del usuario DOCENTE por defecto (credenciales por variables de entorno)."""
    username = os.getenv("SIVIGILA_ADMIN_USER", DEFAULT_ADMIN_USER)
    password = os.getenv("SIVIGILA_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    nombre_completo = os.getenv("SIVIGILA_ADMIN_NOMBRE", DEFAULT_ADMIN_NOMBRE)

    async with async_session_factory() as session:
        user = await session.scalar(select(Usuario).where(Usuario.username == username))
        if user is None:
            user = Usuario(
                username=username,
                hashed_password=get_password_hash(password),
                nombre_completo=nombre_completo,
                rol=RolEnum.DOCENTE,
                activo=True,
            )
            session.add(user)
        else:
            user.hashed_password = get_password_hash(password)
            user.nombre_completo = nombre_completo
            user.rol = RolEnum.DOCENTE
            user.activo = True
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_users())
