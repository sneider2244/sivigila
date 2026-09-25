import asyncio
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Evento, Usuario
from app.db.session import AsyncSessionLocal
from app.domain.enums import Rol
from app.domain.permissions import permisos_por_defecto
from app.domain.security import hash_password

EVENTOS_DEFAULT: list[dict[str, Any]] = [
    {
        "codigo": "205",
        "nombre": "Enfermedad de Chagas",
        "campos": [
            {"key": "sintomas", "label": "Síntomas", "tipo": "texto"},
            {"key": "fiebre", "label": "Fiebre", "tipo": "si_no"},
            {"key": "cardiopatia", "label": "Cardiopatía chagásica", "tipo": "si_no"},
            {"key": "megasindrome", "label": "Megasíndrome (esofágico/colónico)", "tipo": "si_no"},
            {
                "key": "via_transmision",
                "label": "Vía de transmisión probable",
                "tipo": "lista",
                "opciones": ["Vectorial", "Transfusional", "Congénita", "Oral", "Desconocida"],
            },
            {
                "key": "resultado_serologia",
                "label": "Resultado serología",
                "tipo": "lista",
                "opciones": ["Reactivo", "No reactivo", "Indeterminado", "Pendiente"],
            },
        ],
    },
    {
        "codigo": "100",
        "nombre": "Accidente Ofídico",
        "campos": [
            {"key": "actividad", "label": "Actividad al momento del accidente", "tipo": "texto"},
            {"key": "localizacion", "label": "Localización de la mordedura", "tipo": "texto"},
            {"key": "edema", "label": "Edema", "tipo": "si_no"},
            {"key": "dolor", "label": "Dolor", "tipo": "si_no"},
            {"key": "necrosis", "label": "Necrosis", "tipo": "si_no"},
            {"key": "shock", "label": "Shock hipovolémico", "tipo": "si_no"},
            {"key": "suero_antiofidico", "label": "Suero antiofídico administrado", "tipo": "si_no"},
            {
                "key": "gravedad",
                "label": "Gravedad del accidente",
                "tipo": "lista",
                "opciones": ["Leve", "Moderado", "Severo"],
            },
        ],
    },
    {
        "codigo": "210",
        "nombre": "Dengue",
        "campos": [
            {"key": "fiebre", "label": "Fiebre ≥ 38°C", "tipo": "si_no"},
            {"key": "signos_alarma", "label": "Signos de alarma", "tipo": "si_no"},
            {"key": "dolor_abdominal", "label": "Dolor abdominal intenso", "tipo": "si_no"},
            {"key": "sangrado", "label": "Sangrado espontáneo", "tipo": "si_no"},
            {
                "key": "clasificacion_dengue",
                "label": "Clasificación",
                "tipo": "lista",
                "opciones": [
                    "Dengue sin signos de alarma",
                    "Dengue con signos de alarma",
                    "Dengue grave",
                ],
            },
            {
                "key": "resultado_igm",
                "label": "Resultado IgM",
                "tipo": "lista",
                "opciones": ["Positivo", "Negativo", "Pendiente"],
            },
        ],
    },
]


async def _seed_eventos(session: AsyncSession) -> None:
    total = await session.scalar(select(func.count()).select_from(Evento))
    if total:
        return
    for ev in EVENTOS_DEFAULT:
        session.add(Evento(codigo=ev["codigo"], nombre=ev["nombre"], campos_json=ev["campos"]))
    await session.commit()


async def _seed_admin(session: AsyncSession) -> None:
    total = await session.scalar(select(func.count()).select_from(Usuario))
    if total:
        return
    password_hash, salt = hash_password(settings.admin_password)
    session.add(
        Usuario(
            username=settings.admin_username,
            password_hash=password_hash,
            salt=salt,
            nombre_completo=settings.admin_nombre,
            rol=Rol.SUPER_ADMIN.value,
            permisos=permisos_por_defecto(Rol.SUPER_ADMIN),
            activo=True,
        )
    )
    await session.commit()


async def seed(session: AsyncSession) -> None:
    await _seed_eventos(session)
    await _seed_admin(session)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
