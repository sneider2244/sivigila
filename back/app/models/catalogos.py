"""Modelos de catálogos oficiales: DIVIPOLA, eventos SIVIGILA, ocupaciones y etnias.

Estos catálogos son datos de referencia públicos (comboboxes del formulario). Se
modelan con códigos oficiales como clave primaria natural (String), no con IDs
sintéticos, para alinear la API 1:1 con el formato SIVIGILA/DIVIPOLA.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Departamento(Base):
    """Departamento de Colombia (código DIVIPOLA de 2 dígitos, ej. "05")."""

    __tablename__ = "departamentos"

    codigo: Mapped[str] = mapped_column(String(2), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)


class Municipio(Base):
    """Municipio de Colombia (código DIVIPOLA de 5 dígitos: dpto + muni)."""

    __tablename__ = "municipios"

    codigo: Mapped[str] = mapped_column(String(5), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    departamento_codigo: Mapped[str] = mapped_column(
        String(2), ForeignKey("departamentos.codigo"), nullable=False, index=True
    )


class Evento(Base):
    """Evento de notificación obligatoria SIVIGILA (ej. "100" Accidente Ofídico)."""

    __tablename__ = "eventos"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Ocupacion(Base):
    """Ocupación del paciente (clasificación usada en la ficha SIVIGILA)."""

    __tablename__ = "ocupaciones"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)


class Etnia(Base):
    """Pertenencia étnica del paciente (clasificación DANE/INS)."""

    __tablename__ = "etnias"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
