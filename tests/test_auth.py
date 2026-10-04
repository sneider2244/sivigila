import logging

from fastapi.testclient import TestClient

from tests.utils import CLAVE, crear_usuario, iniciar_sesion, post, token_csrf


def test_login_no_muestra_credenciales_demo(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "sivigila2026" not in r.text
    assert "Admin123!" not in r.text
    assert 'name="csrf_token"' in r.text


def test_login_correcto_redirige_a_primera_pantalla(client, db):
    crear_usuario(db, "digi")
    r = iniciar_sesion(client, "digi")
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_login_incorrecto_muestra_error_y_audita(client, db):
    crear_usuario(db, "digi")
    r = iniciar_sesion(client, "digi", "mala")
    assert r.status_code == 401
    assert "Usuario o contraseña incorrectos." in r.text
    with db.get_conn() as c:
        acciones = [f["accion"] for f in c.execute("SELECT accion FROM auditoria")]
    assert "LOGIN_FALLIDO" in acciones


def test_post_sin_token_csrf_es_rechazado(client, db):
    crear_usuario(db, "digi")
    r = client.post("/login", data={"username": "digi", "password": CLAVE}, follow_redirects=False)
    assert r.status_code == 403


def test_token_csrf_por_encabezado_htmx(client, db):
    crear_usuario(db, "digi")
    token = token_csrf(client)
    r = client.post(
        "/login",
        data={"username": "digi", "password": CLAVE},
        headers={"X-CSRF-Token": token},
        follow_redirects=False,
    )
    assert r.status_code == 303


def test_login_regenera_token_csrf(client, db):
    crear_usuario(db, "digi")
    antes = token_csrf(client)
    iniciar_sesion(client, "digi")
    assert token_csrf(client) != antes


def test_ruta_protegida_sin_sesion_redirige_a_login(client):
    r = client.get("/sin-acceso", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_peticion_htmx_sin_sesion_pide_redireccion(client):
    r = client.get("/sin-acceso", headers={"HX-Request": "true"}, follow_redirects=False)
    assert r.status_code == 401
    assert r.headers["HX-Redirect"] == "/login"


def test_logout_cierra_la_sesion(client, db):
    crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    r = post(client, "/logout")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    assert client.get("/sin-acceso", follow_redirects=False).headers["location"] == "/login"


def test_usuario_sin_ninguna_pantalla_va_a_sin_acceso(client, db):
    nada = {k: False for k in db.PERMISOS_LABELS}
    crear_usuario(db, "nadie", rol="consulta", permisos=nada)
    r = iniciar_sesion(client, "nadie")
    assert r.headers["location"] == "/sin-acceso"
    pagina = client.get("/sin-acceso")
    assert pagina.status_code == 200
    assert "ninguna sección" in pagina.text




def test_bloqueo_tras_cinco_intentos_y_desbloqueo(client, db, monkeypatch):
    from sivigila import auth

    crear_usuario(db, "digi")
    reloj = [1000.0]
    monkeypatch.setattr(auth, "_ahora", lambda: reloj[0])
    for _ in range(5):
        iniciar_sesion(client, "digi", "mala")
    r = iniciar_sesion(client, "digi")  # clave correcta, pero bloqueado
    assert r.status_code == 429
    assert "Espera 10 minutos" in r.text
    reloj[0] += 601
    assert iniciar_sesion(client, "digi").status_code == 303


def test_usuario_sembrado_debe_cambiar_password(client):
    r = iniciar_sesion(client, "admin", "Admin123!")
    assert r.headers["location"] == "/cambiar-password"
    r = client.get("/sin-acceso", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/cambiar-password"


def test_cambiar_password_valida_campos(client, db):
    crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    r = post(client, "/cambiar-password",
             {"actual": "mala", "nueva": "abc", "confirmacion": "xyz"})
    assert r.status_code == 200
    assert "La contraseña actual no es correcta." in r.text
    assert "Debe tener al menos 6 caracteres." in r.text
    assert "No coincide con la nueva contraseña." in r.text


def test_cambiar_password_correcto(client, db):
    iniciar_sesion(client, "admin", "Admin123!")
    r = post(client, "/cambiar-password",
             {"actual": "Admin123!", "nueva": "NuevaClave9", "confirmacion": "NuevaClave9"})
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert db.get_user_by_username("admin")["debe_cambiar_password"] == 0
    post(client, "/logout")
    assert iniciar_sesion(client, "admin", "NuevaClave9").status_code == 303


def test_usuario_desactivado_pierde_la_sesion(client, db):
    usuario = crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    db.set_user_active(usuario["id"], False)
    r = client.get("/sin-acceso", follow_redirects=False)
    assert r.headers["location"] == "/login"


def test_pagina_404(client):
    r = client.get("/no-existe")
    assert r.status_code == 404
    assert "No encontrado" in r.text


def test_error_500_no_expone_ni_registra_el_detalle(db, caplog):
    from sivigila.main import create_app

    app = create_app()

    @app.get("/explota")
    def explota():
        raise RuntimeError("Paciente Ana Pérez CC 1032456789")

    with TestClient(app, raise_server_exceptions=False) as c:
        with caplog.at_level(logging.ERROR, logger="sivigila"):
            r = c.get("/explota")
    assert r.status_code == 500
    assert "Ocurrió un error inesperado" in r.text
    assert "1032456789" not in r.text
    assert "RuntimeError" in caplog.text
    assert "1032456789" not in caplog.text
