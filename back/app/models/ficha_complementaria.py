"""Modelo de la ficha de datos complementarios (Task B6).

Representa la sección dinámica de datos complementarios del formulario SIVIGILA
(`datos-complementarios.html`). El contenido se almacena como JSONB para acomodar
cualquier tipo de ficha (Accidente Ofídico, Dengue, Chagas, etc.) sin alterar el
esquema relacional. Hay una única ficha complementaria por ficha básica (UNIQUE).

La sintaxis legacy `Column` se migra a `Mapped`/`mapped_column` (SQLAlchemy 2.0),
siguiendo el patrón ya establecido en `ficha_basica.py`.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FichaDatosComplementarios(Base):
    """Datos complementarios de una notificación individual SIVIGILA (JSONB dinámico)."""

    __tablename__ = "fichas_datos_complementarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Una única ficha complementaria por ficha básica (relación 1:1).
    ficha_basica_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "fichas_datos_basicos.id",
            name="fk_fichas_complementarias_ficha_basica",
        ),
        nullable=False,
        unique=True,
    )

    # Código del evento SIVIGILA (redundante con la ficha básica, pero el contrato
    # lo exige en la tabla para poder despachar la validación sin joins).
    cod_evento: Mapped[str] = mapped_column(String(10), nullable=False)

    # JSONB dinámico: estructura específica por evento. Para Accidente Ofídico
    # ("100"/"820") sigue el esquema documentado en `docs/BACKEND_ARCH.md` (sección 3).
    contenido: Mapped[dict] = mapped_column(JSONB, nullable=False)
