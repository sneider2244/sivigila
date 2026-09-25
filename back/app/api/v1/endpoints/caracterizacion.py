"""Endpoints CRUD de caracterización UPGD (Task B4).

RBAC (matriz del contrato):
- Autenticación obligatoria en todos los endpoints (get_current_user).
- UPGD: solo accede (lectura/escritura) a su propia `cod_upgd`; cualquier otro
  `cod_prestador` -> 403.
- MUNICIPAL, DEPARTAMENTAL, NACIONAL, DOCENTE: lectura de todo.
- DOCENTE: además puede crear/actualizar cualquier UPGD (setup de escenarios).
- UI: sin acceso a este módulo (403).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import require_roles
from app.models.upgd import UPGDCaracterizacion
from app.models.usuario import RolEnum, Usuario
from app.schemas.upgd import (
    UPGDCaracterizacionCreate,
    UPGDCaracterizacionOut,
    UPGDCaracterizacionUpdate,
)

router = APIRouter(prefix="/upgd", tags=["caracterizacion-upgd"])

_ROLES_LECTURA = (
    RolEnum.UPGD,
    RolEnum.MUNICIPAL,
    RolEnum.DEPARTAMENTAL,
    RolEnum.NACIONAL,
    RolEnum.DOCENTE,
)

_ROLES_ESCRITURA = (RolEnum.UPGD, RolEnum.DOCENTE)

_DETALLE_NO_ENCONTRADA = "UPGD no encontrada"
_DETALLE_SIN_PERMISO = "No posee los permisos necesarios para realizar esta operación en SIVIGILA."
_DETALLE_DUPLICADA = "Ya existe una UPGD con ese cod_prestador"

_lectura_dependency = require_roles(*_ROLES_LECTURA)
_escritura_dependency = require_roles(*_ROLES_ESCRITURA)


def _asegurar_upgd_propia(usuario: Usuario, cod_prestador: str) -> None:
    """Lanza 403 si el usuario UPGD intenta acceder a un cod_prestador ajeno."""
    if usuario.rol == RolEnum.UPGD and usuario.cod_upgd != cod_prestador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_DETALLE_SIN_PERMISO,
        )


@router.get("", response_model=list[UPGDCaracterizacionOut])
async def listar_upgd(
    current_user: Usuario = Depends(_lectura_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[UPGDCaracterizacion]:
    """Lista UPGD. Un usuario UPGD solo ve su propia entidad."""
    stmt = select(UPGDCaracterizacion).order_by(UPGDCaracterizacion.cod_prestador)
    if current_user.rol == RolEnum.UPGD:
        stmt = stmt.where(UPGDCaracterizacion.cod_prestador == current_user.cod_upgd)
    return list(await db.scalars(stmt))


@router.get("/{cod_prestador}", response_model=UPGDCaracterizacionOut)
async def obtener_upgd(
    cod_prestador: str,
    current_user: Usuario = Depends(_lectura_dependency),
    db: AsyncSession = Depends(get_db),
) -> UPGDCaracterizacion:
    """Consulta una UPGD por su cod_prestador."""
    _asegurar_upgd_propia(current_user, cod_prestador)
    upgd = await db.get(UPGDCaracterizacion, cod_prestador)
    if upgd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_NO_ENCONTRADA,
        )
    return upgd


@router.post("", response_model=UPGDCaracterizacionOut, status_code=status.HTTP_201_CREATED)
async def crear_upgd(
    payload: UPGDCaracterizacionCreate,
    current_user: Usuario = Depends(_escritura_dependency),
    db: AsyncSession = Depends(get_db),
) -> UPGDCaracterizacion:
    """Crea una UPGD. Solo DOCENTE (cualquiera) y UPGD (la propia)."""
    _asegurar_upgd_propia(current_user, payload.cod_prestador)
    existente = await db.get(UPGDCaracterizacion, payload.cod_prestador)
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_DETALLE_DUPLICADA,
        )
    upgd = UPGDCaracterizacion(**payload.model_dump())
    db.add(upgd)
    await db.commit()
    await db.refresh(upgd)
    return upgd


@router.put("/{cod_prestador}", response_model=UPGDCaracterizacionOut)
async def actualizar_upgd(
    cod_prestador: str,
    payload: UPGDCaracterizacionUpdate,
    current_user: Usuario = Depends(_escritura_dependency),
    db: AsyncSession = Depends(get_db),
) -> UPGDCaracterizacion:
    """Actualiza (parcialmente) una UPGD existente."""
    _asegurar_upgd_propia(current_user, cod_prestador)
    upgd = await db.get(UPGDCaracterizacion, cod_prestador)
    if upgd is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_NO_ENCONTRADA,
        )
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(upgd, campo, valor)
    await db.commit()
    await db.refresh(upgd)
    return upgd
