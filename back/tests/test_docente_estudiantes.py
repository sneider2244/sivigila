"""Tests de FP2: listado de estudiantes + asignación masiva (bulk, idempotente)."""

import asyncio

import pytest
from conftest import TestSessionFactory
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.docente import EscenarioAsignacion
from app.models.usuario import RolEnum, Usuario

DOCENTE_USERNAME = "docente"
DOCENTE_PASSWORD = "docente123"

UPGD_USERNAME = "fp2_upgd"
UPGD_PASSWORD = "fp2upgd123"

ESTUDIANTES = (
    ("fp2_ana@test.com", "ana123", "Ana Martínez", "FP2001", RolEnum.UPGD),
    ("fp2_benito@test.com", "ben123", "Benito Ríos", "FP2002", RolEnum.UI),
    ("fp2_carla@test.com", "car123", "Carla Gómez", "FP2003", RolEnum.MUNICIPAL),
)

ESTUDIANTE_INEXISTENTE_ID = 999999


def _escenario_payload(**overrides) -> dict:
    data = {
        "titulo": "Dengue para bulk",
        "descripcion": "Escenario para pruebas de asignación masiva.",
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


_IDS: dict[str, int] = {}


async def _seed_estudiantes() -> None:
    """Crea (idempotente) los estudiantes de prueba y un usuario UPGD no-DOCENTE."""
    async with TestSessionFactory() as session:
        for username, password, nombre, num_id, rol in ESTUDIANTES:
            usuario = await session.scalar(
                select(Usuario).where(Usuario.username == username)
            )
            if usuario is None:
                usuario = Usuario(
                    username=username,
                    hashed_password=get_password_hash(password),
                    nombre_completo=nombre,
                    numero_identificacion=num_id,
                    rol=rol,
                    activo=True,
                )
                session.add(usuario)
                await session.flush()
            _IDS[username] = usuario.id
        if await session.scalar(select(Usuario).where(Usuario.username == UPGD_USERNAME)) is None:
            session.add(
                Usuario(
                    username=UPGD_USERNAME,
                    hashed_password=get_password_hash(UPGD_PASSWORD),
                    nombre_completo="Usuario UPGD FP2",
                    numero_identificacion="FP2000",
                    rol=RolEnum.UPGD,
                    activo=True,
                )
            )
        await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_estudiantes() -> None:
    asyncio.run(_seed_estudiantes())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


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


async def _asignaciones_count(escenario_id: int) -> int:
    async with TestSessionFactory() as session:
        rows = await session.execute(
            select(EscenarioAsignacion).where(
                EscenarioAsignacion.escenario_id == escenario_id
            )
        )
        return len(list(rows.scalars()))


async def test_listar_estudiantes_excluye_docente(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get("/api/v1/docente/estudiantes", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(item["rol"] != "DOCENTE" for item in data)
    usernames = {item["username"] for item in data}
    assert "docente" not in usernames
    for username in _IDS:
        assert username in usernames


async def test_listar_estudiantes_filtro_q_nombre(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(
        "/api/v1/docente/estudiantes", params={"q": "gómez"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["username"] == "fp2_carla@test.com" for item in data)
    assert not any(item["username"] == "fp2_ana@test.com" for item in data)


async def test_listar_estudiantes_filtro_q_username(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(
        "/api/v1/docente/estudiantes",
        params={"q": "fp2_benito"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [item["username"] for item in data] == ["fp2_benito@test.com"]


async def test_listar_estudiantes_filtro_q_identificacion(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(
        "/api/v1/docente/estudiantes",
        params={"q": "FP2002"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [item["username"] for item in data] == ["fp2_benito@test.com"]


async def test_bulk_asignar_multiples_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Bulk múltiple")
    ids = [_IDS["fp2_ana@test.com"], _IDS["fp2_benito@test.com"]]

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": ids},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {a["estudiante_id"] for a in data} == set(ids)
    assert all(a["estado"] == "ASIGNADO" for a in data)
    assert all(a["escenario_id"] == esc["id"] for a in data)
    assert all(a["ficha_basica_id"] is None for a in data)


async def test_bulk_asignar_idempotente_no_duplica(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Bulk idempotente")
    ids = [_IDS["fp2_ana@test.com"], _IDS["fp2_carla@test.com"]]

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": ids},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 2

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": ids},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert resp.json() == []

    assert await _asignaciones_count(esc["id"]) == 2


async def test_bulk_asignar_parcial_nuevo_y_existente(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Bulk parcial")
    id_a = _IDS["fp2_ana@test.com"]
    id_b = _IDS["fp2_benito@test.com"]

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [id_a]},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 1

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [id_a, id_b]},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 1
    assert data[0]["estudiante_id"] == id_b

    assert await _asignaciones_count(esc["id"]) == 2


async def test_bulk_asignar_escenario_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.post(
        "/api/v1/docente/escenarios/999999/asignar",
        json={"estudiante_ids": [_IDS["fp2_ana@test.com"]]},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_bulk_asignar_estudiante_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Bulk 404 estudiante")
    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [_IDS["fp2_ana@test.com"], ESTUDIANTE_INEXISTENTE_ID]},
        headers=_auth(token),
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert str(ESTUDIANTE_INEXISTENTE_ID) in detail


async def test_bulk_asignar_lista_vacia_422(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Bulk vacío")
    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": []},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_listar_estudiantes_no_docente_403(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get("/api/v1/docente/estudiantes", headers=_auth(token))
    assert resp.status_code == 403


async def test_bulk_asignar_no_docente_403(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Bulk 403")
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [_IDS["fp2_ana@test.com"]]},
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_asignaciones_por_escenario(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Asignaciones por escenario")
    ids = [_IDS["fp2_ana@test.com"], _IDS["fp2_benito@test.com"]]
    await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": ids},
        headers=_auth(token),
    )

    resp = await client.get(
        f"/api/v1/docente/escenarios/{esc['id']}/asignaciones",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(a["escenario_id"] == esc["id"] for a in data)
    por_id = {a["estudiante_id"]: a for a in data}
    assert por_id[_IDS["fp2_ana@test.com"]]["estudiante_numero_identificacion"] == "FP2001"
    assert all("estudiante_numero_identificacion" in a for a in data)


async def test_asignaciones_por_escenario_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    resp = await client.get(
        "/api/v1/docente/escenarios/999999/asignaciones", headers=_auth(token)
    )
    assert resp.status_code == 404


async def test_asignaciones_por_escenario_no_docente_403(client: AsyncClient) -> None:
    docente_token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, docente_token, titulo="Asignaciones 403")
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.get(
        f"/api/v1/docente/escenarios/{esc['id']}/asignaciones", headers=_auth(token)
    )
    assert resp.status_code == 403
