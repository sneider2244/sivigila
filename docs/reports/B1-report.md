# B1 — Scaffold e Infraestructura del Backend SIVIGILA

**Estado:** DONE
**Fecha:** 2026-09-25
**Alcance:** Solo scaffold + infraestructura (sin lógica de negocio).

---

## 1. Resumen ejecutivo

Se creó el esqueleto del backend FastAPI bajo `back/` alineado con `docs/BACKEND_ARCH.md`
(capa `api/` → `core/` → `db/` → `models/` → `schemas/`, NO hexagonal), con motor
asíncrono `asyncpg`, Alembic, Docker Compose (Postgres 16 + Redis 7) y verificación
end-to-end (venv + install editable, containers healthy, `alembic upgrade head`,
`ruff check`, `pytest`, import de `app.main`).

## 2. Archivos creados

```
back/
├── pyproject.toml                  # PEP 621 (pre-existente, verificado)
├── README.md                       # requerido por `readme = "README.md"`
├── .env.example                    # todas las variables de entorno documentadas
├── .gitignore
├── docker-compose.yml              # postgres:16 + redis:7 con healthchecks
├── alembic.ini                     # sqlalchemy.url apuntando a postgres
├── alembic/
│   ├── env.py                      # motor asíncrono (async_engine_from_config)
│   ├── script.py.mako
│   ├── README
│   └── versions/
│       ├── .gitkeep
│       └── 46739a8b908c_initial_baseline.py   # migración baseline vacía
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI + CORS + /health + include v1 router
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py              # api_router (incluye health)
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py       # GET /api/v1/health
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Settings (pydantic-settings)
│   │   └── database.py             # engine async + sessionmaker + Base + get_db
│   ├── db/__init__.py              # base.py / seed_data.py → tareas futuras
│   ├── models/__init__.py          # modelos → tareas futuras
│   └── schemas/__init__.py         # schemas → tareas futuras
└── tests/
    └── test_health.py              # TestClient → GET /health
```

### Contenido clave

- **`app/core/config.py`**: `Settings(BaseSettings)` con `DATABASE_URL`, `REDIS_URL`,
  `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`,
  `CORS_ORIGINS` (parseado como `list[str]`). `env_file=".env"`, `extra="ignore"`.
  Instancia singleton `settings`.
- **`app/core/database.py`**: `create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)`,
  `async_sessionmaker(expire_on_commit=False)`, `Base(DeclarativeBase)` y dependencia
  `get_db()` (AsyncGenerator).
- **`app/main.py`**: `FastAPI(title="SIVIGILA API")`, `CORSMiddleware` con
  `allow_origins=settings.CORS_ORIGINS` (default `http://localhost:3000`), `include_router(api_router, prefix="/api/v1")`
  y `GET /health` global.
- **`app/api/v1/api.py`**: `api_router` que incluye `health.router`.
- **`app/api/v1/endpoints/health.py`**: `GET /health` → `{"status": "ok"}`.

## 3. Versiones resueltas (pip freeze, dependencias directas)

| Dependencia | Versión |
|---|---|
| fastapi | 0.141.1 |
| uvicorn | 0.53.0 |
| sqlalchemy | 2.1.0 |
| asyncpg | 0.31.0 |
| alembic | 1.20.0 |
| pydantic | 2.13.5 |
| pydantic-settings | 2.15.0 |
| passlib | 1.7.4 |
| argon2-cffi | 25.1.0 |
| pyjwt | 2.15.0 |
| redis | 8.1.0 |
| pytest | 9.1.1 |
| pytest-asyncio | 1.4.0 |
| httpx | 0.28.1 |
| ruff | 0.16.9 |
| greenlet | 3.5.6 |
| starlette | 1.7.0 |

Python del entorno: 3.12.3 (venv en `back/.venv`).

Nota: `redis>=5.0` resolvió a `8.1.0` (última estable). `sqlalchemy>=2.0` → `2.1.0`.
Todo lo demás dentro de los pisos declarados en `pyproject.toml`.

## 4. Comandos ejecutados (salida clave recortada)

```sh
# venv + install editable
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
# -> Successfully installed ... fastapi-0.141.1 ... sqlalchemy-2.1.0 ...

# Docker Compose
docker compose up -d
# -> Container sivigila-postgres Started / sivigila-redis Started
docker compose ps
# NAME                SERVICE    STATUS
# sivigila-postgres   postgres   Up (healthy)   0.0.0.0:5432->5432/tcp
# sivigila-redis      redis      Up (healthy)   0.0.0.0:6379->6379/tcp

# Migración baseline + upgrade
.venv/bin/alembic revision -m "initial baseline"
# -> Generating .../46739a8b908c_initial_baseline.py
.venv/bin/alembic upgrade head
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Running upgrade  -> 46739a8b908c, initial baseline

# Lint
.venv/bin/ruff check .
# -> All checks passed!

# Tests
.venv/bin/pytest -q
# -> 1 passed, 1 warning in 0.79s
# (warning: StarletteDeprecationWarning sobre httpx/httpx2 del testclient)

# Import (sin levantar uvicorn)
.venv/bin/python -c "from app.main import app"
# -> (sin error)
```

## 5. Desviaciones del spec (con justificación)

1. **`Base` en `app/core/database.py`** (y no en `app/db/base.py`): el task item 4 lo
   pide explícitamente ahí, y el código de modelos del propio `BACKEND_ARCH.md` hace
   `from app.core.database import Base`. Consistente con la doc.
2. **`app/db/base.py` y `app/db/seed_data.py` no creados**: son contenido de tareas
   futuras (seed de DIVIPOLA/Eventos), fuera del alcance "sin lógica de negocio".
   Se dejó el paquete `app/db/` con `__init__.py`.
3. **Módulos de negocio no creados** (`auth.py`, `caracterizacion.py`, `fichas_basicas.py`,
   `fichas_complementarias.py`, `catalogos.py`, `docente.py`, y `models/`+`schemas/`
   específicos): explícitamente fuera de B1. La estructura de directorios coincide con la doc.
4. **`README.md` añadido**: `pyproject.toml` declara `readme = "README.md"`; sin el archivo
   el build editable falla.
5. **Migración baseline vacía** (no autogenerada): no hay modelos todavía, por lo que
   `autogenerate` no detecta nada. Se creó una revisión vacía (`upgrade`/`downgrade` = `pass`)
   para demostrar que el motor async + conexión a Postgres funcionan.
6. **Ruff**: se añadió `known-first-party = ["app"]` y `per-file-ignores` para
   `alembic/versions/*` (E501, F401, I001, UP007, UP035, W291). Las migraciones las genera
   Alembic y no siguen las reglas de lint (p. ej. `from typing import Union, Sequence`).
7. **Nota menor**: `pip install -e` dentro de un repo git registra el paquete editable con
   la URL de origen (`-e git+...@commit#egg=sivigila_backend&subdirectory=back`) en
   `pip freeze`. No afecta imports ni ejecución (apunta al checkout local).

## 6. Cómo levantar el stack

```sh
cd back

# 1. Entorno virtual (solo primera vez)
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# 2. Infraestructura (Postgres 16 + Redis 7)
docker compose up -d          # docker compose ps  → ambos "healthy"

# 3. Migraciones
.venv/bin/alembic upgrade head

# 4. API
cp .env.example .env          # opcional (los defaults ya funcionan)
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000
# Health: GET http://localhost:8000/health  → {"status":"ok"}
# Health v1: GET http://localhost:8000/api/v1/health

# 5. Calidad
.venv/bin/ruff check .
.venv/bin/pytest
```

## 7. Verificación (evidencia)

| Verificación | Resultado |
|---|---|
| `pip install -e ".[dev]"` | OK (editable instalado) |
| `docker compose up -d` + `ps` | OK — postgres y redis `(healthy)` |
| `alembic upgrade head` | OK — `46739a8b908c, initial baseline` |
| `ruff check .` | OK — "All checks passed!" |
| `pytest -q` | OK — `1 passed` |
| `python -c "from app.main import app"` | OK — sin error |
