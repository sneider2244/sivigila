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
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent


def _db_path() -> str:
    return os.environ.get("SIVIGILA_DB_PATH") or str(RAIZ_REPO / "sivigila.db")


# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------

def normalizar(texto):
    """Minúsculas y sin tildes, para buscar 'perez' y encontrar 'PÉREZ'."""
    if texto is None:
        return None
    descompuesto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").casefold()


@contextmanager
def get_conn():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.create_function("normalizar", 1, normalizar, deterministic=True)
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
    sesion_version        INTEGER NOT NULL DEFAULT 0,
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
        # Bases de la versión de escritorio: sus claves (incluidas las sembradas, que están
        # publicadas en el README y en el historial de git) se deben cambiar al primer ingreso.
        conn.execute("UPDATE usuarios SET debe_cambiar_password = 1")
    if "sesion_version" not in columnas:
        conn.execute("ALTER TABLE usuarios ADD COLUMN sesion_version INTEGER NOT NULL DEFAULT 0")


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
    """Cambia la clave y cierra todas las sesiones abiertas del usuario."""
    pw_hash, salt = _hash_password(new_password)
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET password_hash = ?, salt = ?, debe_cambiar_password = ?, "
            "sesion_version = sesion_version + 1 WHERE id = ?",
            (pw_hash, salt, 1 if debe_cambiar else 0, user_id),
        )


def invalidar_sesiones(user_id):
    """Hace inválidas todas las cookies de sesión emitidas hasta ahora para el usuario."""
    with get_conn() as conn:
        conn.execute("UPDATE usuarios SET sesion_version = sesion_version + 1 WHERE id = ?", (user_id,))


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
        # Sin distinguir mayúsculas ni tildes; '%' y '_' escritos por el usuario son texto.
        sql += r""" AND (normalizar(n.primer_nombre) LIKE ? ESCAPE '\'
                        OR normalizar(n.primer_apellido) LIKE ? ESCAPE '\'
                        OR normalizar(n.numero_id) LIKE ? ESCAPE '\'
                        OR normalizar(n.codigo_ficha) LIKE ? ESCAPE '\')"""
        texto = normalizar(filtro_texto).replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        like = f"%{texto}%"
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
