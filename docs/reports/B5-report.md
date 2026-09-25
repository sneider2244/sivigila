# Reporte B5 — CRUD de Notificación Individual · Datos Básicos

## Estado

**Completado.** Todos los artefactos implementados, migración aplicada, tests y lint en verde.

---

## Archivos creados

| Archivo | Descripción |
| ------- | ----------- |
| `app/models/ficha_basica.py` | Modelo `FichaDatosBasicos` (SQLAlchemy 2.0 `Mapped`/`mapped_column`) + enums de dominio. |
| `app/schemas/ficha_basica.py` | Schemas Pydantic v2: `FichaDatosBasicosCreate`, `FichaDatosBasicosOut`, `FichaDatosBasicosUpdate`. |
| `app/api/v1/endpoints/fichas_basicas.py` | Endpoints CRUD + RBAC. |
| `alembic/versions/45be635431fb_ficha_datos_basicos.py` | Migración autogenerada (crea `fichas_datos_basicos` + 3 índices + FK). |
| `tests/test_ficha_basica.py` | 8 tests de integración (patrón async del proyecto). |

## Archivos modificados

| Archivo | Cambio |
| ------- | ------ |
| `app/models/__init__.py` | Exporta `FichaDatosBasicos` y enums (`Sexo`, `UndMedEdad`, `AreaOcurrencia`, `ClasificacionCaso`, `CondicionFinal`). |
| `app/schemas/__init__.py` | Exporta los 3 schemas de ficha básica. |
| `app/api/v1/api.py` | Registra `fichas_basicas.router` (tag `fichas-datos-basicos`). |

---

## Esquema de tabla (contrato exacto)

Tabla `fichas_datos_basicos`, columnas en orden del `docs/BACKEND_ARCH.md` §2, implementadas con `Mapped`/`mapped_column`:

| Columna | Tipo | Nullable | Default | Notas |
| ------- | ---- | -------- | ------- | ----- |
| `id` | Integer PK | no | auto | |
| `cod_upgd` | String(20) | no | — | indexado |
| `subindice` | String(5) | no | `"01"` | |
| `cod_evento` | String(10) | no | — | indexado |
| `f_grabacion` | Date | no | — | ISO |
| `f_notificacion` | Date | no | — | ISO |
| `anio` | Integer | no | — | |
| `semana_epidemiologica` | Integer | no | — | |
| `tipo_id` | String(5) | no | — | |
| `num_id` | String(20) | no | — | indexado |
| `primer_nombre` | String(50) | no | — | |
| `segundo_nombre` | String(50) | sí | — | |
| `primer_apellido` | String(50) | no | — | |
| `segundo_apellido` | String(50) | sí | — | |
| `telefono` | String(20) | sí | — | |
| `f_nacimiento` | Date | no | — | ISO |
| `edad` | Integer | no | — | |
| `und_med_edad` | Integer | no | — | 1 años / 2 meses / 3 días |
| `sexo` | String(1) | no | — | `M` / `F` |
| `identidad_genero` | Integer | no | `1` | |
| `orientacion_sexual` | Integer | no | `1` | |
| `pais_ocurrencia` | String(50) | no | `"COLOMBIA"` | |
| `dpto_ocurrencia` | String(5) | no | — | |
| `muni_ocurrencia` | String(5) | no | — | |
| `area_ocurrencia` | Integer | no | — | 1 cabecera / 2 centro poblado / 3 rural |
| `grupos_poblacionales` | JSONB | no | `{}` | dict libre |
| `clasificacion_caso` | Integer | no | — | 1..4 |
| `hospitalizado` | Boolean | no | `false` | |
| `condicion_final` | Integer | no | `1` | 1 vivo / 2 muerto |
| `creado_por_usuario_id` | Integer | sí | — | FK `usuarios.id` |

Índices: `ix_fichas_datos_basicos_cod_upgd`, `ix_fichas_datos_basicos_cod_evento`, `ix_fichas_datos_basicos_num_id`.

---

## Decisiones de diseño

### Enums de dominio (IntEnum/str Enum)
Se definieron en `app/models/ficha_basica.py`:

- `Sexo(str, enum.Enum)`: `M` / `F` (patrón `str+Enum` con `noqa: UP042`, consistente con `RolEnum`).
- `UndMedEdad(IntEnum)`: `ANIOS=1`, `MESES=2`, `DIAS=3`.
- `AreaOcurrencia(IntEnum)`: `CABECERA=1`, `CENTRO_POBLADO=2`, `RURAL=3`.
- `ClasificacionCaso(IntEnum)`: `SOSPECHOSO=1`, `PROBABLE=2`, `CONFIRMADO=3`, `DESCARTADO=4`.
- `CondicionFinal(IntEnum)`: `VIVO=1`, `MUERTO=2`.

**RULING (mismo que B4 en `NivelComplejidad`):** las columnas se persisten como `Integer`/`String(1)` para que el contrato JSON quede en tipos primitivos (`int`, `"M"`/`"F"`). La validación de rango y el tipado por enum se aplican en la capa Pydantic. Así el frontend recibe exactamente `"sexo": "M"`, `"und_med_edad": 1`, etc., sin serialización de enums.

### `grupos_poblacionales` como JSONB
Se usa `sqlalchemy.dialects.postgresql.JSONB` (no `JSON`) con `default=dict` (callable, evita el antipatrón de default mutable). El backend **no** valida su contenido, solo que sea `dict`; lo persiste tal cual, como exige el contrato.

### `FichaDatosBasicosUpdate`
Se define pero **no se expone** ningún endpoint PUT/PATCH en este alcance (Sprint 3). Se incluye por completitud del contrato y para no romper la exportación esperada.

### Decisión RBAC

| Rol | POST | GET (detalle) | GET (lista) |
| --- | ---- | ------------- | ----------- |
| `UPGD` | sí (cod_upgd forzada a la propia) | sí (ajena → 403) | sí (filtrado a su `cod_upgd`) |
| `DOCENTE` | sí (cualquier `cod_upgd`) | sí | sí (sin filtro) |
| `MUNICIPAL` / `DEPARTAMENTAL` / `NACIONAL` | no (403) | sí | sí (sin filtro) |
| `UI` | no (403) | no (403) | no (403) |

Detalles de implementación:

- `_ROLES_LECTURA = (UPGD, MUNICIPAL, DEPARTAMENTAL, NACIONAL, DOCENTE)`.
- `_ROLES_ESCRITURA = (UPGD, DOCENTE)`.
- En `crear_ficha_basica`, para `UPGD` se descarta `payload.cod_upgd` y se impone `current_user.cod_upgd`; para `DOCENTE` se respeta el valor enviado.
- En `listar_fichas_basicas`, un `UPGD` fuerza el filtro `cod_upgd == current_user.cod_upgd` e ignora el query param `cod_upgd` (no puede forjar el filtro). El resto de roles usan el query param `cod_upgd` si viene.
- En `obtener_ficha_basica`, tras resolver la ficha se llama `_asegurar_ficha_propia` → 403 si el `UPGD` apunta a una `cod_upgd` ajena.
- `creado_por_usuario_id` se setea desde `current_user.id` (nunca del payload).

### Filtros del listado (query params)
`cod_evento`, `semana` (→ `semana_epidemiologica`), `anio`, `num_id`, `cod_upgd`. Todos opcionales y combinables.

---

## Formas JSON exactas

### Request `POST /api/v1/fichas/datos-basicos`

```json
{
  "cod_upgd": "150010123456",
  "subindice": "01",
  "cod_evento": "100",
  "f_grabacion": "2026-09-25",
  "f_notificacion": "2026-09-25",
  "anio": 2026,
  "semana_epidemiologica": 38,
  "tipo_id": "CC",
  "num_id": "1023456789",
  "primer_nombre": "Pepito",
  "segundo_nombre": "Antonio",
  "primer_apellido": "Perez",
  "segundo_apellido": "Gomez",
  "telefono": "3001234567",
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
  "grupos_poblacionales": {"gestante": false, "desplazado": false},
  "clasificacion_caso": 1,
  "hospitalizado": false,
  "condicion_final": 1
}
```

Campos con default (pueden omitirse): `subindice`, `segundo_nombre`, `segundo_apellido`, `telefono`, `identidad_genero`, `orientacion_sexual`, `pais_ocurrencia`, `grupos_poblacionales`, `hospitalizado`, `condicion_final`.

### Response (201 / 200) — `FichaDatosBasicosOut`

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
  "num_id": "1023456789",
  "primer_nombre": "Pepito",
  "segundo_nombre": "Antonio",
  "primer_apellido": "Perez",
  "segundo_apellido": "Gomez",
  "telefono": "3001234567",
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
  "grupos_poblacionales": {"gestante": false, "desplazado": false},
  "clasificacion_caso": 1,
  "hospitalizado": false,
  "condicion_final": 1,
  "creado_por_usuario_id": 1
}
```

### Listado `GET /api/v1/fichas/datos-basicos`
Array de `FichaDatosBasicosOut` (misma forma de arriba).

---

## Salida de pruebas

### `.venv/bin/pytest -q` (suite completa)

```
29 passed, 36 warnings in 7.25s
```

### `tests/test_ficha_basica.py` (aislado)

```
8 passed, 16 warnings in 3.82s
```

Casos cubiertos:

| Test | Verifica |
| ---- | -------- |
| `test_sin_auth_401` | GET y POST sin token → 401 |
| `test_crear_201` | 201 + campos y defaults + `creado_por_usuario_id` + fechas ISO |
| `test_leer_200` | 200 + campos del objeto |
| `test_leer_inexistente_404` | 404 |
| `test_listar_con_filtro` | filtro por `cod_evento` devuelve solo la coincidencia |
| `test_upgd_forja_cod_upgd_se_impone_la_suya` | UPGD envía `cod_upgd` ajena → se persiste la propia |
| `test_upgd_ficha_ajena_403` | UPGD lee ficha de otra UPGD → 403 |
| `test_upgd_solo_ve_sus_fichas` | listado de UPGD solo contiene sus fichas |

### `.venv/bin/ruff check .`

```
All checks passed!
```

### `.venv/bin/alembic upgrade head`

```
Running upgrade 024c8692085a -> 45be635431fb, ficha_datos_basicos
```

---

## Desviaciones / decisiones con respecto al contrato

1. **`cod_upgd` requerido en el payload de creación.** El contrato lo marca "obligatorio"; se exige `min_length=1` en `FichaDatosBasicosCreate`. Para `UPGD` el backend lo sobreescribe (forzado a la propia), por lo que no hay ambigüedad.
2. **`grupos_poblacionales` con `default=dict` (callable)** en vez de `default={}` literal, para evitar el antipatrón de mutable default en SQLAlchemy. Efecto observable idéntico: columna `JSONB NOT NULL` con `{}` al crear.
3. **`creado_por_usuario_id` nullable en el modelo** (FK a `usuarios.id`), pero siempre se setea desde `current_user.id` en el endpoint. Se deja nullable para permitir borrados lógicos/auditoría futura sin bloquear la FK; el contrato no exige `NOT NULL` explícito.
4. **`FichaDatosBasicosUpdate` definido pero sin endpoint.** Sin PUT/PATCH en este alcance (Sprint 3), como indica el contrato. Se exporta por completitud.
5. **`subindice`, `identidad_genero`, `orientacion_sexual`, `hospitalizado`, `condicion_final`** tienen `nullable=False` con default Python-side (no server default). El ORM siempre las rellena; una inserción por SQL crudo requeriría explicitarlas. No afecta el contrato REST.

## Notas / riesgos

- No se valida que `cod_upgd` exista en `upgd_caracterizacion` (el contrato no lo pide; `cod_upgd` en la ficha es String indexado, sin FK). Si en Sprint 3 se quiere integridad referencial, agregar FK + migración.
- Warnings de pytest son pre-existentes (`crypt` deprecado, `InsecureKeyLengthWarning` por `SECRET_KEY` corto de 23 bytes, `httpx`/`testclient`). No introducidos por esta tarea.
