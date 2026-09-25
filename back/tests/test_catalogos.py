"""Tests del módulo de catálogos oficiales (Task B3)."""

from httpx import AsyncClient


async def test_departamentos(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/departamentos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 33
    codigos = {d["codigo"] for d in data}
    assert "05" in codigos
    assert "11" in codigos
    assert data[0]["codigo"] == "05"  # orden lexicográfico por código


async def test_municipios_sin_filtro(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/municipios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 100
    assert any(m["codigo"] == "05001" for m in data)  # Medellín
    assert any(m["codigo"] == "76001" for m in data)  # Cali


async def test_municipios_filtro_departamento(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/municipios", params={"departamento": "05"})
    assert resp.status_code == 200
    data = resp.json()
    assert data  # no vacío
    assert all(m["departamento_codigo"] == "05" for m in data)
    nombres = {m["nombre"] for m in data}
    assert "Medellín" in nombres


async def test_municipios_filtro_sin_resultados(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/municipios", params={"departamento": "00"})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_eventos(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/eventos")
    assert resp.status_code == 200
    data = resp.json()
    codigos = {e["codigo"] for e in data}
    assert "100" in codigos  # Accidente Ofídico (referenciado en el plan)
    ofidico = next(e for e in data if e["codigo"] == "100")
    assert ofidico["nombre"] == "Accidente Ofídico"


async def test_ocupaciones(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/ocupaciones")
    assert resp.status_code == 200
    assert len(resp.json()) >= 10


async def test_etnias(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/catalogos/etnias")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    nombres = {e["nombre"] for e in data}
    assert "Indígena" in nombres
    assert "Ninguno de los anteriores" in nombres
