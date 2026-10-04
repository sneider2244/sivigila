# SIVIGILA Web — Diseño de migración

- **Fecha:** 2026-10-03
- **Estado:** aprobado en conversación, pendiente revisión del documento
- **Rama:** `feat/migracion-web`

## 1. Contexto y objetivo

Hoy SIVIGILA Moderno es una app de escritorio (CustomTkinter + SQLite) que reproduce el flujo de
notificación de SIVIGILA: login, caracterización de la UPGD, ficha individual (datos básicos,
complementarios por evento, laboratorios), listado y gestión de usuarios.

El objetivo es **reemplazarla por una app web** con las mismas pantallas y flujo, y corregir los
fallos detectados en el análisis.

### Decisiones tomadas

| Tema | Decisión |
|---|---|
| Stack | FastAPI + Jinja2 (render en servidor) + HTMX |
| Usuarios | Una sola institución, varios digitadores; todos ven todas las fichas |
| Despliegue | Solo local por ahora (`uvicorn`) |
| App de escritorio | Se reemplaza: `app.py` se elimina al terminar la migración |
| Alcance | Mismas funciones + corrección de fallos detectados |
| Base de datos | SQLite (se mantiene); base nueva, sin migración de datos (la actual tiene 0 fichas) |

### Criterios de éxito

1. `uvicorn sivigila.main:app` levanta la app y el flujo completo funciona en el navegador: login →
   UPGD → ficha (básicos, complementarios, laboratorios) → terminar → listado → usuarios.
2. Toda ruta protegida responde **403** a un usuario sin el permiso correspondiente, aunque la llame
   directamente por URL.
3. La suite `pytest` pasa completa.
4. `sivigila.db` y `__pycache__/` dejan de estar versionados.

### Fuera de alcance

Docker, PostgreSQL, HTTPS, despliegue en la nube, exportar a Excel, pruebas end-to-end en navegador,
separación de datos por UPGD (multi-institución).

## 2. Estructura

```
sivigila/
├─ sivigila/
│  ├─ __init__.py
│  ├─ main.py          # crea la app FastAPI, monta rutas, estáticos, manejadores de error
│  ├─ db.py            # database.py actual + lista blanca de columnas
│  ├─ auth.py          # sesión, usuario actual, CSRF, require_permiso(), bloqueo de login
│  ├─ validacion.py    # validación de fechas, campos dinámicos por evento
│  ├─ routes/
│  │  ├─ login.py
│  │  ├─ dashboard.py
│  │  ├─ upgd.py
│  │  ├─ fichas.py     # ficha individual + laboratorios
│  │  ├─ listado.py
│  │  └─ usuarios.py
│  ├─ templates/       # base.html (barra lateral por permisos) + una plantilla por pantalla + parciales HTMX
│  └─ static/          # css propio + htmx.min.js versionado (sin CDN)
├─ tests/
├─ requirements.txt
├─ .gitignore          # sivigila.db, __pycache__/, venv/, .venv/
└─ README.md           # actualizado con cómo correr la versión web
```

Principios:

- `db.py` es la única capa que habla con SQLite. Las rutas validan entrada, llaman a `db` y
  renderizan plantilla; no contienen SQL.
- Cada ruta declara su permiso con `Depends(require_permiso("<clave>"))`.
- HTMX solo donde aporta: campos complementarios al cambiar de evento, tabla de laboratorios,
  buscador del listado. El resto son formularios HTML normales.
- Dependencias: `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart`, `itsdangerous`;
  `pytest` y `httpx` para tests. Se elimina `customtkinter`.

## 3. Autenticación y sesión

- `POST /login` usa `verify_password` actual (PBKDF2-SHA256, 200k iteraciones, sal por usuario,
  `compare_digest`).
- Sesión en cookie firmada (`SessionMiddleware` de Starlette, `itsdangerous`) que guarda solo
  `user_id` y el token CSRF. Cookie `HttpOnly`, `SameSite=Lax`; `Secure` configurable para cuando
  haya HTTPS.
- La clave de firma se lee de la variable de entorno `SIVIGILA_SECRET_KEY`. Si no existe, se usa una
  clave de desarrollo y se escribe una advertencia en el log al arrancar.
- En cada petición el usuario se relee de la base: si está inactivo o ya no existe, se cierra la
  sesión y se redirige a `/login`. Cambios de permisos aplican de inmediato.
- **Bloqueo:** 5 intentos fallidos para un mismo username en 10 minutos bloquean ese username por
  10 minutos. Contador en memoria del proceso (suficiente para uso local; se pierde al reiniciar).
- **Credenciales por defecto:**
  - La pantalla de login ya no muestra credenciales.
  - `admin` / `SIVIGILA` se siembran solo si la tabla `usuarios` está vacía (comportamiento actual).
  - Se agrega la columna `debe_cambiar_password` (INTEGER, default 0). Quedan con 1: los dos usuarios
    sembrados (`admin` y `SIVIGILA`, cuyas claves están publicadas en el README), los usuarios que crea
    un admin y los que reciben una contraseña restablecida. Mientras sea 1, cualquier ruta redirige a
    `/cambiar-password` hasta que la cambie.
  - Longitud mínima de contraseña: 6 caracteres (la misma de hoy).
- **CSRF:** token por sesión. Todo formulario lleva `<input type="hidden" name="csrf_token">`; las
  peticiones HTMX lo envían en el encabezado `X-CSRF-Token` (configurado una vez en `base.html`).
  Toda petición `POST`/`DELETE` sin token válido → 403.
- `GET /logout` → `POST /logout` (con CSRF), registra en auditoría solo si hay usuario.

## 4. Autorización

Se conservan `ROLES_JERARQUIA`, `PERMISOS_DEFAULT` y `PERMISOS_LABELS` tal como están.

| Ruta | Permiso requerido |
|---|---|
| `GET /` (dashboard) | `ver_reportes` |
| `GET /listado`, `GET /listado/resultados` | `ver_reportes` |
| `/upgd`, `/upgd/nueva`, `/upgd/{id}`, `/upgd/{id}/activar` | `gestionar_caracterizacion` |
| `GET /fichas/nueva`, `POST /fichas` | `notificar_individual` |
| `GET /fichas/{id}` | `notificar_individual` o `editar_notificaciones` o `ver_reportes` (solo lectura si no tiene `editar_notificaciones`) |
| `POST /fichas/{id}`, `POST /fichas/{id}/terminar`, `POST /fichas/{id}/eliminar` | `editar_notificaciones` |
| `GET /fichas/campos` | `notificar_individual` o `editar_notificaciones` |
| `POST /fichas/{id}/laboratorios`, `POST /fichas/{id}/laboratorios/{lab_id}/eliminar` | `gestionar_laboratorios` |
| `/usuarios/*` | `gestionar_usuarios` + `puede_gestionar(actor, objetivo)` |

- Usuario sin permiso que no tiene ninguna pantalla accesible por defecto: tras el login se le lleva
  a la primera pantalla que sí tenga permitida; si no tiene ninguna, ve una página informativa.
- La barra lateral se arma con los mismos permisos (solo visual; la protección es la del servidor).
- **Corrección:** `roles_asignables(actor)` devuelve solo roles con rango **estrictamente menor** que
  el del actor, excepto `super_admin`, que puede asignar cualquiera. Así coincide con
  `puede_gestionar`. El texto de la UI se ajusta a "rango inferior al tuyo".

## 5. Pantallas

### 5.1 Dashboard (`/`)
Tarjetas de acceso (filtradas por permisos) y barras de casos por evento con
`count_notificaciones_por_evento()`, dibujadas con HTML/CSS (sin librería de gráficos).

### 5.2 UPGD (`/upgd`)
- `/upgd` lista las UPGD configuradas (como hoy). `/upgd/nueva` crea; `/upgd/{id}` edita.
- Formulario con los mismos campos y recursos (checkboxes) que hoy.
- **Corrección:** editar una UPGD la actualiza (`upsert_upgd(data, upgd_id)`) en vez de crear otra.
- "Usar en sesión" (`POST /upgd/{id}/activar`) guarda la UPGD activa en la sesión (`upgd_id`); la
  ficha nueva la usa. Si la sesión no tiene una, se toma la primera UPGD registrada (como hoy).
- Al editar una ficha existente se conserva su `upgd_id` original (hoy se sobrescribía con la UPGD
  activa de la sesión).

### 5.3 Ficha individual (`/fichas/nueva`, `/fichas/{id}`)
- Una página, tres pestañas (Datos básicos, Complementarios, Laboratorios). Cambiar de pestaña es
  solo CSS/JS local: no hay viaje al servidor ni se pierde lo escrito.
- **Complementarios:** se generan desde `eventos.campos_json`. Al cambiar el evento, HTMX llama
  `GET /fichas/campos?evento=<codigo>` y reemplaza solo esa pestaña. Mapeo:
  `si_no` → radio Sí/No, `lista` → `<select>` con sus opciones, `texto` → `<input type="text">`.
- **Guardar:** valida formato y guarda con `estado_ficha = "En proceso"`. Si es nueva, redirige a
  `/fichas/{id}`. Una ficha nueva solo muestra "Guardar"; "Terminar" aparece cuando ya existe.
- **Terminar:** valida completo (obligatorios de básicos y todos los complementarios definidos) y
  pasa a `"Terminada"`. Una ficha terminada sigue siendo editable por quien tenga
  `editar_notificaciones` (igual que hoy).
- **Eliminar:** confirmación dentro de la página (no `alert()`/`confirm()` del navegador). Borra en
  cascada sus laboratorios (FK existente).
- **Laboratorios:** pestaña habilitada solo si la ficha ya tiene id. Agregar/quitar con HTMX
  redibuja la tabla. Al quitar, el servidor verifica que `lab.notificacion_id == id` de la URL;
  si no coincide → 404.
- Edad: se calcula en el servidor desde `fecha_nacimiento` al guardar; ya no es un campo libre.

### 5.4 Listado (`/listado`)
Buscador con `hx-get="/listado/resultados"` y `hx-trigger="keyup changed delay:300ms"`, filtro por
evento, paginación de 50 (`LIMIT/OFFSET` agregado a `list_notificaciones`). Cada fila enlaza a su
ficha y muestra el estado.

### 5.5 Usuarios (`/usuarios`)
Listado, crear, editar (nombre, rol, permisos granulares), activar/desactivar y restablecer
contraseña, todos como páginas o formularios en página (sin diálogos modales del navegador).
Cada acción valida `gestionar_usuarios` y `puede_gestionar`. Al cambiar el rol en el formulario,
HTMX recarga los permisos por defecto de ese rol (`GET /usuarios/permisos?rol=`), igual que hoy
lo hace la ventana de escritorio.

## 6. Capa de datos (`db.py`)

- Parte de `database.py` actual; se conservan esquema, siembra de eventos y funciones.
- **Lista blanca de columnas:** al iniciar se lee `PRAGMA table_info` de `notificaciones`,
  `laboratorios` y `upgd`. `create_notificacion`, `update_notificacion`, `add_laboratorio` y
  `upsert_upgd` lanzan `ValueError` si reciben una clave fuera de la lista. Elimina el riesgo de los
  nombres de columna interpolados con f-string.
- Ruta de la base configurable con `SIVIGILA_DB_PATH` (default: `sivigila.db` en la raíz del repo);
  los tests la apuntan a un archivo temporal.
- `PRAGMA foreign_keys = ON` en cada conexión (necesario para el `ON DELETE CASCADE`).
- Cambios de esquema (`debe_cambiar_password`) se aplican con `ALTER TABLE ... ADD COLUMN` si la
  columna no existe, para no romper una base ya creada.

## 7. Validación y errores

- **Fechas:** `<input type="date">` en el navegador; el servidor valida formato ISO `YYYY-MM-DD`,
  que no sean futuras y el orden lógico: nacimiento ≤ inicio de síntomas ≤ consulta ≤ notificación
  (solo entre las que vengan llenas).
- **Campos dinámicos:** se rechazan claves que no estén en `campos_json` del evento y valores de
  `lista` fuera de sus opciones.
- Si la validación falla, se re-renderiza el mismo formulario con los valores enviados y el mensaje
  junto a cada campo (código 422 para peticiones HTMX, 200 con errores para formularios normales).
- Sin sesión → redirect a `/login`. Sin permiso → página 403 "No tienes permiso para …".
  Registro inexistente → página 404.
- Error no controlado → página 500 genérica; el detalle va al log del servidor **sin datos
  personales del paciente** (solo ruta, id y tipo de excepción) — Ley 1581.
- **Auditoría:** se conservan los `log_action` actuales y se agregan `login_fallido`,
  `login_bloqueado` y `acceso_denegado` (con ruta y permiso, sin datos del paciente).

## 8. Limpieza del repo

- `.gitignore` con `sivigila.db`, `*.db-journal`, `__pycache__/`, `venv/`, `.venv/`.
- `git rm --cached sivigila.db __pycache__/database.cpython-314.pyc`.
- Eliminar `app.py` y `database.py` una vez la web cubra todas las pantallas.
- Limpiar el docstring con texto de prueba (`app.py:13-17`) — desaparece al borrar `app.py`.
- README: cómo crear el venv, instalar, definir `SIVIGILA_SECRET_KEY` y correr
  `uvicorn sivigila.main:app --reload`; ya sin credenciales visibles más allá del admin inicial
  con cambio obligatorio.

## 9. Tests (`pytest` + `fastapi.testclient`)

Cada test usa una base SQLite temporal (`SIVIGILA_DB_PATH` en `tmp_path`).

| Archivo | Cubre |
|---|---|
| `test_db.py` | lista blanca de columnas, hash/verificación, `puede_gestionar`, `roles_asignables`, `upsert_upgd` actualiza |
| `test_auth.py` | login ok/falla, bloqueo tras 5 intentos, usuario inactivo, cambio de contraseña obligatorio, CSRF ausente → 403 |
| `test_permisos.py` | parametrizado: cada ruta protegida devuelve 403 para un usuario sin el permiso |
| `test_fichas.py` | crear → complementarios → laboratorio → terminar → eliminar; validación de fechas; campos dinámicos inválidos; borrar laboratorio de otra ficha → 404 |
| `test_listado.py` | filtro por texto y evento, paginación |

## 10. Orden de construcción (sugerido para el plan)

1. Esqueleto: paquete, `main.py`, `db.py` con lista blanca, `.gitignore`, tests de `db`.
2. Login, sesión, CSRF, `require_permiso`, `base.html` con barra lateral.
3. Dashboard y UPGD.
4. Ficha individual con complementarios y laboratorios.
5. Listado.
6. Usuarios.
7. Retirar `app.py`/`database.py`, actualizar README.
