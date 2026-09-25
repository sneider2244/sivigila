"""Endpoints del módulo Docente (Task B8): escenarios clínicos y evaluación.

RBAC (matriz del contrato):
- `/docente/*` -> solo rol DOCENTE (`require_roles(RolEnum.DOCENTE)`).
- `/estudiante/*` -> cualquier rol autenticado (`get_current_user`).

Flujo:
1. El docente crea escenarios (`POST /docente/escenarios`).
2. Asigna escenarios a estudiantes (`POST /docente/escenarios/{id}/asignar`).
3. El estudiante lista sus escenarios asignados (`GET /estudiante/escenarios`).
4. El docente evalúa la ficha diligenciada contra los datos esperados
   (`POST /docente/evaluar`).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rbac import require_roles
from app.core.security import get_current_user
from app.models.docente import EscenarioAsignacion, EscenarioClinico, EstadoAsignacion
from app.models.ficha_basica import FichaDatosBasicos
from app.models.ficha_complementaria import FichaDatosComplementarios
from app.models.usuario import RolEnum, Usuario
from app.schemas.docente import (
    AsignacionCreate,
    AsignacionOut,
    EscenarioCreate,
    EscenarioOut,
    EvaluacionDetalle,
    EvaluacionResult,
    EvaluarRequest,
)

router = APIRouter(tags=["docente"])

_docente_dependency = require_roles(RolEnum.DOCENTE)

_DETALLE_ESCENARIO_NO_ENCONTRADO = "Escenario clínico no encontrado"
_DETALLE_FICHA_NO_ENCONTRADA = "Ficha de datos básicos no encontrada"
_DETALLE_ESTUDIANTE_NO_ENCONTRADO = "Estudiante no encontrado"

# Campos planos de `fichas_datos_basicos` que participan en la evaluación.
_CAMPOS_PLANOS = (
    "cod_evento",
    "clasificacion_caso",
    "hospitalizado",
    "condicion_final",
    "area_ocurrencia",
    "sexo",
)


@router.post(
    "/docente/escenarios",
    response_model=EscenarioOut,
    status_code=status.HTTP_201_CREATED,
)
async def crear_escenario(
    payload: EscenarioCreate,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> EscenarioClinico:
    """Crea un escenario clínico (solo DOCENTE)."""
    escenario = EscenarioClinico(
        titulo=payload.titulo,
        descripcion=payload.descripcion,
        cod_evento=payload.cod_evento,
        datos_esperados=payload.datos_esperados,
        activo=payload.activo,
        creado_por_id=current_user.id,
    )
    db.add(escenario)
    await db.commit()
    await db.refresh(escenario)
    return escenario


@router.get("/docente/escenarios", response_model=list[EscenarioOut])
async def listar_escenarios(
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[EscenarioClinico]:
    """Lista todos los escenarios clínicos (solo DOCENTE)."""
    stmt = select(EscenarioClinico).order_by(EscenarioClinico.id)
    return list(await db.scalars(stmt))


@router.post(
    "/docente/escenarios/{escenario_id}/asignar",
    response_model=AsignacionOut,
    status_code=status.HTTP_201_CREATED,
)
async def asignar_escenario(
    escenario_id: int,
    payload: AsignacionCreate,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> AsignacionOut:
    """Asigna un escenario a un estudiante (solo DOCENTE)."""
    escenario = await db.get(EscenarioClinico, escenario_id)
    if escenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESCENARIO_NO_ENCONTRADO,
        )

    estudiante = await db.get(Usuario, payload.estudiante_id)
    if estudiante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESTUDIANTE_NO_ENCONTRADO,
        )

    asignacion = EscenarioAsignacion(
        escenario_id=escenario_id,
        estudiante_id=payload.estudiante_id,
        estado=EstadoAsignacion.ASIGNADO,
    )
    db.add(asignacion)
    await db.commit()
    await db.refresh(asignacion)

    return AsignacionOut(
        id=asignacion.id,
        escenario_id=escenario.id,
        escenario_titulo=escenario.titulo,
        estudiante_id=estudiante.id,
        estudiante_username=estudiante.username,
        estudiante_nombre=estudiante.nombre_completo,
        estado=asignacion.estado,
        ficha_basica_id=asignacion.ficha_basica_id,
    )


@router.get("/docente/asignaciones", response_model=list[AsignacionOut])
async def listar_asignaciones(
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionOut]:
    """Lista las asignaciones con título del escenario y datos del estudiante (DOCENTE)."""
    stmt = (
        select(
            EscenarioAsignacion,
            EscenarioClinico.titulo,
            Usuario.username,
            Usuario.nombre_completo,
        )
        .join(EscenarioClinico, EscenarioClinico.id == EscenarioAsignacion.escenario_id)
        .join(Usuario, Usuario.id == EscenarioAsignacion.estudiante_id)
        .order_by(EscenarioAsignacion.id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        AsignacionOut(
            id=asignacion.id,
            escenario_id=asignacion.escenario_id,
            escenario_titulo=titulo,
            estudiante_id=asignacion.estudiante_id,
            estudiante_username=username,
            estudiante_nombre=nombre_completo,
            estado=asignacion.estado,
            ficha_basica_id=asignacion.ficha_basica_id,
        )
        for asignacion, titulo, username, nombre_completo in rows
    ]


@router.get("/estudiante/escenarios", response_model=list[EscenarioOut])
async def listar_escenarios_estudiante(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EscenarioClinico]:
    """Lista los escenarios asignados al usuario autenticado (cualquier rol)."""
    stmt = (
        select(EscenarioClinico)
        .join(EscenarioAsignacion, EscenarioAsignacion.escenario_id == EscenarioClinico.id)
        .where(EscenarioAsignacion.estudiante_id == current_user.id)
        .order_by(EscenarioClinico.id)
    )
    return list(await db.scalars(stmt))


@router.post("/docente/evaluar", response_model=EvaluacionResult)
async def evaluar_ficha(
    payload: EvaluarRequest,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> EvaluacionResult:
    """Evalúa una ficha (y su complementaria si aplica) contra `datos_esperados`.

    Compara los campos planos de `fichas_datos_basicos` (`_CAMPOS_PLANOS`) y, si
    `datos_esperados` incluye la clave `contenido`, compara cada clave de primer
    nivel contra `fichas_datos_complementarios.contenido`.
    """
    ficha = await db.get(FichaDatosBasicos, payload.ficha_basica_id)
    if ficha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_FICHA_NO_ENCONTRADA,
        )

    escenario = await db.get(EscenarioClinico, payload.escenario_id)
    if escenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESCENARIO_NO_ENCONTRADO,
        )

    datos_esperados = escenario.datos_esperados or {}
    detalle: list[EvaluacionDetalle] = []

    for campo in _CAMPOS_PLANOS:
        if campo not in datos_esperados:
            continue
        esperado = datos_esperados[campo]
        obtenido = getattr(ficha, campo)
        detalle.append(
            EvaluacionDetalle(
                campo=campo,
                esperado=esperado,
                obtenido=obtenido,
                correcto=esperado == obtenido,
            )
        )

    contenido_esperado = datos_esperados.get("contenido")
    if isinstance(contenido_esperado, dict) and contenido_esperado:
        complementaria = await db.scalar(
            select(FichaDatosComplementarios).where(
                FichaDatosComplementarios.ficha_basica_id == ficha.id
            )
        )
        contenido_obtenido = (
            complementaria.contenido if complementaria is not None else {}
        )
        for clave, esperado in contenido_esperado.items():
            obtenido = (
                contenido_obtenido.get(clave)
                if isinstance(contenido_obtenido, dict)
                else None
            )
            detalle.append(
                EvaluacionDetalle(
                    campo=f"contenido.{clave}",
                    esperado=esperado,
                    obtenido=obtenido,
                    correcto=esperado == obtenido,
                )
            )

    total = len(detalle)
    aciertos = sum(1 for d in detalle if d.correcto)
    puntaje = round((aciertos / total) * 100, 2) if total else 100.0

    return EvaluacionResult(
        puntaje=puntaje,
        aciertos=aciertos,
        total=total,
        detalle=detalle,
    )
