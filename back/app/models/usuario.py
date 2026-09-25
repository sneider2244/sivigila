from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.upgd import UPGDCaracterizacion


class RolEnum(str, enum.Enum):  # noqa: UP042 - patrón documentado en BACKEND_ARCH.md
    """Roles del sistema SIVIGILA (matriz RBAC)."""

    UPGD = "UPGD"
    UI = "UI"
    MUNICIPAL = "MUNICIPAL"
    DEPARTAMENTAL = "DEPARTAMENTAL"
    NACIONAL = "NACIONAL"
    DOCENTE = "DOCENTE"


class Usuario(Base):
    """Usuario autenticable del simulador."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    rol: Mapped[RolEnum] = mapped_column(
        SQLEnum(RolEnum, name="rol_enum"), nullable=False, default=RolEnum.UPGD
    )
    cod_upgd: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey(
            "upgd_caracterizacion.cod_prestador",
            name="fk_usuarios_cod_upgd_upgd_caracterizacion",
        ),
        nullable=True,
        index=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    upgd: Mapped[UPGDCaracterizacion | None] = relationship(back_populates="usuarios")
