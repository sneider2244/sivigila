"""Esquemas Pydantic v2 de la ficha de datos básicos (Task B5)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.ficha_basica import (
    AreaOcurrencia,
    ClasificacionCaso,
    CondicionFinal,
    Sexo,
    UndMedEdad,
)


class FichaDatosBasicosBase(BaseModel):
    """Campos comunes de la ficha (sin `id`, sin `cod_upgd`, sin auditoría)."""

    subindice: str = Field(default="01", min_length=1, max_length=5)
    cod_evento: str = Field(min_length=1, max_length=10)
    f_grabacion: date
    f_notificacion: date
    anio: int
    semana_epidemiologica: int

    tipo_id: str = Field(min_length=1, max_length=5)
    num_id: str = Field(min_length=1, max_length=20)
    primer_nombre: str = Field(min_length=1, max_length=50)
    segundo_nombre: str | None = Field(default=None, max_length=50)
    primer_apellido: str = Field(min_length=1, max_length=50)
    segundo_apellido: str | None = Field(default=None, max_length=50)
    telefono: str | None = Field(default=None, max_length=20)
    f_nacimiento: date
    edad: int
    und_med_edad: UndMedEdad
    sexo: Sexo
    identidad_genero: int = 1
    orientacion_sexual: int = 1

    pais_ocurrencia: str = Field(default="COLOMBIA", max_length=50)
    dpto_ocurrencia: str = Field(min_length=1, max_length=5)
    muni_ocurrencia: str = Field(min_length=1, max_length=5)
    area_ocurrencia: AreaOcurrencia

    grupos_poblacionales: dict = Field(default_factory=dict)

    clasificacion_caso: ClasificacionCaso
    hospitalizado: bool = False
    condicion_final: CondicionFinal = CondicionFinal.VIVO


class FichaDatosBasicosCreate(FichaDatosBasicosBase):
    """Payload de creación.

    `cod_upgd` es requerido en el payload (el frontend siempre lo envía). Para un
    usuario UPGD el backend descarta el valor recibido e impone su propia UPGD
    (`current_user.cod_upgd`); para DOCENTE se respeta el valor enviado.
    """

    cod_upgd: str = Field(min_length=1, max_length=20)


class FichaDatosBasicosUpdate(BaseModel):
    """Payload de actualización parcial (reservado para Sprint 3 — no expuesto)."""

    model_config = ConfigDict(extra="forbid")

    cod_upgd: str | None = Field(default=None, min_length=1, max_length=20)
    subindice: str | None = Field(default=None, min_length=1, max_length=5)
    cod_evento: str | None = Field(default=None, min_length=1, max_length=10)
    f_grabacion: date | None = None
    f_notificacion: date | None = None
    anio: int | None = None
    semana_epidemiologica: int | None = None
    tipo_id: str | None = Field(default=None, min_length=1, max_length=5)
    num_id: str | None = Field(default=None, min_length=1, max_length=20)
    primer_nombre: str | None = Field(default=None, min_length=1, max_length=50)
    segundo_nombre: str | None = Field(default=None, max_length=50)
    primer_apellido: str | None = Field(default=None, min_length=1, max_length=50)
    segundo_apellido: str | None = Field(default=None, max_length=50)
    telefono: str | None = Field(default=None, max_length=20)
    f_nacimiento: date | None = None
    edad: int | None = None
    und_med_edad: UndMedEdad | None = None
    sexo: Sexo | None = None
    identidad_genero: int | None = None
    orientacion_sexual: int | None = None
    pais_ocurrencia: str | None = Field(default=None, max_length=50)
    dpto_ocurrencia: str | None = Field(default=None, min_length=1, max_length=5)
    muni_ocurrencia: str | None = Field(default=None, min_length=1, max_length=5)
    area_ocurrencia: AreaOcurrencia | None = None
    grupos_poblacionales: dict | None = None
    clasificacion_caso: ClasificacionCaso | None = None
    hospitalizado: bool | None = None
    condicion_final: CondicionFinal | None = None


class FichaDatosBasicosOut(FichaDatosBasicosBase):
    """Representación pública de una ficha (respuesta de la API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cod_upgd: str
    creado_por_usuario_id: int | None
