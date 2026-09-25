# STATUS — ledger de ejecución SIVIGILA

> Recovery map: si la sesión se cae o se reanuda en otro turno, leer este archivo
> y `git status` es suficiente para retomar. Las tareas marcadas `complete` NO se
> re-despachan.

## Cómo retomar

1. Leer `docs/STATUS.md` (este archivo) hasta la sección "Progreso".
2. Retomar en la primera tarea sin `complete`, respetando su carril (Backend vs Frontend).
3. Los reportes de subagentes están en `docs/reports/` (no hace falta abrirlos salvo fallo).

## Convención de tareas

- `B*` = backend (`back/`), secuenciales entre sí.
- `F*` = frontend (`front/`), secuenciales entre sí.
- Backend y Frontend corren en paralelo (directorios separados, sin archivos compartidos).

## Sprint 1 — Fundamentos, Autenticación y Catálogos

- [x] **B1** Scaffold FastAPI + infra (Docker Postgres/Redis, Alembic, config, health) — ver `docs/reports/B1-report.md`
- [x] **B2** Modelo Usuario + RolEnum + RBAC + JWT auth (login, refresh, RequiereRol) — ver `docs/reports/B2-report.md`
- [x] **B3** Catálogos oficiales (modelos + seed DIVIPOLA/eventos + endpoints) — ver `docs/reports/B3-report.md`
- [x] **F1** Reorganización `src/` + SCSS + deps + stores/lib/types — ver `docs/reports/F1-report.md`
- [x] **F2** Módulo de Autenticación (login page, useAuth, Zustand session, TanStack Query) — ver `docs/reports/F2-report.md`

## Rulings (decisiones tomadas en nombre del usuario)

- **R1** ~~No se commitea sin pedido explícito~~ SUPERSEDIDO por R6 (el usuario autorizó commitear). (Coste si falla: perdida de granularidad de rollback en git.)
- **R2** Python 3.12, Postgres 16 + Redis 7 por Docker (no hay clientes locales). (Coste: requiere Docker corriendo.)
- **R3** Gestor de paquetes pip + venv (`uv` no instalado); `pyproject.toml` sigue siendo el manifiesto. (Coste: instalación más lenta que uv.)
- **R4** Carriles backend/frontend en paralelo; dentro de cada carril, secuencial. (Coste: si hubiera una dependencia cruzada oculta, habría conflicto.)
- **R5** Revisión ligera: el implementador se auto-verifica (pytest/ruff/lint/build) y reporta evidencia; no se despachan subagentes revisores por tarea para conservar contexto. (Coste: menor rigor de revisión que el flujo SDD completo.)
- **R6** Commits autorizados por el usuario ("porfa vaya commiteando", 2026-09-25). Convencionales, sin atribución de IA ni `Co-Authored-By`. Se commitea a medida que se avanza. (Coste: ninguno, es pedido explícito.)
- **R7** `Usuario.cod_upgd` sin ForeignKey por ahora: `upgd_caracterizacion` es de Sprint 2 y aún no existe. FK/relationship se agregan en Sprint 2. (Coste: re-migración menor al añadir la FK.)
- **R8** SQLAlchemy 2.0 estilo moderno (`Mapped`/`mapped_column`), no el `Column` legacy que aparece en `docs/BACKEND_ARCH.md` (paste crudo del spec). (Coste: desviación cosmética del doc.)
- **R9** RBAC como dependency factory `require_roles(*roles)`, no la clase `RequiereRol` del doc (su patrón `Depends` en `__call__` no funciona bien en FastAPI). Mismo detalle 403. (Coste: desviación de implementación, semántica idéntica.)
- **R10** Contrato de login: backend devuelve `{ access_token, refresh_token, token_type, usuario }` (snake_case, `id` int). Frontend mapea a tipos camelCase. Se corrigió mismatch `user`→`usuario` y `id` string→number en `front/src/lib/auth.ts` + `types/index.ts`. (Coste: ninguno, es la reconciliación correcta.)
- **R11** Endpoints `/catalogos/*` sin auth (datos de referencia para comboboxes pre-login). (Coste: si luego se requiere restringirlos, hay que agregar dependencia de auth y tests.)

## Progreso

- `2026-09-25` B1 y F1 completos (DONE, auto-verificados). Backend: health `{"status":"ok"}`, pytest `1 passed`, ruff clean, Postgres16+Redis7 healthy vía Docker, `alembic upgrade head` OK. Frontend: lint y `next build` limpios. Gotchas Next 16 registrados en `docs/reports/F1-report.md` (Turbopack, `@use` vs `@import`, `src/app` shadowing, Geist→Inter).
- `2026-09-25` B2 y F2 completos. Backend: pytest `6 passed`, ruff clean, `alembic upgrade head` (tabla `usuarios` + enum `rol_enum`), login verificado en vivo (200). Frontend: lint + build limpios; contrato de login reconciliado con backend (R10). Quedan 2 warnings no bloqueantes en backend: `SECRET_KEY` default corto (rotar en prod) y ajustes de lint documentados.
- `2026-09-25` B3 completo → **Sprint 1 terminado**. pytest `13 passed`, ruff clean, migración `catalogos` aplicada, seed idempotente. Sembrado: 33 departamentos, 124 municipios, 19 eventos, 13 ocupaciones, 6 etnias (datos curados, no completos — ampliar sin tocar el seed). Endpoints `/catalogos/*` sin auth (R11).
