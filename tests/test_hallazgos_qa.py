"""Hallazgos de la validación en navegador (QA con playwright), cada uno con su test."""

from tests.utils import crear_ficha, crear_upgd, post


# --- Medio 1: no se siembra un segundo usuario con clave publicada ---

def test_solo_se_siembra_el_admin(db):
    assert db.get_user_by_username("admin") is not None
    assert not db.username_exists("SIVIGILA")
    assert len(db.list_users()) == 1


# --- Medio 2: las tablas se desplazan dentro de su contenedor en pantallas angostas ---

def test_listado_envuelve_la_tabla_en_contenedor_con_scroll(client, db, digitador):
    crear_ficha(db, crear_upgd(db), digitador["id"])
    r = client.get("/listado/resultados")
    assert '<div class="tabla-scroll">' in r.text


def test_css_define_contenedor_con_scroll_horizontal(client):
    css = client.get("/static/app.css").text
    assert ".tabla-scroll" in css
    assert "overflow-x: auto" in css


# --- Bajo: recargar la URL de un POST fallido no da 405 ---

def test_recargar_terminar_redirige_a_la_ficha(client, db, digitador):
    ficha_id = crear_ficha(db, crear_upgd(db), digitador["id"])
    r = client.get(f"/fichas/{ficha_id}/terminar", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == f"/fichas/{ficha_id}"


def test_recargar_crear_ficha_redirige_al_formulario(client, digitador):
    r = client.get("/fichas", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/fichas/nueva"


def test_terminar_fallido_sigue_mostrando_errores(client, db, digitador):
    ficha_id = crear_ficha(db, crear_upgd(db), digitador["id"])
    r = post(client, f"/fichas/{ficha_id}/terminar",
             {"codigo_evento": "210", "numero_id": "1000", "primer_nombre": "Ana"})
    assert r.status_code == 200
    assert "Revisa los campos marcados." in r.text
