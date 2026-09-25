"""Modelo de la ficha de notificación individual — Datos Básicos (Task B5).

Representa la sección "Datos Básicos" del formulario SIVIGILA (`sivigila.html`).
Las columnas siguen EXACTAMENTE el contrato documentado en `docs/BACKEND_ARCH.md`
(sección 2), migrando la sintaxis legacy `Column` a `Mapped`/`mapped_column`.
"""

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Sexo(str, enum.Enum):  # noqa: UP042 - patrón consistente con RolEnum
    """Sexo biológico del paciente (valores oficiales del formulario)."""

    MASCULINO = "M"
    FEMENINO = "F"


class UndMedEdad(enum.IntEnum):
    """Unidad de medida de la edad (1: años, 2: meses, 3: días)."""

    ANIOS = 1
    MESES = 2
    DIAS = 3


class AreaOcurrencia(enum.IntEnum):
    """Área de ocurrencia del caso (1: cabecera, 2: centro poblado, 3: rural)."""

    CABECERA = 1
    CENTRO_POBLADO = 2
    RURAL = 3


class ClasificacionCaso(enum.IntEnum):
    """Clasificación inicial del caso (1: sospechoso, 2: probable, 3: confirmado, 4: descartado)."""

    SOSPECHOSO = 1
    PROBABLE = 2
    CONFIRMADO = 3
    DESCARTADO = 4


class CondicionFinal(enum.IntEnum):
    """Condición final del paciente (1: vivo, 2: muerto)."""

    VIVO = 1
    MUERTO = 2


class FichaDatosBasicos(Base):
    """Ficha de datos básicos de una notificación individual SIVIGILA."""

    __tablename__ = "fichas_datos_basicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Encabezado de notificación
    cod_upgd: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    subindice: Mapped[str] = mapped_column(String(5), nullable=False, default="01")
    cod_evento: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    f_grabacion: Mapped[date] = mapped_column(Date, nullable=False)
    f_notificacion: Mapped[date] = mapped_column(Date, nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    semana_epidemiologica: Mapped[int] = mapped_column(Integer, nullable=False)

    # Identificación del paciente
    tipo_id: Mapped[str] = mapped_column(String(5), nullable=False)
    num_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    primer_nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    segundo_nombre: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primer_apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    segundo_apellido: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    f_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    edad: Mapped[int] = mapped_column(Integer, nullable=False)
    # RULING: se persiste como Integer (contrato JSON: int 1..3). La validación
    # del rango y el tipado por enum se aplican en la capa Pydantic (UndMedEdad).
    und_med_edad: Mapped[int] = mapped_column(Integer, nullable=False)
    sexo: Mapped[str] = mapped_column(String(1), nullable=False)
    identidad_genero: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    orientacion_sexual: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Ubicación y demografía
    pais_ocurrencia: Mapped[str] = mapped_column(String(50), nullable=False, default="COLOMBIA")
    dpto_ocurrencia: Mapped[str] = mapped_column(String(5), nullable=False)
    muni_ocurrencia: Mapped[str] = mapped_column(String(5), nullable=False)
    # RULING: idem, int 1..3 validado por AreaOcurrencia en Pydantic.
    area_ocurrencia: Mapped[int] = mapped_column(Integer, nullable=False)

    # Grupos poblacionales (JSONB libre; el frontend guarda los extras condicionales)
    grupos_poblacionales: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Datos clínicos
    # RULING: int 1..4 validado por ClasificacionCaso en Pydantic.
    clasificacion_caso: Mapped[int] = mapped_column(Integer, nullable=False)
    hospitalizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # RULING: int 1..2 validado por CondicionFinal en Pydantic.
    condicion_final: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Auditoría del simulador
    creado_por_usuario_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", name="fk_fichas_basicas_creado_por_usuario"),
        nullable=True,
    )
