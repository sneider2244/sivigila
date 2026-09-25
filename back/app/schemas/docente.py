"""Esquemas Pydantic v2 del módulo Docente (Task B8).

Incluye los payloads y representaciones de escenarios clínicos, asignaciones y
del resultado de la evaluación automatizada de fichas diligenciadas.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.docente import EstadoAsignacion
from app.models.usuario import RolEnum


class EscenarioCreate(BaseModel):
    """Payload de creación de un escenario clínico (solo DOCENTE)."""

    model_config = ConfigDict(extra="forbid")

    titulo: str = Field(min_length=1, max_length=200)
    descripcion: str = Field(min_length=1, max_length=2000)
    cod_evento: str = Field(min_length=1, max_length=10)
    datos_esperados: dict
    activo: bool = True


class EscenarioOut(BaseModel):
    """Representación pública de un escenario clínico (respuesta de la API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: str
    cod_evento: str
    datos_esperados: dict
    activo: bool
    creado_por_id: int


class AsignacionCreate(BaseModel):
    """Payload para asignar un escenario a múltiples estudiantes (bulk)."""

    model_config = ConfigDict(extra="forbid")

    estudiante_ids: list[int]

    @field_validator("estudiante_ids")
    @classmethod
    def _no_vacia(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("estudiante_ids no puede estar vacía")
        return value


class AsignacionOut(BaseModel):
    """Representación de una asignación con datos desnormalizados para el listado."""

    id: int
    escenario_id: int
    escenario_titulo: str
    estudiante_id: int
    estudiante_username: str
    estudiante_nombre: str
    estado: EstadoAsignacion
    ficha_basica_id: int | None


class EstudianteOut(BaseModel):
    """Representación de un estudiante para el listado del docente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nombre_completo: str
    rol: RolEnum
    numero_identificacion: str | None
    activo: bool


class EvaluarRequest(BaseModel):
    """Payload de evaluación automatizada de una ficha contra un escenario."""

    model_config = ConfigDict(extra="forbid")

    ficha_basica_id: int
    escenario_id: int


class EvaluacionDetalle(BaseModel):
    """Resultado de un único campo comparado."""

    campo: str
    esperado: Any
    obtenido: Any
    correcto: bool


class EvaluacionResult(BaseModel):
    """Resultado global de la evaluación automatizada."""

    puntaje: float
    aciertos: int
    total: int
    detalle: list[EvaluacionDetalle]
