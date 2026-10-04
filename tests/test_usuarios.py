import pytest

from tests.utils import crear_usuario, iniciar_sesion, post


@pytest.fixture
def jefa(db, client):
    usuario = crear_usuario(db, "jefa", rol="admin")
    iniciar_sesion(client, "jefa")
    return usuario


def _nuevo(**extra):
    datos = {"username": "nuevo.digi", "nombre_completo": "Nuevo Digitador",
             "password": "clave123", "rol": "digitador",
             "perm_notificar_individual": "1", "perm_ver_reportes": "1"}
    datos.update(extra)
    return datos


def test_lista_usuarios(client, db, jefa):
    crear_usuario(db, "digi")
    r = client.get("/usuarios")
    assert r.status_code == 200
    assert "Usuario digi" in r.text


def test_crear_usuario_queda_con_cambio_obligatorio(client, db, jefa):
    r = post(client, "/usuarios/nuevo", _nuevo())
    assert r.status_code == 303
    creado = db.get_user_by_username("nuevo.digi")
    assert creado["rol"] == "digitador"
    assert creado["debe_cambiar_password"] == 1
    assert creado["creado_por"] == jefa["id"]
    permisos = db.get_permisos(creado)
    assert permisos["notificar_individual"] is True
    assert permisos["gestionar_laboratorios"] is False


def test_crear_usuario_valida(client, db, jefa):
    crear_usuario(db, "digi")
    r = post(client, "/usuarios/nuevo", _nuevo(username="digi", password="123", nombre_completo=""))
    assert r.status_code == 200
    assert "Ese código de usuario ya existe." in r.text
    assert "Debe tener al menos 6 caracteres." in r.text
    assert "Este campo es obligatorio." in r.text


def test_admin_no_puede_asignar_rol_igual_o_superior(client, db, jefa):
    r = post(client, "/usuarios/nuevo", _nuevo(rol="admin"))
    assert r.status_code == 200
    assert "No puedes asignar ese rol." in r.text
    assert not db.username_exists("nuevo.digi")


def test_admin_no_puede_editar_otro_admin(client, db, jefa):
    otra = crear_usuario(db, "otra", rol="admin")
    assert client.get(f"/usuarios/{otra['id']}/editar").status_code == 403
    r = post(client, f"/usuarios/{otra['id']}/editar",
             {"nombre_completo": "Hackeada", "rol": "consulta"})
    assert r.status_code == 403
    assert db.get_user_by_id(otra["id"])["nombre_completo"] == "Usuario otra"


def test_admin_edita_digitador(client, db, jefa):
    digi = crear_usuario(db, "digi")
    r = post(client, f"/usuarios/{digi['id']}/editar",
             {"nombre_completo": "Digi Editado", "rol": "consulta", "perm_ver_reportes": "1"})
    assert r.status_code == 303
    editado = db.get_user_by_id(digi["id"])
    assert editado["nombre_completo"] == "Digi Editado"
    assert editado["rol"] == "consulta"


def test_desactivar_y_activar(client, db, jefa):
    digi = crear_usuario(db, "digi")
    assert post(client, f"/usuarios/{digi['id']}/activo", {"activo": "0"}).status_code == 303
    assert db.get_user_by_id(digi["id"])["activo"] == 0
    post(client, f"/usuarios/{digi['id']}/activo", {"activo": "1"})
    assert db.get_user_by_id(digi["id"])["activo"] == 1


def test_no_puede_desactivarse_a_si_mismo(client, db):
    superu = crear_usuario(db, "super", rol="super_admin")
    iniciar_sesion(client, "super")
    r = post(client, f"/usuarios/{superu['id']}/activo", {"activo": "0"})
    assert r.status_code == 403
    assert db.get_user_by_id(superu["id"])["activo"] == 1


def test_restablecer_password(client, db, jefa):
    digi = crear_usuario(db, "digi")
    r = post(client, f"/usuarios/{digi['id']}/password", {"password": "otra-clave"})
    assert r.status_code == 303
    actualizado = db.get_user_by_id(digi["id"])
    assert actualizado["debe_cambiar_password"] == 1
    assert db.verify_password("otra-clave", actualizado["password_hash"], actualizado["salt"])


def test_restablecer_password_corta(client, db, jefa):
    digi = crear_usuario(db, "digi")
    r = post(client, f"/usuarios/{digi['id']}/password", {"password": "123"})
    assert r.status_code == 200
    assert "Debe tener al menos 6 caracteres." in r.text


def test_permisos_por_defecto_del_rol(client, jefa):
    r = client.get("/usuarios/permisos?rol=consulta", headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert 'name="perm_ver_reportes" value="1" checked' in r.text
    assert 'name="perm_notificar_individual" value="1" checked' not in r.text
