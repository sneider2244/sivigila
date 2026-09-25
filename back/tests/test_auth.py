"""Tests del módulo de autenticación y RBAC (Task B2)."""

from fastapi import APIRouter, Depends
from httpx import AsyncClient

from app.core.rbac import require_roles
from app.main import app
from app.models.usuario import RolEnum, Usuario

TEST_USERNAME = "docente"
TEST_PASSWORD = "docente123"

_test_router = APIRouter()

_upgd_only_dependency = require_roles(RolEnum.UPGD)


@_test_router.get("/test/upgd-only")
async def upgd_only(current_user: Usuario = Depends(_upgd_only_dependency)) -> dict:
    return {"rol": current_user.rol.value}


app.include_router(_test_router)


async def _login(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200
    return resp.json()


async def test_login_success(client: AsyncClient) -> None:
    data = await _login(client)
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["usuario"]["username"] == TEST_USERNAME
    assert data["usuario"]["rol"] == "DOCENTE"


async def test_login_wrong_password(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": TEST_USERNAME, "password": "incorrecta"},
    )
    assert resp.status_code == 401


async def test_me_with_valid_token(client: AsyncClient) -> None:
    token = (await _login(client))["access_token"]
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == TEST_USERNAME


async def test_me_without_token(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_rbac_403_for_docente(client: AsyncClient) -> None:
    token = (await _login(client))["access_token"]
    resp = await client.get(
        "/test/upgd-only", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
