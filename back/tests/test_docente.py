"""Tests del módulo Docente (Task B8): escenarios clínicos y evaluación."""

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

ESTUDIANTE_USERNAME = "estudiante_test"
ESTUDIANTE_PASSWORD = "estudiante123"

FICHA_INEXISTENTE_ID = 999999


def _escenario_payload(**overrides) -> dict:
    data = {
        "titulo": "Dengue con signos de alarma",
        "descripcion": "Paciente con fiebre y exantema en zona endémica.",
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
    data = {
        "cod_upgd": UPGD_OWN_COD,
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
    """Crea (idempotente) la UPGD de referencia y los usuarios UPGD + estudiante."""
    async with TestSessionFactory() as session:
        if await session.get(UPGDCaracterizacion, UPGD_OWN_COD) is None:
            session.add(
                UPGDCaracterizacion(
                    cod_prestador=UPGD_OWN_COD,
                    razon_social="UPGD Test Docente",
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
        usuarios = (
            (UPGD_USERNAME, UPGD_PASSWORD, "Usuario UPGD Test", RolEnum.UPGD, UPGD_OWN_COD),
            (
                ESTUDIANTE_USERNAME,
                ESTUDIANTE_PASSWORD,
                "Estudiante Test",
                RolEnum.UPGD,
                UPGD_OWN_COD,
            ),
        )
        for username, password, nombre, rol, cod_upgd in usuarios:
            if await session.scalar(select(Usuario).where(Usuario.username == username)) is None:
                session.add(
                    Usuario(
                        username=username,
                        hashed_password=get_password_hash(password),
                        nombre_completo=nombre,
                        rol=rol,
                        cod_upgd=cod_upgd,
                        activo=True,
                    )
                )
        await session.commit()


@pytest.fixture(scope="module", autouse=True)
def _setup_docente() -> None:
    asyncio.run(_seed_usuarios())


async def _login(client: AsyncClient, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _login_response(client: AsyncClient, username: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200
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


async def test_crear_escenario_docente_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token)
    assert esc["id"] > 0
    assert esc["titulo"] == "Dengue con signos de alarma"
    assert esc["cod_evento"] == "110"
    assert esc["activo"] is True
    assert esc["creado_por_id"] is not None
    assert esc["datos_esperados"]["contenido"] == {"fiebre": True, "exantema": False}


async def test_crear_escenario_upgd_403(client: AsyncClient) -> None:
    token = await _login(client, UPGD_USERNAME, UPGD_PASSWORD)
    resp = await client.post(
        "/api/v1/docente/escenarios",
        json=_escenario_payload(),
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_asignar_201(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Escenario asignable")
    login_est = await _login_response(client, ESTUDIANTE_USERNAME, ESTUDIANTE_PASSWORD)
    estudiante_id = login_est["usuario"]["id"]

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [estudiante_id]},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    asignacion = data[0]
    assert asignacion["estado"] == "ASIGNADO"
    assert asignacion["escenario_id"] == esc["id"]
    assert asignacion["estudiante_id"] == estudiante_id
    assert asignacion["escenario_titulo"] == "Escenario asignable"
    assert asignacion["estudiante_username"] == ESTUDIANTE_USERNAME
    assert asignacion["estudiante_nombre"] == "Estudiante Test"
    assert asignacion["ficha_basica_id"] is None


async def test_estudiante_lista_escenarios_200(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token, titulo="Escenario para estudiante")
    login_est = await _login_response(client, ESTUDIANTE_USERNAME, ESTUDIANTE_PASSWORD)
    est_token = login_est["access_token"]
    estudiante_id = login_est["usuario"]["id"]

    resp = await client.post(
        f"/api/v1/docente/escenarios/{esc['id']}/asignar",
        json={"estudiante_ids": [estudiante_id]},
        headers=_auth(token),
    )
    assert resp.status_code == 201

    resp = await client.get("/api/v1/estudiante/escenarios", headers=_auth(est_token))
    assert resp.status_code == 200
    data = resp.json()
    assert any(e["escenario"]["id"] == esc["id"] for e in data)


async def test_evaluar_200_con_puntaje(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token)
    ficha = await _crear_ficha(client, token)

    resp = await client.post(
        "/api/v1/fichas/datos-complementarios",
        json={
            "ficha_basica_id": ficha["id"],
            "cod_evento": "110",
            "contenido": {"fiebre": True, "exantema": False},
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/api/v1/docente/evaluar",
        json={"ficha_basica_id": ficha["id"], "escenario_id": esc["id"]},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["puntaje"] == 100.0
    assert data["aciertos"] == 8
    assert data["total"] == 8
    assert all(d["correcto"] for d in data["detalle"])
    campos = {d["campo"] for d in data["detalle"]}
    assert "cod_evento" in campos
    assert "contenido.fiebre" in campos


async def test_evaluar_ficha_inexistente_404(client: AsyncClient) -> None:
    token = await _login(client, DOCENTE_USERNAME, DOCENTE_PASSWORD)
    esc = await _crear_escenario(client, token)
    resp = await client.post(
        "/api/v1/docente/evaluar",
        json={"ficha_basica_id": FICHA_INEXISTENTE_ID, "escenario_id": esc["id"]},
        headers=_auth(token),
    )
    assert resp.status_code == 404
