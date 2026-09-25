# SIVIGILA Moderno — Instrucciones para agentes

Sistema de vigilancia en salud pública. En migración de app de escritorio
(CustomTkinter + SQLite) a aplicación web.

## Stack

FastAPI · Jinja2 + HTMX · PostgreSQL · SQLAlchemy 2.0 · Alembic · Docker

## Comandos

- Tests: `pytest`
- Lint: `ruff check .`
- Formato: `ruff format .`
- Migraciones: `alembic upgrade head` / `alembic revision --autogenerate -m "..."`
- Dev: `uvicorn app.main:app --reload`

## Antes de tocar código

Leé `docs/`:

- `docs/architecture.md` — arquitectura objetivo y estructura de carpetas
- `docs/rules.md` — convenciones y constraints (obligatorio)
- `docs/domain.md` — roles, permisos, estados y campos dinámicos
- `docs/plan.md` — fases de la migración y estado actual

## Reglas rápidas

- Nunca commitear sin que lo pidan explícitamente.
- Nunca commitear `sivigila.db`, `.env`, `__pycache__/` ni secretos.
- Seguir `docs/rules.md` al pie de la letra.
- No comentar código salvo que se pida.
