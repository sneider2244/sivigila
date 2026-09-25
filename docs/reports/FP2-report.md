# FP2 — Listado de estudiantes + asignación masiva

> Fase 2 (backend) del FLOW_PLAN. Implementa `GET /docente/estudiantes?q=`,
> el unique constraint `(escenario_id, estudiante_id)` y reemplaza el single-assign
> por bulk `POST /docente/escenarios/{id}/asignar` con `{ estudiante_ids: [int] }`.

## Estado

- **pytest**: 71 passed
- **ruff**: All checks passed!
- **alembic**: `upgrade head` OK → `7dfc951b4e38 (head)`

## Archivos creados / modificados

### Creados

- `alembic/versions/7dfc951b4e38_unique_asignacion_escenario_estudiante.py` — unique constraint generado por autogenerate.
- `tests/test_docente_estudiantes.py` — 12 tests (listado + filtros + bulk + idempotencia + 404/403/422).

### Modificados

- `app/models/docente.py` — `UniqueConstraint("escenario_id", "estudiante_id", name="uq_escenario_asignaciones_escenario_estudiante")` en `EscenarioAsignacion.__table_args__`.
- `app/schemas/docente.py` — `AsignacionCreate` ahora `{ estudiante_ids: list[int] }` (con validator no-vacía); nuevo `EstudianteOut`.
- `app/schemas/__init__.py` — exporta `EstudianteOut`.
- `app/api/v1/endpoints/docente.py` — `GET /docente/estudiantes` + bulk `asignar_escenarios`; removida la constante `_DETALLE_ESTUDIANTE_NO_ENCONTRADO` (sin uso).
- `tests/test_docente.py` — `test_asignar_201` y `test_estudiante_lista_escenarios_200` migrados al body bulk `{ estudiante_ids: [...] }`.

## Contratos de API (shapes JSON exactos)

### `GET /api/v1/docente/estudiantes?q=` → `200`

Item (solo usuarios `rol != DOCENTE`, orden `nombre_completo`):

```json
{
  "id": 2,
  "username": "fp2_ana@test.com",
  "nombre_completo": "Ana Martínez",
  "rol": "UPGD",
  "numero_identificacion": "FP2001",
  "activo": true
}
```

`q` filtra case-insensitive (`ilike %q%`) sobre `nombre_completo` OR `username` OR `numero_identificacion`.

### `POST /api/v1/docente/escenarios/{escenario_id}/asignar` → `201`

Request:

```json
{ "estudiante_ids": [2, 3] }
```

Response (`list[AsignacionOut]` — flat, solo las creadas):

```json
[
  {
    "id": 5,
    "escenario_id": 1,
    "escenario_titulo": "Dengue para bulk",
    "estudiante_id": 2,
    "estudiante_username": "fp2_ana@test.com",
    "estudiante_nombre": "Ana Martínez",
    "estado": "ASIGNADO",
    "ficha_basica_id": null
  }
]
```

Errores:

- `404` — escenario inexistente (`detail: "Escenario clínico no encontrado"`).
- `404` — algún `estudiante_id` no existe (`detail: "Estudiante(s) no encontrado(s): [999999]"`).
- `422` — `estudiante_ids` vacía (validator Pydantic `_no_vacia`).
- `403` — rol no-DOCENTE.

## Reglas de negocio implementadas

- **Idempotencia**: se deduplica el input (`dict.fromkeys`) y se consultan los pares ya existentes con un único `select(...).in_(...)`; solo se crean los nuevos en estado `ASIGNADO` (`EstadoAsignacion.ASIGNADO`). Re-asignar los mismos ids devuelve `[]` (201) sin duplicar.
- **Validación de estudiantes**: un solo query `in_` para resolver todos los ids; si falta alguno → 404 con la lista de ids inválidos en el `detail`.
- **Enums, no strings**: `RolEnum.DOCENTE` en el filtro, `EstadoAsignacion.ASIGNADO` en la creación.
- **Columnas SQL explícitas**: `select(Usuario).where(Usuario.rol != RolEnum.DOCENTE)` y `or_(Usuario.nombre_completo.ilike(...), Usuario.username.ilike(...), Usuario.numero_identificacion.ilike(...))`.
- **Unique constraint**: `(escenario_id, estudiante_id)` en el modelo + migración (sin duplicados preexistentes en dev, verificado por query).

## Tests (`tests/test_docente_estudiantes.py`)

| Test | Caso | Esperado |
|------|------|----------|
| `test_listar_estudiantes_excluye_docente` | listado incluye no-DOCENTE y excluye `docente` | `200`, `rol != DOCENTE` |
| `test_listar_estudiantes_filtro_q_nombre` | `q="gómez"` (case-insensitive) | solo `fp2_carla` |
| `test_listar_estudiantes_filtro_q_username` | `q="fp2_benito"` (email) | solo `fp2_benito` |
| `test_listar_estudiantes_filtro_q_identificacion` | `q="FP2002"` | solo `fp2_benito` |
| `test_bulk_asignar_multiples_201` | bulk 2 ids | `201`, 2 creadas |
| `test_bulk_asignar_idempotente_no_duplica` | re-asignar mismos ids | `201` con `[]`, count DB == 2 |
| `test_bulk_asignar_parcial_nuevo_y_existente` | mix nuevo + ya asignado | solo el nuevo, count == 2 |
| `test_bulk_asignar_escenario_inexistente_404` | escenario 999999 | `404` |
| `test_bulk_asignar_estudiante_inexistente_404` | id válido + 999999 | `404` con id en detail |
| `test_bulk_asignar_lista_vacia_422` | `estudiante_ids: []` | `422` |
| `test_listar_estudiantes_no_docente_403` | UPGD lista estudiantes | `403` |
| `test_bulk_asignar_no_docente_403` | UPGD asigna | `403` |

## Desviaciones / decisiones

1. **Status code del bulk**: el contrato no especifica status; mantengo `201 CREATED` (consistente con el single anterior y con los endpoints de creación del codebase). El body es `list[AsignacionOut]` de las creadas.
2. **`estudiante_ids` duplicados en el payload**: se deduplican con `dict.fromkeys` (idempotencia extra, no contemplada explícitamente pero alineada con el espíritu idempotente).
3. **404 de estudiante inexistente**: `detail` incluye la lista de ids inválidos (`"Estudiante(s) no encontrado(s): [999999]"`) para cumplir el contrato "detail que incluya el/los id(s) inválido(s)".
4. **`_DETALLE_ESTUDIANTE_NO_ENCONTRADO`**: removida por quedar sin uso tras el cambio a bulk (ruff no la flaggea, pero es código muerto).
5. **Asignación no filtra rol del estudiante**: el contrato solo pide validar existencia (404), no restringir por rol; se asignan usuarios de cualquier rol (incluidos otros roles, consistente con el endpoint original).

## Preocupaciones / observaciones

- Los warnings de pytest son pre-existentes (argon2/crypt, `InsecureKeyLengthWarning`, `StarletteDeprecationWarning`, `HTTP_422_UNPROCESSABLE_ENTITY`) — ajenos a esta fase, no afectan tests ni lint.
- El unique constraint se creó vía autogenerate sobre la DB dev sin duplicados (verificado: `GROUP BY ... HAVING count(*) > 1` → ninguno).
