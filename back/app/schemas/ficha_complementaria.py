"""Esquemas Pydantic v2 de la ficha de datos complementarios.

El campo `contenido` (JSONB) es un `dict` GENÉRICO: se persiste tal cual, sin
validación por evento (la validación específica se reintroduce cuando exista un
formulario/ esquema por evento).
"""

from pydantic import BaseModel, ConfigDict, Field


class FichaDatosComplementariosBase(BaseModel):
    """Campos comunes (sin `id`). El `contenido` es un dict genérico."""

    model_config = ConfigDict(extra="forbid")

    cod_evento: str = Field(min_length=1, max_length=10)
    contenido: dict


class FichaDatosComplementariosCreate(FichaDatosComplementariosBase):
    """Payload de creación: referencia a la ficha básica + código de evento + contenido."""

    ficha_basica_id: int


class FichaDatosComplementariosUpdate(FichaDatosComplementariosBase):
    """Payload de actualización (PUT): código de evento + contenido (sin referencia)."""


class FichaDatosComplementariosOut(BaseModel):
    """Representación pública de una ficha complementaria (respuesta de la API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ficha_basica_id: int
    cod_evento: str
    contenido: dict
