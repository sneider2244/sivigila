# Reglas y constraints

Obligatorio para todo el código nuevo. El objetivo es no repetir los errores
del legacy.

## Arquitectura

- El dominio y los servicios **NO** importan FastAPI, Jinja2 ni nada de `web/`.
- La UI nunca accede directo a la base de datos: siempre pasa por un service.
- Un router no tiene lógica de negocio: valida entrada y delega.
- Un service no construye respuestas HTTP ni templates.

## Código

- **Enums, no strings.** `EstadoFicha.TERMINADA`, `Rol.ADMIN`, `TipoCampo.LISTA`.
  Nunca `"Terminada"`, `"admin"`, `"lista"` sueltos.
- **Pydantic valida todo lo que entra.** Fechas (`AAAA-MM-DD`), edades,
  campos dinámicos. No confiar en el cliente.
- **SQL con columnas explícitas.** Prohibido armar `INSERT`/`UPDATE` con
  `", ".join(data.keys())`. Los campos se declaran.
- **Sin magic numbers ni magic strings.** Si un valor se repite, va a `domain/`.
- **Sin comentarios** salvo que se pidan.
- Nombres de código en inglés o español, pero consistente dentro de un módulo.
- Funciones chicas; si un módulo pasa ~300 líneas, dividir.

## Seguridad

- Contraseñas: hash + salt (PBKDF2 portado o argon2). Nunca texto plano.
- Secretos por variables de entorno (`.env`). Nada hardcodeado en prod.
- CSRF activo en todo POST.
- Rate-limit en el login.
- No loguear contraseñas ni tokens.

## Datos

- **Nunca** versionar `sivigila.db`, `.env`, `__pycache__/` ni dumps.
- Cambios de esquema solo por migración Alembic, nunca a mano.
- Toda acción sensible se registra en `auditoria`.

## Git

- No commitear sin pedido explícito.
- Commits convencionales. Sin atribución de IA ni `Co-Authored-By`.
- No commitear secretos.

## Calidad

- Cada feature nueva con tests. El legacy tiene 0 tests; no seguir ese camino.
- Antes de dar algo por terminado: `ruff check .` y `pytest` en verde.
