"""Tests del módulo de caracterización UPGD (Task B4)."""

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
UPGD_NUEVO_COD = "150010222222"
UPGD_INEXISTENTE_COD = "999999999999"


def _payload(cod_prestador: str) -> dict:
    return {
        "cod_prestador": cod_prestador,
        "razon_social": "Hospital Simulado SIVIGILA",
        "nit": "900000000-1",
        "nivel_complejidad": 2,
        "cove": True,
        "unidad_analisis": True,
        "internet": True,
        "activo": True,
        "departamento_codigo": "05",
        "municipio_codigo": "05001",
    }


async def _seed_upgd_data() -> None:
    """Crea (idempotente) el usuario UPGD y dos UPGD de referencia."""
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
def _setup_upgd() -> None:
    asyncio.run(_seed_upgd_data())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_sin_auth_401(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/upgd/{UPGD_OWN_COD}")
    assert resp.status_code == 401


async def test_crear_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.post(
        "/api/v1/upgd", json=_payload(UPGD_NUEVO_COD), headers=_auth(token)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["cod_prestador"] == UPGD_NUEVO_COD
    assert data["nivel_complejidad"] == 2
    assert data["activo"] is True


async def test_leer_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(f"/api/v1/upgd/{UPGD_OWN_COD}", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["cod_prestador"] == UPGD_OWN_COD
    assert data["razon_social"] == "UPGD Propia"
    assert data["departamento_codigo"] == "05"
    assert data["municipio_codigo"] == "05001"


async def test_leer_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(f"/api/v1/upgd/{UPGD_INEXISTENTE_COD}", headers=_auth(token))
    assert resp.status_code == 404


async def test_update_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.put(
        f"/api/v1/upgd/{UPGD_OWN_COD}",
        json={"razon_social": "UPGD Propia Actualizada", "nivel_complejidad": 3},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["razon_social"] == "UPGD Propia Actualizada"
    assert data["nivel_complejidad"] == 3
    # El resto de campos no enviados deben conservarse.
    assert data["nit"] == "900000000-1"


async def test_upgd_ajeno_403(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get(f"/api/v1/upgd/{UPGD_OTRO_COD}", headers=_auth(token))
    assert resp.status_code == 403


async def test_upgd_propio_200(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get(f"/api/v1/upgd/{UPGD_OWN_COD}", headers=_auth(token))
    assert resp.status_code == 200


async def test_upgd_propio_update_ajeno_403(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.put(
        f"/api/v1/upgd/{UPGD_OTRO_COD}",
        json={"razon_social": "Intento ajeno"},
        headers=_auth(token),
    )
    assert resp.status_code == 403
