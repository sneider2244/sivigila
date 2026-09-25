"""Seed de datos iniciales para desarrollo (usuario DOCENTE + catálogos oficiales)."""

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.catalogos import Departamento, Etnia, Evento, Municipio, Ocupacion
from app.models.usuario import RolEnum, Usuario

DEFAULT_ADMIN_USER = "docente"
DEFAULT_ADMIN_PASSWORD = "docente123"
DEFAULT_ADMIN_NOMBRE = "Usuario Docente"

# ---------------------------------------------------------------------------
# Catálogos oficiales (datos de referencia).
#
# NOTA DE CURACIÓN: los códigos DIVIPOLA de departamentos y de las capitales
# (terminación "001") son oficiales y completos. Los municipios no capitales
# son una selección representativa de los principales por departamento; la
# lista completa (~1100 municipios) se puede añadir a `MUNICIPIOS` sin tocar
# el resto del seed. Los eventos son un subconjunto educativo de los eventos
# de notificación obligatoria SIVIGILA. Ocupaciones es una lista acotada y
# Etnia sigue la clasificación oficial DANE/INS (6 grupos, completa).
# ---------------------------------------------------------------------------

# 33 departamentos (32 + Bogotá D.C.), códigos DIVIPOLA oficiales.
DEPARTAMENTOS: list[tuple[str, str]] = [
    ("05", "Antioquia"),
    ("08", "Atlántico"),
    ("11", "Bogotá D.C."),
    ("13", "Bolívar"),
    ("15", "Boyacá"),
    ("17", "Caldas"),
    ("18", "Caquetá"),
    ("19", "Cauca"),
    ("20", "Cesar"),
    ("23", "Córdoba"),
    ("25", "Cundinamarca"),
    ("27", "Chocó"),
    ("41", "Huila"),
    ("44", "La Guajira"),
    ("47", "Magdalena"),
    ("50", "Meta"),
    ("52", "Nariño"),
    ("54", "Norte de Santander"),
    ("63", "Quindío"),
    ("66", "Risaralda"),
    ("68", "Santander"),
    ("70", "Sucre"),
    ("73", "Tolima"),
    ("76", "Valle del Cauca"),
    ("81", "Arauca"),
    ("85", "Casanare"),
    ("86", "Putumayo"),
    ("88", "San Andrés"),
    ("91", "Amazonas"),
    ("94", "Guainía"),
    ("95", "Guaviare"),
    ("97", "Vaupés"),
    ("99", "Vichada"),
]

# (codigo, nombre, departamento_codigo) — capitales + municipios principales.
MUNICIPIOS: list[tuple[str, str, str]] = [
    # Antioquia
    ("05001", "Medellín", "05"),
    ("05045", "Apartadó", "05"),
    ("05088", "Bello", "05"),
    ("05266", "Envigado", "05"),
    ("05360", "Itagüí", "05"),
    ("05615", "Rionegro", "05"),
    ("05837", "Turbo", "05"),
    # Atlántico
    ("08001", "Barranquilla", "08"),
    ("08078", "Baranoa", "08"),
    ("08433", "Malambo", "08"),
    ("08758", "Soledad", "08"),
    # Bogotá D.C.
    ("11001", "Bogotá D.C.", "11"),
    # Bolívar
    ("13001", "Cartagena", "13"),
    ("13244", "El Carmen de Bolívar", "13"),
    ("13430", "Magangué", "13"),
    ("13836", "Turbaco", "13"),
    # Boyacá
    ("15001", "Tunja", "15"),
    ("15176", "Chiquinquirá", "15"),
    ("15238", "Duitama", "15"),
    ("15572", "Puerto Boyacá", "15"),
    ("15759", "Sogamoso", "15"),
    # Caldas
    ("17001", "Manizales", "17"),
    ("17174", "Chinchiná", "17"),
    ("17380", "La Dorada", "17"),
    ("17867", "Villamaría", "17"),
    # Caquetá
    ("18001", "Florencia", "18"),
    ("18592", "Puerto Rico", "18"),
    ("18753", "San Vicente del Caguán", "18"),
    # Cauca
    ("19001", "Popayán", "19"),
    ("19548", "Piendamó", "19"),
    ("19573", "Puerto Tejada", "19"),
    ("19698", "Santander de Quilichao", "19"),
    # Cesar
    ("20001", "Valledupar", "20"),
    ("20011", "Aguachica", "20"),
    ("20060", "Bosconia", "20"),
    # Córdoba
    ("23001", "Montería", "23"),
    ("23162", "Cereté", "23"),
    ("23417", "Lorica", "23"),
    ("23466", "Montelíbano", "23"),
    ("23660", "Sahagún", "23"),
    # Cundinamarca
    ("25175", "Chía", "25"),
    ("25269", "Facatativá", "25"),
    ("25290", "Fusagasugá", "25"),
    ("25307", "Girardot", "25"),
    ("25754", "Soacha", "25"),
    ("25899", "Zipaquirá", "25"),
    # Chocó
    ("27001", "Quibdó", "27"),
    ("27361", "Istmina", "27"),
    ("27615", "Riosucio", "27"),
    # Huila
    ("41001", "Neiva", "41"),
    ("41298", "Garzón", "41"),
    ("41396", "La Plata", "41"),
    ("41551", "Pitalito", "41"),
    # La Guajira
    ("44001", "Riohacha", "44"),
    ("44430", "Maicao", "44"),
    ("44650", "San Juan del Cesar", "44"),
    ("44847", "Uribia", "44"),
    # Magdalena
    ("47001", "Santa Marta", "47"),
    ("47189", "Ciénaga", "47"),
    ("47245", "El Banco", "47"),
    ("47288", "Fundación", "47"),
    # Meta
    ("50001", "Villavicencio", "50"),
    ("50006", "Acacías", "50"),
    ("50313", "Granada", "50"),
    ("50573", "Puerto López", "50"),
    # Nariño
    ("52001", "Pasto", "52"),
    ("52356", "Ipiales", "52"),
    ("52835", "Tumaco", "52"),
    ("52838", "Túquerres", "52"),
    # Norte de Santander
    ("54001", "Cúcuta", "54"),
    ("54498", "Ocaña", "54"),
    ("54518", "Pamplona", "54"),
    ("54874", "Villa del Rosario", "54"),
    # Quindío
    ("63001", "Armenia", "63"),
    ("63130", "Calarcá", "63"),
    ("63401", "La Tebaida", "63"),
    ("63470", "Montenegro", "63"),
    # Risaralda
    ("66001", "Pereira", "66"),
    ("66170", "Dosquebradas", "66"),
    ("66682", "Santa Rosa de Cabal", "66"),
    # Santander
    ("68001", "Bucaramanga", "68"),
    ("68081", "Barrancabermeja", "68"),
    ("68276", "Floridablanca", "68"),
    ("68307", "Girón", "68"),
    ("68547", "Piedecuesta", "68"),
    ("68679", "San Gil", "68"),
    # Sucre
    ("70001", "Sincelejo", "70"),
    ("70215", "Corozal", "70"),
    ("70708", "San Marcos", "70"),
    ("70820", "Tolú", "70"),
    # Tolima
    ("73001", "Ibagué", "73"),
    ("73168", "Chaparral", "73"),
    ("73268", "Espinal", "73"),
    ("73349", "Honda", "73"),
    ("73449", "Melgar", "73"),
    # Valle del Cauca
    ("76001", "Cali", "76"),
    ("76109", "Buenaventura", "76"),
    ("76111", "Buga", "76"),
    ("76147", "Cartago", "76"),
    ("76520", "Palmira", "76"),
    ("76834", "Tuluá", "76"),
    ("76892", "Yumbo", "76"),
    # Arauca
    ("81001", "Arauca", "81"),
    ("81736", "Saravena", "81"),
    ("81794", "Tame", "81"),
    # Casanare
    ("85001", "Yopal", "85"),
    ("85010", "Aguazul", "85"),
    ("85250", "Paz de Ariporo", "85"),
    ("85440", "Villanueva", "85"),
    # Putumayo
    ("86001", "Mocoa", "86"),
    ("86320", "Orito", "86"),
    ("86568", "Puerto Asís", "86"),
    ("86865", "Valle del Guamuez", "86"),
    # San Andrés
    ("88001", "San Andrés", "88"),
    ("88564", "Providencia", "88"),
    # Amazonas
    ("91001", "Leticia", "91"),
    ("91540", "Puerto Nariño", "91"),
    # Guainía
    ("94001", "Inírida", "94"),
    # Guaviare
    ("95001", "San José del Guaviare", "95"),
    ("95025", "El Retorno", "95"),
    # Vaupés
    ("97001", "Mitú", "97"),
    ("97161", "Carurú", "97"),
    # Vichada
    ("99001", "Puerto Carreño", "99"),
    ("99773", "Cumaribo", "99"),
]

# (codigo, nombre, descripcion) — subconjunto educativo de eventos SIVIGILA.
EVENTOS: list[tuple[str, str, str | None]] = [
    ("100", "Accidente Ofídico", "Mordedura por serpiente venenosa y su atención."),
    ("110", "Dengue", "Dengue (sin signos de alarma)."),
    ("115", "Dengue grave", "Dengue con signos de alarma / dengue grave."),
    ("120", "Malaria", "Malaria (todas las especies)."),
    ("130", "Chagas", "Enfermedad de Chagas (tripanosomiasis americana)."),
    ("140", "Leishmaniasis", "Leishmaniasis cutánea y mucosa."),
    ("150", "Leptospirosis", "Leptospirosis."),
    ("160", "Fiebre amarilla", "Fiebre amarilla."),
    ("200", "Sífilis gestacional", "Sífilis gestacional."),
    ("210", "Sífilis congénita", "Sífilis congénita."),
    ("220", "VIH / Sida", "Infección por VIH y mortalidad por Sida."),
    ("230", "Tuberculosis", "Tuberculosis (todas las formas)."),
    ("240", "Lepra", "Lepra (enfermedad de Hansen)."),
    ("300", "Intoxicación por plaguicidas", "Intoxicaciones agudas por plaguicidas."),
    ("310", "Intoxicación por fármacos", "Intoxicaciones agudas por fármacos."),
    ("400", "Mortalidad materna", "Mortalidad materna."),
    ("410", "Mortalidad perinatal", "Mortalidad perinatal y neonatal tardía."),
    ("500", "Bajo peso al nacer", "Bajo peso al nacer."),
    (
        "820",
        "Agresión por animal transmisor de rabia",
        "Agresiones por animales potencialmente transmisores de rabia.",
    ),
]

# Ocupaciones (lista acotada de las más comunes en la ficha SIVIGILA).
OCUPACIONES: list[tuple[str, str]] = [
    ("1", "Ama de casa"),
    ("2", "Estudiante"),
    ("3", "Agricultor"),
    ("4", "Ganadero"),
    ("5", "Minero"),
    ("6", "Comerciante"),
    ("7", "Profesional"),
    ("8", "Docente"),
    ("9", "Personal de salud"),
    ("10", "Conductor"),
    ("11", "Militar / Policía"),
    ("12", "Desempleado"),
    ("13", "Otro"),
]

# Etnias reconocidas (clasificación oficial DANE/INS — 6 grupos, completa).
ETNIAS: list[tuple[str, str]] = [
    ("1", "Indígena"),
    ("2", "ROM (Gitano)"),
    ("3", "Raizal (San Andrés y Providencia)"),
    ("4", "Palenquero (San Basilio de Palenque)"),
    ("5", "Negro, mulato, afrocolombiano o afrodescendiente"),
    ("6", "Ninguno de los anteriores"),
]


async def seed_users() -> None:
    """Upsert del usuario DOCENTE por defecto (credenciales por variables de entorno)."""
    username = os.getenv("SIVIGILA_ADMIN_USER", DEFAULT_ADMIN_USER)
    password = os.getenv("SIVIGILA_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    nombre_completo = os.getenv("SIVIGILA_ADMIN_NOMBRE", DEFAULT_ADMIN_NOMBRE)

    async with async_session_factory() as session:
        user = await session.scalar(select(Usuario).where(Usuario.username == username))
        if user is None:
            user = Usuario(
                username=username,
                hashed_password=get_password_hash(password),
                nombre_completo=nombre_completo,
                rol=RolEnum.DOCENTE,
                activo=True,
            )
            session.add(user)
        else:
            user.hashed_password = get_password_hash(password)
            user.nombre_completo = nombre_completo
            user.rol = RolEnum.DOCENTE
            user.activo = True
        await session.commit()


async def _insert_missing(session: AsyncSession, instances: list) -> int:
    """Inserta solo las instancias cuyo `codigo` (PK) aún no existe. Retorna insertados."""
    model = type(instances[0])
    existing = set(await session.scalars(select(model.codigo)))
    to_add = [inst for inst in instances if inst.codigo not in existing]
    if to_add:
        session.add_all(to_add)
    return len(to_add)


async def seed_catalogos(
    session_factory: async_sessionmaker[AsyncSession] = async_session_factory,
) -> dict[str, int]:
    """Siembra idempotente de catálogos (no duplica registros existentes)."""
    departamentos = [Departamento(codigo=c, nombre=n) for c, n in DEPARTAMENTOS]
    municipios = [
        Municipio(codigo=c, nombre=n, departamento_codigo=d) for c, n, d in MUNICIPIOS
    ]
    eventos = [Evento(codigo=c, nombre=n, descripcion=d) for c, n, d in EVENTOS]
    ocupaciones = [Ocupacion(codigo=c, nombre=n) for c, n in OCUPACIONES]
    etnias = [Etnia(codigo=c, nombre=n) for c, n in ETNIAS]

    async with session_factory() as session:
        inserted = {
            "departamentos": await _insert_missing(session, departamentos),
            "municipios": await _insert_missing(session, municipios),
            "eventos": await _insert_missing(session, eventos),
            "ocupaciones": await _insert_missing(session, ocupaciones),
            "etnias": await _insert_missing(session, etnias),
        }
        await session.commit()
    return inserted


async def seed() -> None:
    """Ejecuta todos los seeds del proyecto."""
    await seed_users()
    inserted = await seed_catalogos()
    print("Seed usuarios: OK (docente).")
    print(f"Seed catálogos: {inserted}")


if __name__ == "__main__":
    asyncio.run(seed())
