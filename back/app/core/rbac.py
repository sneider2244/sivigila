"""Dependencias de control de acceso por rol (RBAC)."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.usuario import RolEnum, Usuario

_DETALLE_SIN_PERMISO = (
    "No posee los permisos necesarios para realizar esta operación en SIVIGILA."
)


def require_roles(*roles: RolEnum) -> Callable[..., Any]:
    """Factory que retorna una dependencia que exige pertenecer a los roles dados.

    Uso::

        @router.get("/...")
        async def endpoint(usuario: Usuario = Depends(require_roles(RolEnum.UPGD))):
            ...
    """

    async def _dependency(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_DETALLE_SIN_PERMISO,
            )
        return current_user

    return _dependency
