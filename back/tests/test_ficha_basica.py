"""Tests del módulo de ficha de datos básicos (Task B5)."""

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

UPGD_USERNAME = "upgd_test"
UPGD_PASSWORD = "upgd123"
UPGD_OWN_COD = "150010123456"
UPGD_OTRO_COD = "150010654321"

FICHA_INEXISTENTE_ID = 999999


def _payload(cod_upgd: str, **overrides) -> dict:
    data = {
        "cod_upgd": cod_upgd,
        "cod_evento": "100",
        "f_grabacion": "2026-09-25",
        "f_notificacion": "2026-09-25",
        "anio": 2026,
        "semana_epidemiologica": 38,
        "tipo_id": "CC",
        "num_id": "1023456789",
        "primer_nombre": "Pepito",
        "segundo_nombre": "Antonio",
        "primer_apellido": "Perez",
        "segundo_apellido": "Gomez",
        "telefono": "3001234567",
        "f_nacimiento": "1990-01-15",
        "edad": 36,
        "und_med_edad": 1,
        "sexo": "M",
        "identidad_genero": 1,
        "orientacion_sexual": 1,
        "pais_ocurrencia": "COLOMBIA",
        "dpto_ocurrencia": "05",
        "muni_ocurrencia": "05001",
        "area_ocurrencia": 1,
        "grupos_poblacionales": {"gestante": False, "desplazado": False},
        "clasificacion_caso": 1,
        "hospitalizado": False,
        "condicion_final": 1,
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
def _setup_fichas() -> None:
    asyncio.run(_seed_upgd_user())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _crear(client: AsyncClient, token: str, **overrides) -> dict:
    cod_upgd = overrides.pop("cod_upgd", UPGD_OWN_COD)
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_payload(cod_upgd, **overrides),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_sin_auth_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/fichas/datos-basicos")
    assert resp.status_code == 401
    resp = await client.post(
        "/api/v1/fichas/datos-basicos", json=_payload(UPGD_OWN_COD)
    )
    assert resp.status_code == 401


async def test_crear_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    data = await _crear(client, token, num_id="1023456789")
    assert data["id"] > 0
    assert data["cod_upgd"] == UPGD_OWN_COD
    assert data["cod_evento"] == "100"
    assert data["num_id"] == "1023456789"
    assert data["sexo"] == "M"
    assert data["und_med_edad"] == 1
    assert data["area_ocurrencia"] == 1
    assert data["clasificacion_caso"] == 1
    assert data["condicion_final"] == 1
    assert data["grupos_poblacionales"] == {"gestante": False, "desplazado": False}
    assert data["creado_por_usuario_id"] is not None
    assert data["f_grabacion"] == "2026-09-25"
    assert data["f_notificacion"] == "2026-09-25"


async def test_leer_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    creada = await _crear(client, token, num_id="1023456790")
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{creada['id']}", headers=_auth(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == creada["id"]
    assert data["primer_nombre"] == "Pepito"
    assert data["segundo_nombre"] == "Antonio"
    assert data["primer_apellido"] == "Perez"
    assert data["dpto_ocurrencia"] == "05"
    assert data["muni_ocurrencia"] == "05001"


async def test_leer_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{FICHA_INEXISTENTE_ID}", headers=_auth(token)
    )
    assert resp.status_code == 404


async def test_listar_con_filtro(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    await _crear(
        client, token, cod_evento="100", num_id="1023456791", anio=2026, semana_epidemiologica=38
    )
    await _crear(
        client, token, cod_evento="210", num_id="1023456792", anio=2026, semana_epidemiologica=39
    )

    resp = await client.get(
        "/api/v1/fichas/datos-basicos", params={"cod_evento": "210"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["cod_evento"] == "210"
    assert data[0]["num_id"] == "1023456792"


async def test_upgd_forja_cod_upgd_se_impone_la_suya(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    data = await _crear(client, token, cod_upgd=UPGD_OTRO_COD, num_id="1023456793")
    assert data["cod_upgd"] == UPGD_OWN_COD


async def test_upgd_ficha_ajena_403(client: AsyncClient) -> None:
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ajena = await _crear(client, token_docente, cod_upgd=UPGD_OTRO_COD, num_id="1023456794")

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{ajena['id']}", headers=_auth(token_upgd)
    )
    assert resp.status_code == 403


async def test_upgd_solo_ve_sus_fichas(client: AsyncClient) -> None:
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    await _crear(client, token_docente, cod_upgd=UPGD_OTRO_COD, num_id="1023456795")

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    await _crear(client, token_upgd, num_id="1023456796")

    resp = await client.get("/api/v1/fichas/datos-basicos", headers=_auth(token_upgd))
    assert resp.status_code == 200
    data = resp.json()
    assert all(ficha["cod_upgd"] == UPGD_OWN_COD for ficha in data)
    assert any(ficha["num_id"] == "1023456796" for ficha in data)
