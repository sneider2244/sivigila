import pytest

from tests.utils import crear_ficha, crear_upgd


@pytest.fixture
def upgd_id(db):
    return crear_upgd(db)


def _filas(html):
    return html.count('class="fila-ficha"')


def test_listado_muestra_fichas(client, db, digitador, upgd_id):
    crear_ficha(db, upgd_id, digitador["id"], primer_nombre="Carla")
    r = client.get("/listado")
    assert r.status_code == 200
    assert "Carla" in r.text
    assert _filas(r.text) == 1


def test_filtra_por_texto_y_evento(client, db, digitador, upgd_id):
    crear_ficha(db, upgd_id, digitador["id"], primer_nombre="Carla", numero_id="111")
    crear_ficha(db, upgd_id, digitador["id"], primer_nombre="Diego", numero_id="222", codigo_evento="100")
    r = client.get("/listado/resultados?q=Carla")
    assert _filas(r.text) == 1 and "Carla" in r.text
    assert "<html" not in r.text
    r = client.get("/listado/resultados?evento=100")
    assert _filas(r.text) == 1 and "Diego" in r.text


def test_busqueda_con_apostrofo_y_tildes(client, db, digitador, upgd_id):
    crear_ficha(db, upgd_id, digitador["id"], primer_nombre="Seán", primer_apellido="O'Neil")
    assert _filas(client.get("/listado/resultados", params={"q": "O'Neil"}).text) == 1
    assert _filas(client.get("/listado/resultados", params={"q": "Seán"}).text) == 1


def test_paginacion(client, db, digitador, upgd_id):
    for i in range(55):
        crear_ficha(db, upgd_id, digitador["id"], numero_id=str(i))
    r = client.get("/listado/resultados?pagina=1")
    assert _filas(r.text) == 50
    assert "55 fichas" in r.text
    assert _filas(client.get("/listado/resultados?pagina=2").text) == 5


@pytest.mark.parametrize("pagina, esperadas", [("abc", 50), ("-3", 50), ("999", 5)])
def test_pagina_invalida_no_rompe(client, db, digitador, upgd_id, pagina, esperadas):
    for i in range(55):
        crear_ficha(db, upgd_id, digitador["id"], numero_id=str(i))
    r = client.get(f"/listado/resultados?pagina={pagina}")
    assert r.status_code == 200
    assert _filas(r.text) == esperadas


def test_texto_con_html_se_escapa(client, db, digitador, upgd_id):
    crear_ficha(db, upgd_id, digitador["id"], primer_nombre="<script>alert(1)</script>")
    r = client.get("/listado")
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text
