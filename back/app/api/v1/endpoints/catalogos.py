"""Endpoints de consulta de catálogos oficiales (datos de referencia públicos).

RULING: estos endpoints NO llevan dependencias de autenticación. Son datos de
referencia (DIVIPOLA, eventos, ocupaciones, etnias) que el frontend necesita para
poblar comboboxes incluso antes del login. Si se requiere restringirlos en el
futuro, se agrega `Depends(get_current_user)` por endpoint sin cambiar el contrato.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.catalogos import Departamento, Etnia, Evento, Municipio, Ocupacion
from app.schemas.catalogo import (
    DepartamentoOut,
    EtniaOut,
    EventoOut,
    MunicipioOut,
    OcupacionOut,
)

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/departamentos", response_model=list[DepartamentoOut])
async def listar_departamentos(
    db: AsyncSession = Depends(get_db),
) -> list[Departamento]:
    """Lista los 33 departamentos de Colombia ordenados por código DIVIPOLA."""
    return list(await db.scalars(select(Departamento).order_by(Departamento.codigo)))


@router.get("/municipios", response_model=list[MunicipioOut])
async def listar_municipios(
    departamento: str | None = Query(
        default=None,
        description="Código DIVIPOLA de departamento (2 dígitos) para filtrar.",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[Municipio]:
    """Lista municipios, opcionalmente filtrados por código de departamento."""
    stmt = select(Municipio).order_by(Municipio.codigo)
    if departamento is not None:
        stmt = stmt.where(Municipio.departamento_codigo == departamento)
    return list(await db.scalars(stmt))


@router.get("/eventos", response_model=list[EventoOut])
async def listar_eventos(db: AsyncSession = Depends(get_db)) -> list[Evento]:
    """Lista los eventos de notificación obligatoria SIVIGILA."""
    return list(await db.scalars(select(Evento).order_by(Evento.codigo)))


@router.get("/ocupaciones", response_model=list[OcupacionOut])
async def listar_ocupaciones(db: AsyncSession = Depends(get_db)) -> list[Ocupacion]:
    """Lista las ocupaciones disponibles en la ficha."""
    return list(await db.scalars(select(Ocupacion).order_by(Ocupacion.codigo)))


@router.get("/etnias", response_model=list[EtniaOut])
async def listar_etnias(db: AsyncSession = Depends(get_db)) -> list[Etnia]:
    """Lista las etnias reconocidas (clasificación DANE/INS)."""
    return list(await db.scalars(select(Etnia).order_by(Etnia.codigo)))
