# SIVIGILA — Instrucciones para agentes

Simulador educativo del Sistema de Vigilancia en Salud Pública (SIVIGILA) de Colombia. Repo con dos subproyectos independientes:

- `front/` — Frontend Next.js 16 (App Router, SPA/SSR). Leé `front/AGENTS.md` antes de tocar código ahí.
- `back/` — Backend FastAPI (API REST) + PostgreSQL + Redis. Leé `docs/BACKEND_ARCH.md`.

## Documentación obligatoria (leer antes de tocar código)

- `docs/PROJECT_PLAN.md` — objetivos, estrategia y cronograma (4 sprints).
- `docs/FRONTEND_ARCH.md` — stack, estructura, SCSS y componentes frontend.
- `docs/BACKEND_ARCH.md` — stack, estructura, modelos de datos y RBAC backend.
- `docs/BACKEND_SUBAGENT_PROMPT.md` — prompt de delegación para el sub-agente backend.

## Arquitectura (fuente de verdad: `docs/`)

```
Next.js (SSR, SCSS, React Hook Form)  →  FastAPI (JWT, RBAC, Pydantic)  →  PostgreSQL (JSONB) + Redis (token blacklist)
```

- El frontend es una SPA/SSR en `front/`; NO es server-rendered por Jinja2. La decisión anterior (Jinja2/HTMX) quedó descartada.
- El backend expone API REST bajo `back/app/api/v1/endpoints/`. Estructura layered (`api/`, `core/`, `db/`, `models/`, `schemas/`), no hexagonal.

### Roles RBAC (6)

`UPGD`, `UI`, `MUNICIPAL`, `DEPARTAMENTAL`, `NACIONAL`, `DOCENTE`. Ver matriz en `docs/PROJECT_PLAN.md`.

## Comandos

### `front/`

- Dev: `npm run dev` · Lint: `npm run lint` · Build: `npm run build`

### `back/`

- Dev: `uvicorn app.main:app --reload`
- Tests: `pytest` · Lint: `ruff check .` · Formato: `ruff format .`
- Migraciones: `alembic upgrade head` / `alembic revision --autogenerate -m "..."`
- Seed (idempotente: usuario DOCENTE + catálogos + UPGD demo): `python -m app.db.seed`
- Limpieza de datos demo (borra fichas/escenarios/asignaciones/estudiantes; conserva catálogos, UPGD demo y DOCENTE): `python -m app.db.clean`

## Convenciones de arquitectura (obligatorias)

- Enums, no strings (`RolEnum.UPGD`, `clasificacion_caso`); Pydantic valida todo input; SQL con columnas explícitas (nunca `", ".join(keys)`).
- Cambios de esquema SOLO por migración Alembic. Secretos por variables de entorno.
- Datos complementarios dinámicos van en columnas JSONB (`FichaDatosComplementarios.contenido`).

## Git

- Commits convencionales, sin atribución de IA ni `Co-Authored-By`.
- Nunca commitear `.db`, `.env`, `__pycache__/`, `node_modules/` ni secretos.
- No commitear sin pedido explícito.
