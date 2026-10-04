# SIVIGILA Moderno 🩺

Versión web moderna del flujo de notificación del Software SIVIGILA
(login → caracterización → notificación individual → datos complementarios →
laboratorio → terminar), construida en **Python** con:

- **FastAPI + Jinja2** → páginas generadas en el servidor; **HTMX** solo para
  las partes que cambian sin recargar (campos complementarios, laboratorios,
  buscador del listado).
- **SQLite** → base de datos local, sin necesidad de instalar un servidor.
- **Login real** → contraseñas con PBKDF2-SHA256 + sal, sesión en cookie
  firmada, protección CSRF y bloqueo tras 5 intentos fallidos.
- **Permisos validados en el servidor** → cada ruta exige su permiso; ocultar
  un botón es solo comodidad visual.
- **Formularios dinámicos** → la pestaña "Datos complementarios" se genera
  según el evento (ya vienen Chagas, Accidente Ofídico y Dengue).

## 1. Requisitos

- Python 3.13

## 2. Instalación

```powershell
git clone https://github.com/sneider2244/sivigila.git
cd sivigila
```

Windows (PowerShell):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Si PowerShell no deja activar el entorno, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Linux / macOS:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 3. Ejecución local

Con el entorno virtual activado:

```powershell
uvicorn sivigila.main:app --reload
```

Abre http://127.0.0.1:8000 e ingresa con uno de estos usuarios:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | Super administrador |
| `SIVIGILA` | `sivigila2026` | Digitador |

Los dos piden cambiar la contraseña en el primer ingreso. Los demás usuarios
se crean desde **Usuarios**.

### La base de datos

El repo **incluye** `sivigila.db`, una base SQLite de prueba que trae esos dos
usuarios, una UPGD de ejemplo y ninguna ficha. Ojo: al usarla la modificas, y
`git status` la va a mostrar como cambiada; no commitees esos cambios.

Para empezar con una base vacía, apunta `SIVIGILA_DB_PATH` a un archivo que no
exista. La app la crea al arrancar y siembra solo el usuario `admin` con
`Admin123!`:

```powershell
$env:SIVIGILA_DB_PATH = "mi-base.db"     # Linux/macOS: export SIVIGILA_DB_PATH=mi-base.db
uvicorn sivigila.main:app --reload
```

### Variables de entorno

Ninguna es obligatoria para correrla en tu máquina.

| Variable | Para qué |
|---|---|
| `SIVIGILA_SECRET_KEY` | Firma de la cookie de sesión. Sin ella se usa una clave de desarrollo y se avisa en el log. |
| `SIVIGILA_DB_PATH` | Ruta de la base SQLite (por defecto `sivigila.db` en la raíz). |
| `SIVIGILA_COOKIE_SECURE` | `1` para marcar la cookie como `Secure` (cuando haya HTTPS). |

## 4. Tests

```powershell
python -m pytest
```

## 5. Roles y permisos

| Rol | Puede... |
|---|---|
| **Super administrador** | Todo, incluso gestionar a otros administradores. |
| **Administrador** | Notificar, caracterización, laboratorios y gestionar usuarios de rango *digitador* o *consulta*. |
| **Digitador** | Diligenciar y editar fichas, laboratorios y caracterización. No administra usuarios. |
| **Consulta** | Panel, listado y fichas en solo lectura. |

Cada usuario tiene además **permisos granulares** que se ajustan desde
**Usuarios → Editar**. Al cambiar el rol, los permisos se cargan con los de
ese rol y luego se pueden ajustar uno por uno. Los usuarios creados por un
administrador, o a quienes se les restablece la clave, deben cambiarla en su
siguiente ingreso.

## 6. Flujo de uso

1. **Login** con código de usuario y contraseña.
2. **Caracterización**: registra o edita la UPGD y márcala "Usar en sesión".
3. **Notificación individual**:
   - Pestaña 1 — Datos básicos del paciente. La edad se calcula sola desde la
     fecha de nacimiento.
   - Pestaña 2 — Datos complementarios según el evento.
   - Pestaña 3 — Laboratorios (disponible cuando la ficha ya está guardada).
4. **Guardar** deja la ficha "En proceso"; **Terminar** valida que esté
   completa y la marca "Terminada".
5. **Fichas registradas**: búsqueda mientras escribes, filtro por evento y
   paginación de 50.
6. **Panel principal**: accesos rápidos y casos notificados por evento.

## 7. Estructura

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

## 8. Cómo agregar un evento con su propio formulario

En `sivigila/db.py`, dentro de `EVENTOS_DEFAULT`, agrega un bloque como:

```python
{
    "codigo": "220",
    "nombre": "Leptospirosis",
    "campos": [
        {"key": "fiebre", "label": "Fiebre", "tipo": "si_no"},
        {"key": "mialgias", "label": "Mialgias", "tipo": "si_no"},
        {"key": "resultado", "label": "Resultado de laboratorio", "tipo": "lista",
         "opciones": ["Positivo", "Negativo", "Pendiente"]},
    ],
},
```

Tipos de campo soportados: `texto`, `si_no`, `lista` (con `opciones`). Los
eventos solo se siembran en una base nueva.

## 9. Notas de seguridad

- Las contraseñas se guardan con `hashlib.pbkdf2_hmac` (200.000 iteraciones,
  sal por usuario).
- La `sivigila.db` del repo es solo de prueba y no tiene fichas. Una base con
  fichas reales contiene datos de pacientes (Ley 1581): nunca se commitea ni se
  comparte. Si vas a registrar datos reales, usa `SIVIGILA_DB_PATH` con una
  ruta fuera del repo.
- Las contraseñas de los usuarios de prueba son públicas: fuera de tu máquina,
  arranca con una base vacía y define `SIVIGILA_SECRET_KEY`.
- Los logs del servidor no incluyen datos de pacientes: solo ruta, método y
  tipo de error.
