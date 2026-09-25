# SIVIGILA — Simulador educativo

Simulador web del Sistema de Vigilancia en Salud Pública (SIVIGILA) de Colombia, para entrenar a estudiantes de enfermería y salud pública en el diligenciamiento de fichas de notificación.

Monorepo con dos subproyectos independientes:

- `front/` — Frontend **Next.js 16** (App Router, SPA/SSR, React Hook Form + Zod, Zustand, TanStack Query, SCSS Modules).
- `back/` — Backend **FastAPI** (API REST, SQLAlchemy 2.0 async, Pydantic v2, JWT + RBAC) con **PostgreSQL** + **Redis**.

```
Next.js (SSR, SCSS)  →  FastAPI (JWT, RBAC, Pydantic)  →  PostgreSQL (JSONB) + Redis
```

Documentación de arquitectura en [`docs/`](docs/): `PROJECT_PLAN.md`, `BACKEND_ARCH.md`, `FRONTEND_ARCH.md` y `STATUS.md` (ledger de ejecución).

## Prerrequisitos

- **Docker** + **Docker Compose** (para PostgreSQL 16 y Redis 7).
- **Python 3.12+**.
- **Node.js 24** (o compatible) con `npm`.

---

## Backend (`back/`)

```bash
cd back

# 1. Infraestructura: levanta Postgres y Redis
docker compose up -d

# 2. Entorno virtual + dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configuración (opcional: ya hay defaults válidos para local)
cp .env.example .env

# 4. Migraciones de esquema
alembic upgrade head

# 5. Seed inicial (idempotente): usuario DOCENTE + catálogos + UPGD demo
python -m app.db.seed

# 6. Levantar la API (http://localhost:8000)
uvicorn app.main:app --reload
```

- API en `http://localhost:8000`, salud en `GET /health`.
- Documentación interactiva: `http://localhost:8000/docs` (Swagger).

## Frontend (`front/`)

```bash
cd front

npm install
npm run dev   # http://localhost:3000
```

El frontend apunta por defecto a `http://localhost:8000/api/v1` (no requiere `.env`). Si usás otra URL, creá `front/.env.local` con:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Credenciales demo

- **Docente**: usuario `docente`, contraseña `docente123` (la siembra el seed).
- **Estudiante**: se auto-registra desde el login con su correo + número de identificación (sin contraseña tradicional).

## Flujo de un demo

1. Docente entra → crea un **escenario clínico** (caso en lenguaje natural + evento).
2. Docente **asigna** el escenario a estudiantes (buscador + selección masiva).
3. Estudiante ve su escenario en "Mis escenarios" → diligencia **Datos Básicos → Datos Complementarios → Entrega** (con guardado parcial y borrador).
4. Docente revisa las **asignaciones del caso** y abre la ficha de cada estudiante ("Ver ficha").

## Comandos útiles

Backend (desde `back/`):

- Tests: `pytest`
- Lint / formato: `ruff check .` · `ruff format .`
- Migración nueva: `alembic revision --autogenerate -m "descripción"`
- Seed: `python -m app.db.seed`
- **Limpiar datos demo** (borra fichas/escenarios/asignaciones/estudiantes; conserva catálogos, UPGD demo y DOCENTE): `python -m app.db.clean`

Frontend (desde `front/`):

- Lint: `npm run lint` · Build: `npm run build`

## Roles RBAC

`UPGD`, `UI`, `MUNICIPAL`, `DEPARTAMENTAL`, `NACIONAL`, `DOCENTE`. El rol de estudiante es una etiqueta dinámica (cambiable desde el header) y no bloquea el flujo educativo; el RBAC jerárquico queda diferido como modo avanzado.
