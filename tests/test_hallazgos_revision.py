"""Hallazgos de la revisión final de la rama (críticos e importantes), cada uno con su test."""

import logging
import sqlite3
import sys

from tests.utils import (
    CLAVE, crear_ficha, crear_upgd, crear_usuario, ficha_completa, iniciar_sesion, post,
)

DOC_FICTICIO = "1032456789"  # datos sintéticos

ESQUEMA_VIEJO_USUARIOS = (
    "CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, "
    "password_hash TEXT NOT NULL, salt TEXT NOT NULL, nombre_completo TEXT NOT NULL, "
    "rol TEXT NOT NULL DEFAULT 'digitador', permisos TEXT NOT NULL DEFAULT '{}', "
    "activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL, creado_por INTEGER)"
)


def _filas(html):
    return html.count('class="fila-ficha"')


# --- Crítico 1: la migración debe forzar el cambio de clave a los usuarios existentes ---

def test_migracion_obliga_a_cambiar_clave_a_usuarios_existentes(tmp_path, monkeypatch):
    ruta = tmp_path / "vieja.db"
    conn = sqlite3.connect(ruta)
    conn.execute(ESQUEMA_VIEJO_USUARIOS)
    conn.execute(
        "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, rol, permisos, creado_en) "  # datos sintéticos
        "VALUES ('admin', 'x', 'y', 'Administrador', 'super_admin', '{}', '2026-01-01')"  # datos sintéticos
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("SIVIGILA_DB_PATH", str(ruta))
    from sivigila import db

    db.init_db()
    assert db.get_user_by_username("admin")["debe_cambiar_password"] == 1


# --- Crítico 2: no se pueden otorgar permisos que el actor no tiene ---

def _todos_los_permisos(db):
    return {f"perm_{k}": "1" for k in db.PERMISOS_LABELS}


def test_crear_usuario_no_otorga_permisos_que_el_actor_no_tiene(client, db):
    crear_usuario(db, "jefe", rol="admin", permisos={"gestionar_usuarios": True})
    iniciar_sesion(client, "jefe")
    r = post(client, "/usuarios/nuevo", {
        "username": "titere", "nombre_completo": "Títere", "password": "clave123",
        "rol": "digitador", **_todos_los_permisos(db),
    })
    assert r.status_code == 303
    permisos = db.get_permisos(db.get_user_by_username("titere"))
    assert permisos == {k: k == "gestionar_usuarios" for k in db.PERMISOS_LABELS}


def test_editar_usuario_no_cambia_permisos_que_el_actor_no_tiene(client, db):
    digi = crear_usuario(db, "digi")  # permisos por defecto de digitador
    crear_usuario(db, "jefe", rol="admin", permisos={"gestionar_usuarios": True})
    iniciar_sesion(client, "jefe")
    r = post(client, f"/usuarios/{digi['id']}/editar",
             {"nombre_completo": "Digi", "rol": "digitador", "perm_gestionar_usuarios": "1"})
    assert r.status_code == 303
    permisos = db.get_permisos(db.get_user_by_id(digi["id"]))
    # El jefe puede dar lo que él tiene, y no puede quitar lo que no tiene.
    assert permisos == {**db.permisos_por_defecto("digitador"), "gestionar_usuarios": True}


# --- Importante 3: logout y cambio/restablecimiento de clave invalidan sesiones ---

def _get_con_cookie(client, url, cookie):
    client.cookies.clear()
    return client.get(url, headers={"Cookie": f"sivigila_sesion={cookie}"}, follow_redirects=False)


def test_logout_invalida_una_cookie_copiada(client, db):
    crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    robada = client.cookies.get("sivigila_sesion")
    assert _get_con_cookie(client, "/", robada).status_code == 200
    iniciar_sesion(client, "digi")
    post(client, "/logout")
    r = _get_con_cookie(client, "/", robada)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_restablecer_clave_cierra_sesiones_abiertas(client, db):
    digi = crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    db.reset_password(digi["id"], "otra-clave")
    r = client.get("/", follow_redirects=False)
    assert r.headers["location"] == "/login"


def test_cambiar_clave_propia_mantiene_la_sesion_actual(client, db):
    crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    post(client, "/cambiar-password",
         {"actual": CLAVE, "nueva": "NuevaClave9", "confirmacion": "NuevaClave9"})
    assert client.get("/", follow_redirects=False).status_code == 200


# --- Importante 4: Guardar deja la ficha "En proceso" ---

def test_guardar_ficha_terminada_la_regresa_a_en_proceso(client, db, digitador):
    ficha_id = crear_ficha(db, crear_upgd(db), digitador["id"])
    post(client, f"/fichas/{ficha_id}/terminar", ficha_completa())
    assert db.get_notificacion(ficha_id)["estado_ficha"] == "Terminada"
    post(client, f"/fichas/{ficha_id}",
         {"codigo_evento": "205", "numero_id": "1000", "primer_nombre": "Ana"})
    assert db.get_notificacion(ficha_id)["estado_ficha"] == "En proceso"


# --- Importante 5: búsqueda sin distinguir mayúsculas ni tildes, comodines como texto ---

def test_busqueda_ignora_mayusculas_y_tildes(client, db, digitador):
    crear_ficha(db, crear_upgd(db), digitador["id"], primer_nombre="José", primer_apellido="PÉREZ")  # datos sintéticos
    for q in ("Pérez", "pérez", "perez", "jose", "JOSÉ"):
        r = client.get("/listado/resultados", params={"q": q})
        assert _filas(r.text) == 1, q


def test_busqueda_trata_comodines_como_texto(client, db, digitador):
    crear_ficha(db, crear_upgd(db), digitador["id"], primer_nombre="Ana")
    for q in ("_", "%"):
        assert _filas(client.get("/listado/resultados", params={"q": q}).text) == 0, q


# --- Importante 6: un error en una petición HTMX recarga la página en vez de quedar mudo ---

def test_htmx_sin_permiso_pide_recargar(client, db):
    autor = crear_usuario(db, "autor")
    ficha_id = crear_ficha(db, crear_upgd(db), autor["id"])
    crear_usuario(db, "lector", rol="consulta")
    iniciar_sesion(client, "lector")
    r = post(client, f"/fichas/{ficha_id}/laboratorios", {"prueba": "IgM"},
             headers={"HX-Request": "true"})
    assert r.status_code == 403
    assert r.headers.get("HX-Refresh") == "true"


def test_htmx_con_token_vencido_pide_recargar(client, db, digitador):
    r = client.post("/fichas/1/laboratorios", data={"prueba": "IgM"},
                    headers={"HX-Request": "true", "X-CSRF-Token": "token-viejo"})
    assert r.status_code == 403
    assert r.headers.get("HX-Refresh") == "true"


def test_error_normal_no_pide_recargar(client, digitador):
    assert "HX-Refresh" not in client.get("/no-existe").headers


# --- Importante 7: los logs de uvicorn no llevan query strings ni mensajes de excepción ---

def test_filtro_quita_query_string_del_access_log():
    from sivigila.main import FiltroDatosSensibles

    registro = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1:5000", "GET", f"/listado/resultados?q={DOC_FICTICIO}", "1.1", 200), None,
    )
    assert FiltroDatosSensibles().filter(registro)
    mensaje = registro.getMessage()
    assert DOC_FICTICIO not in mensaje
    assert "/listado/resultados" in mensaje


def test_filtro_quita_el_mensaje_de_la_excepcion():
    from sivigila.main import FiltroDatosSensibles

    try:
        raise RuntimeError(f"dato sensible {DOC_FICTICIO}")
    except RuntimeError:
        exc_info = sys.exc_info()
    registro = logging.LogRecord("uvicorn.error", logging.ERROR, "", 0,
                                 "Exception in ASGI application", (), exc_info)
    FiltroDatosSensibles().filter(registro)
    texto = logging.Formatter().format(registro)
    assert DOC_FICTICIO not in texto
    assert "RuntimeError" in texto


def test_create_app_instala_el_filtro_en_uvicorn(db):
    from sivigila.main import FiltroDatosSensibles, create_app

    create_app()
    for nombre in ("uvicorn.access", "uvicorn.error"):
        filtros = logging.getLogger(nombre).filters
        assert any(isinstance(f, FiltroDatosSensibles) for f in filtros), nombre
