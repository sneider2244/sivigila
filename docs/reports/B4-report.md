# B4 — CRUD de Caracterización UPGD

**Estado:** Completado y verificado.
**Fecha:** 2026-09-25
**Alcance:** Modelo `UPGDCaracterizacion`, FK `Usuario.cod_upgd`, esquemas Pydantic, endpoints CRUD + RBAC, migración Alembic, seed de ejemplo y tests.

---

## Archivos creados / modificados

| Archivo | Acción |
| ------- | ------ |
| `app/models/upgd.py` | **Creado** — modelo `UPGDCaracterizacion` + enum `NivelComplejidad` |
| `app/models/usuario.py` | **Modificado** — FK `cod_upgd` -> `upgd_caracterizacion.cod_prestador` + `relationship` |
| `app/models/__init__.py` | **Modificado** — exporta `UPGDCaracterizacion` y `NivelComplejidad` |
| `app/schemas/upgd.py` | **Creado** — `Create` / `Update` / `Out` (Pydantic v2) |
| `app/schemas/__init__.py` | **Modificado** — exporta los nuevos esquemas (+ fix typo `Etnia` -> `EtniaOut`) |
| `app/api/v1/endpoints/caracterizacion.py` | **Creado** — endpoints CRUD + RBAC |
| `app/api/v1/api.py` | **Modificado** — wiring del router |
| `app/db/seed.py` | **Modificado** — `seed_upgd()` (UPGD de ejemplo vinculada a DOCENTE) |
| `alembic/versions/024c8692085a_upgd_caracterizacion.py` | **Creado** (autogenerate) — tabla + FK |
| `tests/test_caracterizacion.py` | **Creado** — 8 tests |

---

## Contrato JSON (exacto, snake_case)

### `UPGDCaracterizacion` — tabla `upgd_caracterizacion`

| Campo | Tipo SQL | JSON | Notas |
| ----- | -------- | ---- | ----- |
| `cod_prestador` | `String(12)` PK | `str` | ej. `"150010123456"` |
| `razon_social` | `String(255)` | `str` | no nulo |
| `nit` | `String(20)` | `str` | no nulo |
| `nivel_complejidad` | `Integer` | `int` | rango 1..4 (validado por `NivelComplejidad` IntEnum) |
| `cove` | `Boolean` | `bool` | default `false` |
| `unidad_analisis` | `Boolean` | `bool` | default `false` |
| `internet` | `Boolean` | `bool` | default `false` |
| `activo` | `Boolean` | `bool` | default `true` |
| `departamento_codigo` | `String(2)` FK | `str \| null` | -> `departamentos.codigo` |
| `municipio_codigo` | `String(5)` FK | `str \| null` | -> `municipios.codigo` |

### Endpoints (bajo `/api/v1`)

| Método | Ruta | Éxito | Errores |
| ------ | ---- | ----- | ------- |
| `GET` | `/upgd` | `200` lista | `401`, `403` |
| `GET` | `/upgd/{cod_prestador}` | `200` | `401`, `403`, `404` |
| `POST` | `/upgd` | `201` | `401`, `403`, `409`, `422` |
| `PUT` | `/upgd/{cod_prestador}` | `200` | `401`, `403`, `404`, `422` |

### Ejemplo de respuesta (`GET /upgd/150010123456`)

```json
{
  "cod_prestador": "150010123456",
  "razon_social": "Hospital Simulado SIVIGILA",
  "nit": "900000000-1",
  "nivel_complejidad": 2,
  "cove": true,
  "unidad_analisis": true,
  "internet": true,
  "activo": true,
  "departamento_codigo": "05",
  "municipio_codigo": "05001"
}
```

---

## Decisiones de RBAC

| Rol | `GET /upgd` y `GET /upgd/{cod}` | `POST` / `PUT` |
| --- | ------------------------------- | -------------- |
| `UPGD` | solo su propia `cod_upgd` (otra -> `403`) | solo la propia (otra -> `403`) |
| `MUNICIPAL` | todo | **no** (403) |
| `DEPARTAMENTAL` | todo | **no** (403) |
| `NACIONAL` | todo | **no** (403) |
| `DOCENTE` | todo | cualquiera (setup de escenarios) |
| `UI` | **no** (403) | **no** (403) |

- Implementado con `require_roles(*roles)` de `app/core/rbac.py`, reutilizado como
  singletons de módulo (`_lectura_dependency`, `_escritura_dependency`) para evitar B008.
- La verificación "UPGD propio vs ajeno" se hace con `_asegurar_upgd_propia()`:
  si `usuario.rol == UPGD` y `usuario.cod_upgd != cod_prestador` -> `403`.
- El rol `UI` no aparece en el contrato (opera con fichas, no con caracterización),
  por lo que queda excluido de ambos conjuntos de roles y recibe `403`.

---

## Rulings / desviaciones

1. **`nivel_complejidad` como `Integer` en BD, `IntEnum` en capa Pydantic.**
   El contrato exige `int` en el JSON (1..4). Se persiste `Integer` y la validación
   del rango + tipado se hace con `NivelComplejidad(IntEnum)` en `schemas/upgd.py`.
   Al serializar, Pydantic v2 emite `int`, por lo que el contrato se cumple 1:1.
   *Motivo:* evita crear un tipo ENUM nativo en Postgres y mantiene el JSON como entero.

2. **FK `Usuario.cod_upgd` con nombre explícito.**
   `ForeignKey(..., name="fk_usuarios_cod_upgd_upgd_caracterizacion")`. Sin nombre,
   el autogenerate generaba `drop_constraint(None, ...)` que falla en `downgrade`.
   Con nombre explícito, `upgrade`/`downgrade` son simétricos y `alembic check`
   reporta *"No new upgrade operations detected"* (sin drift).

3. **`409 Conflict` en `POST` duplicado.**
   El contrato no lo especifica, pero se agregó para no exponer un `IntegrityError`
   500 al reutilizar un `cod_prestador`. Documentado aquí como ruling.

4. **Forward references en relationships.**
   Se usa el patrón canónico SQLAlchemy 2.0: `from __future__ import annotations`
   + import bajo `TYPE_CHECKING` + anotación sin comillas. Ruff (F821/UP037) limpio
   y resolución por registry correcta en runtime.

5. **Fix de typo preexistente en `app/schemas/__init__.py`.**
   `__all__` declaraba `"Etnia"` en vez de `"EtniaOut"` (F401). Se corrigió a
   `"EtniaOut"`; ningún módulo importaba `Etnia` desde `app.schemas`, por lo que no
   hay impacto.

---

## Resultados de verificación

```
alembic upgrade head  -> OK (migración 024c8692085a aplicada; sin operaciones pendientes)
alembic check         -> "No new upgrade operations detected."
ruff check .          -> All checks passed!
pytest -q             -> 21 passed, 22 warnings
```

- Tests de caracterización (8): `crear_201`, `leer_200`, `leer_inexistente_404`,
  `update_200`, `sin_auth_401`, `upgd_ajeno_403`, `upgd_propio_200`,
  `upgd_propio_update_ajeno_403`.
- Seed `seed()` ejecutado con éxito (idempotente): UPGD de ejemplo
  `150010123456` creada y vinculada al usuario `docente`.

---

## Notas / próximos pasos

- El proyecto aún no define una naming convention global en `Base.metadata`.
  Con este cambio, solo la FK nueva de `usuarios` quedó nombrada explícitamente;
  el resto de constraints conserva los nombres por defecto de Postgres. Si se quiere
  estabilidad total de autogenerate a futuro, evaluar adoptar una convención en un
  PR aparte (scope distinto a B4).
- `GET /upgd` (listado) quedó implementado como endpoint opcional del contrato,
  útil para el dashboard de DOCENTE.
