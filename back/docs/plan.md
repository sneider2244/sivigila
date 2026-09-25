# Plan de migración a FastAPI

De app de escritorio (CustomTkinter + SQLite) a aplicación web multiusuario.
Este documento es el plan completo y autocontenido. La referencia técnica
durable vive en `architecture.md`, `rules.md` y `domain.md`.

## Estado

- [x] Diagnóstico del legacy
- [x] Decisiones de stack
- [x] **Paso A** — scaffolding de conocimiento (`AGENTS.md` + `docs/`)
- [x] **Paso B** — higiene git (`.gitignore`, destrackear DB/pycache)
- [x] **Fase 1** — scaffolding FastAPI (código listo; pendiente verificar runtime)
- [x] **Fase 2** — dominio + modelos + migración inicial + seeds (código listo; pendiente verificar)
- [x] `pyproject.toml`
- [ ] **Fase 3** en adelante
- [ ] Mover el legacy a rama `legacy-desktop`

## Decisiones cerradas

| Tema | Elección |
|------|----------|
| Frontend | Jinja2 + HTMX (server-rendered) |
| Base de datos | PostgreSQL (SQLAlchemy 2.0 + Alembic) |
| Deploy | Docker + Oracle Cloud Always Free (app + Postgres + Caddy) |
| Auth | Sesión + cookie + CSRF |
| Alcance | Paridad total por fases |

## Stack / dependencias

```
fastapi · uvicorn[standard] · gunicorn          # app + servidor
sqlalchemy>=2.0 · alembic · psycopg[binary]     # datos + migraciones
pydantic-settings · jinja2 · python-multipart   # config + templates + forms
itsdangerous · starlette-csrf                    # sesión + CSRF
pwdlib[argon2]                                   # hashing (o portar PBKDF2)
pytest · pytest-asyncio · httpx · ruff           # calidad
```

## Mapeo legacy → nuevo

| Legacy (`app.py` / `database.py`) | Nuevo |
|-----------------------------------|-------|
| `SivigilaApp.show_frame` (navegación) | Rutas HTTP + `base.html` con sidebar |
| `BaseScreen` + sidebar + permisos | `base.html` + dependency `require_permission()` |
| Cada `XxxFrame` | Router + template + service |
| `messagebox` | Flash messages / errores inline |
| `IndividualFrame` (3 tabs) | 3 rutas/parciales; form dinámico igual (JSON validado) |
| SQL dinámico por dict (`upsert_upgd`, etc.) | Columnas explícitas + Pydantic |
| `_seed_eventos` solo-si-vacío | Migraciones Alembic |
| PBKDF2 a mano | Se reusa (o se sube a argon2) |

## Qué se mejora de raíz

1. **Alembic** → resuelve que agregar un evento no haga nada en una DB existente.
2. **Pydantic** → validación de fechas/edad y fin del SQL armado con `dict.keys()`.
3. **Enums** → `EstadoFicha.TERMINADA` en vez de `"Terminada"`.
4. **Dependency de permisos** → un solo lugar para autorizar, no repetido por frame.
5. **CSRF + sesiones** → obligatorio con formularios + cookies.
6. **Secretos por env** → fuera `Admin123!` hardcodeado en producción.

## Fases

### Fase 0 — Higiene
`.gitignore`, destrackear `sivigila.db` y `__pycache__/`, `pyproject.toml`.
Mover el Tkinter a la rama `legacy-desktop`.
**Entregable**: repo limpio. *(gitignore + destrackeo ya hechos)*

### Fase 1 — Scaffolding
App factory, `config.py` con `.env`, sesión SQLAlchemy, Alembic inicializado,
`base.html` con sidebar + CSS, ruta `/health`.
**Entregable**: `docker compose up` levanta y responde.

### Fase 2 — Dominio + modelos + seeds
Enums (`Rol`, `EstadoFicha`, `TipoCampo`), modelos ORM, migración inicial,
seed de eventos + admin desde env.
**Entregable**: `alembic upgrade head` crea todo.

### Fase 3 — Auth
Login/logout, sesión, `current_user`, `require_permission`, CSRF, rate-limit
en login, auditoría de LOGIN/LOGOUT.
**Entregable**: login real funcionando.

### Fase 4 — Usuarios
CRUD + jerarquía de roles + permisos granulares (paridad con `UsuariosFrame`).

### Fase 5 — UPGD
Caracterización + "usar en sesión" (paridad con `CaracterizacionFrame`).

### Fase 6 — Notificaciones
Datos básicos + formulario dinámico por evento vía HTMX + guardar/terminar/
eliminar (paridad con `IndividualFrame`).

### Fase 7 — Laboratorios
Agregar/listar/eliminar resultados por ficha.

### Fase 8 — Dashboard + Listado + Auditoría
Indicadores por evento, buscador/filtro por evento, bitácora de auditoría.

### Fase 9 — Tests + hardening
pytest (services + routers), security headers, CSRF en todos los POST,
tests de permisos.
**Ojo**: hoy hay 0 tests; esta fase no es opcional.

### Fase 10 — Deploy (Oracle Cloud Always Free)

**Repo**
- `Dockerfile` multi-stage: stage Node compila el SCSS, stage Python copia el
  CSS y corre la app.
- `docker-compose.prod.yml`: `app` (gunicorn + uvicorn workers), `db` (Postgres
  sin puerto expuesto), `caddy` (TLS automático con Let's Encrypt), volúmenes
  persistentes, `restart: unless-stopped`.
- Entrypoint que corre `alembic upgrade head` antes de arrancar.
- `Caddyfile` y `.env.production` (nunca commiteado).

**Oracle**
- VM Ampere A1 (ARM), Ubuntu 24.04, 4 OCPU / 24 GB (always free).
- Security List: ingress 22 / 80 / 443. Las imágenes Ubuntu traen `iptables`
  que también bloquea 80/443; hay que abrirlos ahí.
- Docker + compose plugin, clonar repo,
  `docker compose -f docker-compose.prod.yml up -d --build`.

**Operación**
- Backups: `pg_dump` por cron a Object Storage + rotación.
- Actualizar: `git pull && docker compose -f docker-compose.prod.yml up -d --build`.
- Hardening: SSH con clave, sin root, fail2ban.

**Advertencias**
- Capacidad ARM: Oracle a veces responde "Out of host capacity" al crear la VM;
  reintentar o esperar. Los micro AMD (1 GB) quedan chicos para Postgres+app.
- Se necesita un dominio propio para HTTPS válido (~US$10/año). Oracle da IP
  pública, no dominio.
- La imagen debe ser multi-arch (arm64); `python:3.12-slim`, Node y dart-sass
  soportan ARM.

## Estrategia de testing

- **Unit**: services (permisos, workflow de ficha, validación de campos dinámicos).
- **Integración**: routers con `httpx.TestClient` (login requerido, 403 sin
  permiso, CSRF).
- **DB de test**: SQLite in-memory para velocidad; 1 test de integración
  contra Postgres en CI.

## Mapa de rutas

```
GET/POST /login                     POST /logout
GET /                               dashboard + indicadores
GET/POST /upgd                      POST /upgd/{id}/activar
GET /notificaciones                 GET /notificaciones/nueva
POST /notificaciones                GET/POST /notificaciones/{id}
POST /notificaciones/{id}/terminar  POST /notificaciones/{id}/eliminar
GET  /notificaciones/campos-complementarios?evento=XXX   # partial HTMX
POST /notificaciones/{id}/laboratorios   DELETE /notificaciones/{id}/laboratorios/{lab_id}
GET/POST /usuarios                  /usuarios/nuevo | /{id}/editar | /{id}/clave | /{id}/activar
```

Autorización centralizada: dependency `require_permission("...")`.

## Fuera de alcance (por ahora)

- Export/import al formato nacional SIVIGILA (`codigo_ficha`, `ajuste`,
  `semana`). Si se necesita, diseñarlo en la Fase 2, no después.
- UI de gestión de eventos (se agregan por migración).
- Recuperación de contraseña por email.

## Riesgos

- Repo público con credenciales por defecto: rotar y limpiar historial antes
  de producción.
- El legacy se conserva en la rama `legacy-desktop` hasta cerrar la migración.

## Decisiones pendientes

- **Fase 3**: portar PBKDF2 tal cual vs subir a **argon2**.
- **Fase 3**: sesiones **server-side** (tabla `sesiones`, revocables) vs
  **cookie firmada** (más simple).

## Documentos relacionados

- `architecture.md` — capas, estructura de carpetas, modelo de datos.
- `rules.md` — convenciones y constraints obligatorios.
- `domain.md` — roles, permisos, estados, campos dinámicos, seeds.
