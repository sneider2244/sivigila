"""Tests del módulo de ficha de datos complementarios (Task B6)."""

import asyncio

import pytest
from conftest import TestSessionFactory
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.upgd import UPGDCaracterizacion
from app.models.usuario import RolEnum, Usuario

DOCENTE_USERNAME = "docente"
DOCENTE_PASSWORD = "docente123"

UPGD_USERNAME = "upgd_complemento"
UPGD_PASSWORD = "upgd123"
UPGD_OWN_COD = "150010123456"
UPGD_OTRO_COD = "150010654321"

FICHA_INEXISTENTE_ID = 999999


def _payload_ficha_basica(cod_upgd: str, num_id: str, **overrides) -> dict:
    data = {
        "cod_upgd": cod_upgd,
        "cod_evento": "100",
        "f_grabacion": "2026-09-25",
        "f_notificacion": "2026-09-25",
        "anio": 2026,
        "semana_epidemiologica": 38,
        "tipo_id": "CC",
        "num_id": num_id,
        "primer_nombre": "Pepito",
        "primer_apellido": "Perez",
        "f_nacimiento": "1990-01-15",
        "edad": 36,
        "und_med_edad": 1,
        "sexo": "M",
        "dpto_ocurrencia": "05",
        "muni_ocurrencia": "05001",
        "area_ocurrencia": 1,
        "clasificacion_caso": 1,
    }
    data.update(overrides)
    return data


def _contenido_ofidico_valido() -> dict:
    return {
        "datos_accidente": {
            "fecha": "2026-09-24",
            "direccion": "CRA 23 SUR 9-87",
            "agente_agresor": 17,
        },
        "manifestaciones_locales": {
            "edema": True,
            "dolor": True,
            "eritema": False,
            "equimosis": False,
            "flictenas": False,
            "necrosis_local": False,
        },
        "manifestaciones_sistemicas": {
            "nauseas": False,
            "vomito": False,
            "dolor_abdominal": False,
            "bradicardia": False,
            "hipotension": False,
            "sangrado": False,
        },
        "complicaciones": {
            "celulitis": False,
            "necrosis": False,
            "insuficiencia_renal": False,
            "hipoxia": True,
        },
        "atencion_hospitalaria": {
            "empleo_suero": 2,
            "dosis": None,
        },
    }


def _payload_complementaria(ficha_basica_id: int, **overrides) -> dict:
    data = {
        "ficha_basica_id": ficha_basica_id,
        "cod_evento": "100",
        "contenido": _contenido_ofidico_valido(),
    }
    data.update(overrides)
    return data


async def _seed_upgd_user() -> None:
    """Crea (idempotente) las UPGD de referencia y el usuario UPGD de prueba."""
    async with TestSessionFactory() as session:
        for cod, razon in ((UPGD_OWN_COD, "UPGD Propia"), (UPGD_OTRO_COD, "UPGD Ajena")):
            if await session.get(UPGDCaracterizacion, cod) is None:
                session.add(
                    UPGDCaracterizacion(
                        cod_prestador=cod,
                        razon_social=razon,
                        nit="900000000-1",
                        nivel_complejidad=2,
                        cove=True,
                        unidad_analisis=True,
                        internet=True,
                        activo=True,
                        departamento_codigo="05",
                        municipio_codigo="05001",
                    )
                )
        await session.flush()
        existing = await session.scalar(select(Usuario).where(Usuario.username == UPGD_USERNAME))
        if existing is None:
            session.add(
                Usuario(
                    username=UPGD_USERNAME,
                    hashed_password=get_password_hash(UPGD_PASSWORD),
                    nombre_completo="Usuario UPGD Test",
                    rol=RolEnum.UPGD,
                    cod_upgd=UPGD_OWN_COD,
                    activo=True,
                )
            )
            await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_complemento() -> None:
    asyncio.run(_seed_upgd_user())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _crear_ficha_basica(
    client: AsyncClient, token: str, cod_upgd: str, num_id: str
) -> int:
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_payload_ficha_basica(cod_upgd, num_id),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_sin_auth_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/fichas/datos-complementarios/1")
    assert resp.status_code == 401
    resp = await client.post(
        "/api/v1/fichas/datos-complementarios", json=_payload_complementaria(1)
    )
    assert resp.status_code == 401


async def test_crear_ofidico_valido_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha_basica(client, token, UPGD_OWN_COD, "1023456700")

    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json=_payload_complementaria(ficha_id),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] > 0
    assert data["ficha_basica_id"] == ficha_id
    assert data["cod_evento"] == "100"
    assert data["contenido"]["datos_accidente"]["agente_agresor"] == 17
    assert data["contenido"]["atencion_hospitalaria"]["dosis"] is None


async def test_contenido_generico_aceptado_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha_basica(client, token, UPGD_OWN_COD, "1023456701")

    # El contenido ya no se valida por evento: se acepta cualquier dict.
    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json={
            "ficha_basica_id": ficha_id,
            "cod_evento": "100",
            "contenido": {"observacion": "forma libre", "n": 1},
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text


async def test_ficha_basica_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json=_payload_complementaria(FICHA_INEXISTENTE_ID),
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_any_rol_puede_crear_complementaria_201(client: AsyncClient) -> None:
    # RBAC desacoplado (R20): cualquier rol autenticado puede crear, sin scoping.
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ajena_id = await _crear_ficha_basica(client, token_docente, UPGD_OTRO_COD, "1023456702")

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json=_payload_complementaria(ajena_id),
        headers=_auth(token_upgd),
    )
    assert resp.status_code == 201, resp.text


async def test_upgd_ficha_propia_201(client: AsyncClient) -> None:
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    propia_id = await _crear_ficha_basica(client, token_docente, UPGD_OWN_COD, "1023456703")

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json=_payload_complementaria(propia_id),
        headers=_auth(token_upgd),
    )
    assert resp.status_code == 201, resp.text


async def test_leer_200_y_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha_basica(client, token, UPGD_OWN_COD, "1023456704")
    await client.post(
        "/api/v1/fichas/datos-complementarios",
        json=_payload_complementaria(ficha_id),
        headers=_auth(token),
    )

    resp = await client.get(
        f"/api/v1/fichas/datos-complementarios/{ficha_id}", headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json()["ficha_basica_id"] == ficha_id

    resp = await client.get(
        f"/api/v1/fichas/datos-complementarios/{FICHA_INEXISTENTE_ID}", headers=_auth(token)
    )
    assert resp.status_code == 404


async def test_crear_generico_dict_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha_basica(client, token, UPGD_OWN_COD, "1023456705")

    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json={
            "ficha_basica_id": ficha_id,
            "cod_evento": "110",
            "contenido": {"campo_libre": "cualquier-cosa", "n": 1},
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["cod_evento"] == "110"
    assert resp.json()["contenido"] == {"campo_libre": "cualquier-cosa", "n": 1}
