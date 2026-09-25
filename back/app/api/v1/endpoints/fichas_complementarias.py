"""Endpoints CRUD de la ficha de datos complementarios (Task B6).

RBAC (matriz del contrato):
- Autenticación obligatoria en todos los endpoints (get_current_user).
- UPGD: solo puede crear/actualizar complementarias para fichas de su propia
  `cod_upgd` (ficha ajena -> 403); puede leer las suyas.
- MUNICIPAL, DEPARTAMENTAL, NACIONAL: lectura de todo.
- DOCENTE: lectura de todo y además puede crear/actualizar (cualquier UPGD).
- UI: sin acceso a este módulo (403).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import require_roles
from app.models.ficha_basica import FichaDatosBasicos
from app.models.ficha_complementaria import FichaDatosComplementarios
from app.models.usuario import RolEnum, Usuario
from app.schemas.ficha_complementaria import (
    FichaDatosComplementariosCreate,
    FichaDatosComplementariosOut,
    FichaDatosComplementariosUpdate,
)

router = APIRouter(prefix="/fichas", tags=["fichas-datos-complementarios"])

_ROLES_LECTURA = (
    RolEnum.UPGD,
    RolEnum.MUNICIPAL,
    RolEnum.DEPARTAMENTAL,
    RolEnum.NACIONAL,
    RolEnum.DOCENTE,
)

_ROLES_ESCRITURA = (RolEnum.UPGD, RolEnum.DOCENTE)

_DETALLE_NO_ENCONTRADA = "Ficha de datos complementarios no encontrada"
_DETALLE_FICHA_BASICA_NO_ENCONTRADA = "Ficha de datos básicos no encontrada"
_DETALLE_DUPLICADA = "Ya existe una ficha complementaria para esa ficha básica"
_DETALLE_SIN_PERMISO = "No posee los permisos necesarios para realizar esta operación en SIVIGILA."

_lectura_dependency = require_roles(*_ROLES_LECTURA)
_escritura_dependency = require_roles(*_ROLES_ESCRITURA)


def _asegurar_ficha_propia(usuario: Usuario, cod_upgd: str) -> None:
    """Lanza 403 si un usuario UPGD intenta acceder a una ficha ajena."""
    if usuario.rol == RolEnum.UPGD and usuario.cod_upgd != cod_upgd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_DETALLE_SIN_PERMISO,
        )


async def _obtener_ficha_basica(db: AsyncSession, ficha_basica_id: int) -> FichaDatosBasicos:
    """Resuelve la ficha básica referida o lanza 404."""
    ficha_basica = await db.get(FichaDatosBasicos, ficha_basica_id)
    if ficha_basica is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_FICHA_BASICA_NO_ENCONTRADA,
        )
    return ficha_basica


async def _obtener_complementaria(
    db: AsyncSession, ficha_basica_id: int
) -> FichaDatosComplementarios:
    """Resuelve la complementaria por ficha_basica_id o lanza 404."""
    complementaria = await db.scalar(
        select(FichaDatosComplementarios).where(
            FichaDatosComplementarios.ficha_basica_id == ficha_basica_id
        )
    )
    if complementaria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_NO_ENCONTRADA,
        )
    return complementaria


@router.post(
    "/datos-complementarios",
    response_model=FichaDatosComplementariosOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_complementaria(
    payload: FichaDatosComplementariosCreate,
    current_user: Usuario = Depends(_escritura_dependency),
    db: AsyncSession = Depends(get_db),
) -> FichaDatosComplementarios:
    """Crea la ficha complementaria asociada a una ficha básica existente."""
    ficha_basica = await _obtener_ficha_basica(db, payload.ficha_basica_id)
    _asegurar_ficha_propia(current_user, ficha_basica.cod_upgd)

    duplicada = await db.scalar(
        select(FichaDatosComplementarios).where(
            FichaDatosComplementarios.ficha_basica_id == payload.ficha_basica_id
        )
    )
    if duplicada is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_DETALLE_DUPLICADA,
        )

    complementaria = FichaDatosComplementarios(
        ficha_basica_id=payload.ficha_basica_id,
        cod_evento=payload.cod_evento,
        contenido=payload.contenido,
    )
    db.add(complementaria)
    await db.commit()
    await db.refresh(complementaria)
    return complementaria


@router.get("/datos-complementarios/{ficha_basica_id}", response_model=FichaDatosComplementariosOut)
async def obtener_complementaria(
    ficha_basica_id: int,
    current_user: Usuario = Depends(_lectura_dependency),
    db: AsyncSession = Depends(get_db),
) -> FichaDatosComplementarios:
    """Consulta la ficha complementaria de una ficha básica por su id."""
    complementaria = await _obtener_complementaria(db, ficha_basica_id)
    ficha_basica = await _obtener_ficha_basica(db, complementaria.ficha_basica_id)
    _asegurar_ficha_propia(current_user, ficha_basica.cod_upgd)
    return complementaria


@router.put("/datos-complementarios/{ficha_basica_id}", response_model=FichaDatosComplementariosOut)
async def actualizar_complementaria(
    ficha_basica_id: int,
    payload: FichaDatosComplementariosUpdate,
    current_user: Usuario = Depends(_escritura_dependency),
    db: AsyncSession = Depends(get_db),
) -> FichaDatosComplementarios:
    """Actualiza (cod_evento + contenido) una ficha complementaria existente."""
    complementaria = await _obtener_complementaria(db, ficha_basica_id)
    ficha_basica = await _obtener_ficha_basica(db, complementaria.ficha_basica_id)
    _asegurar_ficha_propia(current_user, ficha_basica.cod_upgd)

    complementaria.cod_evento = payload.cod_evento
    complementaria.contenido = payload.contenido
    await db.commit()
    await db.refresh(complementaria)
    return complementaria
