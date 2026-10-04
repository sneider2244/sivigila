from datetime import date, timedelta

import pytest

from tests.utils import crear_ficha, crear_upgd, post


@pytest.fixture
def ficha_id(db, digitador):
    return crear_ficha(db, crear_upgd(db), digitador["id"])


def test_agregar_laboratorio_devuelve_tabla(client, db, ficha_id):
    r = post(client, f"/fichas/{ficha_id}/laboratorios",
             {"prueba": "IgM Dengue", "muestra": "Suero", "fecha_toma": date.today().isoformat()},
             headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "IgM Dengue" in r.text
    assert "<html" not in r.text
    assert len(db.list_laboratorios(ficha_id)) == 1


def test_agregar_laboratorio_sin_prueba_es_422(client, db, ficha_id):
    r = post(client, f"/fichas/{ficha_id}/laboratorios", {"muestra": "Suero"},
             headers={"HX-Request": "true"})
    assert r.status_code == 422
    assert "Este campo es obligatorio." in r.text
    assert 'value="Suero"' in r.text
    assert db.list_laboratorios(ficha_id) == []


def test_agregar_laboratorio_con_fecha_futura_es_422(client, db, ficha_id):
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = post(client, f"/fichas/{ficha_id}/laboratorios", {"prueba": "IgM", "fecha_toma": manana})
    assert r.status_code == 422
    assert db.list_laboratorios(ficha_id) == []


def test_quitar_laboratorio(client, db, ficha_id):
    lab_id = db.add_laboratorio(ficha_id, {"prueba": "IgM"})
    r = post(client, f"/fichas/{ficha_id}/laboratorios/{lab_id}/eliminar")
    assert r.status_code == 200
    assert "Sin resultados registrados aún." in r.text
    assert db.get_laboratorio(lab_id) is None


def test_no_se_quita_laboratorio_de_otra_ficha(client, db, digitador, ficha_id):
    otra = crear_ficha(db, crear_upgd(db, "Otra"), digitador["id"])
    lab_ajeno = db.add_laboratorio(otra, {"prueba": "IgG"})
    r = post(client, f"/fichas/{ficha_id}/laboratorios/{lab_ajeno}/eliminar")
    assert r.status_code == 404
    assert db.get_laboratorio(lab_ajeno) is not None


def test_laboratorio_en_ficha_inexistente_404(client, digitador):
    assert post(client, "/fichas/999/laboratorios", {"prueba": "IgM"}).status_code == 404
