# Report B7 — Estados de fichas + trazabilidad

## Estado: COMPLETO ✅

## Resumen ejecutivo

Implementación del ciclo de vida de las fichas de datos básicos con una máquina
de estados (`EstadoFicha`: `NOTIFICADA`, `EN_AJUSTE`, `CONFIRMADA`, `DESCARTADA`)
y una bitácora de trazabilidad (`FichaTrazabilidad`) que registra cada transición
(quién, de qué estado a qué estado, código de ajuste 0..6 y observación). Se
añadió la columna `estado` a `fichas_datos_basicos` (default `NOTIFICADA`), se
crearon dos endpoints (`POST .../estado` y `GET .../trazabilidad`) con RBAC y se
cubrió todo con tests.

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `back/app/models/trazabilidad.py` | Modelo ORM `FichaTrazabilidad` (`Mapped`/`mapped_column`). |
| `back/app/schemas/trazabilidad.py` | `EstadoTransitionRequest` + `TrazabilidadOut`. |
| `back/alembic/versions/a67a6cf60073_estados_y_trazabilidad.py` | Migración de la columna `estado`, enum `estado_ficha` y tabla de trazabilidad. |
| `back/tests/test_estado_ficha.py` | 10 tests del módulo. |
| `docs/reports/B7-report.md` | Este reporte. |

## Archivos modificados

- `back/app/models/ficha_basica.py` — enum `EstadoFicha` + columna `estado`.
- `back/app/models/__init__.py` — export de `EstadoFicha` y `FichaTrazabilidad`.
- `back/app/schemas/ficha_basica.py` — campo `estado` en `FichaDatosBasicosBase`.
- `back/app/schemas/__init__.py` — export de `EstadoTransitionRequest` y `TrazabilidadOut`.
- `back/app/api/v1/endpoints/fichas_basicas.py` — dos endpoints + máquina de estados.

## Modelo de datos

### Enum `EstadoFicha` (`app/models/ficha_basica.py`)

```python
class EstadoFicha(str, enum.Enum):
    NOTIFICADA = "NOTIFICADA"
    EN_AJUSTE = "EN_AJUSTE"
    CONFIRMADA = "CONFIRMADA"
    DESCARTADA = "DESCARTADA"
```

Se persiste como enum nativo de PostgreSQL (`estado_ficha`) compartido entre la
columna `fichas_datos_basicos.estado` y las dos columnas de trazabilidad.

### Columna añadida a `fichas_datos_basicos`

```python
estado: Mapped[EstadoFicha] = mapped_column(
    SQLEnum(EstadoFicha, name="estado_ficha"),
    nullable=False,
    default=EstadoFicha.NOTIFICADA,
    server_default=EstadoFicha.NOTIFICADA.value,
)
```

### Tabla `fichas_trazabilidad`

```python
class FichaTrazabilidad(Base):
    __tablename__ = "fichas_trazabilidad"

    id: Mapped[int]                                  # PK
    ficha_basica_id: Mapped[int]                     # FK -> fichas_datos_basicos.id (indexed)
    estado_anterior: Mapped[EstadoFicha]             # enum estado_ficha
    estado_nuevo: Mapped[EstadoFicha]                # enum estado_ficha
    usuario_id: Mapped[int]                          # FK -> usuarios.id
    ajuste: Mapped[int | None]                       # 0..6 (validado en Pydantic)
    observacion: Mapped[str | None]                  # String(500)
    f_cambio: Mapped[datetime]                       # DateTime(timezone=True), auto
```

FKs nombradas: `fk_fichas_trazabilidad_ficha_basica` y `fk_fichas_trazabilidad_usuario`.
`f_cambio` usa `default=lambda: datetime.now(UTC)` (timezone-aware, seteado en el
momento del insert por el ORM).

## JSON shapes exactos

### `POST /api/v1/fichas/datos-basicos/{ficha_id}/estado`

Request (body):

```json
{
  "estado_nuevo": "EN_AJUSTE",
  "ajuste": 2,
  "observacion": "revisar datos de identificación"
}
```

- `estado_nuevo`: obligatorio, uno de `NOTIFICADA | EN_AJUSTE | CONFIRMADA | DESCARTADA`.
- `ajuste`: opcional, entero `0..6` (Pydantic `ge=0, le=6` → 422 si fuera de rango).
- `observacion`: opcional, string (`max_length=500`).
- `extra="forbid"`: rechaza claves no contempladas.

Response (200): la ficha actualizada (shape de `FichaDatosBasicosOut`), incluye
el nuevo `estado`:

```json
{
  "id": 1,
  "cod_upgd": "150010123456",
  "subindice": "01",
  "cod_evento": "100",
  "f_grabacion": "2026-09-25",
  "f_notificacion": "2026-09-25",
  "anio": 2026,
  "semana_epidemiologica": 38,
  "tipo_id": "CC",
  "num_id": "1023456800",
  "primer_nombre": "Pepito",
  "segundo_nombre": null,
  "primer_apellido": "Perez",
  "segundo_apellido": null,
  "telefono": null,
  "f_nacimiento": "1990-01-15",
  "edad": 36,
  "und_med_edad": 1,
  "sexo": "M",
  "identidad_genero": 1,
  "orientacion_sexual": 1,
  "pais_ocurrencia": "COLOMBIA",
  "dpto_ocurrencia": "05",
  "muni_ocurrencia": "05001",
  "area_ocurrencia": 1,
  "grupos_poblacionales": {},
  "clasificacion_caso": 1,
  "hospitalizado": false,
  "condicion_final": 1,
  "estado": "EN_AJUSTE",
  "creado_por_usuario_id": 1
}
```

### `GET /api/v1/fichas/datos-basicos/{ficha_id}/trazabilidad`

Response (200): lista ordenada por `f_cambio` **descendente**:

```json
[
  {
    "id": 3,
    "ficha_basica_id": 1,
    "estado_anterior": "NOTIFICADA",
    "estado_nuevo": "CONFIRMADA",
    "usuario_id": 1,
    "ajuste": null,
    "observacion": null,
    "f_cambio": "2026-09-25T03:52:10.123456+00:00"
  },
  {
    "id": 2,
    "ficha_basica_id": 1,
    "estado_anterior": "EN_AJUSTE",
    "estado_nuevo": "NOTIFICADA",
    "usuario_id": 1,
    "ajuste": null,
    "observacion": null,
    "f_cambio": "2026-09-25T03:52:05.654321+00:00"
  }
]
```

`f_cambio` se serializa ISO 8601 con offset UTC (`+00:00`).

## Reglas de transición (máquina de estados)

Definida en `_TRANSICIONES_PERMITIDAS` (`fichas_basicas.py`):

| Estado actual | Transiciones permitidas |
|---------------|-------------------------|
| `NOTIFICADA`  | `EN_AJUSTE`, `CONFIRMADA`, `DESCARTADA` |
| `EN_AJUSTE`   | `NOTIFICADA`, `CONFIRMADA`, `DESCARTADA` |
| `CONFIRMADA`  | `EN_AJUSTE` (reabrir) |
| `DESCARTADA`  | `NOTIFICADA` (reactivar) |

- Una transición no permitida (incluida `estado_nuevo == estado_actual`) devuelve
  **422** con detalle `"Transición de estado no permitida: {prev} -> {next}."`.
- El contrato no enumeraba la matriz explícitamente ("valida transición"); esta
  matriz es una decisión de diseño documentada aquí. Refleja el flujo real de
  SIVIGILA: notificación → revisión (ajuste/aprobar/descartar) → re-notificación.

## Endpoints

| Método | Ruta | Respuestas |
|--------|------|------------|
| `POST` | `/api/v1/fichas/datos-basicos/{ficha_id}/estado` | 200, 401, 403, 404, 422 |
| `GET` | `/api/v1/fichas/datos-basicos/{ficha_id}/trazabilidad` | 200, 401, 403, 404 |

### RBAC implementado

- **Todo requiere auth** (`get_current_user`).
- `POST .../estado`: solo `MUNICIPAL`, `DEPARTAMENTAL`, `NACIONAL`, `DOCENTE`
  (`require_roles`). `UPGD`/`UI` → **403**.
- `GET .../trazabilidad`: cualquier rol autenticado (`get_current_user` directo,
  incluye `UI`). `UPGD` solo sus propias fichas: si `ficha.cod_upgd !=
  current_user.cod_upgd` → **403** (`_asegurar_ficha_propia`).

## Migración Alembic

- `alembic revision --autogenerate -m "estados_y_trazabilidad"` → `a67a6cf60073`.
- El autogenerado referenciaba el enum `estado_ficha` en `create_table` y en
  `add_column`; se reescribió para crear el enum **una sola vez** con
  `estado_ficha.create(op.get_bind(), checkfirst=True)` (y `create_type=False` en
  la instancia compartida), y dropearlo en el `downgrade`.
- `alembic upgrade head` → aplicada correctamente (head `a67a6cf60073`).

## Verificación

| Comando | Resultado |
|---------|-----------|
| `.venv/bin/alembic upgrade head` | ✅ OK (head `a67a6cf60073`) |
| `.venv/bin/ruff check .` | ✅ All checks passed! |
| `.venv/bin/pytest -q` | ✅ 46 passed (16.00s) |

### Output de tests del módulo

```
tests/test_estado_ficha.py .......... 10 passed
```

Los 10 tests cubren: 401 sin auth (POST y GET), transición válida 200
(`NOTIFICADA -> EN_AJUSTE`), 403 UPGD intenta transición, 422 ajuste fuera de
rango (7 y -1), 422 `estado_nuevo` inválido, 422 transición no permitida
(`CONFIRMADA -> DESCARTADA`), 200 lista de trazabilidad (orden desc y 3 filas),
404 ficha inexistente (POST y GET), y 403 UPGD sobre trazabilidad de ficha ajena
(+ sanity 200 sobre la propia).

## Desviaciones y decisiones

1. **Matriz de transiciones definida por diseño** (el contrato no la enumera).
   Se eligió la máquina descrita arriba; si el cliente/negocio define otra, basta
   con ajustar `_TRANSICIONES_PERMITIDAS`.
2. **422 para transición no permitida** (no 400): se alinea con el resto de
   validaciones del contrato que ya usan 422 (`estado_nuevo` inválido, `ajuste`
   fuera de rango). Se documenta por si se prefiere 409/400 semántico.
3. **`ajuste` opcional y no condicionado a `EN_AJUSTE`**: el contrato lo declara
   opcional (`ajuste?: int`), así que no se fuerza su presencia al solicitar
   ajuste. Solo se valida el rango 0..6 cuando viene presente.
4. **Tarea opcional 5 (consistencia `cod_evento` complementaria vs. básica): NO
   implementada** (prioridad baja). Se mantiene el comportamiento de B6; la
   complementaria persiste su propio `cod_evento` sin validar contra la básica.
5. **`server_default` en `estado`**: se añadió `server_default='NOTIFICADA'` para
   que `ADD COLUMN ... NOT NULL` sea seguro ante filas preexistentes (aunque la
   base de desarrollo estaba vacía al momento de la migración).
6. **`f_cambio` sin `server_default`**: el valor lo setea el ORM (`default` Python,
   timezone-aware UTC). Evita divergencias de zona horaria entre app y DB; todas
   las escrituras pasan por el ORM.
7. **`GET .../trazabilidad` usa `get_current_user` directo** (incluye `UI`), tal
   como pide el contrato ("cualquier rol autenticado"), en lugar de reutilizar
   `_ROLES_LECTURA` (que excluye a `UI`).

## Nota de seguridad / RBAC

- Autenticación JWT obligatoria en ambos endpoints.
- Roles validados con `require_roles` y `get_current_user` (enums, no strings).
- `usuario_id` en trazabilidad se toma siempre de `current_user.id` (no del body).
- `estado_anterior` se lee del estado actual persistido de la ficha (no del body).
