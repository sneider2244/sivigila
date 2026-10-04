import sqlite3

import pytest

from tests.utils import CLAVE, crear_ficha, crear_upgd, crear_usuario


def test_init_db_siembra_usuarios_con_cambio_obligatorio_y_eventos(db):
    admin = db.get_user_by_username("admin")
    demo = db.get_user_by_username("SIVIGILA")
    assert admin["rol"] == "super_admin"
    assert admin["debe_cambiar_password"] == 1
    assert demo["debe_cambiar_password"] == 1
    assert [e["codigo"] for e in db.list_eventos()] == ["100", "210", "205"]


def test_init_db_agrega_columna_en_base_existente(tmp_path, monkeypatch):
    ruta = tmp_path / "vieja.db"
    conn = sqlite3.connect(ruta)
    conn.execute(
        "CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, "
        "password_hash TEXT NOT NULL, salt TEXT NOT NULL, nombre_completo TEXT NOT NULL, "
        "rol TEXT NOT NULL DEFAULT 'digitador', permisos TEXT NOT NULL DEFAULT '{}', "
        "activo INTEGER NOT NULL DEFAULT 1, creado_en TEXT NOT NULL, creado_por INTEGER)"
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("SIVIGILA_DB_PATH", str(ruta))
    from sivigila import db

    db.init_db()
    with db.get_conn() as c:
        columnas = {r["name"] for r in c.execute("PRAGMA table_info(usuarios)")}
    assert "debe_cambiar_password" in columnas


def test_verify_password(db):
    usuario = crear_usuario(db, "digi")
    assert db.verify_password(CLAVE, usuario["password_hash"], usuario["salt"])
    assert not db.verify_password("otra", usuario["password_hash"], usuario["salt"])


def test_create_notificacion_rechaza_columna_desconocida(db):
    upgd_id = crear_upgd(db)
    with pytest.raises(ValueError, match="columna_falsa"):
        db.create_notificacion(
            {"upgd_id": upgd_id, "codigo_evento": "210", "columna_falsa": "x"}, None
        )


def test_update_notificacion_rechaza_columna_desconocida_e_id(db):
    upgd_id = crear_upgd(db)
    usuario = crear_usuario(db, "digi")
    ficha_id = crear_ficha(db, upgd_id, usuario["id"])
    with pytest.raises(ValueError):
        db.update_notificacion(ficha_id, {"nombre; DROP TABLE usuarios": "x"})
    with pytest.raises(ValueError):
        db.update_notificacion(ficha_id, {"id": 99})


def test_add_laboratorio_y_upgd_rechazan_columna_desconocida(db):
    upgd_id = crear_upgd(db)
    usuario = crear_usuario(db, "digi")
    ficha_id = crear_ficha(db, upgd_id, usuario["id"])
    with pytest.raises(ValueError):
        db.add_laboratorio(ficha_id, {"prueba": "IgM", "otra": "x"})
    with pytest.raises(ValueError):
        db.upsert_upgd({"razon_social": "X", "cod_prestador": "1", "otra": "x"})


def test_upsert_upgd_actualiza_sin_crear_otra(db):
    upgd_id = crear_upgd(db, "Hospital A")
    db.upsert_upgd({"razon_social": "Hospital B"}, upgd_id)
    filas = db.list_upgd()
    assert len(filas) == 1
    assert filas[0]["razon_social"] == "Hospital B"


def test_roles_asignables():
    from sivigila import db

    assert db.roles_asignables("super_admin") == ["super_admin", "admin", "digitador", "consulta"]
    assert db.roles_asignables("admin") == ["digitador", "consulta"]
    assert db.roles_asignables("digitador") == ["consulta"]
    assert db.roles_asignables("consulta") == []


def test_puede_gestionar(db):
    jefa = crear_usuario(db, "jefa", rol="admin")
    otra_admin = crear_usuario(db, "otra", rol="admin")
    digi = crear_usuario(db, "digi")
    superu = crear_usuario(db, "super", rol="super_admin")
    assert db.puede_gestionar(jefa, digi)
    assert not db.puede_gestionar(jefa, otra_admin)
    assert db.puede_gestionar(superu, jefa)
    assert not db.puede_gestionar(digi, digi)


def test_list_notificaciones_pagina_y_cuenta(db):
    upgd_id = crear_upgd(db)
    usuario = crear_usuario(db, "digi")
    for i in range(7):
        crear_ficha(db, upgd_id, usuario["id"], numero_id=f"9{i}", primer_nombre=f"Persona{i}")
    crear_ficha(db, upgd_id, usuario["id"], codigo_evento="100", numero_id="555")
    assert db.count_notificaciones() == 8
    assert db.count_notificaciones(codigo_evento="100") == 1
    assert db.count_notificaciones("Persona3") == 1
    assert len(db.list_notificaciones(limite=5)) == 5
    assert len(db.list_notificaciones(limite=5, offset=5)) == 3


def test_reset_password_marca_cambio_obligatorio(db):
    usuario = crear_usuario(db, "digi")
    db.reset_password(usuario["id"], "nueva-clave")
    assert db.get_user_by_id(usuario["id"])["debe_cambiar_password"] == 1
    db.reset_password(usuario["id"], "otra-clave", debe_cambiar=False)
    assert db.get_user_by_id(usuario["id"])["debe_cambiar_password"] == 0


def test_get_laboratorio_y_cascada(db):
    upgd_id = crear_upgd(db)
    usuario = crear_usuario(db, "digi")
    ficha_id = crear_ficha(db, upgd_id, usuario["id"])
    lab_id = db.add_laboratorio(ficha_id, {"prueba": "IgM"})
    assert db.get_laboratorio(lab_id)["notificacion_id"] == ficha_id
    db.delete_notificacion(ficha_id)
    assert db.get_laboratorio(lab_id) is None
