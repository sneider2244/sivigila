import re

from tests.utils import crear_ficha, crear_upgd, crear_usuario, iniciar_sesion, post


def test_dashboard_muestra_conteo_por_evento(client, db, digitador):
    upgd_id = crear_upgd(db)
    crear_ficha(db, upgd_id, digitador["id"])
    r = client.get("/")
    assert r.status_code == 200
    assert "Dengue" in r.text
    assert "<strong>1</strong>" in r.text


def test_dashboard_sin_upgd_muestra_aviso(client, digitador):
    r = client.get("/")
    assert "Aún no has configurado ninguna UPGD" in r.text


def test_dashboard_oculta_secciones_sin_permiso(client, db):
    crear_usuario(db, "lector", rol="consulta")
    iniciar_sesion(client, "lector")
    r = client.get("/")
    assert r.status_code == 200
    assert 'href="/usuarios"' not in r.text
    assert 'href="/upgd"' not in r.text
    assert 'href="/listado"' in r.text


def test_crear_upgd(client, db, digitador):
    r = post(client, "/upgd/nueva", {
        "cod_prestador": "110010000001", "razon_social": "Hospital Central",
        "naturaleza_juridica": "Pública", "internet": "1",
    })
    assert r.status_code == 303
    assert r.headers["location"] == "/upgd?guardada=1"
    filas = db.list_upgd()
    assert len(filas) == 1
    assert filas[0]["internet"] == 1
    assert filas[0]["computador"] == 0
    assert filas[0]["fecha_caracteriza"] is not None


def test_crear_upgd_sin_obligatorios_no_guarda(client, db, digitador):
    r = post(client, "/upgd/nueva", {"cod_prestador": "", "razon_social": ""})
    assert r.status_code == 200
    assert "Este campo es obligatorio." in r.text
    assert db.list_upgd() == []


def test_crear_upgd_con_opcion_invalida(client, db, digitador):
    r = post(client, "/upgd/nueva", {
        "cod_prestador": "1", "razon_social": "X", "naturaleza_juridica": "Inventada",
    })
    assert "Selecciona una opción de la lista." in r.text
    assert db.list_upgd() == []


def test_editar_upgd_no_crea_otra(client, db, digitador):
    upgd_id = crear_upgd(db, "Hospital A")
    r = post(client, f"/upgd/{upgd_id}", {"cod_prestador": "1", "razon_social": "Hospital B"})
    assert r.status_code == 303
    filas = db.list_upgd()
    assert len(filas) == 1
    assert filas[0]["razon_social"] == "Hospital B"


def test_activar_upgd_en_sesion(client, db, digitador):
    crear_upgd(db, "A Primero")
    segunda = crear_upgd(db, "B Segundo")
    r = post(client, f"/upgd/{segunda}/activar")
    assert r.status_code == 303
    pagina = client.get("/upgd").text
    fila = re.search(rf'<tr id="upgd-{segunda}">(.*?)</tr>', pagina, re.S).group(1)
    assert "En uso" in fila


def test_upgd_inexistente_404(client, digitador):
    assert client.get("/upgd/999").status_code == 404
