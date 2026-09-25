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
from sqlalchemy import or_, select
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
    EntregaRequest,
    EscenarioCreate,
    EscenarioEstudianteOut,
    EscenarioOut,
    EstudianteAsignacionOut,
    EstudianteOut,
    EvaluacionDetalle,
    EvaluacionResult,
    EvaluarRequest,
)

router = APIRouter(tags=["docente"])

_docente_dependency = require_roles(RolEnum.DOCENTE)

_DETALLE_ESCENARIO_NO_ENCONTRADO = "Escenario clínico no encontrado"
_DETALLE_FICHA_NO_ENCONTRADA = "Ficha de datos básicos no encontrada"
_DETALLE_ASIGNACION_NO_ENCONTRADA = "Asignación de escenario no encontrada"
_DETALLE_ENTREGA_SIN_PERMISO = (
    "No posee los permisos necesarios para realizar esta operación en SIVIGILA."
)

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


@router.get("/docente/escenarios/{escenario_id}", response_model=EscenarioOut)
async def obtener_escenario(
    escenario_id: int,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> EscenarioClinico:
    """Obtiene un escenario por su id (solo DOCENTE)."""
    escenario = await db.get(EscenarioClinico, escenario_id)
    if escenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESCENARIO_NO_ENCONTRADO,
        )
    return escenario


@router.get("/docente/estudiantes", response_model=list[EstudianteOut])
async def listar_estudiantes(
    q: str | None = None,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[Usuario]:
    """Lista usuarios no-DOCENTE (solo DOCENTE) con búsqueda opcional `q`."""
    stmt = select(Usuario).where(Usuario.rol != RolEnum.DOCENTE)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Usuario.nombre_completo.ilike(pattern),
                Usuario.username.ilike(pattern),
                Usuario.numero_identificacion.ilike(pattern),
            )
        )
    stmt = stmt.order_by(Usuario.nombre_completo)
    return list(await db.scalars(stmt))


@router.post(
    "/docente/escenarios/{escenario_id}/asignar",
    response_model=list[AsignacionOut],
    status_code=status.HTTP_201_CREATED,
)
async def asignar_escenarios(
    escenario_id: int,
    payload: AsignacionCreate,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionOut]:
    """Asigna un escenario a varios estudiantes (bulk, idempotente; solo DOCENTE).

    Salta los pares `(escenario_id, estudiante_id)` ya existentes y crea solo los
    nuevos en estado `ASIGNADO`. Devuelve únicamente las asignaciones creadas.
    """
    escenario = await db.get(EscenarioClinico, escenario_id)
    if escenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESCENARIO_NO_ENCONTRADO,
        )

    estudiante_ids = list(dict.fromkeys(payload.estudiante_ids))

    estudiantes = await db.scalars(
        select(Usuario).where(Usuario.id.in_(estudiante_ids))
    )
    por_id = {estudiante.id: estudiante for estudiante in estudiantes}
    inexistentes = [uid for uid in estudiante_ids if uid not in por_id]
    if inexistentes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estudiante(s) no encontrado(s): {inexistentes}",
        )

    ya_asignados = set(
        await db.scalars(
            select(EscenarioAsignacion.estudiante_id).where(
                EscenarioAsignacion.escenario_id == escenario_id,
                EscenarioAsignacion.estudiante_id.in_(estudiante_ids),
            )
        )
    )

    creadas: list[AsignacionOut] = []
    for estudiante_id in estudiante_ids:
        if estudiante_id in ya_asignados:
            continue
        estudiante = por_id[estudiante_id]
        asignacion = EscenarioAsignacion(
            escenario_id=escenario_id,
            estudiante_id=estudiante_id,
            estado=EstadoAsignacion.ASIGNADO,
        )
        db.add(asignacion)
        await db.flush()
        creadas.append(
            AsignacionOut(
                id=asignacion.id,
                escenario_id=escenario.id,
                escenario_titulo=escenario.titulo,
                estudiante_id=estudiante.id,
                estudiante_username=estudiante.username,
                estudiante_nombre=estudiante.nombre_completo,
                estudiante_numero_identificacion=estudiante.numero_identificacion,
                estado=asignacion.estado,
                ficha_basica_id=asignacion.ficha_basica_id,
            )
        )

    await db.commit()
    return creadas


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
            Usuario.numero_identificacion,
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
            estudiante_numero_identificacion=numero_identificacion,
            estado=asignacion.estado,
            ficha_basica_id=asignacion.ficha_basica_id,
        )
        for asignacion, titulo, username, nombre_completo, numero_identificacion in rows
    ]


@router.get(
    "/docente/escenarios/{escenario_id}/asignaciones",
    response_model=list[AsignacionOut],
)
async def listar_asignaciones_escenario(
    escenario_id: int,
    current_user: Usuario = Depends(_docente_dependency),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionOut]:
    """Lista las asignaciones de UN escenario con datos del estudiante (DOCENTE).

    Ordenado por nombre para facilitar la revisión de muchos estudiantes.
    """
    escenario = await db.get(EscenarioClinico, escenario_id)
    if escenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ESCENARIO_NO_ENCONTRADO,
        )

    stmt = (
        select(
            EscenarioAsignacion,
            Usuario.username,
            Usuario.nombre_completo,
            Usuario.numero_identificacion,
        )
        .join(Usuario, Usuario.id == EscenarioAsignacion.estudiante_id)
        .where(EscenarioAsignacion.escenario_id == escenario_id)
        .order_by(Usuario.nombre_completo)
    )
    rows = (await db.execute(stmt)).all()
    return [
        AsignacionOut(
            id=asignacion.id,
            escenario_id=escenario_id,
            escenario_titulo=escenario.titulo,
            estudiante_id=asignacion.estudiante_id,
            estudiante_username=username,
            estudiante_nombre=nombre_completo,
            estudiante_numero_identificacion=numero_identificacion,
            estado=asignacion.estado,
            ficha_basica_id=asignacion.ficha_basica_id,
        )
        for asignacion, username, nombre_completo, numero_identificacion in rows
    ]


@router.get("/estudiante/escenarios", response_model=list[EstudianteAsignacionOut])
async def listar_escenarios_estudiante(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EstudianteAsignacionOut]:
    """Lista las asignaciones del usuario autenticado (cualquier rol).

    Devuelve la vista sin `datos_esperados` (no-leak): cada asignación incluye el
    escenario anidado con `id`, `titulo`, `descripcion` y `cod_evento`.
    """
    stmt = (
        select(EscenarioAsignacion, EscenarioClinico)
        .join(EscenarioClinico, EscenarioClinico.id == EscenarioAsignacion.escenario_id)
        .where(EscenarioAsignacion.estudiante_id == current_user.id)
        .order_by(EscenarioAsignacion.id)
    )
    rows = (await db.execute(stmt)).all()
    return [
        EstudianteAsignacionOut(
            id=asignacion.id,
            estado=asignacion.estado,
            ficha_basica_id=asignacion.ficha_basica_id,
            escenario=EscenarioEstudianteOut.model_validate(escenario),
        )
        for asignacion, escenario in rows
    ]


async def _marcar_asignacion(
    db: AsyncSession,
    asignacion_id: int,
    ficha_basica_id: int,
    current_user: Usuario,
    estado: EstadoAsignacion,
) -> EstudianteAsignacionOut:
    """Valida la asignación (propia) y la ficha, actualiza y devuelve la vista."""
    asignacion = await db.get(EscenarioAsignacion, asignacion_id)
    if asignacion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_ASIGNACION_NO_ENCONTRADA,
        )
    if asignacion.estudiante_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_DETALLE_ENTREGA_SIN_PERMISO,
        )

    ficha = await db.get(FichaDatosBasicos, ficha_basica_id)
    if ficha is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_DETALLE_FICHA_NO_ENCONTRADA,
        )

    asignacion.ficha_basica_id = ficha_basica_id
    asignacion.estado = estado
    await db.commit()
    await db.refresh(asignacion)

    escenario = await db.get(EscenarioClinico, asignacion.escenario_id)
    return EstudianteAsignacionOut(
        id=asignacion.id,
        estado=asignacion.estado,
        ficha_basica_id=asignacion.ficha_basica_id,
        escenario=EscenarioEstudianteOut.model_validate(escenario),
    )


@router.post(
    "/estudiante/escenarios/{asignacion_id}/progreso",
    response_model=EstudianteAsignacionOut,
)
async def progresar_escenario(
    asignacion_id: int,
    payload: EntregaRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EstudianteAsignacionOut:
    """Guarda parcialmente: vincula la ficha básica y marca EN_PROGRESO.

    Permite retomar la entrega desde datos complementarios sin perder lo
    diligenciado.
    """
    return await _marcar_asignacion(
        db, asignacion_id, payload.ficha_basica_id, current_user, EstadoAsignacion.EN_PROGRESO
    )


@router.post(
    "/estudiante/escenarios/{asignacion_id}/entregar",
    response_model=EstudianteAsignacionOut,
)
async def entregar_escenario(
    asignacion_id: int,
    payload: EntregaRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EstudianteAsignacionOut:
    """Entrega la ficha de una asignación propia y la marca como COMPLETADO.

    404 si la asignación o la ficha no existen; 403 si la asignación pertenece a
    otro estudiante.
    """
    return await _marcar_asignacion(
        db, asignacion_id, payload.ficha_basica_id, current_user, EstadoAsignacion.COMPLETADO
    )


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
