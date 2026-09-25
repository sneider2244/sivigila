"""Tests de FP3: desacople RBAC en ficha + escenarios del estudiante + entrega.

Cubre el contrato de `docs/FLOW_PLAN.md` (Fase 3):
- Cualquier rol autenticado (ej. MUNICIPAL) crea ficha sin 400.
- Ficha sin `cod_upgd` en el payload -> UPGD demo.
- `GET /estudiante/escenarios` expone `EstudianteAsignacionOut` SIN `datos_esperados`.
- `POST /estudiante/escenarios/{id}/entregar`: OK, 403 ajena, 404 inexistente.
"""

import asyncio

import pytest
from conftest import TestSessionFactory
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.usuario import RolEnum, Usuario

DOCENTE_USERNAME = "docente"
DOCENTE_PASSWORD = "docente123"

MUNI_USERNAME = "fp3_muni@test.com"
MUNI_PASSWORD = "fp3muni123"

AJENO_USERNAME = "fp3_ajeno@test.com"
AJENO_PASSWORD = "fp3ajeno123"

COD_UPGD_DEMO = "150010123456"
ASIGNACION_INEXISTENTE_ID = 999999
FICHA_INEXISTENTE_ID = 999999


def _escenario_payload(**overrides) -> dict:
    data = {
        "titulo": "Dengue FP3",
        "descripcion": "Escenario para el flujo del estudiante.",
        "cod_evento": "110",
        "datos_esperados": {
            "cod_evento": "110",
            "clasificacion_caso": 1,
            "hospitalizado": False,
            "condicion_final": 1,
            "area_ocurrencia": 3,
            "sexo": "M",
            "contenido": {"fiebre": True, "exantema": False},
        },
    }
    data.update(overrides)
    return data


def _ficha_payload(**overrides) -> dict:
    """Payload de ficha SIN `cod_upgd` (debe resolverse a la UPGD demo)."""
    data = {
        "cod_evento": "110",
        "f_grabacion": "2026-09-25",
        "f_notificacion": "2026-09-25",
        "anio": 2026,
        "semana_epidemiologica": 38,
        "tipo_id": "CC",
        "num_id": "1023457001",
        "primer_nombre": "Pepito",
        "segundo_nombre": None,
        "primer_apellido": "Perez",
        "segundo_apellido": None,
        "telefono": None,
        "f_nacimiento": "1990-01-15",
        "edad": 36,
        "und_med_edad": 1,
        "sexo": "M",
        "identidad_genero": 1,
        "orientacion_sexual": 1,
        "pais_ocurrencia": "COLOMBIA",
        "dpto_ocurrencia": "05",
        "muni_ocurrencia": "05001",
        "area_ocurrencia": 3,
        "grupos_poblacionales": {},
        "clasificacion_caso": 1,
        "hospitalizado": False,
        "condicion_final": 1,
    }
    data.update(overrides)
    return data


async def _seed_usuarios() -> None:
    """Crea (idempotente) el estudiante MUNICIPAL y el estudiante ajeno (UI)."""
    async with TestSessionFactory() as session:
        usuarios = (
            (MUNI_USERNAME, MUNI_PASSWORD, "Estudiante MUNICIPAL FP3", RolEnum.MUNICIPAL),
            (AJENO_USERNAME, AJENO_PASSWORD, "Estudiante Ajeno FP3", RolEnum.UI),
        )
        for username, password, nombre, rol in usuarios:
            if await session.scalar(select(Usuario).where(Usuario.username == username)) is None:
                session.add(
                    Usuario(
                        username=username,
                        hashed_password=get_password_hash(password),
                        nombre_completo=nombre,
                        rol=rol,
                        activo=True,
                    )
                )
        await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_estudiante() -> None:
    asyncio.run(_seed_usuarios())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _login_response(client: AsyncClient, username: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _crear_escenario(client: AsyncClient, token: str, **overrides) -> dict:
    resp = await client.post(
        "/api/v1/docente/escenarios",
        json=_escenario_payload(**overrides),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _crear_ficha(client: AsyncClient, token: str, **overrides) -> dict:
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_ficha_payload(**overrides),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _asignar(
    client: AsyncClient, token: str, escenario_id: int, estudiante_ids: list[int]
) -> list[dict]:
    resp = await client.post(
        f"/api/v1/docente/escenarios/{escenario_id}/asignar",
        json={"estudiante_ids": estudiante_ids},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_municipal_crea_ficha_sin_cod_upgd_default_demo(client: AsyncClient) -> None:
    """Cualquier rol (MUNICIPAL) crea ficha sin 400 y obtiene la UPGD demo."""
    token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.post(
        "/api/v1/fichas/datos-basicos",
        json=_ficha_payload(),
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["cod_upgd"] == COD_UPGD_DEMO
    assert data["id"] > 0


async def test_entregar_ok_completado(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Entrega OK FP3")

    muni_login = await _login_response(client, MUNI_USERNAME, MUNI_PASSWORD)
    muni_token = muni_login["access_token"]
    muni_id = muni_login["usuario"]["id"]

    asignaciones = await _asignar(client, docente_token, esc["id"], [muni_id])
    asignacion_id = asignaciones[0]["id"]

    ficha = await _crear_ficha(client, muni_token)

    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{asignacion_id}/entregar",
        json={"ficha_basica_id": ficha["id"]},
        headers=_auth(muni_token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == asignacion_id
    assert data["estado"] == "COMPLETADO"
    assert data["ficha_basica_id"] == ficha["id"]
    assert data["escenario"]["id"] == esc["id"]
    assert data["escenario"]["titulo"] == "Entrega OK FP3"
    assert "datos_esperados" not in data["escenario"]


async def test_entregar_asignacion_ajena_403(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Entrega ajena FP3")

    ajeno_id = (await _login_response(client, AJENO_USERNAME, AJENO_PASSWORD))["usuario"]["id"]
    asignaciones = await _asignar(client, docente_token, esc["id"], [ajeno_id])
    asignacion_id = asignaciones[0]["id"]

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    ficha = await _crear_ficha(client, muni_token)

    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{asignacion_id}/entregar",
        json={"ficha_basica_id": ficha["id"]},
        headers=_auth(muni_token),
    )
    assert resp.status_code == 403


async def test_entregar_asignacion_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{ASIGNACION_INEXISTENTE_ID}/entregar",
        json={"ficha_basica_id": 1},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_entregar_ficha_inexistente_404(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Ficha inexistente FP3")

    muni_id = (await _login_response(client, MUNI_USERNAME, MUNI_PASSWORD))["usuario"]["id"]
    asignaciones = await _asignar(client, docente_token, esc["id"], [muni_id])
    asignacion_id = asignaciones[0]["id"]

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{asignacion_id}/entregar",
        json={"ficha_basica_id": FICHA_INEXISTENTE_ID},
        headers=_auth(muni_token),
    )
    assert resp.status_code == 404


async def test_get_escenarios_sin_datos_esperados(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="No leak FP3")

    muni_id = (await _login_response(client, MUNI_USERNAME, MUNI_PASSWORD))["usuario"]["id"]
    await _asignar(client, docente_token, esc["id"], [muni_id])

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.get("/api/v1/estudiante/escenarios", headers=_auth(muni_token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    item = next(a for a in data if a["escenario"]["id"] == esc["id"])
    assert set(item.keys()) == {"id", "estado", "ficha_basica_id", "escenario"}
    assert set(item["escenario"].keys()) == {"id", "titulo", "descripcion", "cod_evento"}
    assert "datos_esperados" not in item
    assert "datos_esperados" not in item["escenario"]


async def test_progreso_ok_en_progreso(client: AsyncClient) -> None:
    """El guardado parcial vincula la ficha y marca EN_PROGRESO (sin completar)."""
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Progreso FP3")

    muni_login = await _login_response(client, MUNI_USERNAME, MUNI_PASSWORD)
    muni_token = muni_login["access_token"]
    muni_id = muni_login["usuario"]["id"]

    asignaciones = await _asignar(client, docente_token, esc["id"], [muni_id])
    asignacion_id = asignaciones[0]["id"]

    ficha = await _crear_ficha(client, muni_token)

    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{asignacion_id}/progreso",
        json={"ficha_basica_id": ficha["id"]},
        headers=_auth(muni_token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["estado"] == "EN_PROGRESO"
    assert data["ficha_basica_id"] == ficha["id"]
    assert data["escenario"]["id"] == esc["id"]


async def test_progreso_asignacion_ajena_403(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Progreso ajeno FP3")

    ajeno_id = (await _login_response(client, AJENO_USERNAME, AJENO_PASSWORD))["usuario"]["id"]
    asignaciones = await _asignar(client, docente_token, esc["id"], [ajeno_id])
    asignacion_id = asignaciones[0]["id"]

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    ficha = await _crear_ficha(client, muni_token)

    resp = await client.post(
        f"/api/v1/estudiante/escenarios/{asignacion_id}/progreso",
        json={"ficha_basica_id": ficha["id"]},
        headers=_auth(muni_token),
    )
    assert resp.status_code == 403


async def test_get_escenario_estudiante_ok(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(
        client, docente_token, titulo="Caso visible", descripcion="Descripción del caso"
    )

    muni_id = (await _login_response(client, MUNI_USERNAME, MUNI_PASSWORD))["usuario"]["id"]
    asignaciones = await _asignar(client, docente_token, esc["id"], [muni_id])
    asignacion_id = asignaciones[0]["id"]

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.get(
        f"/api/v1/estudiante/escenarios/{asignacion_id}", headers=_auth(muni_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == asignacion_id
    assert data["escenario"]["titulo"] == "Caso visible"
    assert data["escenario"]["descripcion"] == "Descripción del caso"
    assert "datos_esperados" not in data["escenario"]


async def test_get_escenario_estudiante_ajeno_403(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Ajeno get FP3")

    ajeno_id = (await _login_response(client, AJENO_USERNAME, AJENO_PASSWORD))["usuario"]["id"]
    asignaciones = await _asignar(client, docente_token, esc["id"], [ajeno_id])
    asignacion_id = asignaciones[0]["id"]

    muni_token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.get(
        f"/api/v1/estudiante/escenarios/{asignacion_id}", headers=_auth(muni_token)
    )
    assert resp.status_code == 403


async def test_get_escenario_estudiante_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, MUNI_USERNAME, MUNI_PASSWORD)
    resp = await client.get(
        f"/api/v1/estudiante/escenarios/{ASIGNACION_INEXISTENTE_ID}", headers=_auth(token)
    )
    assert resp.status_code == 404
