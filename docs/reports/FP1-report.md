# FP1 — Registro de estudiantes + rol dinámico

> Fase 1 (backend) del FLOW_PLAN. Implementa `POST /auth/register` (auto-login) y
> `PATCH /auth/me` (rol dinámico), más la columna `numero_identificacion` en `usuarios`.

## Estado

- **pytest**: 59 passed
- **ruff**: All checks passed!
- **alembic**: `upgrade head` OK → `7e0bf827495d (head)`

## Archivos creados / modificados

### Creados

- `alembic/versions/7e0bf827495d_usuarios_numero_identificacion.py` — migración generada por autogenerate.
- `tests/test_register.py` — 7 tests (patrón async, igual que `test_auth.py`).

### Modificados

- `app/models/usuario.py` — columna `numero_identificacion: Mapped[str | None] = mapped_column(String(20), nullable=True)`.
- `app/schemas/usuario.py` — `RegisterRequest`, `RolUpdateRequest`; `UsuarioOut` ahora incluye `numero_identificacion`.
- `app/schemas/__init__.py` — exporta `RegisterRequest` y `RolUpdateRequest`.
- `app/api/v1/endpoints/auth.py` — `POST /register` y `PATCH /me`.

## Contratos de API (shapes JSON exactos)

### `POST /api/v1/auth/register` → `201`

Request:

```json
{
  "email": "estudiante1@test.com",
  "nombre_completo": "Estudiante Uno",
  "numero_identificacion": "1030456789",
  "rol": "UPGD"
}
```

(`rol` es opcional; default `UPGD`.)

Response (mismo shape que `login`):

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "username": "estudiante1@test.com",
    "nombre_completo": "Estudiante Uno",
    "numero_identificacion": "1030456789",
    "rol": "UPGD",
    "cod_upgd": "150010123456",
    "activo": true
  }
}
```

Errores:

- `422` — `rol == DOCENTE` (`detail: "El rol DOCENTE no está disponible"`); también email/nombre/número vacíos o email sin formato básico (regex `^[^@\s]+@[^@\s]+\.[^@\s]+$`).
- `409` — email duplicado (`detail: "Ya existe un usuario con ese email"`).

### `PATCH /api/v1/auth/me` → `200`

Request:

```json
{ "rol": "UI" }
```

Response (shape `UsuarioOut`):

```json
{
  "id": 1,
  "username": "estudiante1@test.com",
  "nombre_completo": "Estudiante Uno",
  "numero_identificacion": "1030456789",
  "rol": "UI",
  "cod_upgd": "150010123456",
  "activo": true
}
```

Error: `422` si `rol == DOCENTE`.

## Reglas de negocio implementadas

- `rol` default `UPGD`; `DOCENTE` rechazado con 422 tanto en register como en PATCH.
- Email = `username`; `numero_identificacion` = password (hash Argon2) y se guarda **en claro** (R-numero).
- `cod_upgd` por defecto `"150010123456"` (R-cod-upgd, UPGD demo).
- Validaciones por Pydantic `field_validator` (strip + no vacío; regex de email). Enums (`RolEnum`), no strings.

## Tests (`tests/test_register.py`)

| Test | Caso | Esperado |
|------|------|----------|
| `test_register_ok_auto_login` | registro OK + `GET /auth/me` con el token | `201`, me→`200` con el email |
| `test_register_email_duplicado_409` | mismo email dos veces | `409` |
| `test_register_rol_docente_422` | `rol="DOCENTE"` | `422` |
| `test_register_email_vacio_422` | email en blanco | `422` |
| `test_login_estudiante_email_numero` | login `username=email`, `password=numero` | `200` |
| `test_patch_me_cambia_rol` | PATCH a `UI` + verificar en `/auth/me` | `200`, rol reflejado |
| `test_patch_me_a_docente_422` | PATCH a `DOCENTE` | `422` |

## Desviaciones / decisiones

1. **Status code del register**: el contrato no especifica status; usé `201 CREATED` (REST idiomático, consistente con los endpoints de creación del codebase — `test_caracterizacion.py::test_crear_201`, `docente`). El body mantiene exactamente el shape de `login`.
2. **Validación de email**: `email-validator` NO está instalado, así que usé `EmailStr`… no, usé una regex básica en un `field_validator` (no agrego dependencia nueva).
3. **Rechazo de DOCENTE**: lo hice a nivel de endpoint (no en el schema) para dar un `detail` claro y semántico en el 422, en vez del detalle genérico de Pydantic.
4. **Test DB y FK de `cod_upgd`**: `conftest.py` solo siembra catálogos + usuario DOCENTE (sin UPGD). Como `register` setea `cod_upgd="150010123456"` (FK a `upgd_caracterizacion.cod_prestador`), el test file siembra la UPGD demo en un fixture `module`-scoped (mismo patrón que `test_caracterizacion.py`).

## Preocupaciones / observaciones

- Warning de deprecación (no-error): `HTTP_422_UNPROCESSABLE_ENTITY` está deprecado en fastapi 0.141.1 (sugiere `HTTP_422_UNPROCESSABLE_CONTENT`). Lo dejé por consistencia con el resto del codebase (que usa `status.HTTP_*`); no afecta tests ni lint.
- Warning pre-existente de JWT (`InsecureKeyLengthWarning`) por `SECRET_KEY` corto en dev — ajeno a esta fase.
- `numero_identificacion` se persiste en claro por diseño (R-numero); solo apto para el simulador educativo.
