"""Endpoints CRUD de la ficha de datos básicos (Task B5).

RBAC (matriz del contrato):
- Autenticación obligatoria en todos los endpoints (get_current_user).
- UPGD: `cod_upgd` se fuerza a su propia UPGD (no puede forjar ajenas); solo
  ve/edita sus propias fichas (listado filtrado; ficha ajena -> 403).
- MUNICIPAL, DEPARTAMENTAL, NACIONAL, DOCENTE: lectura de todo.
- DOCENTE: además puede crear fichas (para cualquier UPGD).
- UI: sin acceso a este módulo (403).
- Sin PUT/edición en este alcance (Sprint 3, con ajustes).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import require_roles
from app.models.ficha_basica import FichaDatosBasicos
from app.models.usuario import RolEnum, Usuario
from app.schemas.ficha_basica import FichaDatosBasicosCreate, FichaDatosBasicosOut

router = APIRouter(prefix="/fichas", tags=["fichas-datos-basicos"])

_ROLES_LECTURA = (
    RolEnum.UPGD,
    RolEnum.MUNICIPAL,
    RolEnum.DEPARTAMENTAL,
    RolEnum.NACIONAL,
    RolEnum.DOCENTE,
)

_ROLES_ESCRITURA = (RolEnum.UPGD, RolEnum.DOCENTE)

_DETALLE_NO_ENCONTRADA = "Ficha de datos básicos no encontrada"
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


@router.post(
    "/datos-basicos",
    response_model=FichaDatosBasicosOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_ficha_basica(
    payload: FichaDatosBasicosCreate,
    current_user: Usuario = Depends(_escritura_dependency),
    db: AsyncSession = Depends(get_db),
) -> FichaDatosBasicos:
    """Crea una notificación individual de datos básicos."""
    cod_upgd = payload.cod_upgd
    if current_user.rol == RolEnum.UPGD:
        cod_upgd = current_user.cod_upgd or ""
    if not cod_upgd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario UPGD no tiene una UPGD asignada (cod_upgd vacío).",
        )

    datos = payload.model_dump()
    datos["cod_upgd"] = cod_upgd
    ficha = FichaDatosBasicos(**datos, creado_por_usuario_id=current_user.id)
    db.add(ficha)
    await db.commit()
    await db.refresh(ficha)
    return ficha


@router.get("/datos-basicos/{ficha_id}", response_model=FichaDatosBasicosOut)
async def obtener_ficha_basica(
    ficha_id: int,
    current_user: Usuario = Depends(_lectura_dependency),
    db: AsyncSession = Depends(get_db),
) -> FichaDatosBasicos:
    """Consulta una ficha por su id."""
    ficha = await db.get(FichaDatosBasicos, ficha_id)
    if ficha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_NO_ENCONTRADA,
        )
    _asegurar_ficha_propia(current_user, ficha.cod_upgd)
    return ficha


@router.get("/datos-basicos", response_model=list[FichaDatosBasicosOut])
async def listar_fichas_basicas(
    cod_evento: str | None = Query(default=None, description="Código del evento SIVIGILA."),
    semana: int | None = Query(default=None, description="Semana epidemiológica."),
    anio: int | None = Query(default=None, description="Año de notificación."),
    num_id: str | None = Query(default=None, description="Número de identificación del paciente."),
    cod_upgd: str | None = Query(default=None, description="Código de la UPGD."),
    current_user: Usuario = Depends(_lectura_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[FichaDatosBasicos]:
    """Lista fichas con filtros opcionales. Un UPGD solo ve sus propias fichas."""
    stmt = select(FichaDatosBasicos).order_by(FichaDatosBasicos.id)
    if current_user.rol == RolEnum.UPGD:
        stmt = stmt.where(FichaDatosBasicos.cod_upgd == current_user.cod_upgd)
    elif cod_upgd is not None:
        stmt = stmt.where(FichaDatosBasicos.cod_upgd == cod_upgd)
    if cod_evento is not None:
        stmt = stmt.where(FichaDatosBasicos.cod_evento == cod_evento)
    if semana is not None:
        stmt = stmt.where(FichaDatosBasicos.semana_epidemiologica == semana)
    if anio is not None:
        stmt = stmt.where(FichaDatosBasicos.anio == anio)
    if num_id is not None:
        stmt = stmt.where(FichaDatosBasicos.num_id == num_id)
    return list(await db.scalars(stmt))
