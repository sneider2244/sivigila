"""Modelo de caracterización de UPGD (Unidad Primaria Generadora de Datos).

Representa la información institucional de una UPGD que el simulador usa para
vincular usuarios (rol UPGD) y para poblar el encabezado de las fichas de
notificación. La clave primaria es el `cod_prestador` oficial (12 caracteres).
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class NivelComplejidad(enum.IntEnum):
    """Nivel de complejidad institucional de la UPGD (rango oficial 1..4)."""

    BAJO = 1
    MEDIO = 2
    ALTO = 3
    MUY_ALTO = 4


class UPGDCaracterizacion(Base):
    """Caracterización institucional de una UPGD."""

    __tablename__ = "upgd_caracterizacion"

    cod_prestador: Mapped[str] = mapped_column(String(12), primary_key=True)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nit: Mapped[str] = mapped_column(String(20), nullable=False)
    # RULING: se persiste como Integer (contrato JSON: int 1..4). La validación
    # del rango y el tipado por enum se aplican en la capa Pydantic (NivelComplejidad).
    nivel_complejidad: Mapped[int] = mapped_column(Integer, nullable=False)
    cove: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unidad_analisis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    internet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    departamento_codigo: Mapped[str | None] = mapped_column(
        String(2), ForeignKey("departamentos.codigo"), nullable=True
    )
    municipio_codigo: Mapped[str | None] = mapped_column(
        String(5), ForeignKey("municipios.codigo"), nullable=True
    )

    usuarios: Mapped[list[Usuario]] = relationship(back_populates="upgd")
