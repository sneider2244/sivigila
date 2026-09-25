# FP3 — Reporte: Desacople de RBAC en la ficha + vista de escenarios del estudiante + entrega

> Fase 3 del `docs/FLOW_PLAN.md`. Contratos implementados exactos (Estudiante + Ficha).

## Estado

- `alembic upgrade head`: **OK** (sin migraciones nuevas — FP3 no cambia esquema).
- `ruff check .`: **All checks passed!**
- `pytest -q`: **77 passed** (incluye los 7 tests nuevos de `test_estudiante_flow.py`).

## Archivos creados / modificados

### Creados
- `back/tests/test_estudiante_flow.py` — 7 tests del flujo estudiante + desacople.

### Modificados
- `back/app/api/v1/endpoints/fichas_basicas.py` — desacople RBAC en `crear_ficha_basica`.
- `back/app/schemas/ficha_basica.py` — `FichaDatosBasicosCreate.cod_upgd` ahora opcional.
- `back/app/schemas/docente.py` — nuevos schemas `EscenarioEstudianteOut`, `EstudianteAsignacionOut`, `EntregaRequest`.
- `back/app/api/v1/endpoints/docente.py` — `GET /estudiante/escenarios` (nueva respuesta) + `POST .../entregar`.
- `back/tests/test_docente.py` — ajusté `test_estudiante_lista_escenarios_200` al nuevo shape (`e["escenario"]["id"]`).

## Cómo quedó el desacople

En `crear_ficha_basica` (`fichas_basicas.py`):

1. La dependencia pasó de `Depends(_escritura_dependency)` (`require_roles(UPGD, DOCENTE)`)
   a `Depends(get_current_user)` → **cualquier rol autenticado** puede crear.
2. Se eliminaron `_ROLES_ESCRITURA` y `_escritura_dependency` (ya no se usan en el módulo).
3. Resolución de `cod_upgd`:

```python
cod_upgd = current_user.cod_upgd or payload.cod_upgd or _COD_UPGD_DEMO  # "150010123456"
```

4. Se eliminó el `raise HTTPException(400, ...)` por `cod_upgd` vacío.
5. El comportamiento UPGD "usa su propia UPGD" se preserva porque `current_user.cod_upgd`
   tiene prioridad sobre `payload.cod_upgd`.

Además, `FichaDatosBasicosCreate.cod_upgd` pasó de `str` (requerido) a `str | None = None`,
para que un payload sin `cod_upgd` caiga en la UPGD demo en lugar de un 422.

## Shapes JSON exactos

### `GET /api/v1/estudiante/escenarios` → `list[EstudianteAsignacionOut]`

```json
[
  {
    "id": 1,
    "estado": "ASIGNADO",
    "ficha_basica_id": null,
    "escenario": {
      "id": 1,
      "titulo": "Dengue FP3",
      "descripcion": "Escenario para el flujo del estudiante.",
      "cod_evento": "110"
    }
  }
]
```

Sin `datos_esperados` en ningún nivel (no-leak).

### `POST /api/v1/estudiante/escenarios/{asignacion_id}/entregar`

Body:

```json
{ "ficha_basica_id": 3 }
```

Respuesta `200` (`EstudianteAsignacionOut`):

```json
{
  "id": 1,
  "estado": "COMPLETADO",
  "ficha_basica_id": 3,
  "escenario": {
    "id": 1,
    "titulo": "Dengue FP3",
    "descripcion": "Escenario para el flujo del estudiante.",
    "cod_evento": "110"
  }
}
```

### Códigos de error de `entregar`

- `404` — asignación no existe (`"Asignación de escenario no encontrada"`).
- `403` — `asignacion.estudiante_id != current_user.id` (entrega de asignación ajena).
- `404` — ficha no existe (`"Ficha de datos básicos no encontrada"`).

Orden de validación en `entregar`: asignación (404) → ownership (403) → ficha (404).
La ownership se chequea antes que la ficha para que un estudiante no pueda sondear la
existencia de una ficha a través de la asignación de otro.

## Schemas nuevos (`app/schemas/docente.py`)

```python
class EscenarioEstudianteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    descripcion: str
    cod_evento: str

class EstudianteAsignacionOut(BaseModel):
    id: int
    estado: EstadoAsignacion
    ficha_basica_id: int | None
    escenario: EscenarioEstudianteOut

class EntregaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ficha_basica_id: int
```

## Tests (`test_estudiante_flow.py`)

1. `test_municipal_crea_ficha_sin_cod_upgd_default_demo` — MUNICIPAL crea ficha sin
   `cod_upgd` → `201`, `cod_upgd == "150010123456"`.
2. `test_entregar_ok_completado` — entrega propia → `200`, `estado == "COMPLETADO"`,
   `ficha_basica_id` seteado, escenario anidado sin `datos_esperados`.
3. `test_entregar_asignacion_ajena_403` — entrega sobre asignación de otro → `403`.
4. `test_entregar_asignacion_inexistente_404` — `asignacion_id` inexistente → `404`.
5. `test_entregar_ficha_inexistente_404` — `ficha_basica_id` inexistente → `404`.
6. `test_get_escenarios_sin_datos_esperados` — `GET /estudiante/escenarios` no incluye
   `datos_esperados` y las keys son exactamente `{id, estado, ficha_basica_id, escenario}`
   y `escenario == {id, titulo, descripcion, cod_evento}`.

## Output de verificación

```
$ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.

$ ruff check .
All checks passed!

$ pytest -q
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed, 123 warnings in 31.11s
```

## Deviations

- Ninguna respecto al contrato. Detalles de implementación (no pedidos, no inventados):
  - Orden de checks en `entregar` (ownership antes que ficha) elegido por seguridad;
    documentado arriba.
  - El `test_docente.py::test_estudiante_lista_escenarios_200` se actualizó porque el
    shape cambió de `list[EscenarioOut]` a `list[EstudianteAsignacionOut]` (el `id`
    top-level ahora es el de la asignación, no el del escenario).

## Concerns

- El `GET /docente/escenarios` (solo DOCENTE) sigue exponiendo `datos_esperados` vía
  `EscenarioOut`. Es correcto por RBAC (solo DOCENTE) y no entra en el alcance FP3, pero
  conviene no reutilizar ese schema para vistas de estudiante (por eso se creó
  `EscenarioEstudianteOut`).
