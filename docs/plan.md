# Plan de migración a FastAPI

De app de escritorio (CustomTkinter + SQLite) a aplicación web.

## Estado

- [x] Diagnóstico del legacy
- [x] Decisiones de stack
- [x] **Paso A** — scaffolding de conocimiento (`AGENTS.md` + `docs/`)
- [ ] **Paso B** — higiene git (`.gitignore`, destrackear DB/pycache)
- [ ] Fase 1 en adelante

## Decisiones

- Frontend: Jinja2 + HTMX (server-rendered)
- DB: PostgreSQL (SQLAlchemy 2.0 + Alembic)
- Deploy: Docker + VPS (app + Postgres + nginx)
- Alcance: paridad total por fases

## Fases

| # | Fase | Entregable |
|---|------|------------|
| 0 | Higiene | `.gitignore`, sacar `sivigila.db` y `__pycache__` del tracking, `pyproject.toml` |
| 1 | Scaffolding | App factory, config, SQLAlchemy, Alembic, `base.html`, `/health`, `docker compose up` |
| 2 | Dominio + modelos | Enums, modelos ORM, migración inicial, seeds |
| 3 | Auth | Login/logout, sesión, `current_user`, `require_permission`, CSRF, rate-limit |
| 4 | Usuarios | CRUD + jerarquía + permisos granulares |
| 5 | UPGD | Caracterización + selección activa |
| 6 | Notificaciones | Datos básicos + form dinámico (HTMX) + guardar/terminar/eliminar |
| 7 | Laboratorios | Agregar/listar/eliminar por ficha |
| 8 | Dashboard + Listado + Auditoría | Indicadores, buscador/filtro, bitácora |
| 9 | Tests + hardening | pytest (services + routers), CSRF, headers, permisos |
| 10 | Deploy | Dockerfile multi-stage, compose, gunicorn, backups |

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

- Export/import al formato nacional SIVIGILA (`codigo_ficha`, `ajuste`, `semana`).
  Si se necesita, diseñarlo en la Fase 2, no después.
- UI de gestión de eventos (se agregan por migración).
- Recuperación de contraseña por email.

## Riesgos

- Repo público con credenciales por defecto: rotar y limpiar historial antes de prod.
- Decidir en Fase 3: PBKDF2 portado vs argon2; sesión server-side vs cookie firmada.
- El legacy se conserva en una rama (`legacy-desktop`) hasta cerrar la migración.
