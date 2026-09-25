# FLOW PLAN — Flujo estudiante + docente (enfoque aprendizaje)

> Spec de ejecución. Cada fase es corta, commiteable y verificable por separado.
> Los subagentes implementan leyendo ESTE archivo (contratos exactos) + los docs existentes.
> Nada fuera de este plan se considera "pedido". Si un subagente detecta algo no definido, lo reporta en su `*-report.md` y no lo inventa.

## Mapa de criterios del usuario (auto-validación)

| # | Criterio | Fase |
|---|----------|------|
| 1 | Estudiante accede con email (usuario) + número de identificación (contraseña) | 1, 4 |
| 2 | Docente accede con usuario + contraseña (solo creado en DB) | — (ya existe) |
| 3 | Registro de estudiante auto-login; rol elegible (todos menos DOCENTE) | 1, 4 |
| 4 | Rol dinámico (cambiable), no-bloqueante; flujo educativo no depende del rol | 1, 3, 4 |
| 5 | Docente ve listado de estudiantes registrados con buscador | 2, 6 |
| 6 | Docente asigna escenarios masivamente (checkboxes) | 2, 6 |
| 7 | Estudiante ve "mis asignaciones"; primera vez vacío | 5 |
| 8 | Estudiante al recargar ve su escenario y puede acceder | 5 |
| 9 | Docente puede ver la identificación (número) del estudiante | 2, 6 |
| 10 | Docente ve las respuestas y evalúa con un clic (sin IDs a mano) | 6 |
| 11 | Home con acceso a módulos; guard de auth; redirect de raíz | 4 |
| 12 | Login con selector Estudiante | Docente | 4 |
| 13 | Enfoque aprendizaje: rol = etiqueta, no candado | 3, 4 |

## Decisiones de diseño (rulings — se copian a `docs/STATUS.md`)

- **R-email**: `email` = `username` (sin columna nueva). `numero_identificacion` = password (hash Argon2).
- **R-numero**: `numero_identificacion` se guarda EN CLARO (columna nullable) para que el docente la vea. Login simbólico, no apto producción.
- **R-rol-dinamico**: rol cambiable vía `PATCH /auth/me`; nunca a `DOCENTE`. El RBAC jerárquico (scoping UPGD, transiciones) queda diferido como modo avanzado.
- **R-cod-upgd**: estudiantes crean ficha con `cod_upgd` por defecto = UPGD demo (`"150010123456"`). Nunca bloquea con 400.
- **R-no-leak**: el estudiante NUNCA recibe `datos_esperados` (es la clave de respuestas). El `GET /estudiante/escenarios` debe exponer una vista sin `datos_esperados`.

## Contratos de API (fuente de verdad para backend y frontend)

### Auth
- `POST /api/v1/auth/register` — body `{ email: str, nombre_completo: str, numero_identificacion: str, rol?: RolEnum }`. Rol default `UPGD`; si `rol == DOCENTE` → 422. Email duplicado → 409. Crea `Usuario(username=email, hashed_password=hash(numero_identificacion), numero_identificacion=..., rol=..., cod_upgd="150010123456", activo=true)`. Respuesta (auto-login, mismo shape que login): `{ access_token, refresh_token, token_type: "bearer", usuario: UsuarioOut }`.
- `PATCH /api/v1/auth/me` — body `{ rol: RolEnum }`. Requiere auth. `rol == DOCENTE` → 422. Actualiza `rol` y devuelve `UsuarioOut`.
- `POST /api/v1/auth/login` — SIN CAMBIOS. Estudiante usa `username=email`, `password=numero_identificacion`.

### Docente
- `GET /api/v1/docente/estudiantes?q=` — solo DOCENTE. Lista usuarios `rol != DOCENTE`. Item: `{ id, username, nombre_completo, rol, numero_identificacion, activo }`. `q` filtra case-insensitive sobre `nombre_completo` OR `username` OR `numero_identificacion`. Orden por `nombre_completo`.
- `POST /api/v1/docente/escenarios/{escenario_id}/asignar` — body `{ estudiante_ids: [int] }` (BULK, reemplaza el single). Solo DOCENTE. Idempotente (salta pares ya asignados). Valida escenario (404) y estudiantes (404 si alguno no existe). Retorna `list[AsignacionOut]` de las creadas.

### Estudiante
- `GET /api/v1/estudiante/escenarios` — requiere auth. Retorna `list[EstudianteAsignacionOut]`:
  ```
  { "id": int, "estado": "ASIGNADO"|"EN_PROGRESO"|"COMPLETADO", "ficha_basica_id": int|null,
    "escenario": { "id": int, "titulo": str, "descripcion": str, "cod_evento": str } }
  ```
  **SIN `datos_esperados`** (no-leak).
- `POST /api/v1/estudiante/escenarios/{asignacion_id}/entregar` — body `{ ficha_basica_id: int }`. Requiere auth. 404 si asignación/ficha no existen; 403 si `asignacion.estudiante_id != current_user.id`. Setea `ficha_basica_id` + `estado=COMPLETADO`. Retorna `EstudianteAsignacionOut`.

### Ficha (desacople RBAC)
- `POST /api/v1/fichas/datos-basicos` — ahora cualquier rol autenticado puede crear. `cod_upgd`: si `current_user.cod_upgd` está seteado se usa; si no, se usa `payload.cod_upgd`; si tampoco, default `"150010123456"`. Eliminar el 400 por `cod_upgd` vacío.

## Fases

### Fase 1 (backend) — registro + rol dinámico
- Migración: columna `numero_identificacion` (String(20), nullable) en `usuarios`.
- `POST /auth/register` + `PATCH /auth/me` (contratos arriba).
- Tests: register OK + auto-login, email duplicado 409, DOCENTE rechazado 422, login como estudiante, patch rol OK, patch a DOCENTE 422.
- Verificar: `alembic upgrade head`, `ruff check .`, `pytest -q`.

### Fase 2 (backend) — listado de estudiantes + asignación masiva
- `GET /docente/estudiantes?q=` (contrato arriba).
- Migración: unique constraint `(escenario_id, estudiante_id)`.
- `POST /docente/escenarios/{id}/asignar` → bulk `{ estudiante_ids }`.
- Tests: listado filtra no-DOCENTE + busca por q, bulk crea múltiples, idempotencia (re-asignar no duplica), 404 estudiante inexistente.

### Fase 3 (backend) — desacople RBAC + entrega + escenarios de estudiante
- Relajar `_ROLES_ESCRITURA` y el `cod_upgd` default en `fichas_basicas.py`.
- `GET /estudiante/escenarios` → nueva respuesta `EstudianteAsignacionOut` (sin datos_esperados).
- `POST /estudiante/escenarios/{asignacion_id}/entregar`.
- Tests: cualquier rol crea ficha (sin 400), entregar OK (COMPLETADO + ficha_basica_id), entregar en asignación ajena 403, estudiante NO ve datos_esperados.

### Fase 4 (frontend) — acceso (dos modos) + registro + home + guard + selector rol
- `/login`: selector **Estudiante | Docente**. Estudiante: email + número identificación. Docente: usuario + contraseña. Link "Registrarme como estudiante" → formulario (email, nombre, número, selector de rol sin DOCENTE) que llama `/auth/register` (auto-login) → redirect.
- Raíz: eliminar `app/page.tsx` (placeholder); crear `(dashboard)/page.tsx` = home con tarjetas de módulos según rol (DOCENTE → "Docente"; estudiante → "Mis escenarios", "Caracterización", "Notificación").
- Guard client-side en `(dashboard)/layout.tsx`: sin sesión → `/login`.
- Actionbar: pestañas según rol; selector de rol dinámico en el Topbar (solo no-DOCENTE) → `PATCH /auth/me` + refresh del store.
- Login post-éxito → `/` (home). Mapper: `numero_identificacion` en los tipos.
- Verificar: `npm run lint` + `npm run build`.

### Fase 5 (frontend) — estudiante: mis escenarios + entrega
- `/mis-escenarios`: lista `GET /estudiante/escenarios`; estado vacío "Aún no tenés escenarios asignados"; badge de estado; botón "Diligenciar".
- "Diligenciar" → abre el formulario de datos básicos con `?asignacion_id=&cod_evento=`; al crear la ficha, llama `entregar(asignacion_id, ficha_id)` y redirige a `/mis-escenarios`.
- Complementarios: link opcional con `?ficha_basica_id=&cod_evento=` tras básica (la evaluación de `contenido` ya tolera ausencia).
- Verificar: `npm run lint` + `npm run build`.

### Fase 6 (frontend) — docente: asignación masiva + evaluar
- Dashboard docente: al asignar, **buscador de estudiantes + checkboxes masivos** (usa `GET /docente/estudiantes` + bulk asignar); muestra `numero_identificacion`.
- Ver respuestas: abrir la ficha de un estudiante desde la asignación (usa `ficha_basica_id`); botón "Evaluar" con un clic (usa `escenario_id` de la asignación, no IDs a mano) → muestra puntaje + detalle.
- Verificar: `npm run lint` + `npm run build`.

## Orden y forma de trabajo

1. Ejecutar fases 1→6 en orden. Cada fase = 1 subagente (backend o frontend).
2. Tras cada fase: verificar, actualizar `docs/STATUS.md`, commit convencional.
3. Backend y frontend NO corren en paralelo en este plan (hay dependencias de contrato entre 1-2-3 → 4-5-6).
4. Reportes de subagente en `docs/reports/` con sufijo de fase (`FP1-report.md`, `FP2-report.md`, ...).
