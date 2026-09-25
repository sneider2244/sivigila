"""Esquemas Pydantic v2 de trazabilidad de estados de fichas (Task B7)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ficha_basica import EstadoFicha


class EstadoTransitionRequest(BaseModel):
    """Payload de una transición de estado de una ficha de datos básicos.

    `ajuste` es el código oficial SIVIGILA (0..6); solo tiene sentido cuando se
    solicita un ajuste (estado_nuevo == EN_AJUSTE), pero el contrato lo mantiene
    opcional y el rango se valida con Pydantic (0..6, de lo contrario 422).
    """

    model_config = ConfigDict(extra="forbid")

    estado_nuevo: EstadoFicha
    ajuste: int | None = Field(default=None, ge=0, le=6)
    observacion: str | None = Field(default=None, max_length=500)


class TrazabilidadOut(BaseModel):
    """Representación pública de una fila de trazabilidad (respuesta de la API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ficha_basica_id: int
    estado_anterior: EstadoFicha
    estado_nuevo: EstadoFicha
    usuario_id: int
    ajuste: int | None
    observacion: str | None
    f_cambio: datetime
