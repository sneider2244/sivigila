"""Esquemas Pydantic v2 del complemento ofídico (Accidente Ofídico, eventos 100/820).

Estos esquemas definen la estructura EXACTA (claves snake_case) que el frontend
envía en el campo `contenido` cuando `cod_evento` es "100" o "820". Se usan para
validar el JSONB dinámico en la capa Pydantic antes de persistirlo.

Referencia de estructura (docs/BACKEND_ARCH.md, sección 3):
    {
      "datos_accidente": {"fecha": "2026-02-21", "direccion": "...", "agente_agresor": 17},
      "manifestaciones_locales": {"edema": true, "dolor": true, ...},
      "manifestaciones_sistemicas": {"nauseas": false, ...},
      "complicaciones": {"celulitis": false, ...},
      "atencion_hospitalaria": {"empleo_suero": 2, "dosis": null}
    }
"""

from datetime import date

from pydantic import BaseModel, ConfigDict


class DatosAccidente(BaseModel):
    """Datos del accidente: fecha, dirección y agente agresor."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    direccion: str
    agente_agresor: int


class ManifestacionesLocales(BaseModel):
    """Manifestaciones clínicas locales (todas booleanas)."""

    model_config = ConfigDict(extra="forbid")

    edema: bool
    dolor: bool
    eritema: bool
    equimosis: bool
    flictenas: bool
    necrosis_local: bool


class ManifestacionesSistemicas(BaseModel):
    """Manifestaciones clínicas sistémicas (todas booleanas)."""

    model_config = ConfigDict(extra="forbid")

    nauseas: bool
    vomito: bool
    dolor_abdominal: bool
    bradicardia: bool
    hipotension: bool
    sangrado: bool


class Complicaciones(BaseModel):
    """Complicaciones derivadas del accidente (todas booleanas)."""

    model_config = ConfigDict(extra="forbid")

    celulitis: bool
    necrosis: bool
    insuficiencia_renal: bool
    hipoxia: bool


class AtencionHospitalaria(BaseModel):
    """Atención hospitalaria recibida (suero antiofídico)."""

    model_config = ConfigDict(extra="forbid")

    empleo_suero: int
    # `dosis` es nullable por contrato (int | null). Se declara opcional para
    # aceptar tanto su ausencia como su valor nulo.
    dosis: int | None = None


class ComplementoOfidico(BaseModel):
    """Estructura completa del complemento de Accidente Ofídico."""

    model_config = ConfigDict(extra="forbid")

    datos_accidente: DatosAccidente
    manifestaciones_locales: ManifestacionesLocales
    manifestaciones_sistemicas: ManifestacionesSistemicas
    complicaciones: Complicaciones
    atencion_hospitalaria: AtencionHospitalaria
