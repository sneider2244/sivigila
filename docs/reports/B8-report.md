# Report B8 — API del módulo Docente (escenarios clínicos + evaluación automatizada)

## Estado: COMPLETO ✅

## Resumen ejecutivo

Implementación del módulo Docente del simulador SIVIGILA (Sprint 4): creación de
escenarios clínicos (`EscenarioClinico`), asignación de escenarios a estudiantes
(`EscenarioAsignacion` con ciclo de vida `ASIGNADO → EN_PROGRESO → COMPLETADO`),
consulta de escenarios por el estudiante y evaluación automatizada de la ficha
diligenciada contra los datos esperados. RBAC estricto: `/docente/*` solo para
`DOCENTE`; `/estudiante/*` para cualquier rol autenticado. Todo cubierto con tests.

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `back/app/models/docente.py` | Modelos ORM `EscenarioClinico` + `EscenarioAsignacion` + enum `EstadoAsignacion`. |
| `back/app/schemas/docente.py` | `EscenarioCreate/Out`, `AsignacionCreate/Out`, `EvaluarRequest`, `EvaluacionDetalle`, `EvaluacionResult`. |
| `back/app/api/v1/endpoints/docente.py` | 6 endpoints + RBAC + motor de evaluación. |
| `back/alembic/versions/14371d7d9097_modulo_docente.py` | Migración de las 2 tablas + enum + índices. |
| `back/tests/test_docente.py` | 6 tests del módulo. |
| `docs/reports/B8-report.md` | Este reporte. |

## Archivos modificados

- `back/app/models/__init__.py` — export de `EscenarioClinico`, `EscenarioAsignacion`, `EstadoAsignacion`.
- `back/app/schemas/__init__.py` — export de los 7 esquemas del módulo.
- `back/app/api/v1/api.py` — `include_router(docente.router, tags=["docente"])`.

## Modelo de datos

### Enum `EstadoAsignacion` (`app/models/docente.py`)

```python
class EstadoAsignacion(str, enum.Enum):
    ASIGNADO = "ASIGNADO"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADO = "COMPLETADO"
```

Persistido como enum nativo PostgreSQL (`estado_asignacion`) con
`server_default='ASIGNADO'`.

### Tabla `escenarios_clinicos`

```python
class EscenarioClinico(Base):
    __tablename__ = "escenarios_clinicos"

    id: Mapped[int]                        # PK
    titulo: Mapped[str]                    # String(200)
    descripcion: Mapped[str]               # String(2000)
    cod_evento: Mapped[str]                # String(10), indexado
    datos_esperados: Mapped[dict]          # JSONB (valores esperados de la ficha)
    activo: Mapped[bool]                   # default True, server_default 'true'
    creado_por_id: Mapped[int]             # FK -> usuarios.id (NOT NULL)
```

### Tabla `escenario_asignaciones`

```python
class EscenarioAsignacion(Base):
    __tablename__ = "escenario_asignaciones"

    id: Mapped[int]                        # PK
    escenario_id: Mapped[int]              # FK -> escenarios_clinicos.id (indexado)
    estudiante_id: Mapped[int]             # FK -> usuarios.id (indexado)
    estado: Mapped[EstadoAsignacion]       # enum estado_asignacion, default ASIGNADO
    ficha_basica_id: Mapped[int | None]    # FK -> fichas_datos_basicos.id (nullable)
```

FKs nombradas: `fk_escenarios_clinicos_creado_por`, `fk_escenario_asignaciones_escenario`,
`fk_escenario_asignaciones_estudiante`, `fk_escenario_asignaciones_ficha_basica`.

## JSON shapes exactos

### `POST /api/v1/docente/escenarios` → 201

Request (body):

```json
{
  "titulo": "Dengue con signos de alarma",
  "descripcion": "Paciente con fiebre y exantema en zona endémica.",
  "cod_evento": "110",
  "datos_esperados": {
    "cod_evento": "110",
    "clasificacion_caso": 1,
    "hospitalizado": false,
    "condicion_final": 1,
    "area_ocurrencia": 3,
    "sexo": "M",
    "contenido": { "fiebre": true, "exantema": false }
  },
  "activo": true
}
```

- `titulo`, `descripcion`, `cod_evento`, `datos_esperados`: obligatorios.
- `activo`: opcional (default `true`).
- `extra="forbid"` en el payload (rechaza claves no contempladas).

Response (201) — `EscenarioOut`:

```json
{
  "id": 1,
  "titulo": "Dengue con signos de alarma",
  "descripcion": "Paciente con fiebre y exantema en zona endémica.",
  "cod_evento": "110",
  "datos_esperados": {
    "cod_evento": "110",
    "clasificacion_caso": 1,
    "hospitalizado": false,
    "condicion_final": 1,
    "area_ocurrencia": 3,
    "sexo": "M",
    "contenido": { "fiebre": true, "exantema": false }
  },
  "activo": true,
  "creado_por_id": 1
}
```

### `GET /api/v1/docente/escenarios` → 200

Lista de `EscenarioOut` (mismo shape anterior), ordenada por `id`.

### `POST /api/v1/docente/escenarios/{escenario_id}/asignar` → 201

Request (body):

```json
{ "estudiante_id": 2 }
```

Response (201) — `AsignacionOut`:

```json
{
  "id": 1,
  "escenario_id": 1,
  "escenario_titulo": "Dengue con signos de alarma",
  "estudiante_id": 2,
  "estudiante_username": "estudiante_test",
  "estudiante_nombre": "Estudiante Test",
  "estado": "ASIGNADO",
  "ficha_basica_id": null
}
```

### `GET /api/v1/docente/asignaciones` → 200

Lista de `AsignacionOut` (mismo shape), un objeto por asignación.

### `GET /api/v1/estudiante/escenarios` → 200

Lista de `EscenarioOut` (solo los escenarios asignados al usuario autenticado).

### `POST /api/v1/docente/evaluar` → 200

Request (body):

```json
{ "ficha_basica_id": 3, "escenario_id": 1 }
```

Response (200) — `EvaluacionResult`:

```json
{
  "puntaje": 100.0,
  "aciertos": 8,
  "total": 8,
  "detalle": [
    { "campo": "cod_evento", "esperado": "110", "obtenido": "110", "correcto": true },
    { "campo": "clasificacion_caso", "esperado": 1, "obtenido": 1, "correcto": true },
    { "campo": "hospitalizado", "esperado": false, "obtenido": false, "correcto": true },
    { "campo": "condicion_final", "esperado": 1, "obtenido": 1, "correcto": true },
    { "campo": "area_ocurrencia", "esperado": 3, "obtenido": 3, "correcto": true },
    { "campo": "sexo", "esperado": "M", "obtenido": "M", "correcto": true },
    { "campo": "contenido.fiebre", "esperado": true, "obtenido": true, "correcto": true },
    { "campo": "contenido.exantema", "esperado": false, "obtenido": false, "correcto": true }
  ]
}
```

## Cómo funciona la evaluación

La evaluación compara la ficha (y su complementaria, si aplica) contra
`escenario.datos_esperados`:

1. **Campos planos de `fichas_datos_basicos`** — se itera sobre los 6 campos del
   contrato (`_CAMPOS_PLANOS`): `cod_evento`, `clasificacion_caso`, `hospitalizado`,
   `condicion_final`, `area_ocurrencia`, `sexo`. Solo se comparan los que están
   presentes como claves en `datos_esperados`.
2. **Contenido complementario** — si `datos_esperados` incluye la clave
   `contenido` (dict no vacío), se resuelve `fichas_datos_complementarios` por
   `ficha_basica_id` y se compara cada clave de primer nivel de
   `datos_esperados["contenido"]` contra `complementaria.contenido`. Si no existe
   complementaria, esos campos se marcan `correcto=false` con `obtenido=null`.
3. **Puntaje** — `aciertos / total * 100`, redondeado a 2 decimales. `total` es
   el número de comparaciones realizadas; si `datos_esperados` no define ningún
   campo evaluable, `total=0` y `puntaje=100.0`.

Cada comparación produce un `detalle` con `campo`, `esperado`, `obtenido` y
`correcto`. Los campos de `contenido` se nombran `contenido.<clave>`.

Errores: `404` si la ficha o el escenario no existen (se valida la ficha primero).

## Endpoints

| Método | Ruta | Respuestas |
|--------|------|------------|
| `POST` | `/api/v1/docente/escenarios` | 201, 401, 403, 422 |
| `GET` | `/api/v1/docente/escenarios` | 200, 401, 403 |
| `POST` | `/api/v1/docente/escenarios/{escenario_id}/asignar` | 201, 401, 403, 404 |
| `GET` | `/api/v1/docente/asignaciones` | 200, 401, 403 |
| `GET` | `/api/v1/estudiante/escenarios` | 200, 401 |
| `POST` | `/api/v1/docente/evaluar` | 200, 401, 403, 404 |

### RBAC implementado

- `/docente/*` → `require_roles(RolEnum.DOCENTE)`. Cualquier otro rol (incluido
  UPGD/UI/MUNICIPAL/...) → **403**.
- `/estudiante/*` → `get_current_user` directo (cualquier rol autenticado).
- `creado_por_id` siempre se toma de `current_user.id` (nunca del body).
- `estudiante_id` en `asignar` valida la existencia del usuario (404 si no existe).

## Migración Alembic

- `alembic revision --autogenerate -m "modulo_docente"` → `14371d7d9097`.
- `alembic upgrade head` → aplicada correctamente (head `14371d7d9097`).
- El autogenerado creó las dos tablas, el enum `estado_asignacion` (vía
  `sa.Enum(...)`) y los tres índices (`cod_evento`, `escenario_id`, `estudiante_id`).

## Verificación

| Comando | Resultado |
|---------|-----------|
| `.venv/bin/alembic upgrade head` | ✅ OK (head `14371d7d9097`) |
| `.venv/bin/ruff check .` | ✅ All checks passed! |
| `.venv/bin/pytest -q` | ✅ 52 passed (19.34s) |

### Output de tests del módulo

```
tests/test_docente.py ......  6 passed
```

Los 6 tests cubren: crear escenario como DOCENTE (201 + shape), crear como UPGD
(403), asignar escenario (201 + shape desnormalizado), estudiante lista sus
escenarios (200), evaluar con puntaje (200, `puntaje=100.0`, `aciertos=8`,
`total=8`, campos planos + `contenido.*`), y evaluar ficha inexistente (404).

## Desviaciones y decisiones

1. **`creado_por_id` NOT NULL** — el contrato lo declara `int FK` sin `nullable`
   (a diferencia de `ficha_basica_id`, que sí marca `nullable`). Se interpretó como
   no nulo: todo escenario lo crea un DOCENTE autenticado.
2. **`GET /estudiante/escenarios` no filtra por `activo`** — el contrato pide
   "lista de escenarios asignados al usuario actual" sin mencionar `activo`, así
   que se devuelven todos los asignados (activos o no). Si se quiere ocultar los
   inactivos, basta añadir `.where(EscenarioClinico.activo.is_(True))`.
3. **Sin constraint de unicidad `(escenario_id, estudiante_id)`** — el contrato no
   la exige, por lo que un docente puede asignar el mismo escenario al mismo
   estudiante más de una vez. Consecuencia: `GET /estudiante/escenarios` (JOIN)
   puede devolver el mismo escenario duplicado. Si se desea, agregar un
   `UniqueConstraint` es trivial, pero está fuera del alcance.
4. **`puntaje=100.0` cuando `total=0`** — si `datos_esperados` no define ningún
   campo evaluable (ni planos ni `contenido`), no hay comparaciones y se devuelve
   100.0 (evita división por cero). Es un edge case defendible; el contrato no lo
   especifica.
5. **Enum `estado_asignacion` sin drop explícito en downgrade** — el autogenerado
   usa `sa.Enum(...)` (crea el tipo nativo en `upgrade`); el `downgrade` dropea las
   tablas pero deja el tipo `estado_asignacion` huérfano (gotcha conocido de
   Alembic). No afecta a `upgrade`/tests. Si se prioriza un `downgrade` limpio, se
   puede replicar el patrón manual de B7 (`postgresql.ENUM(...).drop(checkfirst=True)`).
6. **Evento de prueba `110` (Dengue)** — el test de evaluación usa un evento sin
   esquema ofídico para que `contenido` sea un dict plano de primer nivel, alineado
   con el contrato de evaluación ("claves planas booleanas/valores de primer
   nivel"). Para eventos `100`/`820` el `contenido` es anidado (validado por
   `ComplementoOfidico`), por lo que la comparación plana solo tendría sentido si
   `datos_esperados["contenido"]` se define con las mismas claves de primer nivel.
