import pytest


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Base SQLite temporal, inicializada, para cada test."""
    monkeypatch.setenv("SIVIGILA_DB_PATH", str(tmp_path / "test.db"))
    from sivigila import db as modulo_db

    modulo_db.init_db()
    return modulo_db
