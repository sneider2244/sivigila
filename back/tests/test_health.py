from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_renders_layout():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "SIVIGILA" in response.text
