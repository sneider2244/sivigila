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
