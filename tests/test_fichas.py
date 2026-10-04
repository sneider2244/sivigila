import json
from datetime import date, timedelta

import pytest

from tests.utils import crear_ficha, crear_upgd, crear_usuario, ficha_completa, iniciar_sesion, post


@pytest.fixture
def upgd_id(db):
    return crear_upgd(db)


def test_nueva_sin_upgd_muestra_aviso(client, digitador):
    r = client.get("/fichas/nueva")
    assert r.status_code == 200
    assert "Primero debes configurar" in r.text


def test_nueva_muestra_formulario_con_eventos(client, digitador, upgd_id):
    r = client.get("/fichas/nueva")
    assert "210 - Dengue" in r.text
    assert "Guardar ficha" in r.text
    assert "Terminar" not in r.text


def test_crear_ficha_minima(client, db, digitador, upgd_id):
    r = post(client, "/fichas", {"codigo_evento": "210", "numero_id": "123", "primer_nombre": "Ana"})
    assert r.status_code == 303
    ficha_id = int(r.headers["location"].split("/")[2].split("?")[0])
    ficha = db.get_notificacion(ficha_id)
    assert ficha["estado_ficha"] == "En proceso"
    assert ficha["upgd_id"] == upgd_id
    assert ficha["creado_por"] == digitador["id"]
    anio, semana, _ = date.today().isocalendar()
    assert (ficha["anio"], ficha["semana"]) == (anio, semana)


def test_crear_ficha_sin_obligatorios_no_guarda(client, db, digitador, upgd_id):
    r = post(client, "/fichas", {"codigo_evento": "210", "primer_nombre": "Ana"})
    assert r.status_code == 200
    assert "Este campo es obligatorio." in r.text
    assert 'value="Ana"' in r.text  # conserva lo escrito
    assert db.count_notificaciones() == 0


def test_fecha_futura_rechazada(client, db, digitador, upgd_id):
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = post(client, "/fichas", {"codigo_evento": "210", "numero_id": "1",
                                 "primer_nombre": "Ana", "fecha_consulta": manana})
    assert "La fecha no puede ser posterior a hoy." in r.text
    assert db.count_notificaciones() == 0


def test_complementario_invalido_rechazado(client, db, digitador, upgd_id):
    r = post(client, "/fichas", {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana",
                                 "comp__resultado_igm": "Quizás"})
    assert "Selecciona una opción de la lista." in r.text
    assert db.count_notificaciones() == 0


def test_campos_complementarios_por_evento(client, digitador, upgd_id):
    r = client.get("/fichas/campos?codigo_evento=100", headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "Gravedad del accidente" in r.text
    assert 'name="comp__gravedad"' in r.text
    assert "<html" not in r.text


def test_editar_guarda_y_conserva_upgd(client, db, digitador, upgd_id):
    otra = crear_upgd(db, "Otra UPGD")
    ficha_id = crear_ficha(db, upgd_id, digitador["id"])
    post(client, f"/upgd/{otra}/activar")
    r = post(client, f"/fichas/{ficha_id}", ficha_completa(primer_nombre="Beatriz"))
    assert r.status_code == 303
    ficha = db.get_notificacion(ficha_id)
    assert ficha["primer_nombre"] == "Beatriz"
    assert ficha["upgd_id"] == upgd_id
    assert ficha["edad"] == 30


def test_cambiar_evento_descarta_complementarios_anteriores(client, db, digitador, upgd_id):
    ficha_id = crear_ficha(db, upgd_id, digitador["id"],
                           datos_complementarios=json.dumps({"fiebre": "Sí", "resultado_igm": "Positivo"}))
    r = post(client, f"/fichas/{ficha_id}", {
        "codigo_evento": "100", "numero_id": "1000", "primer_nombre": "Ana",
        "comp__gravedad": "Leve",
    })
    assert r.status_code == 303
    ficha = db.get_notificacion(ficha_id)
    assert ficha["codigo_evento"] == "100"
    assert json.loads(ficha["datos_complementarios"]) == {"gravedad": "Leve"}


def test_terminar_incompleta_no_cambia_estado(client, db, digitador, upgd_id):
    ficha_id = crear_ficha(db, upgd_id, digitador["id"])
    r = post(client, f"/fichas/{ficha_id}/terminar",
             {"codigo_evento": "210", "numero_id": "1000", "primer_nombre": "Ana"})
    assert r.status_code == 200
    assert "Revisa los campos marcados." in r.text
    assert db.get_notificacion(ficha_id)["estado_ficha"] == "En proceso"


def test_terminar_completa(client, db, digitador, upgd_id):
    ficha_id = crear_ficha(db, upgd_id, digitador["id"])
    r = post(client, f"/fichas/{ficha_id}/terminar", ficha_completa())
    assert r.status_code == 303
    assert db.get_notificacion(ficha_id)["estado_ficha"] == "Terminada"


def test_eliminar_ficha_y_sus_laboratorios(client, db, digitador, upgd_id):
    ficha_id = crear_ficha(db, upgd_id, digitador["id"])
    lab_id = db.add_laboratorio(ficha_id, {"prueba": "IgM"})
    r = post(client, f"/fichas/{ficha_id}/eliminar")
    assert r.status_code == 303
    assert r.headers["location"] == "/listado"
    assert db.get_notificacion(ficha_id) is None
    assert db.get_laboratorio(lab_id) is None


def test_consulta_ve_ficha_en_solo_lectura(client, db, upgd_id):
    autor = crear_usuario(db, "autor")
    ficha_id = crear_ficha(db, upgd_id, autor["id"])
    crear_usuario(db, "lector", rol="consulta")
    iniciar_sesion(client, "lector")
    r = client.get(f"/fichas/{ficha_id}")
    assert r.status_code == 200
    assert "Guardar ficha" not in r.text
    assert "Eliminar ficha" not in r.text
    assert 'name="primer_nombre" value="Ana" disabled' in r.text


def test_ficha_inexistente_404(client, digitador):
    assert client.get("/fichas/999").status_code == 404
