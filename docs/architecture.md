# Arquitectura

## Estado actual (legacy)

App de escritorio monolítica en Python:

- `app.py` (1145 líneas) — toda la UI CustomTkinter + navegación + lógica de
  negocio mezclada en los frames.
- `database.py` (536 líneas) — esquema SQLite, seeds, hashing y CRUD.
- `sivigila.db` — SQLite local, versionado por error.

Problemas: sin tests, sin migraciones, SQL armado desde `dict.keys()`, magic
strings, y la UI y el dominio acoplados. No soporta multiusuario en red.

## Arquitectura objetivo

Web, server-rendered, con capas explícitas:

```
Request → Router (web/) → Service (services/) → ORM (db/models) → PostgreSQL
                ↓
           Template (Jinja2 + HTMX)
```

### Capas

| Capa | Responsabilidad | Puede importar |
|------|-----------------|----------------|
| `web/` | HTTP: routers, templates, deps (auth/permisos) | `services/`, `domain/` |
| `services/` | Lógica de negocio, transacciones | `db/`, `domain/` |
| `domain/` | Enums, reglas puras, schemas Pydantic | nada (sin framework) |
| `db/` | Modelos SQLAlchemy, sesión, seeds | `domain/` |

Regla dura: **el dominio y los servicios NO importan FastAPI ni Jinja2.**
La UI nunca habla directo con la base.

### Estructura de carpetas

```
sivigila/
├── app/
│   ├── main.py              # app factory, routers, lifespan
│   ├── config.py            # Settings (pydantic-settings) + .env
│   ├── db/
│   │   ├── session.py       # engine + session
│   │   ├── models.py        # ORM: Usuario, Upgd, Evento, Notificacion, Laboratorio, Auditoria
│   │   └── seed.py          # eventos + admin (desde env)
│   ├── domain/
│   │   ├── enums.py         # Rol, EstadoFicha, TipoCampo
│   │   ├── permissions.py   # jerarquía de roles y permisos
│   │   └── schemas.py       # Pydantic (validación)
│   ├── services/
│   │   ├── auth.py · usuarios.py · upgd.py
│   │   └── eventos.py · notificaciones.py · laboratorios.py · auditoria.py
│   └── web/
│       ├── deps.py          # current_user + require_permission()
│       ├── routers/         # auth, dashboard, upgd, notificaciones, laboratorios, usuarios
│       ├── templates/       # Jinja2 (base.html + una por pantalla)
│       └── static/
├── migrations/              # Alembic
├── tests/
├── docs/
└── docker-compose.yml
```

## Decisiones

| Decisión | Elección | Por qué |
|----------|----------|---------|
| Frontend | Jinja2 + HTMX | La app es formularios CRUD; evita duplicar validaciones y toolchain de Node. Interactividad puntual (form dinámico por evento) vía partial HTMX. |
| Base de datos | PostgreSQL | Multiusuario real en red, concurrencia, integridad y backups. |
| ORM | SQLAlchemy 2.0 | Modelos tipados, fin del SQL por `dict.keys()`. |
| Migraciones | Alembic | Hoy agregar un evento no hace nada en una DB existente; Alembic lo resuelve. |
| Auth | Sesión + cookie + CSRF | Server-rendered con formularios; más simple y seguro que JWT. |
| Deploy | Docker + VPS | Compose: app + Postgres + nginx. Reproducible. |

## Modelo de datos

Se portan las 6 tablas existentes: `usuarios`, `upgd`, `eventos`,
`notificaciones`, `laboratorios`, `auditoria`.

- `eventos.campos_json` se mantiene (formularios dinámicos por evento), pero
  validado con Pydantic contra `TipoCampo` (`texto | si_no | lista`).
- `notificaciones.datos_complementarios` sigue siendo JSON.
- Se agrega tabla `sesiones` si se opta por sesiones server-side revocables.
- No hay datos reales que migrar: solo seeds (2 usuarios, 1 UPGD, 3 eventos).

## Flujo de una notificación

1. Login → sesión.
2. Caracterización de UPGD → se marca una como activa en sesión.
3. Notificación individual:
   - Página 1: datos básicos del paciente.
   - Página 2: datos complementarios, generados según el evento elegido
     (partial HTMX al cambiar el combo de evento).
   - Página 3: laboratorios (requiere ficha guardada).
4. Guardar → `En proceso`; Terminar → `Terminada`.
