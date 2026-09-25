"""Esquemas Pydantic v2 de respuesta para los catálogos oficiales."""

from pydantic import BaseModel, ConfigDict


class DepartamentoOut(BaseModel):
    """Departamento en formato de catálogo."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str


class MunicipioOut(BaseModel):
    """Municipio en formato de catálogo (incluye su departamento)."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    departamento_codigo: str


class EventoOut(BaseModel):
    """Evento de notificación SIVIGILA en formato de catálogo."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    descripcion: str | None


class OcupacionOut(BaseModel):
    """Ocupación en formato de catálogo."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str


class EtniaOut(BaseModel):
    """Etnia en formato de catálogo."""

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
