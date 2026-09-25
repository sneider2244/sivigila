"""Tests del módulo de estados de fichas y trazabilidad (Task B7)."""

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

UPGD_USERNAME = "upgd_estado"
UPGD_PASSWORD = "upgd123"
UPGD_OWN_COD = "150010123456"

FICHA_INEXISTENTE_ID = 999999


def _payload(cod_upgd: str, num_id: str, **overrides) -> dict:
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


async def _seed_upgd_user() -> None:
    """Crea (idempotente) la UPGD de referencia y el usuario UPGD de prueba."""
    async with TestSessionFactory() as session:
        if await session.get(UPGDCaracterizacion, UPGD_OWN_COD) is None:
            session.add(
                UPGDCaracterizacion(
                    cod_prestador=UPGD_OWN_COD,
                    razon_social="UPGD Propia",
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
        existing = await session.scalar(
            select(Usuario).where(Usuario.username == UPGD_USERNAME)
        )
        if existing is None:
            session.add(
                Usuario(
                    username=UPGD_USERNAME,
                    hashed_password=get_password_hash(UPGD_PASSWORD),
                    nombre_completo="Usuario UPGD Estado",
                    rol=RolEnum.UPGD,
                    cod_upgd=UPGD_OWN_COD,
                    activo=True,
                )
            )
            await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_estado() -> None:
    asyncio.run(_seed_upgd_user())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _crear_ficha(client: AsyncClient, token: str, num_id: str) -> int:
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_payload(UPGD_OWN_COD, num_id),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_sin_auth_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/fichas/datos-basicos/1/estado", json={"estado_nuevo": "CONFIRMADA"}
    )
    assert resp.status_code == 401
    resp = await client.get("/api/v1/fichas/datos-basicos/1/trazabilidad")
    assert resp.status_code == 401


async def test_transicion_valida_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token, "1023456800")

    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "EN_AJUSTE", "ajuste": 2, "observacion": "revisar datos"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == ficha_id
    assert data["estado"] == "EN_AJUSTE"


async def test_upgd_intenta_transicion_403(client: AsyncClient) -> None:
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token_docente, "1023456801")

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "CONFIRMADA"},
        headers=_auth(token_upgd),
    )
    assert resp.status_code == 403


async def test_ajuste_fuera_de_rango_422(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token, "1023456802")

    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "EN_AJUSTE", "ajuste": 7},
        headers=_auth(token),
    )
    assert resp.status_code == 422

    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "EN_AJUSTE", "ajuste": -1},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_estado_nuevo_invalido_422(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token, "1023456803")

    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "ESTADO_INEXISTENTE"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_transicion_no_permitida_422(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token, "1023456804")

    await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "CONFIRMADA"},
        headers=_auth(token),
    )
    # CONFIRMADA -> DESCARTADA no está permitida.
    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "DESCARTADA"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_trazabilidad_lista_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ficha_id = await _crear_ficha(client, token, "1023456805")

    await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "EN_AJUSTE", "ajuste": 1},
        headers=_auth(token),
    )
    await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "NOTIFICADA"},
        headers=_auth(token),
    )
    await client.post(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/estado",
        json={"estado_nuevo": "CONFIRMADA"},
        headers=_auth(token),
    )

    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{ficha_id}/trazabilidad", headers=_auth(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Orden descendente por f_cambio: la más reciente primero.
    assert [fila["estado_nuevo"] for fila in data] == ["CONFIRMADA", "NOTIFICADA", "EN_AJUSTE"]
    assert [fila["estado_anterior"] for fila in data] == ["NOTIFICADA", "EN_AJUSTE", "NOTIFICADA"]
    assert data[0]["usuario_id"] is not None
    assert data[0]["f_cambio"] is not None
    assert data[2]["ajuste"] == 1


async def test_ficha_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.post(
        f"/api/v1/fichas/datos-basicos/{FICHA_INEXISTENTE_ID}/estado",
        json={"estado_nuevo": "CONFIRMADA"},
        headers=_auth(token),
    )
    assert resp.status_code == 404
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{FICHA_INEXISTENTE_ID}/trazabilidad",
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_upgd_trazabilidad_ficha_ajena_403(client: AsyncClient) -> None:
    token_docente = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    ajena_id = await _crear_ficha(client, token_docente, "1023456806")

    # La ficha del docente usa UPGD_OWN_COD (misma UPGD del usuario UPGD), así que
    # se crea una ficha de otra UPGD para probar la restricción.
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_payload("999999999999", "1023456807"),
        headers=_auth(token_docente),
    )
    assert resp.status_code == 201, resp.text
    ajena_otra_upgd = resp.json()["id"]

    token_upgd = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{ajena_otra_upgd}/trazabilidad",
        headers=_auth(token_upgd),
    )
    assert resp.status_code == 403

    # Sanity: su propia ficha sí es accesible (lista vacía, 200).
    resp = await client.get(
        f"/api/v1/fichas/datos-basicos/{ajena_id}/trazabilidad", headers=_auth(token_upgd)
    )
    assert resp.status_code == 200
