# B3 — Reporte: Catálogos Oficiales (modelos + seed + endpoints + tests)

**Fecha:** 2026-09-25
**Carril:** Backend (`back/`)
**Estado:** DONE, auto-verificado

## Resumen

Se implementaron los catálogos oficiales del simulador SIVIGILA: modelos ORM
(SQLAlchemy 2.0 moderno), esquemas Pydantic v2, endpoints REST públicos, seed
idempotente con datos reales de Colombia y cobertura de tests. Todo verificado
con `alembic upgrade head`, `ruff`, `pytest` y doble ejecución del seed.

## Archivos creados

| Archivo | Descripción |
|---------|-------------|
| `app/models/catalogos.py` | Modelos `Departamento`, `Municipio`, `Evento`, `Ocupacion`, `Etnia` |
| `app/schemas/catalogo.py` | Esquemas `*Out` con `ConfigDict(from_attributes=True)` |
| `app/api/v1/endpoints/catalogos.py` | Router `/catalogos` con 5 endpoints |
| `alembic/versions/6fce7513b565_catalogos.py` | Migración autogenerada (5 tablas + FK + índice) |
| `tests/test_catalogos.py` | 7 tests de catálogos |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/models/__init__.py` | Exporta los 5 modelos nuevos |
| `app/schemas/__init__.py` | Exporta los 5 esquemas nuevos |
| `app/api/v1/api.py` | `include_router(catalogos.router)` |
| `app/db/seed.py` | `seed_catalogos()` + `seed()` (orquestador) + datos |
| `tests/conftest.py` | Seed de catálogos en el setup de la DB de test |

## Endpoints

Todos bajo `prefix="/catalogos"`, montados en `/api/v1/catalogos/...`:

| Método | Ruta | Filtro |
|--------|------|--------|
| GET | `/catalogos/departamentos` | — |
| GET | `/catalogos/municipios` | `?departamento=<cod>` (opcional) |
| GET | `/catalogos/eventos` | — |
| GET | `/catalogos/ocupaciones` | — |
| GET | `/catalogos/etnias` | — |

## Conteos sembrados (exactos)

| Catálogo | Registros |
|----------|-----------|
| Departamentos | **33** (32 + Bogotá D.C.) |
| Municipios | **124** |
| Eventos | **19** |
| Ocupaciones | **13** |
| Etnias | **6** |

Segunda ejecución del seed: **0 insertados en todos los catálogos** (idempotente).

## Datos: qué está curado vs. qué está completo

- **Departamentos — COMPLETO.** Los 33 (32 departamentos + Bogotá D.C.) con
  códigos DIVIPOLA oficiales de 2 dígitos.
- **Municipios — CURADO (no completo).** 124 municipios: las 33 capitales
  (código terminado en `001`, oficiales y verificados) más una selección
  representativa de los principales por departamento. El DIVIPOLA completo
  (~1100 municipios) **no** se sembró; la estructura (`MUNICIPIOS` como lista de
  tuplas) permite añadir el resto sin tocar el seed. Los códigos de municipios
  no capitales deben verificarse contra DIVIPOLA oficial antes de uso en
  producción.
- **Eventos — CURADO (subconjunto educativo).** 19 eventos de notificación
  obligatoria, incluyendo `100` Accidente Ofídico (referenciado en
  `PROJECT_PLAN.md`), Dengue (`110`/`115`), Malaria (`120`), Chagas, Leptospirosis,
  sífilis, VIH/Sida, tuberculosis, lepra, intoxicaciones y mortalidades. El listado
  completo de eventos SIVIGILA es mayor; los códigos deben validarse contra el
  protocolo oficial del INS antes de uso en producción.
- **Ocupaciones — CURADO.** Lista acotada de 13 ocupaciones comunes de la ficha
  (no es la CUOC completa).
- **Etnias — COMPLETO.** 6 grupos de la clasificación oficial DANE/INS.

## Verificación (evidencia)

- `alembic upgrade head` → OK (migración `6fce7513b565` aplicada; 5 tablas + FK
  `municipios.departamento_codigo` + índice).
- `ruff check .` → **All checks passed!**
- `pytest -q` → **13 passed** (6 auth + 1 health + 7 catálogos; 8 warnings no
  bloqueantes ya documentados en B2).
- `python -m app.db.seed` → OK; segunda ejecución idempotente (0 insertados).

## Rulings / desviaciones

- **R11 — Catálogos públicos sin auth.** Los endpoints de `/catalogos` NO llevan
  dependencia de autenticación: son datos de referencia que el frontend necesita
  para poblar comboboxes incluso antes del login. Documentado en el docstring del
  router; si se requiere restringirlos, se agrega `Depends(get_current_user)` por
  endpoint sin cambiar el contrato.
- **R12 — Códigos como PK natural (String), no ID sintético.** Los catálogos usan
  el código oficial como clave primaria (`"05"`, `"05001"`, `"100"`), alineando la
  API 1:1 con el formato DIVIPOLA/SIVIGILA.
- **R13 — `seed_catalogos` acepta un `session_factory` inyectable.** Permite
  sembrar la DB de test (`sivigila_test`) sin acoplar el seed a la DB de
  desarrollo.
- **R14 — Datos en `app/db/seed.py`, no `app/db/seed_data.py`.** El doc
  `BACKEND_ARCH.md` menciona `seed_data.py`, pero el código existente ya usaba
  `seed.py`; se siguió la convención real del repo. Los catálogos se definieron
  como constantes de módulo (no en un archivo separado) para mantener un único
  punto de seed.
- **R15 — `cod_evento` de la ficha (`String(10)`) es compatible con `Evento.codigo`
  (`String(10)`).** No hay FK ficha→evento en esta tarea; se alinean solo por tipo.

## Concernes / próximos pasos

- Los códigos de eventos y municipios no capitales son "best-effort" y deben
  validarse contra fuentes oficiales (DIVIPOLA 2024, protocolos INS) antes de
  cualquier uso no educativo.
- `Evento.codigo` se dejó como `String(10)` (no `Integer`) para tolerar códigos
  no numéricos futuros y mantener consistencia con `FichaDatosBasicos.cod_evento`.
