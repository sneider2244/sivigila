"""Esquemas Pydantic v2 de la caracterización UPGD."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.upgd import NivelComplejidad


class UPGDCaracterizacionBase(BaseModel):
    """Campos comunes de la caracterización UPGD (sin la clave primaria)."""

    razon_social: str = Field(min_length=1, max_length=255)
    nit: str = Field(min_length=1, max_length=20)
    nivel_complejidad: NivelComplejidad
    cove: bool = False
    unidad_analisis: bool = False
    internet: bool = False
    activo: bool = True
    departamento_codigo: str | None = Field(default=None, min_length=1, max_length=2)
    municipio_codigo: str | None = Field(default=None, min_length=1, max_length=5)


class UPGDCaracterizacionCreate(UPGDCaracterizacionBase):
    """Payload de creación de una UPGD (incluye la clave primaria)."""

    cod_prestador: str = Field(min_length=1, max_length=12)


class UPGDCaracterizacionUpdate(BaseModel):
    """Payload de actualización parcial (todos los campos opcionales)."""

    razon_social: str | None = Field(default=None, min_length=1, max_length=255)
    nit: str | None = Field(default=None, min_length=1, max_length=20)
    nivel_complejidad: NivelComplejidad | None = None
    cove: bool | None = None
    unidad_analisis: bool | None = None
    internet: bool | None = None
    activo: bool | None = None
    departamento_codigo: str | None = Field(default=None, min_length=1, max_length=2)
    municipio_codigo: str | None = Field(default=None, min_length=1, max_length=5)


class UPGDCaracterizacionOut(BaseModel):
    """Representación pública de una UPGD (respuesta de la API)."""

    model_config = ConfigDict(from_attributes=True)

    cod_prestador: str
    razon_social: str
    nit: str
    nivel_complejidad: NivelComplejidad
    cove: bool
    unidad_analisis: bool
    internet: bool
    activo: bool
    departamento_codigo: str | None
    municipio_codigo: str | None
