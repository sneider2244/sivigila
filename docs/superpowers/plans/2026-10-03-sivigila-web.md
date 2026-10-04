# SIVIGILA Web Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la app de escritorio SIVIGILA (CustomTkinter) por una app web FastAPI con las mismas pantallas y flujo, permisos validados en el servidor y los fallos detectados corregidos.

**Architecture:** Paquete `sivigila/` con FastAPI que renderiza HTML en el servidor (Jinja2) y usa HTMX solo para tres interacciones parciales (campos complementarios, laboratorios, buscador del listado). `sivigila/db.py` es el `database.py` actual con lista blanca de columnas; las rutas validan entrada (`validacion.py`), llaman a `db` y renderizan plantilla. Sesión en cookie firmada, CSRF global, y una dependencia `require_permiso()` por ruta.

**Tech Stack:** Python 3.13, FastAPI, Uvicorn, Jinja2, HTMX 2.0.4 (archivo local), SQLite (`sqlite3`), pytest + `fastapi.testclient`.

**Spec:** `docs/superpowers/specs/2026-10-03-sivigila-web-design.md`

## Global Constraints

- Python 3.13. Dependencias de ejecución: `fastapi>=0.115`, `uvicorn[standard]>=0.30`, `jinja2>=3.1`, `python-multipart>=0.0.9`, `itsdangerous>=2.2`. Desarrollo: `pytest>=8`, `httpx>=0.27`. Ninguna otra.
- Toda la interfaz en español de Colombia, tuteando ("Selecciona", "Revisa"), nunca "usted".
- Nunca `alert()`, `confirm()` ni `prompt()` del navegador; confirmaciones dentro de la página.
- HTMX se sirve desde `sivigila/static/htmx.min.js` (versión 2.0.4). Sin CDN.
- Ruta de la base: variable `SIVIGILA_DB_PATH` (default `sivigila.db` en la raíz del repo). Clave de sesión: `SIVIGILA_SECRET_KEY`. Cookie `Secure` solo si `SIVIGILA_COOKIE_SECURE=1`.
- Los logs del servidor nunca incluyen datos personales del paciente (Ley 1581): solo método, ruta, ids y tipo de excepción.
- Acciones de auditoría en MAYÚSCULAS con guion bajo (`LOGIN`, `LOGIN_FALLIDO`, `GUARDA_FICHA`), como hoy.
- Todo `POST` exitoso responde con redirect `303` (patrón POST-redirect-GET), salvo los parciales HTMX.
- Formularios normales con errores de validación: `200` re-renderizando el formulario. Parciales HTMX con errores: `422`.
- Contraseña mínima: 6 caracteres.
- Los commits terminan con la línea `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` cuando los hace un agente.
- Comandos de test desde la raíz del repo con el venv activo: `python -m pytest`.

## Review Focus

1. **HTML o scripts escritos en campos de texto** (nombre `<script>…`): deben verse como texto escapado en listado y ficha, nunca ejecutarse. → test en Task 8.
2. **Cambiar el evento de una ficha ya guardada**: los datos complementarios del evento anterior deben descartarse, no quedar mezclados. → test en Task 6.
3. **Página del listado inválida** (`pagina=abc`, `-3`, `999`): debe caer en la primera o la última página, nunca 500. → test en Task 8.
4. **Búsqueda con apóstrofo o tildes** (`O'Neil`, `Pérez`): debe encontrar la ficha sin error. → test en Task 8.
5. **Permiso revocado o usuario desactivado a mitad de sesión**: la siguiente petición debe recibir 403 o ir a login, sin esperar a que cierre sesión. → tests en Task 3 y Task 10.

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `sivigila/__init__.py` | Marca el paquete |
| `sivigila/db.py` | Única capa SQLite: esquema, migración, siembra, CRUD, lista blanca de columnas, roles |
| `sivigila/catalogos.py` | Definición de campos de formularios (ficha, UPGD, laboratorio), etiquetas de rol |
| `sivigila/validacion.py` | Validación pura de formularios (fechas, listas, complementarios, edad) |
| `sivigila/auth.py` | Sesión, CSRF, `usuario_actual`, `require_permiso`, bloqueo de login, excepciones |
| `sivigila/web.py` | `render()`, `redirigir()`, `primera_pantalla()`, `upgd_activa()`, `es_htmx()` |
| `sivigila/main.py` | `create_app()`, middleware, estáticos, routers, manejadores de error |
| `sivigila/routes/*.py` | Un router por pantalla |
| `sivigila/templates/*.html` | Plantillas Jinja2; parciales HTMX empiezan con `_` |
| `sivigila/static/` | `app.css`, `app.js` (pestañas), `htmx.min.js` |
| `tests/` | `conftest.py` (fixtures), `utils.py` (helpers), un archivo por área |

---

### Task 1: Esqueleto del paquete y capa de datos

**Files:**
- Create: `sivigila/__init__.py`, `sivigila/db.py`, `sivigila/routes/__init__.py`, `requirements-dev.txt`, `pyproject.toml`, `.gitignore`, `tests/__init__.py`, `tests/conftest.py`, `tests/utils.py`, `tests/test_db.py`
- Modify: `requirements.txt`
- Remove from index: `sivigila.db`, `__pycache__/database.cpython-314.pyc`

**Interfaces:**
- Consumes: nada.
- Produces (en `sivigila.db`): `get_conn()`, `init_db()`, `verify_password(password, password_hash, salt) -> bool`, `create_user(username, password, nombre_completo, rol="digitador", permisos=None, creado_por=None, debe_cambiar_password=False)`, `get_user_by_username(username) -> Row|None` (solo activos), `get_user_by_id(id) -> Row|None`, `username_exists(username) -> bool`, `list_users() -> list[Row]`, `update_user(user_id, nombre_completo=None, rol=None, permisos=None)`, `set_user_active(user_id, activo: bool)`, `reset_password(user_id, new_password, debe_cambiar=True)`, `log_action(usuario_id, accion, detalle="")`, `ROLES_JERARQUIA`, `ROLES_DISPONIBLES`, `PERMISOS_DEFAULT`, `PERMISOS_LABELS`, `permisos_por_defecto(rol) -> dict`, `get_permisos(row) -> dict`, `tiene_permiso(row, clave) -> bool`, `puede_gestionar(actor, objetivo) -> bool`, `roles_asignables(rol_actor) -> list[str]`, `list_eventos()`, `get_evento(codigo)`, `upsert_upgd(data, upgd_id=None) -> int`, `list_upgd()`, `get_upgd(id)`, `create_notificacion(data, usuario_id) -> int`, `update_notificacion(id, data)`, `get_notificacion(id)`, `list_notificaciones(filtro_texto="", codigo_evento=None, limite=None, offset=0)`, `count_notificaciones(filtro_texto="", codigo_evento=None) -> int`, `count_notificaciones_por_evento()`, `delete_notificacion(id)`, `add_laboratorio(notificacion_id, data) -> int`, `get_laboratorio(lab_id)`, `list_laboratorios(notificacion_id)`, `delete_laboratorio(lab_id)`.
- Produces (tests): fixture `db`; helpers en `tests/utils.py`: `CLAVE`, `crear_usuario(db, username, rol="digitador", permisos=None)`, `crear_upgd(db, razon_social=...) -> int`, `crear_ficha(db, upgd_id, usuario_id, **extra) -> int`, `ficha_completa(**extra) -> dict`.

- [ ] **Step 1: Crear rama de trabajo y venv**

La rama `feat/migracion-web` ya existe (tiene el spec). Desde la raíz del repo, en PowerShell:

```powershell
git checkout feat/migracion-web
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- [ ] **Step 2: Dependencias y configuración de pytest**

`requirements.txt` (se mantiene `customtkinter` hasta la Task 11, porque `app.py` sigue existiendo):

```
customtkinter>=5.2.2
fastapi>=0.115
uvicorn[standard]>=0.30
jinja2>=3.1
python-multipart>=0.0.9
itsdangerous>=2.2
```

`requirements-dev.txt`:

```
-r requirements.txt
pytest>=8
httpx>=0.27
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

`.gitignore`:

```
sivigila.db
*.db-journal
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
```

Run: `pip install -r requirements-dev.txt`
Expected: termina sin errores.

- [ ] **Step 3: Sacar la base y el .pyc del índice de git**

```powershell
git rm --cached sivigila.db "__pycache__/database.cpython-314.pyc"
```

Expected: `rm 'sivigila.db'` y `rm '__pycache__/database.cpython-314.pyc'`. Los archivos siguen en disco; ya no se versionan. (Siguen en el historial de git; eso no se reescribe en este plan.)

- [ ] **Step 4: Fixtures y helpers de test**

`tests/__init__.py`: archivo vacío.

`tests/conftest.py`:

```python
import pytest


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Base SQLite temporal, inicializada, para cada test."""
    monkeypatch.setenv("SIVIGILA_DB_PATH", str(tmp_path / "test.db"))
    from sivigila import db as modulo_db

    modulo_db.init_db()
    return modulo_db
```

`tests/utils.py`:

```python
from datetime import date, timedelta

CLAVE = "clave-segura-1"


def crear_usuario(db, username, rol="digitador", permisos=None):
    db.create_user(username, CLAVE, f"Usuario {username}", rol=rol, permisos=permisos)
    return db.get_user_by_username(username)


def crear_upgd(db, razon_social="Hospital de Prueba"):
    return db.upsert_upgd(
        {"cod_prestador": "110010000001", "razon_social": razon_social, "activa_sivigila": 1}
    )


def crear_ficha(db, upgd_id, usuario_id, **extra):
    datos = {
        "upgd_id": upgd_id,
        "codigo_evento": "210",
        "numero_id": "1000",
        "primer_nombre": "Ana",
        "primer_apellido": "Pérez",
        "estado_ficha": "En proceso",
        "fecha_notificacion": date.today().isoformat(),
    }
    datos.update(extra)
    return db.create_notificacion(datos, usuario_id)


def ficha_completa(**extra):
    """Formulario de ficha de Dengue (210) con todo lo que exige 'Terminar'."""
    hoy = date.today()
    datos = {
        "codigo_evento": "210",
        "tipo_id": "CC",
        "numero_id": "1032456789",
        "primer_nombre": "Ana",
        "primer_apellido": "Pérez",
        "sexo": "F",
        "fecha_nacimiento": (hoy - timedelta(days=365 * 30 + 10)).isoformat(),
        "fecha_inicio_sintomas": (hoy - timedelta(days=5)).isoformat(),
        "fecha_consulta": (hoy - timedelta(days=3)).isoformat(),
        "clasificacion_caso": "Probable",
        "condicion": "Vivo",
        "hospitalizado": "No",
        "comp__fiebre": "Sí",
        "comp__signos_alarma": "No",
        "comp__dolor_abdominal": "No",
        "comp__sangrado": "No",
        "comp__clasificacion_dengue": "Dengue sin signos de alarma",
        "comp__resultado_igm": "Pendiente",
    }
    datos.update(extra)
    return datos
```

- [ ] **Step 5: Escribir los tests de la capa de datos**

`tests/test_db.py`:

```python
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
```

- [ ] **Step 6: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_db.py -v`
Expected: FAIL / ERROR con `ModuleNotFoundError: No module named 'sivigila'` (o `No module named 'sivigila.db'`).

- [ ] **Step 7: Crear el paquete y `sivigila/db.py`**

`sivigila/__init__.py` y `sivigila/routes/__init__.py`: archivos vacíos.

`sivigila/db.py` — se parte de `database.py` actual. Contenido completo:

```python
"""
Capa de acceso a datos (SQLite) para SIVIGILA Moderno (versión web).
Crea el esquema si no existe, aplica migraciones pequeñas, siembra usuarios/eventos
por defecto y expone funciones CRUD. Es la única capa que habla con SQLite.
"""

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent


def _db_path() -> str:
    return os.environ.get("SIVIGILA_DB_PATH") or str(RAIZ_REPO / "sivigila.db")


# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------

@contextmanager
def get_conn():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Esquema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    username              TEXT UNIQUE NOT NULL,
    password_hash         TEXT NOT NULL,
    salt                  TEXT NOT NULL,
    nombre_completo       TEXT NOT NULL,
    rol                   TEXT NOT NULL DEFAULT 'digitador',
    -- rol ∈ super_admin | admin | digitador | consulta
    permisos              TEXT NOT NULL DEFAULT '{}',   -- JSON de permisos granulares
    activo                INTEGER NOT NULL DEFAULT 1,
    debe_cambiar_password INTEGER NOT NULL DEFAULT 0,
    creado_en             TEXT NOT NULL,
    creado_por            INTEGER
);

CREATE TABLE IF NOT EXISTS upgd (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    cod_prestador           TEXT NOT NULL,
    subred                  TEXT,
    fecha_caracteriza       TEXT,
    fecha_inicio_uso        TEXT,
    razon_social            TEXT NOT NULL,
    nit                     TEXT,
    direccion               TEXT,
    representante_legal     TEXT,
    correo_electronico      TEXT,
    responsable_notif       TEXT,
    telefono                TEXT,
    fecha_constitucion      TEXT,
    naturaleza_juridica     TEXT,
    nivel_complejidad       TEXT,
    tipo_unidad             TEXT,
    estado                  TEXT DEFAULT 'Activa',
    localidad_zona          TEXT,
    notif_iad               INTEGER DEFAULT 0,
    notif_iso               INTEGER DEFAULT 0,
    notif_cab               INTEGER DEFAULT 0,
    unidad_analisis         INTEGER DEFAULT 0,
    cove                    INTEGER DEFAULT 0,
    talento_humano          INTEGER DEFAULT 0,
    fax_modem               INTEGER DEFAULT 0,
    correo_recurso          INTEGER DEFAULT 0,
    internet                INTEGER DEFAULT 0,
    telefax                 INTEGER DEFAULT 0,
    radio_telefono          INTEGER DEFAULT 0,
    computador              INTEGER DEFAULT 0,
    activa_sivigila         INTEGER DEFAULT 1,
    creado_en               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eventos (
    codigo      TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    campos_json TEXT NOT NULL   -- lista de campos dinámicos para "datos complementarios"
);

CREATE TABLE IF NOT EXISTS notificaciones (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    upgd_id                 INTEGER NOT NULL REFERENCES upgd(id),
    codigo_ficha            TEXT,
    ajuste                  INTEGER DEFAULT 0,
    fecha_grabacion         TEXT,
    codigo_evento           TEXT NOT NULL REFERENCES eventos(codigo),
    fecha_notificacion      TEXT,
    anio                    INTEGER,
    semana                  INTEGER,
    tipo_id                 TEXT,
    numero_id               TEXT,
    primer_nombre           TEXT,
    segundo_nombre          TEXT,
    primer_apellido         TEXT,
    segundo_apellido        TEXT,
    telefono                TEXT,
    fecha_nacimiento        TEXT,
    edad                    INTEGER,
    unidad_edad             TEXT,
    sexo                    TEXT,
    nacionalidad            TEXT,
    pais_procedencia        TEXT,
    departamento            TEXT,
    municipio               TEXT,
    area                    TEXT,
    localidad               TEXT,
    centro_poblado          TEXT,
    vereda                  TEXT,
    barrio                  TEXT,
    ocupacion               TEXT,
    tipo_regimen            TEXT,
    administradora          TEXT,
    pertenencia_etnica      TEXT,
    grupo_etnico            TEXT,
    fuente                  TEXT,
    direccion_residencia    TEXT,
    fecha_consulta          TEXT,
    fecha_inicio_sintomas   TEXT,
    clasificacion_caso      TEXT,
    hospitalizado           TEXT,
    fecha_hospitalizacion   TEXT,
    condicion               TEXT,
    fecha_defuncion         TEXT,
    certificado_defuncion   TEXT,
    causa_basica            TEXT,
    nombre_diligencia       TEXT,
    telefono_diligencia     TEXT,
    datos_complementarios   TEXT,  -- JSON dinámico según evento
    estado_ficha            TEXT DEFAULT 'En proceso',  -- En proceso | Terminada
    creado_por              INTEGER REFERENCES usuarios(id),
    creado_en               TEXT NOT NULL,
    actualizado_en          TEXT
);

CREATE TABLE IF NOT EXISTS laboratorios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    notificacion_id INTEGER NOT NULL REFERENCES notificaciones(id) ON DELETE CASCADE,
    fecha_toma      TEXT,
    fecha_recepcion TEXT,
    muestra         TEXT,
    prueba          TEXT,
    agente          TEXT,
    resultado       TEXT,
    fecha_resultado TEXT,
    valor           TEXT,
    creado_en       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auditoria (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER,
    accion      TEXT,
    detalle     TEXT,
    fecha       TEXT NOT NULL
);
"""


def _migrar(conn):
    """Cambios de esquema sobre bases creadas por versiones anteriores."""
    columnas = {r["name"] for r in conn.execute("PRAGMA table_info(usuarios)")}
    if "debe_cambiar_password" not in columnas:
        conn.execute(
            "ALTER TABLE usuarios ADD COLUMN debe_cambiar_password INTEGER NOT NULL DEFAULT 0"
        )


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrar(conn)
    _seed_eventos()
    _seed_admin()


def _validar_columnas(conn, tabla: str, data: dict):
    """Lista blanca: solo se aceptan claves que sean columnas reales de la tabla (sin 'id')."""
    columnas = {r["name"] for r in conn.execute(f"PRAGMA table_info({tabla})")} - {"id"}
    desconocidas = set(data) - columnas
    if desconocidas:
        raise ValueError(
            f"Columnas no válidas para {tabla}: {', '.join(sorted(desconocidas))}"
        )


# ---------------------------------------------------------------------------
# Seguridad de contraseñas (PBKDF2, sin dependencias externas)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: str = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    digest, _ = _hash_password(password, salt)
    return secrets.compare_digest(digest, password_hash)


def _seed_admin():
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) c FROM usuarios").fetchone()
    if row["c"] == 0:
        create_user("admin", "Admin123!", "Administrador SIVIGILA", rol="super_admin",
                    debe_cambiar_password=True)
        create_user("SIVIGILA", "sivigila2026", "Usuario SIVIGILA", rol="digitador",
                    debe_cambiar_password=True)


# ---------------------------------------------------------------------------
# Roles y permisos
# ---------------------------------------------------------------------------

# Jerarquía: un usuario solo puede crear/editar/desactivar usuarios de rango
# inferior al suyo (excepto super_admin, que administra a todos).
ROLES_JERARQUIA = {"super_admin": 3, "admin": 2, "digitador": 1, "consulta": 0}
ROLES_DISPONIBLES = list(ROLES_JERARQUIA.keys())

PERMISOS_DEFAULT = {
    "super_admin": {
        "gestionar_usuarios": True, "gestionar_caracterizacion": True,
        "notificar_individual": True, "editar_notificaciones": True,
        "gestionar_laboratorios": True, "ver_reportes": True,
    },
    "admin": {
        "gestionar_usuarios": True, "gestionar_caracterizacion": True,
        "notificar_individual": True, "editar_notificaciones": True,
        "gestionar_laboratorios": True, "ver_reportes": True,
    },
    "digitador": {
        "gestionar_usuarios": False, "gestionar_caracterizacion": True,
        "notificar_individual": True, "editar_notificaciones": True,
        "gestionar_laboratorios": True, "ver_reportes": True,
    },
    "consulta": {
        "gestionar_usuarios": False, "gestionar_caracterizacion": False,
        "notificar_individual": False, "editar_notificaciones": False,
        "gestionar_laboratorios": False, "ver_reportes": True,
    },
}

PERMISOS_LABELS = {
    "gestionar_usuarios": "Gestionar usuarios (crear, editar, permisos)",
    "gestionar_caracterizacion": "Gestionar caracterización de UPGD",
    "notificar_individual": "Crear notificaciones individuales",
    "editar_notificaciones": "Editar / terminar / eliminar fichas",
    "gestionar_laboratorios": "Gestionar resultados de laboratorio",
    "ver_reportes": "Ver panel de indicadores y reportes",
}


def permisos_por_defecto(rol):
    return dict(PERMISOS_DEFAULT.get(rol, PERMISOS_DEFAULT["consulta"]))


def get_permisos(user_row) -> dict:
    """Devuelve los permisos efectivos de un usuario (fila sqlite3.Row)."""
    try:
        return json.loads(user_row["permisos"]) if user_row["permisos"] else permisos_por_defecto(user_row["rol"])
    except (json.JSONDecodeError, TypeError):
        return permisos_por_defecto(user_row["rol"])


def tiene_permiso(user_row, clave) -> bool:
    return bool(get_permisos(user_row).get(clave, False))


def puede_gestionar(actor_row, objetivo_row) -> bool:
    """¿Puede 'actor' crear/editar/desactivar al usuario 'objetivo'?"""
    if not tiene_permiso(actor_row, "gestionar_usuarios"):
        return False
    rango_actor = ROLES_JERARQUIA.get(actor_row["rol"], 0)
    rango_objetivo = ROLES_JERARQUIA.get(objetivo_row["rol"], 0) if objetivo_row else 0
    if actor_row["rol"] == "super_admin":
        return True
    return rango_actor > rango_objetivo


def roles_asignables(rol_actor) -> list:
    """Roles que un actor puede asignar: super_admin todos; el resto, solo los de rango inferior."""
    if rol_actor == "super_admin":
        return list(ROLES_DISPONIBLES)
    rango_actor = ROLES_JERARQUIA.get(rol_actor, 0)
    return [r for r, rango in ROLES_JERARQUIA.items() if rango < rango_actor]


def create_user(username, password, nombre_completo, rol="digitador",
                permisos=None, creado_por=None, debe_cambiar_password=False):
    pw_hash, salt = _hash_password(password)
    permisos = permisos if permisos is not None else permisos_por_defecto(rol)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, rol, "
            "permisos, debe_cambiar_password, creado_en, creado_por) VALUES (?,?,?,?,?,?,?,?,?)",
            (username, pw_hash, salt, nombre_completo, rol,
             json.dumps(permisos, ensure_ascii=False), 1 if debe_cambiar_password else 0,
             datetime.now().isoformat(), creado_por),
        )


def get_user_by_username(username):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND activo = 1", (username,)
        ).fetchone()


def get_user_by_id(user_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()


def username_exists(username):
    with get_conn() as conn:
        return conn.execute("SELECT 1 FROM usuarios WHERE username = ?", (username,)).fetchone() is not None


def list_users():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, username, nombre_completo, rol, permisos, activo, creado_en "
            "FROM usuarios ORDER BY rol, nombre_completo"
        ).fetchall()


def update_user(user_id, nombre_completo=None, rol=None, permisos=None):
    campos, valores = [], []
    if nombre_completo is not None:
        campos.append("nombre_completo = ?"); valores.append(nombre_completo)
    if rol is not None:
        campos.append("rol = ?"); valores.append(rol)
    if permisos is not None:
        campos.append("permisos = ?"); valores.append(json.dumps(permisos, ensure_ascii=False))
    if not campos:
        return
    valores.append(user_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores)


def set_user_active(user_id, activo: bool):
    with get_conn() as conn:
        conn.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (1 if activo else 0, user_id))


def reset_password(user_id, new_password, debe_cambiar=True):
    pw_hash, salt = _hash_password(new_password)
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET password_hash = ?, salt = ?, debe_cambiar_password = ? WHERE id = ?",
            (pw_hash, salt, 1 if debe_cambiar else 0, user_id),
        )


def log_action(usuario_id, accion, detalle=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auditoria (usuario_id, accion, detalle, fecha) VALUES (?,?,?,?)",
            (usuario_id, accion, detalle, datetime.now().isoformat()),
        )


# ---------------------------------------------------------------------------
# Eventos y campos dinámicos de "datos complementarios"
# ---------------------------------------------------------------------------

EVENTOS_DEFAULT = [
    {
        "codigo": "205",
        "nombre": "Enfermedad de Chagas",
        "campos": [
            {"key": "sintomas", "label": "Síntomas", "tipo": "texto"},
            {"key": "fiebre", "label": "Fiebre", "tipo": "si_no"},
            {"key": "cardiopatia", "label": "Cardiopatía chagásica", "tipo": "si_no"},
            {"key": "megasindrome", "label": "Megasíndrome (esofágico/colónico)", "tipo": "si_no"},
            {"key": "via_transmision", "label": "Vía de transmisión probable",
             "tipo": "lista", "opciones": ["Vectorial", "Transfusional", "Congénita", "Oral", "Desconocida"]},
            {"key": "resultado_serologia", "label": "Resultado serología", "tipo": "lista",
             "opciones": ["Reactivo", "No reactivo", "Indeterminado", "Pendiente"]},
        ],
    },
    {
        "codigo": "100",
        "nombre": "Accidente Ofídico",
        "campos": [
            {"key": "actividad", "label": "Actividad al momento del accidente", "tipo": "texto"},
            {"key": "localizacion", "label": "Localización de la mordedura", "tipo": "texto"},
            {"key": "edema", "label": "Edema", "tipo": "si_no"},
            {"key": "dolor", "label": "Dolor", "tipo": "si_no"},
            {"key": "necrosis", "label": "Necrosis", "tipo": "si_no"},
            {"key": "shock", "label": "Shock hipovolémico", "tipo": "si_no"},
            {"key": "suero_antiofidico", "label": "Suero antiofídico administrado", "tipo": "si_no"},
            {"key": "gravedad", "label": "Gravedad del accidente",
             "tipo": "lista", "opciones": ["Leve", "Moderado", "Severo"]},
        ],
    },
    {
        "codigo": "210",
        "nombre": "Dengue",
        "campos": [
            {"key": "fiebre", "label": "Fiebre ≥ 38°C", "tipo": "si_no"},
            {"key": "signos_alarma", "label": "Signos de alarma", "tipo": "si_no"},
            {"key": "dolor_abdominal", "label": "Dolor abdominal intenso", "tipo": "si_no"},
            {"key": "sangrado", "label": "Sangrado espontáneo", "tipo": "si_no"},
            {"key": "clasificacion_dengue", "label": "Clasificación",
             "tipo": "lista", "opciones": ["Dengue sin signos de alarma", "Dengue con signos de alarma", "Dengue grave"]},
            {"key": "resultado_igm", "label": "Resultado IgM", "tipo": "lista",
             "opciones": ["Positivo", "Negativo", "Pendiente"]},
        ],
    },
]


def _seed_eventos():
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) c FROM eventos").fetchone()
        if row["c"] == 0:
            for ev in EVENTOS_DEFAULT:
                conn.execute(
                    "INSERT INTO eventos (codigo, nombre, campos_json) VALUES (?,?,?)",
                    (ev["codigo"], ev["nombre"], json.dumps(ev["campos"], ensure_ascii=False)),
                )


def list_eventos():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM eventos ORDER BY nombre").fetchall()


def get_evento(codigo):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM eventos WHERE codigo = ?", (codigo,)).fetchone()


# ---------------------------------------------------------------------------
# UPGD (Caracterización)
# ---------------------------------------------------------------------------

def upsert_upgd(data: dict, upgd_id=None):
    data = dict(data)
    with get_conn() as conn:
        _validar_columnas(conn, "upgd", data)
        if upgd_id:
            campos = ", ".join(f"{k} = ?" for k in data)
            conn.execute(f"UPDATE upgd SET {campos} WHERE id = ?", (*data.values(), upgd_id))
            return upgd_id
        data["creado_en"] = datetime.now().isoformat()
        campos = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cur = conn.execute(f"INSERT INTO upgd ({campos}) VALUES ({placeholders})", tuple(data.values()))
        return cur.lastrowid


def list_upgd():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM upgd ORDER BY razon_social").fetchall()


def get_upgd(upgd_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM upgd WHERE id = ?", (upgd_id,)).fetchone()


# ---------------------------------------------------------------------------
# Notificaciones individuales
# ---------------------------------------------------------------------------

def create_notificacion(data: dict, usuario_id: int):
    data = dict(data)
    data["creado_por"] = usuario_id
    data["creado_en"] = datetime.now().isoformat()
    with get_conn() as conn:
        _validar_columnas(conn, "notificaciones", data)
        campos = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cur = conn.execute(
            f"INSERT INTO notificaciones ({campos}) VALUES ({placeholders})", tuple(data.values())
        )
        return cur.lastrowid


def update_notificacion(notificacion_id: int, data: dict):
    data = dict(data)
    data["actualizado_en"] = datetime.now().isoformat()
    with get_conn() as conn:
        _validar_columnas(conn, "notificaciones", data)
        campos = ", ".join(f"{k} = ?" for k in data)
        conn.execute(f"UPDATE notificaciones SET {campos} WHERE id = ?", (*data.values(), notificacion_id))


def get_notificacion(notificacion_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM notificaciones WHERE id = ?", (notificacion_id,)).fetchone()


def _filtro_notificaciones(filtro_texto, codigo_evento):
    sql, params = " WHERE 1=1", []
    if filtro_texto:
        sql += """ AND (n.primer_nombre LIKE ? OR n.primer_apellido LIKE ?
                        OR n.numero_id LIKE ? OR n.codigo_ficha LIKE ?)"""
        like = f"%{filtro_texto}%"
        params += [like, like, like, like]
    if codigo_evento and codigo_evento != "Todos":
        sql += " AND n.codigo_evento = ?"
        params.append(codigo_evento)
    return sql, params


def list_notificaciones(filtro_texto="", codigo_evento=None, limite=None, offset=0):
    where, params = _filtro_notificaciones(filtro_texto, codigo_evento)
    query = """
        SELECT n.*, e.nombre AS evento_nombre, u.razon_social AS upgd_nombre
        FROM notificaciones n
        JOIN eventos e ON e.codigo = n.codigo_evento
        JOIN upgd u ON u.id = n.upgd_id
    """ + where + " ORDER BY n.creado_en DESC, n.id DESC"
    if limite is not None:
        query += " LIMIT ? OFFSET ?"
        params += [limite, offset]
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def count_notificaciones(filtro_texto="", codigo_evento=None) -> int:
    where, params = _filtro_notificaciones(filtro_texto, codigo_evento)
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) c FROM notificaciones n" + where, params).fetchone()["c"]


def count_notificaciones_por_evento():
    with get_conn() as conn:
        return conn.execute(
            """SELECT e.nombre, COUNT(n.id) AS total
               FROM eventos e LEFT JOIN notificaciones n ON n.codigo_evento = e.codigo
               GROUP BY e.codigo ORDER BY total DESC"""
        ).fetchall()


def delete_notificacion(notificacion_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM notificaciones WHERE id = ?", (notificacion_id,))


# ---------------------------------------------------------------------------
# Laboratorios
# ---------------------------------------------------------------------------

def add_laboratorio(notificacion_id, data: dict):
    data = dict(data)
    data["notificacion_id"] = notificacion_id
    data["creado_en"] = datetime.now().isoformat()
    with get_conn() as conn:
        _validar_columnas(conn, "laboratorios", data)
        campos = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cur = conn.execute(f"INSERT INTO laboratorios ({campos}) VALUES ({placeholders})", tuple(data.values()))
        return cur.lastrowid


def get_laboratorio(lab_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM laboratorios WHERE id = ?", (lab_id,)).fetchone()


def list_laboratorios(notificacion_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM laboratorios WHERE notificacion_id = ? ORDER BY fecha_toma", (notificacion_id,)
        ).fetchall()


def delete_laboratorio(lab_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM laboratorios WHERE id = ?", (lab_id,))
```

- [ ] **Step 8: Correr los tests y verificar que pasan**

Run: `python -m pytest tests/test_db.py -v`
Expected: 12 passed.

- [ ] **Step 9: Commit**

```bash
git add .gitignore requirements.txt requirements-dev.txt pyproject.toml sivigila tests
git commit -m "feat: paquete sivigila con capa de datos y lista blanca de columnas"
```

---

### Task 2: App FastAPI, sesión, CSRF y login/logout

**Files:**
- Create: `sivigila/catalogos.py`, `sivigila/auth.py`, `sivigila/web.py`, `sivigila/main.py`, `sivigila/routes/login.py`, `sivigila/templates/base.html`, `sivigila/templates/_macros.html`, `sivigila/templates/login.html`, `sivigila/templates/error.html`, `sivigila/static/app.css`, `sivigila/static/app.js`, `sivigila/static/htmx.min.js`, `tests/test_auth.py`
- Modify: `tests/conftest.py`, `tests/utils.py`

**Interfaces:**
- Consumes: `sivigila.db` (Task 1).
- Produces:
  - `sivigila.catalogos`: `ROL_LABELS`, `SI_NO`, `PREFIJO_COMP = "comp__"`, `CAMPOS_BASICOS`, `OBLIGATORIOS_GUARDAR`, `OBLIGATORIOS_TERMINAR`, `CAMPOS_UPGD`, `OBLIGATORIOS_UPGD`, `RECURSOS_UPGD`, `CAMPOS_LAB`. Cada campo es `{"key", "label", "tipo"}` con `tipo ∈ {"texto","fecha","lista","si_no"}` y `"opciones"` si es lista.
  - `sivigila.auth`: `MIN_PASSWORD = 6`, excepciones `NoAutenticado`, `DebeCambiarPassword`, `SinPermiso(mensaje)`, `obtener_csrf(request) -> str`, `verificar_csrf(request)` (async, dependencia global), `iniciar_sesion(request, usuario)`, `cerrar_sesion(request)`, `usuario_actual(request) -> Row` (dependencia), `require_permiso(*claves)` (fábrica de dependencias; pasa si tiene **alguno**), `esta_bloqueado(username) -> bool`, `registrar_fallo(username)`, `limpiar_intentos(username)`, `reiniciar_intentos()`, `_ahora()`.
  - `sivigila.web`: `templates`, `render(request, plantilla, contexto=None, status_code=200)`, `redirigir(url)`, `es_htmx(request) -> bool`, `primera_pantalla(usuario) -> str`, `upgd_activa(request) -> Row|None`.
  - `sivigila.main`: `create_app() -> FastAPI`, `app`.
  - Plantilla `_macros.html` con `campo(c, valor, error, prefijo="", solo_lectura=false, obligatorio=false)`.
  - Toda página incluye `<meta name="csrf-token" content="...">`.
  - Tests: fixture `client`; helpers `token_csrf(client)`, `post(client, url, data=None, **kw)`, `iniciar_sesion(client, username, clave=CLAVE)`.

- [ ] **Step 1: Descargar HTMX**

Run: `curl -L -o sivigila/static/htmx.min.js https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js`
Expected: archivo de ~50 KB que empieza con `var htmx=function()`. Verifica con `Get-Content sivigila/static/htmx.min.js -TotalCount 1 | Select-Object -First 1` (o abriéndolo).

- [ ] **Step 2: Helpers y fixture de cliente para tests**

Agregar al final de `tests/conftest.py`:

```python
from fastapi.testclient import TestClient


@pytest.fixture
def client(db):
    from sivigila import auth
    from sivigila.main import create_app

    auth.reiniciar_intentos()
    with TestClient(create_app()) as c:
        yield c
```

Agregar al final de `tests/utils.py` (y `import re` arriba del archivo):

```python
_META_CSRF = re.compile(r'name="csrf-token" content="([^"]+)"')


def token_csrf(client):
    """Lee el token CSRF de la sesión actual desde cualquier página (todas lo incluyen)."""
    respuesta = client.get("/login")
    return _META_CSRF.search(respuesta.text).group(1)


def post(client, url, data=None, **kwargs):
    datos = dict(data or {})
    datos["csrf_token"] = token_csrf(client)
    return client.post(url, data=datos, follow_redirects=False, **kwargs)


def iniciar_sesion(client, username, clave=CLAVE):
    return post(client, "/login", {"username": username, "password": clave})
```

- [ ] **Step 3: Escribir los tests de login y CSRF**

`tests/test_auth.py`:

```python
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
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_auth.py -v`
Expected: ERROR en el fixture `client` con `ModuleNotFoundError: No module named 'sivigila.main'`.

- [ ] **Step 5: Catálogo de campos**

`sivigila/catalogos.py`:

```python
"""
Definición de los campos de cada formulario. Cada campo es un dict
{"key", "label", "tipo"} con tipo ∈ texto | fecha | lista | si_no, y "opciones" si es lista.
Es el mismo formato de eventos.campos_json, así un solo macro y un solo validador sirven para todo.
"""

SI_NO = ["Sí", "No"]
PREFIJO_COMP = "comp__"  # prefijo de los campos complementarios en el formulario

ROL_LABELS = {
    "super_admin": "Super administrador",
    "admin": "Administrador",
    "digitador": "Digitador",
    "consulta": "Solo consulta",
}


def _texto(key, label):
    return {"key": key, "label": label, "tipo": "texto"}


def _fecha(key, label):
    return {"key": key, "label": label, "tipo": "fecha"}


def _lista(key, label, opciones):
    return {"key": key, "label": label, "tipo": "lista", "opciones": opciones}


CAMPOS_BASICOS = [
    _lista("tipo_id", "Tipo de identificación", ["CC", "TI", "RC", "CE", "PA", "MS"]),
    _texto("numero_id", "Número de identificación"),
    _texto("primer_nombre", "Primer nombre"),
    _texto("segundo_nombre", "Segundo nombre"),
    _texto("primer_apellido", "Primer apellido"),
    _texto("segundo_apellido", "Segundo apellido"),
    _texto("telefono", "Teléfono"),
    _fecha("fecha_nacimiento", "Fecha de nacimiento"),
    _lista("sexo", "Sexo", ["F", "M", "I"]),
    _texto("nacionalidad", "Nacionalidad"),
    _texto("pais_procedencia", "País de procedencia"),
    _texto("departamento", "Departamento de ocurrencia"),
    _texto("municipio", "Municipio de ocurrencia"),
    _lista("area", "Área", ["Cabecera municipal", "Centro poblado", "Rural disperso"]),
    _texto("barrio", "Barrio"),
    _texto("vereda", "Vereda"),
    _texto("ocupacion", "Ocupación"),
    _lista("tipo_regimen", "Tipo de régimen", ["Contributivo", "Subsidiado", "Especial", "No asegurado"]),
    _texto("administradora", "Administradora (EPS)"),
    _lista("fuente", "Fuente de notificación", ["UPGD", "COVE", "Laboratorio", "Comunitaria"]),
    _texto("direccion_residencia", "Dirección de residencia"),
    _fecha("fecha_consulta", "Fecha de consulta"),
    _fecha("fecha_inicio_sintomas", "Fecha de inicio de síntomas"),
    _lista("clasificacion_caso", "Clasificación del caso",
           ["Sospechoso", "Probable", "Confirmado por laboratorio",
            "Confirmado por clínica", "Confirmado por nexo epidemiológico"]),
    _lista("hospitalizado", "¿Hospitalizado?", SI_NO),
    _fecha("fecha_hospitalizacion", "Fecha de hospitalización"),
    _lista("condicion", "Condición final", ["Vivo", "Fallecido"]),
    _fecha("fecha_defuncion", "Fecha de defunción"),
    _texto("nombre_diligencia", "Nombre de quien diligencia la ficha"),
    _texto("telefono_diligencia", "Teléfono de quien diligencia"),
]

OBLIGATORIOS_GUARDAR = {"numero_id", "primer_nombre"}
OBLIGATORIOS_TERMINAR = {
    "tipo_id", "numero_id", "primer_nombre", "primer_apellido", "sexo",
    "fecha_nacimiento", "fecha_consulta", "fecha_inicio_sintomas",
    "clasificacion_caso", "condicion",
}

CAMPOS_UPGD = [
    _texto("cod_prestador", "Código prestador"),
    _texto("subred", "Subred / seccional"),
    _texto("nit", "NIT"),
    _texto("razon_social", "Razón social"),
    _texto("direccion", "Dirección"),
    _texto("telefono", "Teléfono"),
    _texto("representante_legal", "Representante legal"),
    _texto("correo_electronico", "Correo electrónico"),
    _texto("responsable_notif", "Responsable de la notificación"),
    _lista("naturaleza_juridica", "Naturaleza jurídica",
           ["Privada sin ánimo de lucro", "Privada con ánimo de lucro", "Mixta", "Pública"]),
    _lista("nivel_complejidad", "Nivel de complejidad", ["I Nivel", "II Nivel", "III Nivel"]),
    _lista("tipo_unidad", "Tipo de unidad", ["UPGD", "UI", "Laboratorio"]),
    _texto("localidad_zona", "Localidad o zona (si aplica)"),
    _lista("estado", "Estado de la unidad", ["Activa", "Inactiva"]),
]

OBLIGATORIOS_UPGD = {"cod_prestador", "razon_social"}

RECURSOS_UPGD = {
    "unidad_analisis": "Unidad de análisis",
    "cove": "COVE",
    "talento_humano": "Talento humano disponible",
    "computador": "Computador",
    "fax_modem": "Fax/Módem",
    "correo_recurso": "Correo electrónico",
    "internet": "Internet",
    "telefax": "Telefax",
    "radio_telefono": "Radioteléfono",
}

CAMPOS_LAB = [
    _fecha("fecha_toma", "Fecha de toma"),
    _fecha("fecha_recepcion", "Fecha de recepción"),
    _texto("muestra", "Muestra"),
    _texto("prueba", "Prueba"),
    _texto("agente", "Agente"),
    _texto("resultado", "Resultado"),
    _fecha("fecha_resultado", "Fecha de resultado"),
    _texto("valor", "Valor (si aplica)"),
]
```

- [ ] **Step 6: Autenticación, sesión y CSRF**

`sivigila/auth.py`:

```python
"""Sesión, CSRF, usuario actual, permisos por ruta y bloqueo de login."""

import secrets
import time

from fastapi import Depends, HTTPException, Request

from . import db

MIN_PASSWORD = 6
MAX_INTENTOS = 5
VENTANA_SEG = 600   # se cuentan los fallos de los últimos 10 minutos
BLOQUEO_SEG = 600   # y se bloquea el username 10 minutos

_fallos: dict[str, list[float]] = {}
_bloqueados: dict[str, float] = {}

METODOS_CON_CSRF = {"POST", "PUT", "PATCH", "DELETE"}
RUTAS_SIN_CAMBIO_OBLIGATORIO = {"/cambiar-password", "/logout"}


class NoAutenticado(Exception):
    """No hay sesión válida: se redirige a /login."""


class DebeCambiarPassword(Exception):
    """El usuario debe cambiar su contraseña antes de seguir."""


class SinPermiso(Exception):
    def __init__(self, mensaje="No tienes permiso para acceder a esta sección."):
        super().__init__(mensaje)
        self.mensaje = mensaje


# --- Bloqueo por intentos fallidos (en memoria del proceso) -----------------

def _ahora() -> float:
    return time.monotonic()


def _clave(username: str) -> str:
    return username.strip().lower()


def reiniciar_intentos():
    _fallos.clear()
    _bloqueados.clear()


def esta_bloqueado(username: str) -> bool:
    hasta = _bloqueados.get(_clave(username))
    if hasta is None:
        return False
    if _ahora() < hasta:
        return True
    _bloqueados.pop(_clave(username), None)
    return False


def registrar_fallo(username: str):
    clave, ahora = _clave(username), _ahora()
    recientes = [t for t in _fallos.get(clave, []) if ahora - t < VENTANA_SEG]
    recientes.append(ahora)
    if len(recientes) >= MAX_INTENTOS:
        _bloqueados[clave] = ahora + BLOQUEO_SEG
        recientes = []
    _fallos[clave] = recientes


def limpiar_intentos(username: str):
    _fallos.pop(_clave(username), None)


# --- CSRF y sesión -----------------------------------------------------------

def obtener_csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def verificar_csrf(request: Request):
    """Dependencia global: todo POST/PUT/PATCH/DELETE debe traer el token de la sesión."""
    if request.method not in METODOS_CON_CSRF:
        return
    enviado = request.headers.get("X-CSRF-Token")
    if not enviado:
        formulario = await request.form()
        enviado = formulario.get("csrf_token")
    esperado = request.session.get("csrf_token")
    if not esperado or not enviado or not secrets.compare_digest(str(enviado), esperado):
        raise HTTPException(
            status_code=403,
            detail="La sesión expiró o el formulario no es válido. Recarga la página e intenta de nuevo.",
        )


def iniciar_sesion(request: Request, usuario):
    request.session.clear()  # evita reutilizar una sesión previa (fijación de sesión)
    request.session["user_id"] = usuario["id"]
    request.session["csrf_token"] = secrets.token_urlsafe(32)


def cerrar_sesion(request: Request):
    request.session.clear()


# --- Usuario actual y permisos -----------------------------------------------

def usuario_actual(request: Request):
    """Relee el usuario en cada petición: si lo desactivan, pierde la sesión de inmediato."""
    user_id = request.session.get("user_id")
    usuario = db.get_user_by_id(user_id) if user_id else None
    if usuario is None or not usuario["activo"]:
        request.session.clear()
        raise NoAutenticado()
    request.state.usuario = usuario
    if usuario["debe_cambiar_password"] and request.url.path not in RUTAS_SIN_CAMBIO_OBLIGATORIO:
        raise DebeCambiarPassword()
    return usuario


def require_permiso(*claves: str):
    """Dependencia que exige al menos uno de los permisos indicados."""

    def dependencia(request: Request, usuario=Depends(usuario_actual)):
        if not any(db.tiene_permiso(usuario, c) for c in claves):
            db.log_action(
                usuario["id"], "ACCESO_DENEGADO",
                f"{request.method} {request.url.path} requiere {'|'.join(claves)}",
            )
            raise SinPermiso()
        return usuario

    return dependencia
```

- [ ] **Step 7: Helpers de renderizado**

`sivigila/web.py`:

```python
"""Helpers compartidos por las rutas: render con contexto común, redirects, UPGD activa."""

from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from . import auth, db
from .catalogos import ROL_LABELS

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Orden en que se elige la pantalla de inicio según los permisos del usuario.
PANTALLAS_INICIO = [
    ("ver_reportes", "/"),
    ("notificar_individual", "/fichas/nueva"),
    ("gestionar_caracterizacion", "/upgd"),
    ("gestionar_usuarios", "/usuarios"),
]


def render(request: Request, plantilla: str, contexto: dict | None = None, status_code: int = 200):
    usuario = getattr(request.state, "usuario", None)
    ctx = {
        "usuario": usuario,
        "permisos": db.get_permisos(usuario) if usuario else {},
        "csrf_token": auth.obtener_csrf(request),
        "rol_labels": ROL_LABELS,
    }
    ctx.update(contexto or {})
    return templates.TemplateResponse(request, plantilla, ctx, status_code=status_code)


def redirigir(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def es_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def primera_pantalla(usuario) -> str:
    for permiso, url in PANTALLAS_INICIO:
        if db.tiene_permiso(usuario, permiso):
            return url
    return "/sin-acceso"


def upgd_activa(request: Request):
    """UPGD de la sesión; si no hay (o ya no existe), toma la primera registrada."""
    upgd_id = request.session.get("upgd_id")
    upgd = db.get_upgd(upgd_id) if upgd_id else None
    if upgd is None:
        todas = db.list_upgd()
        upgd = todas[0] if todas else None
        if upgd is not None:
            request.session["upgd_id"] = upgd["id"]
        else:
            request.session.pop("upgd_id", None)
    return upgd
```

- [ ] **Step 8: Rutas de login, logout y sin acceso**

`sivigila/routes/login.py`:

```python
from fastapi import APIRouter, Depends, Request

from .. import auth, db
from ..web import primera_pantalla, redirigir, render

router = APIRouter()


@router.get("/login")
def login_form(request: Request):
    user_id = request.session.get("user_id")
    usuario = db.get_user_by_id(user_id) if user_id else None
    if usuario is not None and usuario["activo"]:
        return redirigir(primera_pantalla(usuario))
    return render(request, "login.html")


@router.post("/login")
async def login(request: Request):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))

    if auth.esta_bloqueado(username):
        db.log_action(None, "LOGIN_BLOQUEADO", username)
        return render(request, "login.html", {
            "error": "Demasiados intentos fallidos. Espera 10 minutos e intenta de nuevo.",
            "username": username,
        }, status_code=429)

    usuario = db.get_user_by_username(username) if username else None
    if usuario is None or not db.verify_password(password, usuario["password_hash"], usuario["salt"]):
        auth.registrar_fallo(username)
        db.log_action(None, "LOGIN_FALLIDO", username)
        return render(request, "login.html", {
            "error": "Usuario o contraseña incorrectos.",
            "username": username,
        }, status_code=401)

    auth.limpiar_intentos(username)
    auth.iniciar_sesion(request, usuario)
    db.log_action(usuario["id"], "LOGIN")
    if usuario["debe_cambiar_password"]:
        return redirigir("/cambiar-password")
    return redirigir(primera_pantalla(usuario))


@router.post("/logout")
def logout(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        db.log_action(user_id, "LOGOUT")
    auth.cerrar_sesion(request)
    return redirigir("/login")


@router.get("/sin-acceso")
def sin_acceso(request: Request, usuario=Depends(auth.usuario_actual)):
    return render(request, "error.html", {
        "titulo": "Sin secciones habilitadas",
        "mensaje": "Tu usuario no tiene ninguna sección habilitada. "
                   "Pide a un administrador que te asigne permisos.",
    })
```

- [ ] **Step 9: Aplicación y manejadores de error**

`sivigila/main.py`:

```python
"""Punto de entrada web: uvicorn sivigila.main:app --reload"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import auth, db
from .routes import login
from .web import es_htmx, redirigir, render

logger = logging.getLogger("sivigila")

CLAVE_DESARROLLO = "solo-para-desarrollo-local-cambiame"
TITULOS_ERROR = {403: "Acceso restringido", 404: "No encontrado", 405: "Acción no permitida"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


def create_app() -> FastAPI:
    secret = os.environ.get("SIVIGILA_SECRET_KEY")
    if not secret:
        logger.warning(
            "SIVIGILA_SECRET_KEY no está definida: se usa una clave de desarrollo. "
            "No uses esta configuración fuera de tu máquina."
        )
        secret = CLAVE_DESARROLLO

    app = FastAPI(
        title="SIVIGILA Moderno",
        lifespan=lifespan,
        dependencies=[Depends(auth.verificar_csrf)],
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret,
        session_cookie="sivigila_sesion",
        max_age=8 * 3600,
        same_site="lax",
        https_only=os.environ.get("SIVIGILA_COOKIE_SECURE") == "1",
    )
    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

    app.include_router(login.router)

    _registrar_errores(app)
    return app


def _registrar_errores(app: FastAPI):
    @app.exception_handler(auth.NoAutenticado)
    async def _no_autenticado(request: Request, exc: auth.NoAutenticado):
        if es_htmx(request):
            return Response(status_code=401, headers={"HX-Redirect": "/login"})
        return redirigir("/login")

    @app.exception_handler(auth.DebeCambiarPassword)
    async def _debe_cambiar(request: Request, exc: auth.DebeCambiarPassword):
        if es_htmx(request):
            return Response(status_code=401, headers={"HX-Redirect": "/cambiar-password"})
        return redirigir("/cambiar-password")

    @app.exception_handler(auth.SinPermiso)
    async def _sin_permiso(request: Request, exc: auth.SinPermiso):
        return render(request, "error.html",
                      {"titulo": "Acceso restringido", "mensaje": exc.mensaje}, status_code=403)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        titulo = TITULOS_ERROR.get(exc.status_code, f"Error {exc.status_code}")
        if exc.status_code == 403:
            mensaje = exc.detail
        elif exc.status_code == 404:
            mensaje = "La página o el registro que buscas no existe."
        else:
            mensaje = "No se pudo completar la acción."
        return render(request, "error.html", {"titulo": titulo, "mensaje": mensaje},
                      status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _error_no_controlado(request: Request, exc: Exception):
        # Solo método, ruta y tipo de excepción: nunca el mensaje, que podría traer datos del paciente.
        logger.error("Error no controlado en %s %s: %s",
                     request.method, request.url.path, type(exc).__name__)
        return render(request, "error.html", {
            "titulo": "Algo salió mal",
            "mensaje": "Ocurrió un error inesperado. Intenta de nuevo; si persiste, avisa al administrador.",
        }, status_code=500)


app = create_app()
```

- [ ] **Step 10: Plantillas base, macro, login y error**

`sivigila/templates/base.html`:

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="csrf-token" content="{{ csrf_token }}">
  <meta name="htmx-config" content='{"responseHandling":[{"code":"204","swap":false},{"code":"[23]..","swap":true},{"code":"422","swap":true},{"code":"[45]..","swap":false,"error":true}]}'>
  <title>{% block titulo %}SIVIGILA{% endblock %} · SIVIGILA Moderno</title>
  <link rel="stylesheet" href="/static/app.css">
  <script src="/static/htmx.min.js" defer></script>
  <script src="/static/app.js" defer></script>
</head>
<body hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
{% if usuario %}
<div class="layout">
  <nav class="sidebar">
    <div class="marca">SIVIGILA<small>Moderno</small></div>
    {% set items = [
      ("/", "Panel principal", "ver_reportes", "dashboard"),
      ("/upgd", "Caracterización", "gestionar_caracterizacion", "upgd"),
      ("/fichas/nueva", "Notificación individual", "notificar_individual", "fichas"),
      ("/listado", "Fichas registradas", "ver_reportes", "listado"),
      ("/usuarios", "Usuarios", "gestionar_usuarios", "usuarios"),
    ] %}
    {% for href, texto, permiso, clave in items %}
      {% if permisos.get(permiso) %}
        <a href="{{ href }}" class="nav{% if activo == clave %} activo{% endif %}">{{ texto }}</a>
      {% endif %}
    {% endfor %}
    <div class="usuario-box">
      <strong>{{ usuario["nombre_completo"] }}</strong>
      <span>{{ rol_labels.get(usuario["rol"], usuario["rol"]) }}</span>
      <a href="/cambiar-password" class="enlace-claro">Cambiar contraseña</a>
    </div>
    <form method="post" action="/logout">
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
      <button class="btn-link">Cerrar sesión</button>
    </form>
  </nav>
{% endif %}
  <main class="{{ 'contenido' if usuario else 'solo' }}">
    {% block contenido %}{% endblock %}
  </main>
{% if usuario %}
</div>
{% endif %}
</body>
</html>
```

`sivigila/templates/_macros.html`:

```html
{% macro campo(c, valor, error, prefijo="", solo_lectura=false, obligatorio=false) %}
{% set nombre = prefijo ~ c.key %}
<div class="campo{% if error %} con-error{% endif %}">
  <label for="{{ nombre }}">{{ c.label }}{% if obligatorio %} *{% endif %}</label>
  {% if c.tipo == "fecha" %}
    <input type="date" id="{{ nombre }}" name="{{ nombre }}" value="{{ valor or '' }}" {% if solo_lectura %}disabled{% endif %}>
  {% elif c.tipo == "lista" %}
    <select id="{{ nombre }}" name="{{ nombre }}" {% if solo_lectura %}disabled{% endif %}>
      <option value="">— Selecciona —</option>
      {% for op in c.opciones %}
        <option value="{{ op }}" {% if valor == op %}selected{% endif %}>{{ op }}</option>
      {% endfor %}
    </select>
  {% elif c.tipo == "si_no" %}
    <div class="radios" id="{{ nombre }}">
      {% for op in ["Sí", "No"] %}
        <label><input type="radio" name="{{ nombre }}" value="{{ op }}" {% if valor == op %}checked{% endif %} {% if solo_lectura %}disabled{% endif %}> {{ op }}</label>
      {% endfor %}
    </div>
  {% else %}
    <input type="text" id="{{ nombre }}" name="{{ nombre }}" value="{{ valor if valor is not none else '' }}" {% if solo_lectura %}disabled{% endif %}>
  {% endif %}
  {% if error %}<p class="campo-error">{{ error }}</p>{% endif %}
</div>
{% endmacro %}
```

`sivigila/templates/login.html`:

```html
{% extends "base.html" %}
{% block titulo %}Iniciar sesión{% endblock %}
{% block contenido %}
<section class="tarjeta login">
  <header class="login-header">
    <h1>SIVIGILA</h1>
    <p>Sistema de Vigilancia en Salud Pública · Moderno</p>
  </header>
  <form method="post" action="/login">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="campo">
      <label for="username">Código de usuario</label>
      <input type="text" id="username" name="username" value="{{ username or '' }}" autocomplete="username" required autofocus>
    </div>
    <div class="campo">
      <label for="password">Contraseña</label>
      <input type="password" id="password" name="password" autocomplete="current-password" required>
    </div>
    {% if error %}<p class="alerta error" role="alert">{{ error }}</p>{% endif %}
    <button class="btn primario ancho">Continuar</button>
  </form>
</section>
{% endblock %}
```

`sivigila/templates/error.html`:

```html
{% extends "base.html" %}
{% block titulo %}{{ titulo }}{% endblock %}
{% block contenido %}
<section class="tarjeta">
  <h1>{{ titulo }}</h1>
  <p>{{ mensaje }}</p>
  {% if enlace %}
    <p><a class="btn primario" href="{{ enlace }}">{{ enlace_texto }}</a></p>
  {% elif not usuario %}
    <p><a href="/login">Ir a iniciar sesión</a></p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 11: CSS y JS**

`sivigila/static/app.js`:

```javascript
// Pestañas de la ficha: solo muestran u ocultan paneles. No hay viaje al servidor y no se pierde lo escrito.
function activarPestana(boton) {
  const grupo = boton.closest("[data-tabs]");
  grupo.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("activa", b === boton));
  document.querySelectorAll("[data-panel]").forEach((p) => {
    p.hidden = p.dataset.panel !== boton.dataset.tab;
  });
}

document.addEventListener("click", (e) => {
  const boton = e.target.closest("[data-tab]");
  if (boton) activarPestana(boton);
});

// Si el servidor devolvió errores, abre la primera pestaña que tenga un campo con error.
document.addEventListener("DOMContentLoaded", () => {
  const conError = document.querySelector("[data-panel] .campo-error");
  if (!conError) return;
  const panel = conError.closest("[data-panel]").dataset.panel;
  const boton = document.querySelector(`[data-tab="${panel}"]`);
  if (boton) activarPestana(boton);
});
```

`sivigila/static/app.css`:

```css
:root {
  --primario: #C8102E; --primario-osc: #9E0C23; --acento: #1F6FEB;
  --fondo: #F4F5F7; --tarjeta: #FFFFFF; --borde: #D9DCE1;
  --texto: #1B1F24; --suave: #5F6672;
  --exito: #2E7D32; --alerta: #B8860B; --peligro: #7A1F1F;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: var(--fondo); color: var(--texto); font-size: 15px; }
h1 { margin: 0 0 4px; font-size: 26px; }
h2 { font-size: 18px; margin: 18px 0 10px; }
.sub { color: var(--suave); margin: 0 0 18px; }
.nota { color: var(--suave); }

.layout { display: flex; min-height: 100vh; }
.sidebar { width: 230px; flex-shrink: 0; background: #181B21; color: #fff; display: flex; flex-direction: column; padding: 20px 14px; gap: 4px; }
.marca { font-size: 20px; font-weight: 700; color: var(--primario); margin-bottom: 18px; }
.marca small { display: block; font-size: 12px; color: #999; font-weight: 400; }
.nav { color: #fff; text-decoration: none; padding: 10px 12px; border-radius: 8px; }
.nav:hover { background: #242832; }
.nav.activo { background: var(--primario); }
.usuario-box { margin-top: auto; background: #20242C; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 2px; font-size: 13px; }
.usuario-box span { color: #999; }
.enlace-claro { color: #9CC3FF; font-size: 12px; }
.btn-link { background: none; border: 0; color: #FF8080; cursor: pointer; padding: 10px 12px; text-align: left; width: 100%; font: inherit; }
.contenido { flex: 1; padding: 24px 28px; max-width: 1200px; }
.solo { display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 16px; }

.tarjeta { background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 14px; padding: 20px; margin-bottom: 18px; }
.sub-tarjeta { border: 1px dashed var(--borde); border-radius: 10px; padding: 14px; margin-bottom: 14px; }
.login { width: 100%; max-width: 420px; padding: 0; overflow: hidden; }
.login-header { background: var(--primario); color: #fff; padding: 22px; text-align: center; }
.login-header h1 { font-size: 28px; }
.login-header p { margin: 4px 0 0; }
.login form { padding: 24px 28px; }

.rejilla { display: grid; gap: 4px 16px; }
.rejilla.dos { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.rejilla.tres { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.rejilla.cuatro { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.campo { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.campo label { font-size: 13px; font-weight: 600; }
input[type=text], input[type=password], input[type=date], input[type=search], select {
  padding: 8px 10px; border: 1px solid var(--borde); border-radius: 8px; font: inherit; background: #fff; width: 100%;
}
.con-error input, .con-error select { border-color: var(--primario); }
.campo-error { color: var(--primario); font-size: 13px; margin: 0; }
.radios { display: flex; gap: 16px; padding: 6px 0; }
.checks { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; margin-bottom: 12px; }

.btn { display: inline-block; border: 0; border-radius: 8px; padding: 10px 18px; font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; color: #fff; background: var(--suave); }
.btn.primario { background: var(--primario); }
.btn.primario:hover { background: var(--primario-osc); }
.btn.secundario { background: var(--acento); }
.btn.exito { background: var(--exito); }
.btn.peligro { background: var(--peligro); }
.btn.chico { padding: 4px 10px; font-size: 13px; }
.btn.ancho { width: 100%; }
.acciones { display: flex; gap: 10px; margin: 12px 0 18px; flex-wrap: wrap; }
.en-linea { display: inline; }

.alerta { padding: 10px 14px; border-radius: 8px; margin: 0 0 14px; }
.alerta.error { background: #FDECEE; color: #8A1020; }
.alerta.exito { background: #E8F5E9; color: #1E5E23; }
.alerta.aviso { background: #FFF6E0; color: #7A5800; }

.pestanas { display: flex; gap: 6px; margin-bottom: -1px; flex-wrap: wrap; }
.pestana { border: 1px solid var(--borde); background: #E9EBEF; border-radius: 10px 10px 0 0; padding: 10px 16px; cursor: pointer; font: inherit; }
.pestana.activa { background: var(--tarjeta); border-bottom-color: var(--tarjeta); font-weight: 600; }

.badge { display: inline-block; padding: 2px 10px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #fff; background: var(--suave); vertical-align: middle; }
.badge.ok { background: var(--exito); }
.badge.pendiente { background: var(--alerta); }
.badge.inactivo { background: var(--peligro); }

.tabla { width: 100%; border-collapse: collapse; background: var(--tarjeta); }
.tabla th, .tabla td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--borde); font-size: 14px; vertical-align: middle; }
.tabla th { color: var(--suave); font-weight: 600; }
.barra { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; align-items: center; }
.barra input[type=search] { flex: 1; min-width: 240px; width: auto; }
.barra select { width: auto; }
.paginacion { display: flex; gap: 8px; align-items: center; margin-top: 12px; }

.tarjetas { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; margin-bottom: 22px; }
.tarjeta-acceso { display: block; background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 14px; padding: 18px; color: inherit; text-decoration: none; }
.tarjeta-acceso:hover { border-color: var(--primario); }
.tarjeta-acceso strong { display: block; font-size: 16px; margin-bottom: 4px; }
.tarjeta-acceso span { color: var(--suave); font-size: 13px; }
.barra-stat { display: grid; grid-template-columns: 220px 1fr 40px; gap: 10px; align-items: center; margin: 8px 0; }
.barra-fondo { background: #E9EBEF; border-radius: 8px; height: 14px; }
.barra-valor { background: var(--primario); border-radius: 8px; height: 14px; }

.zona-peligro { margin-top: 24px; }
.zona-peligro summary { cursor: pointer; color: var(--peligro); font-weight: 600; }

@media (max-width: 900px) {
  .layout { flex-direction: column; }
  .sidebar { width: 100%; }
  .contenido { padding: 16px; }
  .rejilla.dos, .rejilla.tres, .rejilla.cuatro { grid-template-columns: 1fr; }
  .barra-stat { grid-template-columns: 1fr; }
}
```

- [ ] **Step 12: Correr los tests y verificar que pasan**

Run: `python -m pytest tests/test_auth.py -v`
Expected: 10 passed.

- [ ] **Step 13: Commit**

```bash
git add sivigila tests
git commit -m "feat: app FastAPI con sesión, CSRF y login/logout"
```

---

### Task 3: Cambio de contraseña obligatorio, bloqueo de login y páginas de error

**Files:**
- Create: `sivigila/templates/cambiar_password.html`
- Modify: `sivigila/routes/login.py` (agregar rutas `/cambiar-password`), `tests/test_auth.py` (agregar tests)

**Interfaces:**
- Consumes: `auth.MIN_PASSWORD`, `auth.usuario_actual`, `auth._ahora`, `db.reset_password(..., debe_cambiar=False)`, `web.primera_pantalla`.
- Produces: `GET/POST /cambiar-password`.

- [ ] **Step 1: Escribir los tests**

Agregar al final de `tests/test_auth.py`:

```python
import logging

from fastapi.testclient import TestClient


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
        raise RuntimeError("dato sensible 1032456789")  # datos sintéticos

    with TestClient(app, raise_server_exceptions=False) as c:
        with caplog.at_level(logging.ERROR, logger="sivigila"):
            r = c.get("/explota")
    assert r.status_code == 500
    assert "Ocurrió un error inesperado" in r.text
    assert "1032456789" not in r.text
    assert "RuntimeError" in caplog.text
    assert "1032456789" not in caplog.text
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_auth.py -v`
Expected: los nuevos `test_usuario_sembrado_debe_cambiar_password`, `test_cambiar_password_*` FALLAN (la ruta `/cambiar-password` devuelve 404 / no existe). Los demás pueden pasar.

- [ ] **Step 3: Rutas de cambio de contraseña**

Agregar al final de `sivigila/routes/login.py`:

```python
@router.get("/cambiar-password")
def cambiar_password_form(request: Request, usuario=Depends(auth.usuario_actual)):
    return render(request, "cambiar_password.html",
                  {"obligatorio": bool(usuario["debe_cambiar_password"]), "errores": {}})


@router.post("/cambiar-password")
async def cambiar_password(request: Request, usuario=Depends(auth.usuario_actual)):
    form = await request.form()
    actual = str(form.get("actual", ""))
    nueva = str(form.get("nueva", ""))
    confirmacion = str(form.get("confirmacion", ""))

    errores = {}
    if not db.verify_password(actual, usuario["password_hash"], usuario["salt"]):
        errores["actual"] = "La contraseña actual no es correcta."
    if len(nueva) < auth.MIN_PASSWORD:
        errores["nueva"] = f"Debe tener al menos {auth.MIN_PASSWORD} caracteres."
    elif nueva == actual:
        errores["nueva"] = "Debe ser distinta de la actual."
    if nueva != confirmacion:
        errores["confirmacion"] = "No coincide con la nueva contraseña."
    if errores:
        return render(request, "cambiar_password.html",
                      {"obligatorio": bool(usuario["debe_cambiar_password"]), "errores": errores})

    db.reset_password(usuario["id"], nueva, debe_cambiar=False)
    db.log_action(usuario["id"], "CAMBIA_PASSWORD")
    return redirigir(primera_pantalla(usuario))
```

- [ ] **Step 4: Plantilla**

`sivigila/templates/cambiar_password.html`:

```html
{% extends "base.html" %}
{% block titulo %}Cambiar contraseña{% endblock %}
{% block contenido %}
<h1>Cambiar contraseña</h1>
{% if obligatorio %}
  <p class="alerta aviso">Por seguridad, debes cambiar tu contraseña antes de continuar.</p>
{% endif %}
<form method="post" action="/cambiar-password" class="tarjeta" style="max-width: 460px;">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  {% for nombre, etiqueta, auto in [
      ("actual", "Contraseña actual", "current-password"),
      ("nueva", "Nueva contraseña (mínimo 6 caracteres)", "new-password"),
      ("confirmacion", "Repite la nueva contraseña", "new-password")] %}
  <div class="campo{% if errores.get(nombre) %} con-error{% endif %}">
    <label for="{{ nombre }}">{{ etiqueta }}</label>
    <input type="password" id="{{ nombre }}" name="{{ nombre }}" autocomplete="{{ auto }}" required>
    {% if errores.get(nombre) %}<p class="campo-error">{{ errores.get(nombre) }}</p>{% endif %}
  </div>
  {% endfor %}
  <div class="acciones"><button class="btn primario">Guardar nueva contraseña</button></div>
</form>
{% endblock %}
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `python -m pytest tests/test_auth.py -v`
Expected: 17 passed.

- [ ] **Step 6: Commit**

```bash
git add sivigila tests
git commit -m "feat: cambio de contraseña obligatorio, bloqueo de login y páginas de error"
```

---

### Task 4: Panel principal y caracterización de la UPGD

**Files:**
- Create: `sivigila/validacion.py` (solo `parsear_fecha`, `validar_campos`, `validar_upgd` en esta task), `sivigila/routes/dashboard.py`, `sivigila/routes/upgd.py`, `sivigila/templates/dashboard.html`, `sivigila/templates/upgd_lista.html`, `sivigila/templates/upgd_form.html`, `tests/test_dashboard_upgd.py`
- Modify: `sivigila/main.py` (incluir routers), `tests/conftest.py` (fixture `digitador`)

**Interfaces:**
- Consumes: `web.render`, `web.redirigir`, `web.upgd_activa`, `auth.require_permiso`, `catalogos.CAMPOS_UPGD`, `OBLIGATORIOS_UPGD`, `RECURSOS_UPGD`, `SI_NO`.
- Produces:
  - `validacion.parsear_fecha(valor: str) -> date` (lanza `ValueError`), `validacion.validar_campos(campos, form, obligatorios, hoy) -> tuple[dict, dict]` (datos con `None` en vacíos; errores `{clave: mensaje}`), `validacion.validar_upgd(form, hoy) -> tuple[dict, dict]`.
  - Rutas `GET /`, `GET /upgd`, `GET/POST /upgd/nueva`, `GET/POST /upgd/{upgd_id}`, `POST /upgd/{upgd_id}/activar`.
  - Fixture `digitador` (usuario `digi` con sesión iniciada).

- [ ] **Step 1: Fixture de sesión iniciada**

Agregar al final de `tests/conftest.py`:

```python
@pytest.fixture
def digitador(db, client):
    from tests.utils import crear_usuario, iniciar_sesion

    usuario = crear_usuario(db, "digi")
    iniciar_sesion(client, "digi")
    return usuario
```

- [ ] **Step 2: Escribir los tests**

`tests/test_dashboard_upgd.py`:

```python
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
```

- [ ] **Step 3: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_dashboard_upgd.py -v`
Expected: FAIL; `GET /` y `/upgd*` responden 404.

- [ ] **Step 4: Validación base**

`sivigila/validacion.py`:

```python
"""Validación de formularios: fechas, listas cerradas y campos dinámicos por evento."""

import re
from datetime import date

from .catalogos import CAMPOS_UPGD, OBLIGATORIOS_UPGD, RECURSOS_UPGD, SI_NO

_FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parsear_fecha(valor: str) -> date:
    """Convierte 'AAAA-MM-DD' en date. Lanza ValueError si el formato no es ese."""
    if not _FORMATO_FECHA.match(valor):
        raise ValueError(f"Formato de fecha no válido: {valor!r}")
    return date.fromisoformat(valor)


def validar_campos(campos, form, obligatorios, hoy: date):
    """
    Valida los campos definidos en `campos` contra lo enviado en `form`.
    Devuelve (datos, errores): datos con None en los vacíos; errores {clave: mensaje}.
    """
    datos, errores = {}, {}
    for c in campos:
        clave = c["key"]
        valor = str(form.get(clave) or "").strip()
        if not valor:
            datos[clave] = None
            if clave in obligatorios:
                errores[clave] = "Este campo es obligatorio."
            continue
        if c["tipo"] == "fecha":
            try:
                fecha = parsear_fecha(valor)
            except ValueError:
                errores[clave] = "Fecha no válida. Usa el formato AAAA-MM-DD."
                continue
            if fecha > hoy:
                errores[clave] = "La fecha no puede ser posterior a hoy."
                continue
        elif c["tipo"] in ("lista", "si_no"):
            opciones = c.get("opciones") or SI_NO
            if valor not in opciones:
                errores[clave] = "Selecciona una opción de la lista."
                continue
        datos[clave] = valor
    return datos, errores


def validar_upgd(form, hoy: date):
    datos, errores = validar_campos(CAMPOS_UPGD, form, OBLIGATORIOS_UPGD, hoy)
    for clave in RECURSOS_UPGD:
        datos[clave] = 1 if form.get(clave) else 0
    return datos, errores
```

- [ ] **Step 5: Rutas**

`sivigila/routes/dashboard.py`:

```python
from datetime import date

from fastapi import APIRouter, Depends, Request

from .. import db
from ..auth import require_permiso
from ..web import render, upgd_activa

router = APIRouter()


@router.get("/")
def dashboard(request: Request, usuario=Depends(require_permiso("ver_reportes"))):
    stats = db.count_notificaciones_por_evento()
    maximo = max((s["total"] for s in stats), default=0)
    return render(request, "dashboard.html", {
        "activo": "dashboard",
        "stats": stats,
        "maximo": maximo or 1,
        "hay_casos": maximo > 0,
        "upgd": upgd_activa(request),
        "hoy": date.today(),
    })
```

`sivigila/routes/upgd.py`:

```python
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import db
from ..auth import require_permiso
from ..catalogos import CAMPOS_UPGD, OBLIGATORIOS_UPGD, RECURSOS_UPGD
from ..validacion import validar_upgd
from ..web import redirigir, render, upgd_activa

router = APIRouter()
permiso = require_permiso("gestionar_caracterizacion")


def _upgd_o_404(upgd_id: int):
    upgd = db.get_upgd(upgd_id)
    if upgd is None:
        raise HTTPException(status_code=404)
    return upgd


def _form(request, upgd=None, valores=None, errores=None):
    return render(request, "upgd_form.html", {
        "activo": "upgd",
        "upgd": upgd,
        "valores": valores if valores is not None else (dict(upgd) if upgd else dict.fromkeys(RECURSOS_UPGD, 1)),
        "errores": errores or {},
        "campos": CAMPOS_UPGD,
        "obligatorios": OBLIGATORIOS_UPGD,
        "recursos": RECURSOS_UPGD,
    })


@router.get("/upgd")
def lista(request: Request, usuario=Depends(permiso)):
    return render(request, "upgd_lista.html", {
        "activo": "upgd",
        "upgds": db.list_upgd(),
        "upgd_activa": upgd_activa(request),
        "mensaje": "Caracterización guardada correctamente." if request.query_params.get("guardada") else None,
    })


@router.get("/upgd/nueva")
def nueva(request: Request, usuario=Depends(permiso)):
    return _form(request)


@router.post("/upgd/nueva")
async def crear(request: Request, usuario=Depends(permiso)):
    form = await request.form()
    hoy = date.today()
    datos, errores = validar_upgd(form, hoy)
    if errores:
        return _form(request, valores=dict(form), errores=errores)
    datos.update(activa_sivigila=1, fecha_caracteriza=hoy.isoformat(), fecha_inicio_uso=hoy.isoformat())
    nuevo_id = db.upsert_upgd(datos)
    request.session["upgd_id"] = nuevo_id
    db.log_action(usuario["id"], "CREA_UPGD", datos["razon_social"])
    return redirigir("/upgd?guardada=1")


@router.get("/upgd/{upgd_id}")
def editar_form(request: Request, upgd_id: int, usuario=Depends(permiso)):
    return _form(request, upgd=_upgd_o_404(upgd_id))


@router.post("/upgd/{upgd_id}")
async def editar(request: Request, upgd_id: int, usuario=Depends(permiso)):
    upgd = _upgd_o_404(upgd_id)
    form = await request.form()
    hoy = date.today()
    datos, errores = validar_upgd(form, hoy)
    if errores:
        return _form(request, upgd=upgd, valores=dict(form), errores=errores)
    datos["fecha_caracteriza"] = hoy.isoformat()
    db.upsert_upgd(datos, upgd_id)
    db.log_action(usuario["id"], "EDITA_UPGD", f"id={upgd_id}")
    return redirigir("/upgd?guardada=1")


@router.post("/upgd/{upgd_id}/activar")
def activar(request: Request, upgd_id: int, usuario=Depends(permiso)):
    _upgd_o_404(upgd_id)
    request.session["upgd_id"] = upgd_id
    return redirigir("/upgd")
```

En `sivigila/main.py`, cambiar el import de routers y la inclusión:

```python
from .routes import dashboard, login, upgd
```

```python
    for modulo in (login, dashboard, upgd):
        app.include_router(modulo.router)
```

(reemplaza la línea `app.include_router(login.router)`).

- [ ] **Step 6: Plantillas**

`sivigila/templates/dashboard.html`:

```html
{% extends "base.html" %}
{% block titulo %}Panel principal{% endblock %}
{% block contenido %}
<h1>Bienvenido(a), {{ usuario["nombre_completo"].split()[0] }}</h1>
<p class="sub">{{ hoy.strftime("%d/%m/%Y") }}{% if upgd %} · UPGD activa: {{ upgd["razon_social"] }}{% endif %}</p>

<div class="tarjetas">
  {% if permisos.get("gestionar_caracterizacion") %}
  <a class="tarjeta-acceso" href="/upgd"><strong>Caracterización</strong><span>Configura la UPGD que notifica</span></a>
  {% endif %}
  {% if permisos.get("notificar_individual") %}
  <a class="tarjeta-acceso" href="/fichas/nueva"><strong>Individual</strong><span>Diligencia fichas de vigilancia</span></a>
  {% endif %}
  {% if permisos.get("ver_reportes") %}
  <a class="tarjeta-acceso" href="/listado"><strong>Fichas registradas</strong><span>Consulta, edita y filtra notificaciones</span></a>
  {% endif %}
  {% if permisos.get("gestionar_usuarios") %}
  <a class="tarjeta-acceso" href="/usuarios"><strong>Usuarios</strong><span>Crea usuarios y administra permisos</span></a>
  {% endif %}
</div>

<h2>Casos notificados por evento</h2>
<section class="tarjeta">
  {% if hay_casos %}
    {% for s in stats %}
    <div class="barra-stat">
      <span>{{ s["nombre"] }}</span>
      <div class="barra-fondo"><div class="barra-valor" style="width: {{ [4, (s['total'] * 100 / maximo) | round(0)] | max }}%"></div></div>
      <strong>{{ s["total"] }}</strong>
    </div>
    {% endfor %}
  {% else %}
    <p class="nota">Aún no hay fichas registradas.</p>
  {% endif %}
</section>

{% if not upgd %}
<p class="alerta aviso">Aún no has configurado ninguna UPGD. Ve a «Caracterización» antes de notificar casos.</p>
{% endif %}
{% endblock %}
```

`sivigila/templates/upgd_lista.html`:

```html
{% extends "base.html" %}
{% block titulo %}Caracterización{% endblock %}
{% block contenido %}
<h1>Caracterización de la UPGD</h1>
<p class="sub">Configura la unidad notificadora: identificación, contacto y recursos disponibles para la vigilancia epidemiológica.</p>
{% if mensaje %}<p class="alerta exito">{{ mensaje }}</p>{% endif %}
<p><a class="btn primario" href="/upgd/nueva">Nueva UPGD</a></p>
{% if upgds %}
<table class="tabla">
  <thead><tr><th>Razón social</th><th>NIT</th><th>Nivel</th><th>Sesión</th><th></th></tr></thead>
  <tbody>
  {% for u in upgds %}
    {% set en_uso = upgd_activa and u["id"] == upgd_activa["id"] %}
    <tr id="upgd-{{ u['id'] }}">
      <td>{{ u["razon_social"] }}</td>
      <td>{{ u["nit"] or "-" }}</td>
      <td>{{ u["nivel_complejidad"] or "-" }}</td>
      <td>{% if en_uso %}<span class="badge ok">En uso</span>{% endif %}</td>
      <td>
        <a class="btn secundario chico" href="/upgd/{{ u['id'] }}">Editar</a>
        {% if not en_uso %}
        <form method="post" action="/upgd/{{ u['id'] }}/activar" class="en-linea">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <button class="btn chico">Usar en sesión</button>
        </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p class="nota">No hay UPGD registradas todavía.</p>
{% endif %}
{% endblock %}
```

`sivigila/templates/upgd_form.html`:

```html
{% extends "base.html" %}
{% from "_macros.html" import campo %}
{% block titulo %}Caracterización{% endblock %}
{% block contenido %}
<h1>{{ "Editar UPGD" if upgd else "Nueva UPGD" }}</h1>
<p class="sub">Los campos con * son obligatorios.</p>
{% if errores %}<p class="alerta error">Revisa los campos marcados.</p>{% endif %}
<form method="post" action="{{ '/upgd/%d' % upgd['id'] if upgd else '/upgd/nueva' }}" class="tarjeta">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <div class="rejilla dos">
    {% for c in campos %}
      {{ campo(c, valores.get(c.key), errores.get(c.key), obligatorio=c.key in obligatorios) }}
    {% endfor %}
  </div>
  <h2>Recursos adicionales para la vigilancia epidemiológica</h2>
  <div class="checks">
    {% for clave, etiqueta in recursos.items() %}
      <label><input type="checkbox" name="{{ clave }}" value="1" {% if valores.get(clave) and valores.get(clave) != "0" %}checked{% endif %}> {{ etiqueta }}</label>
    {% endfor %}
  </div>
  <div class="acciones">
    <button class="btn primario">Guardar caracterización</button>
    <a class="btn" href="/upgd">Cancelar</a>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 7: Correr los tests y verificar que pasan**

Run: `python -m pytest -v`
Expected: todos pasan (test_db 12, test_auth 17, test_dashboard_upgd 9).

- [ ] **Step 8: Commit**

```bash
git add sivigila tests
git commit -m "feat: panel principal y caracterización de la UPGD editable"
```

---

### Task 5: Validación de la ficha individual

**Files:**
- Modify: `sivigila/validacion.py`
- Create: `tests/test_validacion.py`

**Interfaces:**
- Consumes: `validar_campos`, `parsear_fecha` (Task 4), `catalogos.CAMPOS_BASICOS`, `OBLIGATORIOS_GUARDAR`, `OBLIGATORIOS_TERMINAR`, `PREFIJO_COMP`, `CAMPOS_LAB`.
- Produces:
  - `calcular_edad(nacimiento: date, referencia: date) -> tuple[int, str]` con unidad `"Años" | "Meses" | "Días"`.
  - `validar_ficha(form, evento, completa: bool, hoy: date) -> tuple[dict, dict]`. `evento` es la fila de `db.get_evento` o `None`. `datos` trae las claves de `CAMPOS_BASICOS` + `codigo_evento` (si hay evento) + `edad` + `unidad_edad` + `datos_complementarios` (JSON). Errores de complementarios con clave `"comp__<key>"`; error de campos ajenos al evento en `errores["general"]`.
  - `comp_de_form(form) -> dict` (quita el prefijo `comp__`).
  - `validar_laboratorio(form, hoy) -> tuple[dict, dict]` (`prueba` obligatoria).

- [ ] **Step 1: Escribir los tests**

`tests/test_validacion.py`:

```python
import json
from datetime import date

import pytest

from sivigila.validacion import (
    calcular_edad, comp_de_form, parsear_fecha, validar_campos, validar_ficha,
    validar_laboratorio, validar_upgd,
)
from tests.utils import ficha_completa

HOY = date(2026, 10, 3)


def test_parsear_fecha_solo_acepta_iso():
    assert parsear_fecha("2026-10-03") == HOY
    for malo in ("03/10/2026", "20261003", "2026-13-01"):
        with pytest.raises(ValueError):
            parsear_fecha(malo)


@pytest.mark.parametrize("nacimiento, esperado", [
    (date(1996, 10, 3), (30, "Años")),
    (date(1996, 10, 4), (29, "Años")),
    (date(2026, 5, 3), (5, "Meses")),
    (date(2026, 9, 20), (13, "Días")),
])
def test_calcular_edad(nacimiento, esperado):
    assert calcular_edad(nacimiento, HOY) == esperado


def test_validar_campos_detecta_obligatorio_lista_y_fecha_futura():
    campos = [
        {"key": "a", "label": "A", "tipo": "texto"},
        {"key": "b", "label": "B", "tipo": "lista", "opciones": ["X", "Y"]},
        {"key": "c", "label": "C", "tipo": "fecha"},
        {"key": "d", "label": "D", "tipo": "si_no"},
    ]
    datos, errores = validar_campos(
        campos, {"a": "", "b": "Z", "c": "2026-10-04", "d": "Sí"}, {"a"}, HOY
    )
    assert errores == {
        "a": "Este campo es obligatorio.",
        "b": "Selecciona una opción de la lista.",
        "c": "La fecha no puede ser posterior a hoy.",
    }
    assert datos["d"] == "Sí"
    assert datos["a"] is None


def test_guardar_minimo_sin_errores(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana"}
    datos, errores = validar_ficha(form, db.get_evento("210"), completa=False, hoy=HOY)
    assert errores == {}
    assert datos["codigo_evento"] == "210"
    assert datos["datos_complementarios"] == "{}"
    assert datos["edad"] is None


def test_guardar_exige_numero_id_y_nombre(db):
    _, errores = validar_ficha({"codigo_evento": "210"}, db.get_evento("210"), False, HOY)
    assert set(errores) == {"numero_id", "primer_nombre"}


def test_sin_evento_es_error(db):
    _, errores = validar_ficha({"numero_id": "1", "primer_nombre": "Ana"}, None, False, HOY)
    assert "codigo_evento" in errores


def test_terminar_exige_basicos_y_todos_los_complementarios(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana"}
    _, errores = validar_ficha(form, db.get_evento("210"), completa=True, hoy=HOY)
    assert {"sexo", "fecha_nacimiento", "condicion", "comp__fiebre",
            "comp__clasificacion_dengue"} <= set(errores)


def test_terminar_completa_sin_errores_y_calcula_edad(db):
    hoy = date.today()
    datos, errores = validar_ficha(ficha_completa(), db.get_evento("210"), True, hoy)
    assert errores == {}
    assert datos["edad"] == 30
    assert datos["unidad_edad"] == "Años"
    assert json.loads(datos["datos_complementarios"])["fiebre"] == "Sí"


def test_fechas_fuera_de_orden(db):
    form = ficha_completa(fecha_nacimiento="2020-01-10", fecha_inicio_sintomas="2019-12-01")
    _, errores = validar_ficha(form, db.get_evento("210"), False, date.today())
    assert errores["fecha_inicio_sintomas"] == "No puede ser anterior a la fecha de nacimiento."


def test_hospitalizado_y_fallecido_exigen_fecha_al_terminar(db):
    form = ficha_completa(hospitalizado="Sí", condicion="Fallecido")
    _, errores = validar_ficha(form, db.get_evento("210"), True, date.today())
    assert "fecha_hospitalizacion" in errores
    assert "fecha_defuncion" in errores


def test_complementario_de_otro_evento_es_rechazado(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana", "comp__gravedad": "Leve"}
    _, errores = validar_ficha(form, db.get_evento("210"), False, HOY)
    assert "gravedad" in errores["general"]


def test_opcion_complementaria_invalida(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana",
            "comp__clasificacion_dengue": "Dengue inventado"}
    _, errores = validar_ficha(form, db.get_evento("210"), False, HOY)
    assert errores["comp__clasificacion_dengue"] == "Selecciona una opción de la lista."


def test_comp_de_form_quita_prefijo():
    assert comp_de_form({"comp__fiebre": "Sí", "numero_id": "1"}) == {"fiebre": "Sí"}


def test_validar_laboratorio_exige_prueba():
    _, errores = validar_laboratorio({"muestra": "Suero"}, HOY)
    assert errores == {"prueba": "Este campo es obligatorio."}


def test_validar_upgd_convierte_recursos():
    datos, errores = validar_upgd({"cod_prestador": "1", "razon_social": "X", "cove": "1"}, HOY)
    assert errores == {}
    assert datos["cove"] == 1
    assert datos["internet"] == 0
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_validacion.py -v`
Expected: ERROR de colección con `ImportError: cannot import name 'calcular_edad' from 'sivigila.validacion'`.

- [ ] **Step 3: Implementar**

En `sivigila/validacion.py`, reemplazar todo el bloque de imports (las líneas `import re`, `from datetime import date` y `from .catalogos import ...`) por:

```python
import json
import re
from datetime import date

from .catalogos import (
    CAMPOS_BASICOS, CAMPOS_LAB, CAMPOS_UPGD, OBLIGATORIOS_GUARDAR, OBLIGATORIOS_TERMINAR,
    OBLIGATORIOS_UPGD, PREFIJO_COMP, RECURSOS_UPGD, SI_NO,
)
```

y agregar al final del archivo:

```python
# Orden lógico de las fechas clínicas de la ficha (solo se compara entre las que vengan llenas).
ORDEN_FECHAS = [
    ("fecha_nacimiento", "fecha de nacimiento"),
    ("fecha_inicio_sintomas", "fecha de inicio de síntomas"),
    ("fecha_consulta", "fecha de consulta"),
]


def calcular_edad(nacimiento: date, referencia: date):
    """Edad en años; si es menor de un año, en meses; si es menor de un mes, en días."""
    anios = referencia.year - nacimiento.year - (
        (referencia.month, referencia.day) < (nacimiento.month, nacimiento.day)
    )
    if anios >= 1:
        return anios, "Años"
    meses = (referencia.year - nacimiento.year) * 12 + referencia.month - nacimiento.month
    if referencia.day < nacimiento.day:
        meses -= 1
    if meses >= 1:
        return meses, "Meses"
    return (referencia - nacimiento).days, "Días"


def comp_de_form(form) -> dict:
    return {k[len(PREFIJO_COMP):]: v for k, v in form.items() if k.startswith(PREFIJO_COMP)}


def _validar_orden_fechas(datos, errores):
    anterior = None
    for clave, nombre in ORDEN_FECHAS:
        valor = datos.get(clave)
        if not valor or clave in errores:
            continue
        if anterior and valor < anterior[1]:  # fechas ISO: el orden de texto es el cronológico
            errores[clave] = f"No puede ser anterior a la {anterior[0]}."
        else:
            anterior = (nombre, valor)


def validar_ficha(form, evento, completa: bool, hoy: date):
    """
    Valida la ficha individual. `completa=True` es para "Terminar": exige todos los
    obligatorios de básicos y todos los complementarios del evento.
    """
    obligatorios = OBLIGATORIOS_GUARDAR | (OBLIGATORIOS_TERMINAR if completa else set())
    datos, errores = validar_campos(CAMPOS_BASICOS, form, obligatorios, hoy)

    if evento is None:
        errores["codigo_evento"] = "Selecciona el evento de interés en salud pública."
        campos_comp = []
    else:
        datos["codigo_evento"] = evento["codigo"]
        campos_comp = json.loads(evento["campos_json"])

    if completa:
        if datos.get("hospitalizado") == "Sí" and not datos.get("fecha_hospitalizacion") \
                and "fecha_hospitalizacion" not in errores:
            errores["fecha_hospitalizacion"] = "Obligatoria si el paciente fue hospitalizado."
        if datos.get("condicion") == "Fallecido" and not datos.get("fecha_defuncion") \
                and "fecha_defuncion" not in errores:
            errores["fecha_defuncion"] = "Obligatoria si el paciente falleció."

    _validar_orden_fechas(datos, errores)

    claves_validas = {c["key"] for c in campos_comp}
    enviados = comp_de_form(form)
    desconocidas = sorted(set(enviados) - claves_validas)
    if desconocidas:
        errores["general"] = (
            "El formulario trae campos que no corresponden al evento: " + ", ".join(desconocidas) + "."
        )
    comp, errores_comp = validar_campos(
        campos_comp, enviados, claves_validas if completa else set(), hoy
    )
    errores.update({PREFIJO_COMP + k: v for k, v in errores_comp.items()})
    datos["datos_complementarios"] = json.dumps(
        {k: v for k, v in comp.items() if v is not None}, ensure_ascii=False
    )

    if datos.get("fecha_nacimiento") and "fecha_nacimiento" not in errores:
        datos["edad"], datos["unidad_edad"] = calcular_edad(parsear_fecha(datos["fecha_nacimiento"]), hoy)
    else:
        datos["edad"], datos["unidad_edad"] = None, None
    return datos, errores


def validar_laboratorio(form, hoy: date):
    return validar_campos(CAMPOS_LAB, form, {"prueba"}, hoy)
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `python -m pytest tests/test_validacion.py -v`
Expected: 18 passed.

- [ ] **Step 5: Commit**

```bash
git add sivigila/validacion.py tests/test_validacion.py
git commit -m "feat: validación de ficha individual, complementarios y edad calculada"
```

---

### Task 6: Ficha individual (básicos, complementarios, terminar, eliminar)

**Files:**
- Create: `sivigila/routes/fichas.py`, `sivigila/templates/ficha.html`, `sivigila/templates/_complementarios.html`, `sivigila/templates/_laboratorios.html`, `tests/test_fichas.py`
- Modify: `sivigila/main.py` (incluir router `fichas`)

**Interfaces:**
- Consumes: `validar_ficha`, `comp_de_form` (Task 5), `web.upgd_activa`, `auth.require_permiso`, `catalogos.CAMPOS_BASICOS`, `OBLIGATORIOS_GUARDAR`, `CAMPOS_LAB`.
- Produces: rutas `GET /fichas/nueva`, `POST /fichas`, `GET /fichas/campos?codigo_evento=`, `GET /fichas/{id}`, `POST /fichas/{id}`, `POST /fichas/{id}/terminar`, `POST /fichas/{id}/eliminar`. En `sivigila/routes/fichas.py`: `router`, `_ficha_o_404(ficha_id) -> Row`, `_contexto_labs(request, ficha, valores=None, errores=None) -> dict` (claves `ficha`, `labs`, `puede_labs`, `campos_lab`, `lab_valores`, `lab_errores`). Contenedor HTMX de laboratorios: `<div id="laboratorios">`.

- [ ] **Step 1: Escribir los tests**

`tests/test_fichas.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_fichas.py -v`
Expected: FAIL; las rutas `/fichas*` responden 404.

- [ ] **Step 3: Rutas de la ficha**

`sivigila/routes/fichas.py`:

```python
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import db
from ..auth import require_permiso
from ..catalogos import CAMPOS_BASICOS, CAMPOS_LAB, OBLIGATORIOS_GUARDAR
from ..validacion import comp_de_form, validar_ficha
from ..web import redirigir, render, upgd_activa

router = APIRouter()

MENSAJES = {
    "guardada": "Ficha guardada correctamente.",
    "terminada": "La ficha se guardó como TERMINADA y quedó lista para envío.",
}


def _ficha_o_404(ficha_id: int):
    ficha = db.get_notificacion(ficha_id)
    if ficha is None:
        raise HTTPException(status_code=404)
    return ficha


def _comp_de_ficha(ficha) -> dict:
    if not ficha or not ficha["datos_complementarios"]:
        return {}
    try:
        return json.loads(ficha["datos_complementarios"])
    except (json.JSONDecodeError, TypeError):
        return {}


def _contexto_labs(request: Request, ficha, valores=None, errores=None) -> dict:
    usuario = request.state.usuario
    return {
        "ficha": ficha,
        "labs": db.list_laboratorios(ficha["id"]) if ficha else [],
        "puede_labs": ficha is not None and db.tiene_permiso(usuario, "gestionar_laboratorios"),
        "campos_lab": CAMPOS_LAB,
        "lab_valores": valores or {},
        "lab_errores": errores or {},
    }


def _render_ficha(request: Request, ficha=None, upgd=None, valores=None, comp_valores=None,
                  errores=None, mensaje=None):
    usuario = request.state.usuario
    eventos = db.list_eventos()
    if valores is None:
        valores = dict(ficha) if ficha else {}
    if comp_valores is None:
        comp_valores = _comp_de_ficha(ficha)
    codigo = valores.get("codigo_evento") or (eventos[0]["codigo"] if eventos else None)
    evento = db.get_evento(codigo) if codigo else None
    if upgd is None and ficha is not None:
        upgd = db.get_upgd(ficha["upgd_id"])
    ctx = {
        "activo": "fichas",
        "valores": valores,
        "comp_valores": comp_valores,
        "errores": errores or {},
        "eventos": eventos,
        "codigo_evento": codigo,
        "evento_nombre": evento["nombre"] if evento else None,
        "campos_basicos": CAMPOS_BASICOS,
        "campos_comp": json.loads(evento["campos_json"]) if evento else [],
        "obligatorios": OBLIGATORIOS_GUARDAR,
        "solo_lectura": ficha is not None and not db.tiene_permiso(usuario, "editar_notificaciones"),
        "upgd": upgd,
        "mensaje": mensaje,
    }
    ctx.update(_contexto_labs(request, ficha))
    return render(request, "ficha.html", ctx)


def _sin_upgd(request: Request):
    usuario = request.state.usuario
    puede = db.tiene_permiso(usuario, "gestionar_caracterizacion")
    return render(request, "error.html", {
        "activo": "fichas",
        "titulo": "Notificación individual",
        "mensaje": "Primero debes configurar y seleccionar una UPGD en «Caracterización».",
        "enlace": "/upgd" if puede else None,
        "enlace_texto": "Ir a Caracterización",
    })


@router.get("/fichas/nueva")
def nueva(request: Request, usuario=Depends(require_permiso("notificar_individual"))):
    upgd = upgd_activa(request)
    if upgd is None:
        return _sin_upgd(request)
    return _render_ficha(request, upgd=upgd)


@router.post("/fichas")
async def crear(request: Request, usuario=Depends(require_permiso("notificar_individual"))):
    upgd = upgd_activa(request)
    if upgd is None:
        return _sin_upgd(request)
    form = await request.form()
    hoy = date.today()
    evento = db.get_evento(str(form.get("codigo_evento", "")))
    datos, errores = validar_ficha(form, evento, completa=False, hoy=hoy)
    if errores:
        return _render_ficha(request, upgd=upgd, valores=dict(form),
                             comp_valores=comp_de_form(form), errores=errores)
    anio, semana, _ = hoy.isocalendar()
    datos.update(
        upgd_id=upgd["id"], fecha_notificacion=hoy.isoformat(), fecha_grabacion=hoy.isoformat(),
        anio=anio, semana=semana, estado_ficha="En proceso",
    )
    ficha_id = db.create_notificacion(datos, usuario["id"])
    db.log_action(usuario["id"], "GUARDA_FICHA", f"id={ficha_id}")
    return redirigir(f"/fichas/{ficha_id}?guardada=1")


@router.get("/fichas/campos")
def campos_complementarios(
    request: Request, codigo_evento: str = "",
    usuario=Depends(require_permiso("notificar_individual", "editar_notificaciones")),
):
    evento = db.get_evento(codigo_evento) if codigo_evento else None
    return render(request, "_complementarios.html", {
        "campos_comp": json.loads(evento["campos_json"]) if evento else [],
        "evento_nombre": evento["nombre"] if evento else None,
        "comp_valores": {},
        "errores": {},
        "solo_lectura": False,
    })


@router.get("/fichas/{ficha_id}")
def ver(request: Request, ficha_id: int, usuario=Depends(
        require_permiso("notificar_individual", "editar_notificaciones", "ver_reportes"))):
    ficha = _ficha_o_404(ficha_id)
    mensaje = next((m for clave, m in MENSAJES.items() if request.query_params.get(clave)), None)
    return _render_ficha(request, ficha=ficha, mensaje=mensaje)


async def _actualizar(request: Request, ficha_id: int, usuario, terminar: bool):
    ficha = _ficha_o_404(ficha_id)
    form = await request.form()
    evento = db.get_evento(str(form.get("codigo_evento", "")))
    datos, errores = validar_ficha(form, evento, completa=terminar, hoy=date.today())
    if errores:
        return _render_ficha(request, ficha=ficha, valores=dict(form),
                             comp_valores=comp_de_form(form), errores=errores)
    if terminar:
        datos["estado_ficha"] = "Terminada"
    db.update_notificacion(ficha_id, datos)
    db.log_action(usuario["id"], "TERMINA_FICHA" if terminar else "GUARDA_FICHA", f"id={ficha_id}")
    return redirigir(f"/fichas/{ficha_id}?{'terminada' if terminar else 'guardada'}=1")


@router.post("/fichas/{ficha_id}")
async def guardar(request: Request, ficha_id: int,
                  usuario=Depends(require_permiso("editar_notificaciones"))):
    return await _actualizar(request, ficha_id, usuario, terminar=False)


@router.post("/fichas/{ficha_id}/terminar")
async def terminar(request: Request, ficha_id: int,
                   usuario=Depends(require_permiso("editar_notificaciones"))):
    return await _actualizar(request, ficha_id, usuario, terminar=True)


@router.post("/fichas/{ficha_id}/eliminar")
def eliminar(request: Request, ficha_id: int,
             usuario=Depends(require_permiso("editar_notificaciones"))):
    _ficha_o_404(ficha_id)
    db.delete_notificacion(ficha_id)
    db.log_action(usuario["id"], "ELIMINA_FICHA", f"id={ficha_id}")
    return redirigir("/listado")
```

En `sivigila/main.py`:

```python
from .routes import dashboard, fichas, login, upgd
```

```python
    for modulo in (login, dashboard, upgd, fichas):
        app.include_router(modulo.router)
```

- [ ] **Step 4: Plantillas**

`sivigila/templates/ficha.html`:

```html
{% extends "base.html" %}
{% from "_macros.html" import campo %}
{% block titulo %}Notificación individual{% endblock %}
{% block contenido %}
<h1>Notificación individual{% if ficha %} · Ficha #{{ ficha["id"] }}
  <span class="badge {{ 'ok' if ficha['estado_ficha'] == 'Terminada' else 'pendiente' }}">{{ ficha["estado_ficha"] }}</span>{% endif %}</h1>
<p class="sub">UPGD: {{ upgd["razon_social"] if upgd else "-" }}{% if solo_lectura %} · Solo lectura{% endif %}</p>
{% if mensaje %}<p class="alerta exito">{{ mensaje }}</p>{% endif %}
{% if errores %}<p class="alerta error">Revisa los campos marcados.{% if errores.get("general") %} {{ errores.get("general") }}{% endif %}</p>{% endif %}

<div class="pestanas" data-tabs>
  <button type="button" class="pestana activa" data-tab="basicos">1 · Datos básicos</button>
  <button type="button" class="pestana" data-tab="complementarios">2 · Datos complementarios</button>
  <button type="button" class="pestana" data-tab="laboratorios">3 · Laboratorios</button>
</div>

<form method="post" action="{{ '/fichas/%d' % ficha['id'] if ficha else '/fichas' }}" id="form-ficha">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <section data-panel="basicos" class="tarjeta">
    <div class="campo{% if errores.get('codigo_evento') %} con-error{% endif %}">
      <label for="codigo_evento">Evento de interés en salud pública *</label>
      <select id="codigo_evento" name="codigo_evento"
              hx-get="/fichas/campos" hx-target="#complementarios" hx-swap="innerHTML"
              {% if solo_lectura %}disabled{% endif %}>
        {% for e in eventos %}
          <option value="{{ e['codigo'] }}" {% if e['codigo'] == codigo_evento %}selected{% endif %}>{{ e["codigo"] }} - {{ e["nombre"] }}</option>
        {% endfor %}
      </select>
      {% if errores.get("codigo_evento") %}<p class="campo-error">{{ errores.get("codigo_evento") }}</p>{% endif %}
    </div>
    <div class="rejilla tres">
      {% for c in campos_basicos %}
        {{ campo(c, valores.get(c.key), errores.get(c.key), solo_lectura=solo_lectura, obligatorio=c.key in obligatorios) }}
      {% endfor %}
    </div>
    {% if ficha and ficha["edad"] is not none %}
      <p class="nota">Edad calculada: {{ ficha["edad"] }} {{ ficha["unidad_edad"] }}</p>
    {% endif %}
  </section>

  <section data-panel="complementarios" class="tarjeta" hidden>
    <div id="complementarios">{% include "_complementarios.html" %}</div>
  </section>

  {% if not solo_lectura %}
  <div class="acciones">
    <button class="btn primario">Guardar ficha</button>
    {% if ficha %}<button class="btn exito" formaction="/fichas/{{ ficha['id'] }}/terminar">Terminar</button>{% endif %}
  </div>
  {% endif %}
</form>

<section data-panel="laboratorios" class="tarjeta" hidden>
  {% if not ficha %}
    <p class="nota">Guarda primero la ficha para poder registrar exámenes de laboratorio.</p>
  {% else %}
    <div id="laboratorios">{% include "_laboratorios.html" %}</div>
  {% endif %}
</section>

{% if ficha and permisos.get("editar_notificaciones") %}
<details class="zona-peligro">
  <summary>Eliminar ficha</summary>
  <p>Se borrará la ficha y sus resultados de laboratorio. Esta acción no se puede deshacer.</p>
  <form method="post" action="/fichas/{{ ficha['id'] }}/eliminar">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <button class="btn peligro">Sí, eliminar definitivamente</button>
  </form>
</details>
{% endif %}
{% endblock %}
```

`sivigila/templates/_complementarios.html`:

```html
{% from "_macros.html" import campo %}
{% if campos_comp %}
  <h2>Formulario específico{% if evento_nombre %}: {{ evento_nombre }}{% endif %}</h2>
  <div class="rejilla dos">
    {% for c in campos_comp %}
      {{ campo(c, comp_valores.get(c.key), errores.get("comp__" ~ c.key), prefijo="comp__", solo_lectura=solo_lectura) }}
    {% endfor %}
  </div>
{% else %}
  <p class="nota">Selecciona un evento en la pestaña 1.</p>
{% endif %}
```

`sivigila/templates/_laboratorios.html` (las rutas de agregar/quitar llegan en la Task 7):

```html
{% from "_macros.html" import campo %}
{% if puede_labs %}
<form hx-post="/fichas/{{ ficha['id'] }}/laboratorios" hx-target="#laboratorios" hx-swap="innerHTML" class="sub-tarjeta">
  <div class="rejilla cuatro">
    {% for c in campos_lab %}
      {{ campo(c, lab_valores.get(c.key), lab_errores.get(c.key), obligatorio=c.key == "prueba") }}
    {% endfor %}
  </div>
  <button class="btn secundario">Agregar resultado de laboratorio</button>
</form>
{% endif %}
<h3>Resultados registrados</h3>
{% if labs %}
<table class="tabla">
  <thead><tr><th>Prueba</th><th>Muestra</th><th>Agente</th><th>Resultado</th><th>Valor</th><th>Toma</th><th>Fecha resultado</th>{% if puede_labs %}<th></th>{% endif %}</tr></thead>
  <tbody>
  {% for lab in labs %}
    <tr id="lab-{{ lab['id'] }}">
      <td>{{ lab["prueba"] or "-" }}</td>
      <td>{{ lab["muestra"] or "-" }}</td>
      <td>{{ lab["agente"] or "-" }}</td>
      <td>{{ lab["resultado"] or "-" }}</td>
      <td>{{ lab["valor"] or "-" }}</td>
      <td>{{ lab["fecha_toma"] or "-" }}</td>
      <td>{{ lab["fecha_resultado"] or "-" }}</td>
      {% if puede_labs %}
      <td><button type="button" class="btn peligro chico"
                  hx-post="/fichas/{{ ficha['id'] }}/laboratorios/{{ lab['id'] }}/eliminar"
                  hx-target="#laboratorios" hx-swap="innerHTML">Quitar</button></td>
      {% endif %}
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p class="nota">Sin resultados registrados aún.</p>
{% endif %}
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `python -m pytest -v`
Expected: todos pasan (test_fichas: 14 passed).

- [ ] **Step 6: Commit**

```bash
git add sivigila tests
git commit -m "feat: ficha individual web con complementarios dinámicos, terminar y eliminar"
```

---

### Task 7: Laboratorios con HTMX

**Files:**
- Modify: `sivigila/routes/fichas.py` (agregar dos rutas)
- Create: `tests/test_laboratorios.py`

**Interfaces:**
- Consumes: `_ficha_o_404`, `_contexto_labs` (Task 6), `validacion.validar_laboratorio` (Task 5), `db.add_laboratorio`, `db.get_laboratorio`, `db.delete_laboratorio`.
- Produces: `POST /fichas/{ficha_id}/laboratorios` y `POST /fichas/{ficha_id}/laboratorios/{lab_id}/eliminar`, ambas devuelven el parcial `_laboratorios.html` (422 si hay errores de validación).

- [ ] **Step 1: Escribir los tests**

`tests/test_laboratorios.py`:

```python
from datetime import date, timedelta

import pytest

from tests.utils import crear_ficha, crear_upgd, post


@pytest.fixture
def ficha_id(db, digitador):
    return crear_ficha(db, crear_upgd(db), digitador["id"])


def test_agregar_laboratorio_devuelve_tabla(client, db, ficha_id):
    r = post(client, f"/fichas/{ficha_id}/laboratorios",
             {"prueba": "IgM Dengue", "muestra": "Suero", "fecha_toma": date.today().isoformat()},
             headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "IgM Dengue" in r.text
    assert "<html" not in r.text
    assert len(db.list_laboratorios(ficha_id)) == 1


def test_agregar_laboratorio_sin_prueba_es_422(client, db, ficha_id):
    r = post(client, f"/fichas/{ficha_id}/laboratorios", {"muestra": "Suero"},
             headers={"HX-Request": "true"})
    assert r.status_code == 422
    assert "Este campo es obligatorio." in r.text
    assert 'value="Suero"' in r.text
    assert db.list_laboratorios(ficha_id) == []


def test_agregar_laboratorio_con_fecha_futura_es_422(client, db, ficha_id):
    manana = (date.today() + timedelta(days=1)).isoformat()
    r = post(client, f"/fichas/{ficha_id}/laboratorios", {"prueba": "IgM", "fecha_toma": manana})
    assert r.status_code == 422
    assert db.list_laboratorios(ficha_id) == []


def test_quitar_laboratorio(client, db, ficha_id):
    lab_id = db.add_laboratorio(ficha_id, {"prueba": "IgM"})
    r = post(client, f"/fichas/{ficha_id}/laboratorios/{lab_id}/eliminar")
    assert r.status_code == 200
    assert "Sin resultados registrados aún." in r.text
    assert db.get_laboratorio(lab_id) is None


def test_no_se_quita_laboratorio_de_otra_ficha(client, db, digitador, ficha_id):
    otra = crear_ficha(db, crear_upgd(db, "Otra"), digitador["id"])
    lab_ajeno = db.add_laboratorio(otra, {"prueba": "IgG"})
    r = post(client, f"/fichas/{ficha_id}/laboratorios/{lab_ajeno}/eliminar")
    assert r.status_code == 404
    assert db.get_laboratorio(lab_ajeno) is not None


def test_laboratorio_en_ficha_inexistente_404(client, digitador):
    assert post(client, "/fichas/999/laboratorios", {"prueba": "IgM"}).status_code == 404
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_laboratorios.py -v`
Expected: FAIL; las rutas responden 404/405.

- [ ] **Step 3: Implementar**

En `sivigila/routes/fichas.py`, cambiar el import de validación:

```python
from ..validacion import comp_de_form, validar_ficha, validar_laboratorio
```

y agregar al final del archivo:

```python
@router.post("/fichas/{ficha_id}/laboratorios")
async def agregar_laboratorio(request: Request, ficha_id: int,
                              usuario=Depends(require_permiso("gestionar_laboratorios"))):
    ficha = _ficha_o_404(ficha_id)
    form = await request.form()
    datos, errores = validar_laboratorio(form, date.today())
    if errores:
        return render(request, "_laboratorios.html",
                      _contexto_labs(request, ficha, valores=dict(form), errores=errores),
                      status_code=422)
    db.add_laboratorio(ficha_id, datos)
    db.log_action(usuario["id"], "AGREGA_LABORATORIO", f"ficha={ficha_id}")
    return render(request, "_laboratorios.html", _contexto_labs(request, ficha))


@router.post("/fichas/{ficha_id}/laboratorios/{lab_id}/eliminar")
def eliminar_laboratorio(request: Request, ficha_id: int, lab_id: int,
                         usuario=Depends(require_permiso("gestionar_laboratorios"))):
    ficha = _ficha_o_404(ficha_id)
    lab = db.get_laboratorio(lab_id)
    if lab is None or lab["notificacion_id"] != ficha_id:
        raise HTTPException(status_code=404)
    db.delete_laboratorio(lab_id)
    db.log_action(usuario["id"], "ELIMINA_LABORATORIO", f"ficha={ficha_id} lab={lab_id}")
    return render(request, "_laboratorios.html", _contexto_labs(request, ficha))
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `python -m pytest -v`
Expected: todos pasan (test_laboratorios: 6 passed).

- [ ] **Step 5: Commit**

```bash
git add sivigila tests
git commit -m "feat: laboratorios por ficha con HTMX y verificación de pertenencia"
```

---

### Task 8: Listado de fichas con búsqueda y paginación

**Files:**
- Create: `sivigila/routes/listado.py`, `sivigila/templates/listado.html`, `sivigila/templates/_listado_resultados.html`, `tests/test_listado.py`
- Modify: `sivigila/main.py` (incluir router `listado`)

**Interfaces:**
- Consumes: `db.list_notificaciones(filtro_texto, codigo_evento, limite, offset)`, `db.count_notificaciones(filtro_texto, codigo_evento)` (Task 1).
- Produces: `GET /listado`, `GET /listado/resultados?q=&evento=&pagina=` (parcial). `POR_PAGINA = 50`. Cada fila lleva `class="fila-ficha"`.

- [ ] **Step 1: Escribir los tests**

`tests/test_listado.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_listado.py -v`
Expected: FAIL; `/listado` responde 404.

- [ ] **Step 3: Rutas**

`sivigila/routes/listado.py`:

```python
from math import ceil

from fastapi import APIRouter, Depends, Request

from .. import db
from ..auth import require_permiso
from ..web import render

router = APIRouter()
permiso = require_permiso("ver_reportes")
POR_PAGINA = 50


def _contexto_resultados(request: Request) -> dict:
    q = request.query_params.get("q", "").strip()
    evento = request.query_params.get("evento") or None
    try:
        pagina = int(request.query_params.get("pagina", "1"))
    except ValueError:
        pagina = 1
    total = db.count_notificaciones(q, evento)
    paginas = max(1, ceil(total / POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    filas = db.list_notificaciones(q, evento, limite=POR_PAGINA, offset=(pagina - 1) * POR_PAGINA)
    return {"filas": filas, "total": total, "pagina": pagina, "paginas": paginas,
            "q": q, "evento": evento or ""}


@router.get("/listado")
def listado(request: Request, usuario=Depends(permiso)):
    ctx = _contexto_resultados(request)
    ctx.update(activo="listado", eventos=db.list_eventos())
    return render(request, "listado.html", ctx)


@router.get("/listado/resultados")
def resultados(request: Request, usuario=Depends(permiso)):
    return render(request, "_listado_resultados.html", _contexto_resultados(request))
```

En `sivigila/main.py`:

```python
from .routes import dashboard, fichas, listado, login, upgd
```

```python
    for modulo in (login, dashboard, upgd, fichas, listado):
        app.include_router(modulo.router)
```

- [ ] **Step 4: Plantillas**

`sivigila/templates/listado.html`:

```html
{% extends "base.html" %}
{% block titulo %}Fichas registradas{% endblock %}
{% block contenido %}
<h1>Fichas registradas</h1>
<p class="sub">Busca, filtra, edita o continúa el diligenciamiento de una notificación.</p>
<form id="filtros" class="barra" method="get" action="/listado"
      hx-get="/listado/resultados" hx-target="#resultados" hx-swap="innerHTML"
      hx-trigger="input changed delay:300ms from:#q, change from:#evento, submit">
  <input type="search" id="q" name="q" value="{{ q }}" placeholder="Buscar por nombre, apellido, documento o código de ficha">
  <select id="evento" name="evento">
    <option value="">Todos los eventos</option>
    {% for e in eventos %}
      <option value="{{ e['codigo'] }}" {% if e['codigo'] == evento %}selected{% endif %}>{{ e["codigo"] }} - {{ e["nombre"] }}</option>
    {% endfor %}
  </select>
  <button class="btn secundario">Buscar</button>
  {% if permisos.get("notificar_individual") %}<a class="btn primario" href="/fichas/nueva">Nueva ficha</a>{% endif %}
</form>
<div id="resultados">{% include "_listado_resultados.html" %}</div>
{% endblock %}
```

`sivigila/templates/_listado_resultados.html`:

```html
<p class="nota">{{ total }} ficha{{ "s" if total != 1 }}</p>
{% if filas %}
<table class="tabla">
  <thead><tr><th>Paciente</th><th>Documento</th><th>Evento</th><th>UPGD</th><th>Notificado</th><th>Estado</th><th></th></tr></thead>
  <tbody>
  {% for r in filas %}
    <tr class="fila-ficha">
      <td>{{ ((r["primer_nombre"] or "") ~ " " ~ (r["primer_apellido"] or "")).strip() or "(sin nombre)" }}</td>
      <td>{{ r["tipo_id"] or "" }} {{ r["numero_id"] or "" }}</td>
      <td>{{ r["evento_nombre"] }}</td>
      <td>{{ r["upgd_nombre"] }}</td>
      <td>{{ r["fecha_notificacion"] or "-" }}</td>
      <td><span class="badge {{ 'ok' if r['estado_ficha'] == 'Terminada' else 'pendiente' }}">{{ r["estado_ficha"] }}</span></td>
      <td><a class="btn secundario chico" href="/fichas/{{ r['id'] }}">Abrir</a></td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% if paginas > 1 %}
<nav class="paginacion">
  {% set base = "q=" ~ (q | urlencode) ~ "&evento=" ~ (evento | urlencode) %}
  {% if pagina > 1 %}
    <a class="btn chico" href="/listado?{{ base }}&pagina={{ pagina - 1 }}"
       hx-get="/listado/resultados?{{ base }}&pagina={{ pagina - 1 }}" hx-target="#resultados">Anterior</a>
  {% endif %}
  <span>Página {{ pagina }} de {{ paginas }}</span>
  {% if pagina < paginas %}
    <a class="btn chico" href="/listado?{{ base }}&pagina={{ pagina + 1 }}"
       hx-get="/listado/resultados?{{ base }}&pagina={{ pagina + 1 }}" hx-target="#resultados">Siguiente</a>
  {% endif %}
</nav>
{% endif %}
{% else %}
<p class="nota">No se encontraron fichas con esos criterios.</p>
{% endif %}
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `python -m pytest -v`
Expected: todos pasan (test_listado: 8 passed).

- [ ] **Step 6: Commit**

```bash
git add sivigila tests
git commit -m "feat: listado de fichas con búsqueda en vivo y paginación"
```

---

### Task 9: Gestión de usuarios

**Files:**
- Create: `sivigila/routes/usuarios.py`, `sivigila/templates/usuarios_lista.html`, `sivigila/templates/usuario_form.html`, `sivigila/templates/_permisos.html`, `sivigila/templates/usuario_password.html`, `tests/test_usuarios.py`
- Modify: `sivigila/main.py` (incluir router `usuarios`)

**Interfaces:**
- Consumes: `db.roles_asignables`, `db.puede_gestionar`, `db.create_user(..., debe_cambiar_password=True)`, `db.update_user`, `db.set_user_active`, `db.reset_password` (marca `debe_cambiar`), `auth.MIN_PASSWORD`, `auth.SinPermiso`.
- Produces: `GET /usuarios`, `GET/POST /usuarios/nuevo`, `GET /usuarios/permisos?rol=` (parcial), `GET/POST /usuarios/{id}/editar`, `POST /usuarios/{id}/activo`, `GET/POST /usuarios/{id}/password`. Checkboxes de permisos: `name="perm_<clave>" value="1"`.

- [ ] **Step 1: Escribir los tests**

`tests/test_usuarios.py`:

```python
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
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `python -m pytest tests/test_usuarios.py -v`
Expected: FAIL; `/usuarios*` responde 404.

- [ ] **Step 3: Rutas**

`sivigila/routes/usuarios.py`:

```python
import re

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import auth, db
from ..auth import require_permiso
from ..web import redirigir, render

router = APIRouter()
permiso = require_permiso("gestionar_usuarios")
_FORMATO_USERNAME = re.compile(r"^[A-Za-z0-9._-]{3,30}$")


def _objetivo(actor, user_id: int):
    objetivo = db.get_user_by_id(user_id)
    if objetivo is None:
        raise HTTPException(status_code=404)
    if not db.puede_gestionar(actor, objetivo):
        raise auth.SinPermiso("No puedes gestionar a este usuario: su rol es igual o superior al tuyo.")
    return objetivo


def _permisos_de_form(form) -> dict:
    return {clave: form.get(f"perm_{clave}") == "1" for clave in db.PERMISOS_LABELS}


def _render_form(request, actor, objetivo=None, valores=None, permisos=None, errores=None):
    asignables = db.roles_asignables(actor["rol"])
    if objetivo is not None and objetivo["rol"] not in asignables:
        asignables = asignables + [objetivo["rol"]]
    if valores is None:
        valores = ({"nombre_completo": objetivo["nombre_completo"], "rol": objetivo["rol"]}
                   if objetivo else {"rol": asignables[0]})
    if permisos is None:
        permisos = db.get_permisos(objetivo) if objetivo else db.permisos_por_defecto(valores["rol"])
    return render(request, "usuario_form.html", {
        "activo": "usuarios",
        "objetivo": objetivo,
        "valores": valores,
        "permisos_usuario": permisos,
        "permisos_labels": db.PERMISOS_LABELS,
        "roles": asignables,
        "errores": errores or {},
        "min_password": auth.MIN_PASSWORD,
    })


@router.get("/usuarios")
def lista(request: Request, usuario=Depends(permiso)):
    filas = [
        {"fila": u, "puede": db.puede_gestionar(usuario, u), "es_yo": u["id"] == usuario["id"]}
        for u in db.list_users()
    ]
    return render(request, "usuarios_lista.html", {
        "activo": "usuarios",
        "usuarios": filas,
        "puede_crear": bool(db.roles_asignables(usuario["rol"])),
        "mensaje": "Cambios guardados." if request.query_params.get("ok") else None,
    })


@router.get("/usuarios/permisos")
def permisos_por_rol(request: Request, rol: str = "", usuario=Depends(permiso)):
    return render(request, "_permisos.html", {
        "permisos_usuario": db.permisos_por_defecto(rol),
        "permisos_labels": db.PERMISOS_LABELS,
    })


@router.get("/usuarios/nuevo")
def nuevo_form(request: Request, usuario=Depends(permiso)):
    if not db.roles_asignables(usuario["rol"]):
        raise auth.SinPermiso("Tu rol no puede crear usuarios.")
    return _render_form(request, usuario)


@router.post("/usuarios/nuevo")
async def crear(request: Request, usuario=Depends(permiso)):
    if not db.roles_asignables(usuario["rol"]):
        raise auth.SinPermiso("Tu rol no puede crear usuarios.")
    form = await request.form()
    username = str(form.get("username", "")).strip()
    nombre = str(form.get("nombre_completo", "")).strip()
    password = str(form.get("password", ""))
    rol = str(form.get("rol", ""))
    permisos = _permisos_de_form(form)

    errores = {}
    if not username:
        errores["username"] = "Este campo es obligatorio."
    elif not _FORMATO_USERNAME.match(username):
        errores["username"] = "Usa de 3 a 30 letras, números, punto, guion o guion bajo."
    elif db.username_exists(username):
        errores["username"] = "Ese código de usuario ya existe."
    if not nombre:
        errores["nombre_completo"] = "Este campo es obligatorio."
    if len(password) < auth.MIN_PASSWORD:
        errores["password"] = f"Debe tener al menos {auth.MIN_PASSWORD} caracteres."
    if rol not in db.roles_asignables(usuario["rol"]):
        errores["rol"] = "No puedes asignar ese rol."
    if errores:
        valores = {"username": username, "nombre_completo": nombre,
                   "rol": rol if rol in db.ROLES_DISPONIBLES else db.roles_asignables(usuario["rol"])[0]}
        return _render_form(request, usuario, valores=valores, permisos=permisos, errores=errores)

    db.create_user(username, password, nombre, rol=rol, permisos=permisos,
                   creado_por=usuario["id"], debe_cambiar_password=True)
    db.log_action(usuario["id"], "CREA_USUARIO", username)
    return redirigir("/usuarios?ok=1")


@router.get("/usuarios/{user_id}/editar")
def editar_form(request: Request, user_id: int, usuario=Depends(permiso)):
    return _render_form(request, usuario, objetivo=_objetivo(usuario, user_id))


@router.post("/usuarios/{user_id}/editar")
async def editar(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    form = await request.form()
    nombre = str(form.get("nombre_completo", "")).strip()
    rol = str(form.get("rol", ""))
    permisos = _permisos_de_form(form)

    errores = {}
    if not nombre:
        errores["nombre_completo"] = "Este campo es obligatorio."
    if rol not in db.roles_asignables(usuario["rol"]) and rol != objetivo["rol"]:
        errores["rol"] = "No puedes asignar ese rol."
    if errores:
        valores = {"nombre_completo": nombre, "rol": objetivo["rol"]}
        return _render_form(request, usuario, objetivo=objetivo, valores=valores,
                            permisos=permisos, errores=errores)

    db.update_user(user_id, nombre_completo=nombre, rol=rol, permisos=permisos)
    db.log_action(usuario["id"], "EDITA_USUARIO", f"id={user_id}")
    return redirigir("/usuarios?ok=1")


@router.post("/usuarios/{user_id}/activo")
async def cambiar_activo(request: Request, user_id: int, usuario=Depends(permiso)):
    _objetivo(usuario, user_id)
    if user_id == usuario["id"]:
        raise auth.SinPermiso("No puedes desactivarte a ti mismo.")
    form = await request.form()
    activo = form.get("activo") == "1"
    db.set_user_active(user_id, activo)
    db.log_action(usuario["id"], "ACTIVA_USUARIO" if activo else "DESACTIVA_USUARIO", f"id={user_id}")
    return redirigir("/usuarios?ok=1")


@router.get("/usuarios/{user_id}/password")
def password_form(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    return render(request, "usuario_password.html",
                  {"activo": "usuarios", "objetivo": objetivo, "error": None,
                   "min_password": auth.MIN_PASSWORD})


@router.post("/usuarios/{user_id}/password")
async def restablecer_password(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    form = await request.form()
    password = str(form.get("password", ""))
    if len(password) < auth.MIN_PASSWORD:
        return render(request, "usuario_password.html", {
            "activo": "usuarios", "objetivo": objetivo, "min_password": auth.MIN_PASSWORD,
            "error": f"Debe tener al menos {auth.MIN_PASSWORD} caracteres.",
        })
    db.reset_password(user_id, password, debe_cambiar=True)
    db.log_action(usuario["id"], "RESET_PASSWORD", f"id={user_id}")
    return redirigir("/usuarios?ok=1")
```

En `sivigila/main.py`:

```python
from .routes import dashboard, fichas, listado, login, upgd, usuarios
```

```python
    for modulo in (login, dashboard, upgd, fichas, listado, usuarios):
        app.include_router(modulo.router)
```

- [ ] **Step 4: Plantillas**

`sivigila/templates/usuarios_lista.html`:

```html
{% extends "base.html" %}
{% block titulo %}Usuarios{% endblock %}
{% block contenido %}
<h1>Gestión de usuarios</h1>
<p class="sub">Crea usuarios, asígnales un rol y personaliza sus permisos. Solo puedes gestionar usuarios de rango inferior al tuyo.</p>
{% if mensaje %}<p class="alerta exito">{{ mensaje }}</p>{% endif %}
{% if puede_crear %}<p><a class="btn primario" href="/usuarios/nuevo">Crear nuevo usuario</a></p>{% endif %}
<table class="tabla">
  <thead><tr><th>Nombre</th><th>Usuario</th><th>Rol</th><th>Estado</th><th></th></tr></thead>
  <tbody>
  {% for u in usuarios %}
    {% set f = u.fila %}
    <tr id="usuario-{{ f['id'] }}">
      <td>{{ f["nombre_completo"] }}</td>
      <td>{{ f["username"] }}</td>
      <td>{{ rol_labels.get(f["rol"], f["rol"]) }}</td>
      <td>{% if f["activo"] %}<span class="badge ok">Activo</span>{% else %}<span class="badge inactivo">Inactivo</span>{% endif %}</td>
      <td>
        {% if u.puede %}
          <a class="btn secundario chico" href="/usuarios/{{ f['id'] }}/editar">Editar</a>
          <a class="btn chico" href="/usuarios/{{ f['id'] }}/password">Clave</a>
          {% if not u.es_yo %}
          <form method="post" action="/usuarios/{{ f['id'] }}/activo" class="en-linea">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="hidden" name="activo" value="{{ 0 if f['activo'] else 1 }}">
            <button class="btn chico {{ 'peligro' if f['activo'] else 'exito' }}">{{ "Desactivar" if f["activo"] else "Activar" }}</button>
          </form>
          {% endif %}
        {% else %}
          <span class="nota">Sin permisos sobre este usuario</span>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`sivigila/templates/_permisos.html`:

```html
{% for clave, etiqueta in permisos_labels.items() %}
  <label class="campo-check"><input type="checkbox" name="perm_{{ clave }}" value="1" {% if permisos_usuario.get(clave) %}checked{% endif %}> {{ etiqueta }}</label>
{% endfor %}
```

`sivigila/templates/usuario_form.html`:

```html
{% extends "base.html" %}
{% block titulo %}Usuarios{% endblock %}
{% block contenido %}
<h1>{{ "Editar usuario" if objetivo else "Crear nuevo usuario" }}</h1>
{% if errores %}<p class="alerta error">Revisa los campos marcados.</p>{% endif %}
<form method="post" action="{{ '/usuarios/%d/editar' % objetivo['id'] if objetivo else '/usuarios/nuevo' }}" class="tarjeta" style="max-width: 560px;">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

  <div class="campo{% if errores.get('username') %} con-error{% endif %}">
    <label for="username">Código de usuario</label>
    {% if objetivo %}
      <input type="text" id="username" value="{{ objetivo['username'] }}" disabled>
    {% else %}
      <input type="text" id="username" name="username" value="{{ valores.get('username') or '' }}" required>
    {% endif %}
    {% if errores.get("username") %}<p class="campo-error">{{ errores.get("username") }}</p>{% endif %}
  </div>

  <div class="campo{% if errores.get('nombre_completo') %} con-error{% endif %}">
    <label for="nombre_completo">Nombre completo</label>
    <input type="text" id="nombre_completo" name="nombre_completo" value="{{ valores.get('nombre_completo') or '' }}">
    {% if errores.get("nombre_completo") %}<p class="campo-error">{{ errores.get("nombre_completo") }}</p>{% endif %}
  </div>

  {% if not objetivo %}
  <div class="campo{% if errores.get('password') %} con-error{% endif %}">
    <label for="password">Contraseña inicial (mínimo {{ min_password }} caracteres)</label>
    <input type="password" id="password" name="password" autocomplete="new-password">
    {% if errores.get("password") %}<p class="campo-error">{{ errores.get("password") }}</p>{% endif %}
    <p class="nota">El usuario deberá cambiarla en su primer ingreso.</p>
  </div>
  {% endif %}

  <div class="campo{% if errores.get('rol') %} con-error{% endif %}">
    <label for="rol">Rol</label>
    <select id="rol" name="rol" hx-get="/usuarios/permisos" hx-target="#permisos" hx-swap="innerHTML">
      {% for r in roles %}
        <option value="{{ r }}" {% if r == valores.get('rol') %}selected{% endif %}>{{ rol_labels.get(r, r) }}</option>
      {% endfor %}
    </select>
    {% if errores.get("rol") %}<p class="campo-error">{{ errores.get("rol") }}</p>{% endif %}
  </div>

  <h2>Permisos</h2>
  <div id="permisos" class="checks">{% include "_permisos.html" %}</div>

  <div class="acciones">
    <button class="btn primario">Guardar</button>
    <a class="btn" href="/usuarios">Cancelar</a>
  </div>
</form>
{% endblock %}
```

`sivigila/templates/usuario_password.html`:

```html
{% extends "base.html" %}
{% block titulo %}Restablecer contraseña{% endblock %}
{% block contenido %}
<h1>Restablecer contraseña</h1>
<p class="sub">Nueva contraseña para {{ objetivo["nombre_completo"] }}. Deberá cambiarla en su próximo ingreso.</p>
<form method="post" action="/usuarios/{{ objetivo['id'] }}/password" class="tarjeta" style="max-width: 460px;">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <div class="campo{% if error %} con-error{% endif %}">
    <label for="password">Nueva contraseña (mínimo {{ min_password }} caracteres)</label>
    <input type="password" id="password" name="password" autocomplete="new-password" required>
    {% if error %}<p class="campo-error">{{ error }}</p>{% endif %}
  </div>
  <div class="acciones">
    <button class="btn primario">Guardar nueva contraseña</button>
    <a class="btn" href="/usuarios">Cancelar</a>
  </div>
</form>
{% endblock %}
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `python -m pytest -v`
Expected: todos pasan (test_usuarios: 11 passed).

- [ ] **Step 6: Commit**

```bash
git add sivigila tests
git commit -m "feat: gestión de usuarios con jerarquía de roles validada en el servidor"
```

---

### Task 10: Matriz de permisos por ruta

**Files:**
- Create: `tests/test_permisos.py`

**Interfaces:**
- Consumes: todas las rutas de las Tasks 2–9.
- Produces: la red de seguridad que garantiza el criterio de éxito 2 del spec (403 en toda ruta sin permiso).

- [ ] **Step 1: Escribir los tests**

`tests/test_permisos.py`:

```python
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
```

- [ ] **Step 2: Correr los tests**

Run: `python -m pytest tests/test_permisos.py -v`
Expected: todos pasan. Si alguna ruta falla, el mensaje de la aserción dice cuál; corrige el `Depends(require_permiso(...))` de esa ruta (no el test) y vuelve a correr.

- [ ] **Step 3: Correr la suite completa**

Run: `python -m pytest`
Expected: todos pasan, 0 fallos.

- [ ] **Step 4: Commit**

```bash
git add tests/test_permisos.py
git commit -m "test: matriz de permisos por ruta, sesión y auditoría de acceso denegado"
```

---

### Task 11: Retirar la app de escritorio y documentar

**Files:**
- Delete: `app.py`, `database.py`
- Modify: `requirements.txt` (quitar `customtkinter`), `README.md`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: repo solo con la versión web; README con instrucciones de ejecución.

- [ ] **Step 1: Confirmar que nada importa los módulos de escritorio**

Run: `git grep -n -E "import database|from database|customtkinter" -- sivigila tests`
Expected: sin resultados.

- [ ] **Step 2: Borrar la app de escritorio y su dependencia**

```powershell
git rm app.py database.py
```

`requirements.txt` queda:

```
fastapi>=0.115
uvicorn[standard]>=0.30
jinja2>=3.1
python-multipart>=0.0.9
itsdangerous>=2.2
```

- [ ] **Step 3: Actualizar el README**

Leer `README.md` completo. Reemplazar las secciones de instalación, ejecución, credenciales y estructura (todo lo que mencione `python app.py`, CustomTkinter, la carpeta `sivigila_moderno/` o muestre contraseñas) por:

````markdown
## Requisitos

- Python 3.13

## Instalación

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Ejecución local

```powershell
$env:SIVIGILA_SECRET_KEY = "<una cadena larga y aleatoria>"   # opcional en local; obligatoria fuera de tu máquina
uvicorn sivigila.main:app --reload
```

Abre http://127.0.0.1:8000. La base `sivigila.db` se crea sola en la raíz del repo (no se versiona).

Al crear una base nueva se siembran dos usuarios: `admin` (super administrador) y `SIVIGILA`
(digitador). Las contraseñas iniciales están en `sivigila/db.py` (`_seed_admin`) y ambos deben
cambiarla en su primer ingreso.

| Variable | Para qué |
|---|---|
| `SIVIGILA_SECRET_KEY` | Firma de la cookie de sesión. Sin ella se usa una clave de desarrollo y se avisa en el log. |
| `SIVIGILA_DB_PATH` | Ruta de la base SQLite (por defecto `sivigila.db` en la raíz). |
| `SIVIGILA_COOKIE_SECURE` | `1` para marcar la cookie como `Secure` (cuando haya HTTPS). |

## Tests

```powershell
python -m pytest
```

## Estructura

```
sivigila/
├─ main.py          app FastAPI, middleware y manejo de errores
├─ db.py            única capa que habla con SQLite
├─ auth.py          sesión, CSRF, permisos por ruta, bloqueo de login
├─ validacion.py    validación de formularios
├─ catalogos.py     campos de cada formulario
├─ web.py           helpers de render
├─ routes/          un archivo por pantalla
├─ templates/       plantillas Jinja2 (los parciales HTMX empiezan con _)
└─ static/          CSS, JS de pestañas y htmx.min.js
tests/              pytest
docs/superpowers/   spec y plan de la migración web
```
````

- [ ] **Step 4: Verificación final**

Run: `python -m pytest`
Expected: todos pasan, 0 fallos.

Run (en otra terminal, con el venv activo): `uvicorn sivigila.main:app`
Luego: `curl -s -o NUL -w "%{http_code}" http://127.0.0.1:8000/login`
Expected: `200`. Detener uvicorn con Ctrl+C.

Recorrido manual en el navegador (http://127.0.0.1:8000):
1. Entrar como `admin` → te obliga a cambiar la contraseña.
2. Caracterización → crear una UPGD.
3. Notificación individual → guardar ficha de Dengue → cambiar a la pestaña 2 y ver los campos de Dengue → cambiar el evento a Ofídico y ver que la pestaña 2 cambia sin recargar.
4. Pestaña 3 → agregar un laboratorio y quitarlo.
5. Completar y "Terminar" → estado Terminada.
6. Fichas registradas → buscar por nombre mientras escribes.
7. Usuarios → crear un digitador, cerrar sesión, entrar con él (pide cambiar contraseña).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: retirar app de escritorio y documentar la versión web"
```
