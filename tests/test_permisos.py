import pytest

from tests.utils import crear_ficha, crear_upgd, crear_usuario, iniciar_sesion, post

# (método, ruta, permisos que la habilitan: basta con uno)
RUTAS = [
    ("get", "/", {"ver_reportes"}),
    ("get", "/listado", {"ver_reportes"}),
    ("get", "/listado/resultados", {"ver_reportes"}),
    ("get", "/upgd", {"gestionar_caracterizacion"}),
    ("get", "/upgd/nueva", {"gestionar_caracterizacion"}),
    ("post", "/upgd/nueva", {"gestionar_caracterizacion"}),
    ("get", "/upgd/{upgd}", {"gestionar_caracterizacion"}),
    ("post", "/upgd/{upgd}", {"gestionar_caracterizacion"}),
    ("post", "/upgd/{upgd}/activar", {"gestionar_caracterizacion"}),
    ("get", "/fichas/nueva", {"notificar_individual"}),
    ("post", "/fichas", {"notificar_individual"}),
    ("get", "/fichas/campos?codigo_evento=210", {"notificar_individual", "editar_notificaciones"}),
    ("get", "/fichas/{ficha}", {"notificar_individual", "editar_notificaciones", "ver_reportes"}),
    ("post", "/fichas/{ficha}", {"editar_notificaciones"}),
    ("post", "/fichas/{ficha}/terminar", {"editar_notificaciones"}),
    ("post", "/fichas/{ficha}/eliminar", {"editar_notificaciones"}),
    ("post", "/fichas/{ficha}/laboratorios", {"gestionar_laboratorios"}),
    ("post", "/fichas/{ficha}/laboratorios/{lab}/eliminar", {"gestionar_laboratorios"}),
    ("get", "/usuarios", {"gestionar_usuarios"}),
    ("get", "/usuarios/nuevo", {"gestionar_usuarios"}),
    ("post", "/usuarios/nuevo", {"gestionar_usuarios"}),
    ("get", "/usuarios/permisos?rol=digitador", {"gestionar_usuarios"}),
    ("get", "/usuarios/{otro}/editar", {"gestionar_usuarios"}),
    ("post", "/usuarios/{otro}/editar", {"gestionar_usuarios"}),
    ("post", "/usuarios/{otro}/activo", {"gestionar_usuarios"}),
    ("get", "/usuarios/{otro}/password", {"gestionar_usuarios"}),
    ("post", "/usuarios/{otro}/password", {"gestionar_usuarios"}),
]


@pytest.fixture
def escenario(db):
    duena = crear_usuario(db, "duena", rol="super_admin")
    upgd = crear_upgd(db)
    ficha = crear_ficha(db, upgd, duena["id"])
    lab = db.add_laboratorio(ficha, {"prueba": "IgM"})
    otro = crear_usuario(db, "otro", rol="consulta")
    return {"upgd": upgd, "ficha": ficha, "lab": lab, "otro": otro["id"]}


def _pedir(client, metodo, ruta):
    if metodo == "get":
        return client.get(ruta, follow_redirects=False)
    return post(client, ruta)


@pytest.mark.parametrize("metodo, ruta, _permisos", RUTAS)
def test_usuario_sin_permisos_recibe_403(client, db, escenario, metodo, ruta, _permisos):
    crear_usuario(db, "nadie", rol="consulta", permisos={k: False for k in db.PERMISOS_LABELS})
    iniciar_sesion(client, "nadie")
    r = _pedir(client, metodo, ruta.format(**escenario))
    assert r.status_code == 403, f"{metodo.upper()} {ruta} respondió {r.status_code}"
    assert db.get_notificacion(escenario["ficha"]) is not None
    assert db.get_laboratorio(escenario["lab"]) is not None


@pytest.mark.parametrize("metodo, ruta, permisos", [r for r in RUTAS if r[0] == "get"])
def test_rol_consulta_solo_entra_donde_ver_reportes_basta(client, db, escenario, metodo, ruta, permisos):
    crear_usuario(db, "lector", rol="consulta")
    iniciar_sesion(client, "lector")
    r = _pedir(client, metodo, ruta.format(**escenario))
    esperado = 200 if "ver_reportes" in permisos else 403
    assert r.status_code == esperado, f"GET {ruta} respondió {r.status_code}"


@pytest.mark.parametrize("ruta", [r[1] for r in RUTAS if r[0] == "get"])
def test_sin_sesion_redirige_a_login(client, escenario, ruta):
    r = client.get(ruta.format(**escenario), follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_permiso_revocado_aplica_en_la_siguiente_peticion(client, db, escenario):
    digi = crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    assert client.get("/fichas/nueva").status_code == 200
    permisos = db.get_permisos(digi)
    permisos["notificar_individual"] = False
    db.update_user(digi["id"], permisos=permisos)
    assert client.get("/fichas/nueva").status_code == 403


def test_acceso_denegado_queda_en_auditoria(client, db, escenario):
    crear_usuario(db, "lector", rol="consulta")
    iniciar_sesion(client, "lector")
    client.get("/usuarios")
    with db.get_conn() as c:
        fila = c.execute(
            "SELECT detalle FROM auditoria WHERE accion = 'ACCESO_DENEGADO'"
        ).fetchone()
    assert fila is not None
    assert "/usuarios" in fila["detalle"]
