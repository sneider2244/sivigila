"""Tests de registro de estudiantes y rol dinámico (Fase 1)."""

import asyncio

import pytest
from conftest import TestSessionFactory
from httpx import AsyncClient

from app.models.upgd import UPGDCaracterizacion

DEMO_UPGD_COD = "150010123456"

EMAIL_1 = "estudiante1@test.com"
EMAIL_2 = "estudiante2@test.com"
EMAIL_3 = "estudiante3@test.com"
EMAIL_4 = "estudiante4@test.com"
NUMERO_1 = "1030456789"
NUMERO_3 = "1030456790"
NUMERO_4 = "1030456791"


async def _seed_demo_upgd() -> None:
    """Crea la UPGD demo a la que se vincula `cod_upgd` en el registro."""
    async with TestSessionFactory() as session:
        if await session.get(UPGDCaracterizacion, DEMO_UPGD_COD) is None:
            session.add(
                UPGDCaracterizacion(
                    cod_prestador=DEMO_UPGD_COD,
                    razon_social="UPGD Demo Registro",
                    nit="900000000-1",
                    nivel_complejidad=2,
                    cove=True,
                    unidad_analisis=True,
                    internet=True,
                    activo=True,
                )
            )
            await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_demo_upgd() -> None:
    asyncio.run(_seed_demo_upgd())


def _register_payload(**overrides) -> dict:
    payload = {
        "email": EMAIL_1,
        "nombre_completo": "Estudiante Uno",
        "numero_identificacion": NUMERO_1,
    }
    payload.update(overrides)
    return payload


async def _register(client: AsyncClient, **overrides) -> dict:
    resp = await client.post("/api/v1/auth/register", json=_register_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_register_ok_auto_login(client: AsyncClient) -> None:
    data = await _register(client)
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["usuario"]["username"] == EMAIL_1
    assert data["usuario"]["nombre_completo"] == "Estudiante Uno"
    assert data["usuario"]["numero_identificacion"] == NUMERO_1
    assert data["usuario"]["rol"] == "UPGD"
    assert data["usuario"]["activo"] is True

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == EMAIL_1


async def test_register_email_duplicado_409(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/register", json=_register_payload())
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Ya existe un usuario con ese email"


async def test_register_rol_docente_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json=_register_payload(email=EMAIL_2, rol="DOCENTE"),
    )
    assert resp.status_code == 422


async def test_register_email_vacio_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json=_register_payload(email="   "),
    )
    assert resp.status_code == 422


async def test_login_estudiante_email_numero(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": EMAIL_1, "password": NUMERO_1},
    )
    assert resp.status_code == 200
    assert resp.json()["usuario"]["username"] == EMAIL_1


async def test_patch_me_cambia_rol(client: AsyncClient) -> None:
    data = await _register(client, email=EMAIL_3, numero_identificacion=NUMERO_3)
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.patch("/api/v1/auth/me", json={"rol": "UI"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["rol"] == "UI"

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["rol"] == "UI"


async def test_patch_me_a_docente_422(client: AsyncClient) -> None:
    data = await _register(client, email=EMAIL_4, numero_identificacion=NUMERO_4)
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.patch("/api/v1/auth/me", json={"rol": "DOCENTE"}, headers=headers)
    assert resp.status_code == 422
