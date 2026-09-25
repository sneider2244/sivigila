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

## Sprint 2 — Caracterización UPGD y Notificación Individual Básica

- [x] **B4** CRUD Caracterización UPGD (modelo + FK Usuario + endpoints + RBAC) — ver `docs/reports/B4-report.md`
- [x] **B5** CRUD Notificación Individual - Datos Básicos (modelo FichaDatosBasicos + endpoints + RBAC) — ver `docs/reports/B5-report.md`
- [x] **F3** Formulario responsivo Caracterización UPGD — ver `docs/reports/F3-report.md`
- [x] **F4** Formulario Datos Básicos con validaciones dependientes — ver `docs/reports/F4-report.md`

## Sprint 3 — Datos Complementarios Dinámicos y Sistema de Ajustes

- [x] **B6** FichaDatosComplementarios JSONB + validación Pydantic por evento (Ofídico) — ver `docs/reports/B6-report.md`
- [x] **B7** Estados de fichas (Notificada/En Ajuste/Confirmada/Descartada) + trazabilidad — ver `docs/reports/B7-report.md`
- [x] **F5** Formulario Datos Complementarios (chips Sí/No, síntomas) — ver `docs/reports/F5-report.md`
- [x] **F6** Actionbar sticky + navegación por pestañas + modal búsqueda de casos — ver `docs/reports/F6-report.md`

## Sprint 4 — Módulo Docente/Simulación, Reportes y QA

- [x] **B8** API docentes: escenarios clínicos simulados + evaluación automatizada — ver `docs/reports/B8-report.md`
- [x] **F7** Dashboard del Docente (revisión de diligenciamiento de estudiantes) — ver `docs/reports/F7-report.md`
- [ ] **E2E** Pruebas end-to-end Playwright + auditoría de accesibilidad

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
- **R12** Rol `UI` queda 403 en `/upgd` (la matriz RBAC no le asigna gestión de caracterización; UI solo notifica/transfiere casos). (Coste: si luego UI necesita leer UPGD, agregar permiso.)
- **R13** No hay naming convention global en `Base.metadata` (las FKs se nombran explícitamente). Evaluar adoptar `naming_convention` en un PR futuro para estabilizar `alembic autogenerate`. (Coste: autogenerate puede proponer renombres si no se cuida.)
- **R14** Los campos condicionales del frontend (otraIdentidad, grupoÉtnico, fHospitalización, fDefunción, certificado, gestante, desplazado) se mapean al JSONB `fichas_datos_basicos.grupos_poblacionales` (claves snake_case: `otra_identidad`, `grupo_etnico`, `gestante`, `semanas_gestacion`, `desplazado`, `f_hospitalizacion`, `f_defuncion`, `certificado`). El backend solo persiste el dict. Motivo: el modelo documentado en `BACKEND_ARCH.md` no lista esas columnas y `grupos_poblacionales` es el bucket JSONB para datos dinámicos. (Coste: menos tipado estricto en esos campos; se puede migrar a columnas si se requiere integridad referencial.)
- **R15** Sin `datos-complementarios.html`, el set de síntomas del Accidente Ofídico se define así (y se persiste en el contrato B6/F5): locales {edema,dolor,eritema,equimosis,flictenas,necrosis_local}, sistémicas {nauseas,vomito,dolor_abdominal,bradicardia,hipotension,sangrado}, complicaciones {celulitis,necrosis,insuficiencia_renal,hipoxia}, datos_accidente {fecha,direccion,agente_agresor}, atencion_hospitalaria {empleo_suero,dosis}. `extra="forbid"` en el esquema. (Coste: si aparece el prototipo real, reconciliar estos campos.)
- **R16** Matriz de transiciones de estados definida por diseño (documentada en `docs/reports/B7-report.md`, ajustable en `_TRANSICIONES_PERMITIDAS`). El contrato solo decía "valida transición". (Coste: si el negocio define otra matriz, ajustar la constante.)
- **R17** Shape de asignaciones (`GET /docente/asignaciones`) es PLANA: `{ id, escenario_id, escenario_titulo, estudiante_id, estudiante_username, estudiante_nombre, estado, ficha_basica_id }`. F7 lo modeló anidado (`escenario{...}`, `estudiante{...}`) por error; se corrigió el tipo/mapper/página a flat camelCase. (Coste: ninguno, es la reconciliación correcta.)

## Progreso

- `2026-09-25` B1 y F1 completos (DONE, auto-verificados). Backend: health `{"status":"ok"}`, pytest `1 passed`, ruff clean, Postgres16+Redis7 healthy vía Docker, `alembic upgrade head` OK. Frontend: lint y `next build` limpios. Gotchas Next 16 registrados en `docs/reports/F1-report.md` (Turbopack, `@use` vs `@import`, `src/app` shadowing, Geist→Inter).
- `2026-09-25` B2 y F2 completos. Backend: pytest `6 passed`, ruff clean, `alembic upgrade head` (tabla `usuarios` + enum `rol_enum`), login verificado en vivo (200). Frontend: lint + build limpios; contrato de login reconciliado con backend (R10). Quedan 2 warnings no bloqueantes en backend: `SECRET_KEY` default corto (rotar en prod) y ajustes de lint documentados.
- `2026-09-25` B3 completo → **Sprint 1 terminado**. pytest `13 passed`, ruff clean, migración `catalogos` aplicada, seed idempotente. Sembrado: 33 departamentos, 124 municipios, 19 eventos, 13 ocupaciones, 6 etnias (datos curados, no completos — ampliar sin tocar el seed). Endpoints `/catalogos/*` sin auth (R11).
- `2026-09-25` B4 + F3 completos. Backend: pytest `21 passed`, ruff clean, migración `upgd_caracterizacion` aplicada + FK `usuarios.cod_upgd` (R7 resuelta). Frontend: lint + build limpios, ruta `/caracterizacion` prerenderizada.
- `2026-09-25` B5 + F4 completos → **Sprint 2 terminado**. Backend: pytest `29 passed`, ruff clean, migración `ficha_datos_basicos` aplicada; UPGD fuerza su `cod_upgd`, filtros de listado. Frontend: lint + build limpios, ruta `/notificacion/datos-basicos`; validaciones dependientes vía Zod + `grupos_poblacionales` (R14). Deferred menores: catálogos static placeholder en F4 (wirear a `useCatalogos`) y `cod_upgd` de ficha sin FK (evaluar en Sprint 3).
- `2026-09-25` B6 + F5 completos. Backend: pytest `37 passed`, ruff clean, migración `ficha_datos_complementarios` aplicada; POST duplicado → 409 explícito; validación ofídico con `extra="forbid"`. Frontend: lint + build limpios, ruta `/notificacion/datos-complementarios`; componente `YNChip` para reducir duplicación. Deferred: `cod_evento` de complementaria no se valida contra `ficha_basica.cod_evento` (ver en B7); catálogo `agente_agresor` y `empleo_suero` con convenciones educativas.
- `2026-09-25` B7 + F6 completos → **Sprint 3 terminado**. Backend: pytest `46 passed`, ruff clean, migración `estados_y_trazabilidad` aplicada; matriz de transiciones (R16). Frontend: lint + build limpios; Actionbar sticky + NavigationTabs + Topbar con logout + modal de búsqueda. Deferred: consistencia `cod_evento` complementaria vs básica (prioridad baja); `_base.scss` `overflow-x: hidden` puede interferir con sticky (revisar).
- `2026-09-25` B8 + F7 completos. Backend: pytest `52 passed`, ruff clean, migración `modulo_docente` aplicada; evaluación automatizada por comparación de campos planos + `contenido`. Frontend: lint + build limpios, ruta `/docente/escenarios`; corregido shape plano de asignaciones (R17). Deferred: sin unique constraint `(escenario_id, estudiante_id)`; `GET /estudiante/escenarios` no filtra `activo`; `downgrade` de Alembic no dropea el enum (gotcha autogenerate).
## Descubrimientos

- **Los prototipos HTML no existen en el repo** (`caracterizacion.html`, `sivigila.html`, `datos-complementarios.html`, `caracterizacion.css`). Los docs los citan como fuente de verdad de campos, pero nunca se commitearon. Sprint 2/3 se construye desde el spec que SÍ está en docs: `FichaDatosBasicos` completo en `BACKEND_ARCH.md`, lista parcial UPGD en `BACKEND_SUBAGENT_PROMPT.md`. Si aparecen los prototipos, reconciliar campos.
- **Deferred (menor):** los selects departamento/municipio de F3 usan códigos DANE placeholder. Wirear a `/catalogos/departamentos` y `/catalogos/municipios` (ya existen desde B3) en una tarea de pulido.
