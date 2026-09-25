"""Modelo de trazabilidad de cambios de estado de las fichas (Task B7).

Cada fila registra una transición de estado de una ficha de datos básicos:
quién la hizo (`usuario_id`), de qué estado a qué estado, el código de ajuste
(0..6, opcional) y una observación libre. `f_cambio` se setea automáticamente.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.ficha_basica import EstadoFicha


class FichaTrazabilidad(Base):
    """Bitácora de transiciones de estado de una ficha de datos básicos."""

    __tablename__ = "fichas_trazabilidad"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ficha_basica_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "fichas_datos_basicos.id",
            name="fk_fichas_trazabilidad_ficha_basica",
        ),
        nullable=False,
        index=True,
    )

    estado_anterior: Mapped[EstadoFicha] = mapped_column(
        SQLEnum(EstadoFicha, name="estado_ficha"), nullable=False
    )
    estado_nuevo: Mapped[EstadoFicha] = mapped_column(
        SQLEnum(EstadoFicha, name="estado_ficha"), nullable=False
    )

    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", name="fk_fichas_trazabilidad_usuario"),
        nullable=False,
    )

    # Código de ajuste oficial SIVIGILA (0..6). RULING: int persistido; el rango
    # 0..6 se valida en la capa Pydantic (EstadoTransitionRequest.ajuste).
    ajuste: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    f_cambio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
