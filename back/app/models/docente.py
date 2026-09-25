"""Modelos del módulo Docente (Task B8): escenarios clínicos y asignaciones.

El docente crea escenarios clínicos (`EscenarioClinico`) con los datos esperados
de la ficha y los asigna a estudiantes (`EscenarioAsignacion`). La evaluación
automatizada (`POST /docente/evaluar`) compara la ficha diligenciada por el
estudiante contra `EscenarioClinico.datos_esperados` (JSONB).

La sintaxis sigue `Mapped`/`mapped_column` (SQLAlchemy 2.0), consistente con los
modelos `ficha_basica.py` y `ficha_complementaria.py`.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EstadoAsignacion(str, enum.Enum):  # noqa: UP042 - patrón consistente con RolEnum
    """Ciclo de vida de una asignación de escenario a un estudiante."""

    ASIGNADO = "ASIGNADO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"


class EscenarioClinico(Base):
    """Escenario clínico creado por un docente para entrenar a estudiantes."""

    __tablename__ = "escenarios_clinicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(2000), nullable=False)
    cod_evento: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # JSONB con los valores esperados de la ficha. Estructura:
    #   { "cod_evento": "110", "clasificacion_caso": 1, "hospitalizado": false,
    #     "condicion_final": 1, "area_ocurrencia": 3, "sexo": "M",
    #     "contenido": { "fiebre": true, "exantema": false } }
    datos_esperados: Mapped[dict] = mapped_column(JSONB, nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    creado_por_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", name="fk_escenarios_clinicos_creado_por"),
        nullable=False,
    )


class EscenarioAsignacion(Base):
    """Asignación de un escenario clínico a un estudiante."""

    __tablename__ = "escenario_asignaciones"
    __table_args__ = (
        UniqueConstraint(
            "escenario_id",
            "estudiante_id",
            name="uq_escenario_asignaciones_escenario_estudiante",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    escenario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "escenarios_clinicos.id",
            name="fk_escenario_asignaciones_escenario",
        ),
        nullable=False,
        index=True,
    )
    estudiante_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", name="fk_escenario_asignaciones_estudiante"),
        nullable=False,
        index=True,
    )
    estado: Mapped[EstadoAsignacion] = mapped_column(
        SQLEnum(EstadoAsignacion, name="estado_asignacion"),
        nullable=False,
        default=EstadoAsignacion.ASIGNADO,
        server_default=EstadoAsignacion.ASIGNADO.value,
    )
    ficha_basica_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "fichas_datos_basicos.id",
            name="fk_escenario_asignaciones_ficha_basica",
        ),
        nullable=True,
    )
