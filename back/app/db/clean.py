"""Limpieza de datos transaccionales para dejar un estado demo limpio.

Borra: fichas (básicas + complementarias + trazabilidad), escenarios, asignaciones
y usuarios no-DOCENTE (estudiantes registrados).

Conserva: catálogos oficiales (DIVIPOLA, eventos, ocupaciones, etnias), la UPGD
demo y el usuario DOCENTE.

Uso::

    python -m app.db.clean
"""

import asyncio

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.docente import EscenarioAsignacion, EscenarioClinico
from app.models.ficha_basica import FichaDatosBasicos
from app.models.ficha_complementaria import FichaDatosComplementarios
from app.models.trazabilidad import FichaTrazabilidad
from app.models.usuario import RolEnum, Usuario


async def _contar(session: AsyncSession, model) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


async def clean_demo() -> dict[str, int]:
    """Elimina los datos transaccionales y devuelve el resumen de lo borrado."""
    async with async_session_factory() as session:
        resumen = {
            "fichas_trazabilidad": await _contar(session, FichaTrazabilidad),
            "fichas_complementarias": await _contar(session, FichaDatosComplementarios),
            "escenario_asignaciones": await _contar(session, EscenarioAsignacion),
            "escenarios_clinicos": await _contar(session, EscenarioClinico),
            "fichas_basicas": await _contar(session, FichaDatosBasicos),
            "estudiantes": await session.scalar(
                select(func.count())
                .select_from(Usuario)
                .where(Usuario.rol != RolEnum.DOCENTE)
            )
            or 0,
        }

        # Orden que respeta las FK.
        await session.execute(delete(FichaTrazabilidad))
        await session.execute(delete(FichaDatosComplementarios))
        await session.execute(delete(EscenarioAsignacion))
        await session.execute(delete(EscenarioClinico))
        await session.execute(delete(FichaDatosBasicos))
        await session.execute(delete(Usuario).where(Usuario.rol != RolEnum.DOCENTE))
        await session.commit()

    return resumen


async def main() -> None:
    resumen = await clean_demo()
    total = sum(resumen.values())
    print("Limpieza de datos demo completada.")
    for clave, cantidad in resumen.items():
        print(f"  {clave}: {cantidad}")
    print(f"  TOTAL: {total} registros eliminados")
    print("Conservados: catálogos oficiales, UPGD demo y usuario DOCENTE.")


if __name__ == "__main__":
    asyncio.run(main())
