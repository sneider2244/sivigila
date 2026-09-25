# B2 — Usuarios + RBAC + Autenticación JWT

## Estado

Completado. `pytest` 6/6 green, `ruff check .` green, `alembic upgrade head` aplicado (revisión `6c9a66ee4d82`).

## Archivos creados / modificados

### Creados

| Archivo | Contenido |
| --- | --- |
| `app/models/usuario.py` | `RolEnum` (6 roles) + modelo `Usuario` en estilo SQLAlchemy 2.0 (`Mapped`/`mapped_column`). |
| `app/core/security.py` | Hash Argon2 (Passlib), emisión/decode JWT (PyJWT), `get_current_user` (OAuth2PasswordBearer). |
| `app/core/redis.py` | Cliente Redis asíncrono para blacklist: `blacklist_token(token, ttl)` e `is_blacklisted(token)`. |
| `app/core/rbac.py` | Factory `require_roles(*roles)` → dependencia que valida `current_user.rol`. |
| `app/schemas/usuario.py` | Schemas Pydantic v2: `LoginRequest`, `RefreshRequest`, `TokenResponse`, `UsuarioOut`, `LoginResponse`. |
| `app/api/v1/endpoints/auth.py` | Router `/auth` (login, refresh, logout, me). |
| `app/db/seed.py` | `seed_users()` upsert del DOCENTE por defecto (runnable `python -m app.db.seed`). |
| `alembic/versions/6c9a66ee4d82_add_usuarios_table.py` | Migración de la tabla `usuarios`. |
| `tests/conftest.py` | Fixtures: BD de prueba dedicada `sivigila_test`, override de `get_db`, cliente `httpx.AsyncClient`. |
| `tests/test_auth.py` | 5 tests de autenticación + RBAC. |

### Modificados

| Archivo | Cambio |
| --- | --- |
| `app/models/__init__.py` | Exporta `RolEnum`, `Usuario`. |
| `app/schemas/__init__.py` | Exporta los schemas de usuario. |
| `app/api/v1/api.py` | Incluye `auth.router`. |
| `alembic/env.py` | `import app.models` para que autogenerate vea los modelos. |
| `pyproject.toml` | `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls = ["fastapi.Depends"]`. |

## Forma exacta de la respuesta de `POST /api/v1/auth/login`

Consumida por el frontend (JSON, tokens reales truncados aquí):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "usuario": {
    "id": 1,
    "username": "docente",
    "nombre_completo": "Usuario Docente",
    "rol": "DOCENTE",
    "cod_upgd": null,
    "activo": true
  }
}
```

- `rol` se serializa como string (el valor del `RolEnum`).
- `cod_upgd` es `null` para el usuario DOCENTE por defecto.

### Otros endpoints

- `POST /api/v1/auth/refresh` → body `{"refresh_token": "..."}` → `TokenResponse` (mismo shape sin `usuario`). Rota: revoca el refresh viejo y emite access+refresh nuevos.
- `POST /api/v1/auth/logout` → body `{"refresh_token": "..."}` + `Authorization: Bearer <access>` → revoca ambos tokens en Redis. Retorna `{"detail": "Sesión cerrada"}`.
- `GET /api/v1/auth/me` → `Bearer <access>` → `UsuarioOut`.

## Evidencia de verificación

### `alembic upgrade head`

```
INFO  [alembic.runtime.migration] Running upgrade 46739a8b908c -> 6c9a66ee4d82, add usuarios table
6c9a66ee4d82 (head)
```

### `ruff check .`

```
All checks passed!
```

### `pytest -q`

```
......                                                                   [100%]
6 passed, 8 warnings in 1.29s
```

Los 6 tests: `test_health` (B1, sigue verde) + 5 de `test_auth.py`
(login ok, login password incorrecta 401, `/me` con token 200, `/me` sin token 401, RBAC 403 para DOCENTE).

## Desviaciones / decisiones (rulings)

1. **Sin `ForeignKey` a `upgd_caracterizacion`** (según instrucción). `cod_upgd` quedó como `String(20)` indexado y nullable. La FK/relationship se agrega en Sprint 2 cuando exista la tabla.

2. **`require_roles` como factory en lugar de la clase `RequiereRol`** del doc. La clase con `__call__(self, usuario: Usuario = Depends(...))` no funciona de forma confiable en FastAPI (el `Depends` anidado en un `__call__` no se resuelve igual que una dependencia declarada). La factory `require_roles(*roles) -> dependency` es el patrón que sí funciona y mantiene exactamente los 6 roles y el mensaje 403 literal del doc:
   `"No posee los permisos necesarios para realizar esta operación en SIVIGILA."`

3. **`get_current_user` devuelve 401 en todos los fallos de auth** (token inválido, tipo incorrecto, revocado o usuario inexistente/inactivo). La instrucción mencionaba "404/401"; se eligió 401 uniforme (estándar OAuth2, evita filtrar existencia de usuarios). El 404 no se aplica en este flujo.

4. **`RolEnum` se mantuvo como `(str, enum.Enum)`** (patrón documentado en `BACKEND_ARCH.md`), con `# noqa: UP042` porque Ruff sugiere `enum.StrEnum`. Funcionalmente equivalentes para serialización y SQLAlchemy; se priorizó fidelidad al doc.

5. **`B008` (Depends en defaults) permitido vía config.** Se agregó `extend-immutable-calls = ["fastapi.Depends"]` a `pyproject.toml`, que es el patrón recomendado por Ruff para FastAPI. No cambia comportamiento.

6. **`LoginResponse` con shape plano** (tokens + `usuario` anidado) en lugar de envolver en `token`/`usuario`. Elegido para minimizar anidación en el frontend; documentado arriba.

7. **Blacklist con `ttl` real del token.** `token_remaining_ttl` calcula los segundos restantes a partir del claim `exp`; si `ttl <= 0` no se escribe en Redis. `is_blacklisted` degrada con warning si Redis está caído (no 500); `blacklist_token` (escritura) no degrada.

## Notas / riesgos

- **Advertencias de `SECRET_KEY` corto** (`InsecureKeyLengthWarning` de PyJWT): el default `change-me-in-production` (23 bytes) está por debajo de los 32 bytes recomendados para HS256. No rompe tests, pero **debe rotarse por un secreto >= 32 bytes** en producción (vía `.env`).
- El cliente Redis se crea a nivel de módulo (`Redis.from_url`); conexión lazy, OK para el patrón asíncrono actual. Para producción convendría manejar reconexión/cierre explícito.
- `tests/conftest.py` usa `NullPool` en el engine de test para evitar reutilización de conexiones entre event loops de pytest-asyncio (cada test corre en su propio loop).
