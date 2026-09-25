"""Esquemas Pydantic v2 de la ficha de datos complementarios (Task B6).

La validación del campo `contenido` (JSONB) se despacha según `cod_evento`:
- "100" / "820" (Accidente Ofídico): se valida contra `ComplementoOfidico`.
- Cualquier otro evento: se acepta como `dict` genérico (se extiende luego).
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.schemas.complemento_ofidico import ComplementoOfidico

# Eventos cuyo complemento se valida con el esquema ofídico (Accidente Ofídico).
_COD_EVENTOS_OFIDICOS = {"100", "820"}


class FichaDatosComplementariosBase(BaseModel):
    """Campos comunes (sin `id`). El `contenido` se valida por evento."""

    model_config = ConfigDict(extra="forbid")

    cod_evento: str = Field(min_length=1, max_length=10)
    contenido: dict

    @model_validator(mode="after")
    def _validar_contenido_por_evento(self) -> Self:
        """Despacha la validación del JSONB según el código de evento."""
        if self.cod_evento in _COD_EVENTOS_OFIDICOS:
            try:
                ComplementoOfidico.model_validate(self.contenido)
            except ValidationError as exc:
                raise ValueError(
                    f"contenido inválido para el evento {self.cod_evento}: {exc}"
                ) from exc
        return self


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
