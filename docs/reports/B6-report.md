# Report B6 — Datos Complementarios (JSONB dinámico por evento)

## Estado: COMPLETO ✅

## Resumen ejecutivo

Implementación del módulo de Datos Complementarios con almacenamiento híbrido
JSONB (`FichaDatosComplementarios`), validación Pydantic v2 despachada por
`cod_evento` (esquema ofídico para "100"/"820", genérico `dict` para el resto) y
RBAC completo (UPGD restringido a sus propias fichas, DOCENTE escritura, roles
superiores lectura).

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `back/app/models/ficha_complementaria.py` | Modelo ORM `FichaDatosComplementarios` (`Mapped`/`mapped_column`, JSONB). |
| `back/app/schemas/complemento_ofidico.py` | Esquemas Pydantic v2 de la estructura ofídica (5 sub-esquemas + raíz). |
| `back/app/schemas/ficha_complementaria.py` | `Create`/`Update`/`Out` + validación que despacha al esquema ofídico. |
| `back/app/api/v1/endpoints/fichas_complementarias.py` | Endpoints POST/GET/PUT + RBAC. |
| `back/alembic/versions/5210c2ca17b8_ficha_datos_complementarios.py` | Migración (autogenerada) de la tabla. |
| `back/tests/test_ficha_complementaria.py` | 8 tests del módulo. |
| `docs/reports/B6-report.md` | Este reporte. |

## Archivos modificados

- `back/app/models/__init__.py` — export de `FichaDatosComplementarios`.
- `back/app/schemas/__init__.py` — export de `FichaDatosComplementariosCreate/Update/Out`.
- `back/app/api/v1/api.py` — registro del router `fichas_complementarias`.

## Modelo de datos (tabla `fichas_datos_complementarios`)

```python
class FichaDatosComplementarios(Base):
    __tablename__ = "fichas_datos_complementarios"

    id: Mapped[int]                      # PK
    ficha_basica_id: Mapped[int]         # FK -> fichas_datos_basicos.id, UNIQUE
    cod_evento: Mapped[str]              # String(10)
    contenido: Mapped[dict]              # JSONB
```

- `ficha_basica_id` con `unique=True` (una complementaria por ficha básica, 1:1).
- FK nombrada `fk_fichas_complementarias_ficha_basica`.
- `cod_evento` se persiste redundante respecto de la ficha básica **por contrato**
  (permite despachar la validación y consultas sin joins).

## JSON shapes exactos (esquema ofídico)

Contrato de la API para `cod_evento` en `{"100", "820"}` (Accidente Ofídico):

```json
{
  "datos_accidente": {
    "fecha": "2026-09-24",
    "direccion": "CRA 23 SUR 9-87",
    "agente_agresor": 17
  },
  "manifestaciones_locales": {
    "edema": true, "dolor": true, "eritema": false,
    "equimosis": false, "flictenas": false, "necrosis_local": false
  },
  "manifestaciones_sistemicas": {
    "nauseas": false, "vomito": false, "dolor_abdominal": false,
    "bradicardia": false, "hipotension": false, "sangrado": false
  },
  "complicaciones": {
    "celulitis": false, "necrosis": false,
    "insuficiencia_renal": false, "hipoxia": true
  },
  "atencion_hospitalaria": {
    "empleo_suero": 2,
    "dosis": null
  }
}
```

Esquemas Pydantic v2 (`complemento_ofidico.py`):

- `DatosAccidente`: `fecha: date`, `direccion: str`, `agente_agresor: int`.
- `ManifestacionesLocales`: 6 booleanos (`edema`, `dolor`, `eritema`, `equimosis`, `flictenas`, `necrosis_local`).
- `ManifestacionesSistemicas`: 6 booleanos (`nauseas`, `vomito`, `dolor_abdominal`, `bradicardia`, `hipotension`, `sangrado`).
- `Complicaciones`: 4 booleanos (`celulitis`, `necrosis`, `insuficiencia_renal`, `hipoxia`).
- `AtencionHospitalaria`: `empleo_suero: int`, `dosis: int | None = None`.
- `ComplementoOfidico`: compone los cinco anteriores.

Todos los sub-esquemas usan `ConfigDict(extra="forbid")` para garantizar la
estructura EXACTA (rechaza claves extra no contempladas por el contrato).

## Decisión de validación por evento

La validación se implementa con un `@model_validator(mode="after")` en la clase
base compartida `FichaDatosComplementariosBase` (heredada por `Create` y `Update`):

```python
_COD_EVENTOS_OFIDICOS = {"100", "820"}

@model_validator(mode="after")
def _validar_contenido_por_evento(self) -> Self:
    if self.cod_evento in _COD_EVENTOS_OFIDICOS:
        try:
            ComplementoOfidico.model_validate(self.contenido)
        except ValidationError as exc:
            raise ValueError(f"contenido inválido para el evento {self.cod_evento}: {exc}") from exc
    return self
```

Racional de la decisión:

- **`model_validator(mode="after")` y no `field_validator`**: la validación de
  `contenido` depende de un campo hermano (`cod_evento`). Con `mode="after"`
  ambos campos ya están resueltos, evitando depender del orden de validación.
- **`model_validate` + captura de `ValidationError` → `ValueError`**: propagar
  `ValueError` desde un validator es el patrón documentado de Pydantic v2; se
  convierte en un 422 de FastAPI con el detalle del error anidado.
- **`extra="forbid"`** en el esquema ofídico: cumple el requisito de estructura
  exacta y convierte cualquier error de tipo/typo en 422.
- **Caso genérico**: `contenido: dict` como tipo de campo; sin validación extra
  (se extiende en Sprints posteriores). Esto permite que el endpoint acepte
  complementos de otros eventos (ej. Dengue "110") sin bloquear el flujo.

## Endpoints

| Método | Ruta | Respuestas |
|--------|------|------------|
| `POST` | `/api/v1/fichas/datos-complementarios` | 201 creado, 401, 403, 404, 409, 422 |
| `GET` | `/api/v1/fichas/datos-complementarios/{ficha_basica_id}` | 200, 401, 403, 404 |
| `PUT` | `/api/v1/fichas/datos-complementarios/{ficha_basica_id}` | 200, 401, 403, 404, 422 |

### RBAC implementado

- **Lectura** (`GET`): `UPGD`, `MUNICIPAL`, `DEPARTAMENTAL`, `NACIONAL`, `DOCENTE`.
- **Escritura** (`POST`/`PUT`): `UPGD`, `DOCENTE`.
- **UPGD**: en POST/PUT/GET se resuelve la `FichaDatosBasicos` referida y se
  verifica `ficha.cod_upgd == current_user.cod_upgd`; si no coincide → **403**.
- **DOCENTE**: crea/actualiza cualquier ficha complementaria (setup de escenarios).
- **UI**: sin acceso (403 vía `require_roles`).

Nota de diseño: la complementaria NO almacena `cod_upgd` propio, por lo que la
verificación de pertenencia UPGD se resuelve cargando la ficha básica referida
(`_obtener_ficha_basica`). Esto mantiene una única fuente de verdad para la UPGD.

## Migración Alembic

- `alembic revision --autogenerate -m "ficha_datos_complementarios"` → `5210c2ca17b8`.
- `alembic upgrade head` → aplicada correctamente sobre PostgreSQL 16.
- La migración incluye `UniqueConstraint('ficha_basica_id')`, FK con nombre
  explícito y `JSONB(astext_type=sa.Text())`.

## Verificación

| Comando | Resultado |
|---------|-----------|
| `.venv/bin/alembic upgrade head` | ✅ OK |
| `.venv/bin/ruff check .` | ✅ All checks passed! |
| `.venv/bin/pytest -q` | ✅ 37 passed (11.31s) |

### Output de tests del módulo

```
tests/test_ficha_complementaria.py ................ 8 passed
```

Los 8 tests cubren: 401 sin auth, 201 ofídico válido, 422 ofídico inválido
(edema = string), 404 ficha básica inexistente, 403 UPGD sobre ficha ajena,
201 UPGD sobre ficha propia, GET 200 + 404, y 201 contenido genérico `dict`.

## Desviaciones y decisiones

1. **`cod_evento` redundante en la tabla**: exigido por el contrato. Se persiste
   aunque duplique el valor de la ficha básica. NO se valida que coincida con
   `ficha_basica.cod_evento` (el contrato no lo pide); se deja anotado para
   decidir en Sprint 3 si se impone consistencia.
2. **`409 Conflict` para duplicados**: el contrato define UNIQUE pero no el
   comportamiento ante una segunda POST a la misma `ficha_basica_id`. Se optó por
   devolver 409 explícito (en lugar de un 500 por `IntegrityError`), siguiendo el
   patrón ya existente en `caracterizacion.py`.
3. **`dosis` opcional**: declarado `int | None = None` para aceptar tanto su
   ausencia como `null`. El contrato dice `int | null`; la elección es la
   interpretación más laxa que sigue cumpliendo el ejemplo (`"dosis": null`).
4. **`extra="forbid"`** en el esquema ofídico: refuerza "estructura EXACTA",
   rechazando claves no contempladas. Si el frontend real envía claves adicionales
   en el complemento ofídico, habría que relajarlo (se documenta para revisión).
5. **PUT opcional implementado** como extensión natural del contrato (el contrato
   lo marca "opcional"). Acepta `cod_evento` + `contenido` (sin `ficha_basica_id`,
   que viene en la URL) y reutiliza la misma validación por evento.
6. **Sin `cod_upgd` en la tabla de complementarias**: la pertenencia UPGD se
   resuelve vía la ficha básica. Evita duplicar datos y posibles inconsistencias.

## Nota de seguridad / RBAC

- Autenticación obligatoria en los 3 endpoints vía `get_current_user` (JWT).
- Roles validados con `require_roles` (no con strings sueltos).
- El caso UPGD verifica la ficha básica referida antes de crear/leer/actualizar.
