# FP6 — Reporte: Dashboard docente (asignación masiva + ver ficha + evaluar)

## Estado
Completo. `npm run lint` y `npm run build` pasan.

## Archivos modificados

- `front/src/types/index.ts`
- `front/src/lib/docente.ts`
- `front/src/app/(dashboard)/docente/escenarios/page.tsx`
- `front/src/app/(dashboard)/docente/escenarios/escenarios.module.scss`

## Cambios

### 1. Tipos (`types/index.ts`)
- `EstudianteDocente` + `EstudianteDocenteRaw` (snake_case) + `mapEstudianteDocente`.
- `EscenarioAsignacion` / `EscenarioAsignacionRaw`: añadido `numeroIdentificacion` / `numero_identificacion?` (opcional, defensivo — el contrato `AsignacionOut` no lo incluye; se resuelve del listado de estudiantes).

### 2. `lib/docente.ts`
- `asignarEscenario(escenarioId, estudianteIds: number[])` → `POST .../asignar` con `{ estudiante_ids }`, retorna `EscenarioAsignacion[]` (bulk).
- `getEstudiantes(q?)` → `GET /docente/estudiantes` (mapea a `EstudianteDocente`; `q` opcional).
- `getFichaBasica(id)` → `GET /fichas/datos-basicos/{id}` → `FichaDatosBasicosOut` (reusa `mapFichaDatosBasicosOut`).
- `evaluarFicha` sin cambios.

### 3. `docente/escenarios/page.tsx`
- **Asignación masiva** (`EstudianteSelector`): reemplaza el input de un solo `estudiante_id`. Buscador (`q` → `getEstudiantes`) + checkboxes (nombreCompleto, username, `numeroIdentificacion`). Botón "Asignar seleccionados (N)" → `asignarEscenario(id, ids)`.
- **Ver ficha** (`FichaBasicaModal` + `FichaResumen`): botón "Ver ficha" en `AsignacionRow` si `fichaBasicaId` existe; abre modal leyendo `getFichaBasica(id)` con resumen legible (num_id, nombres, apellidos, cod_evento, clasificacion_caso, hospitalizado, condicion_final, estado, edad, sexo, f_nacimiento, semana, UPGD).
- **Evaluar con un clic**: `handleEvaluar` usa `asignacion.escenarioId` + `asignacion.fichaBasicaId` (flat); no pide IDs a mano. Se resetea resultado previo antes de evaluar.
- **`numeroIdentificacion` en asignaciones**: se resuelve con un `Map<estudianteId, numeroIdentificacion>` a partir de `getEstudiantes()` (queryKey `["docente","estudiantes",""]`, compartido con el selector); fallback a `asignacion.numeroIdentificacion`.
- `EscenarioForm` intacto.

### 4. SCSS
Añadidas clases: `.selector`, `.selectorSearch`, `.selectorActions`, `.estudianteList`, `.estudianteItem`, `.estudianteLabel`, `.estudianteInfo`, `.estudianteNombre`, `.estudianteMeta`, `.overlay`, `.modal`, `.modalHeader`, `.modalTitle`, `.modalClose`, `.modalBody`, `.fichaList`, `.fichaRow`, `.fichaLabel`, `.fichaValue`.

## Flujo

1. Docente abre `/docente/escenarios`; en cada `EscenarioCard` busca estudiantes con `q` (nombre/correo/identificación), marca checkboxes y pulsa "Asignar seleccionados".
2. `asignarEscenario` hace el POST bulk; al éxito invalida `["docente","asignaciones"]` y limpia la selección.
3. En "Asignaciones", cada fila muestra nombre, correo y `numeroIdentificacion`; si hay `ficha_basica_id`, "Ver ficha" abre el modal con el resumen.
4. "Evaluar" (con un clic) envía `ficha_basica_id` + `escenario_id` y pinta puntaje/aciertos/detalle.

## Lint / Build

- `npm run lint` → sin salida (0 errores, 0 warnings).
- `npm run build` → "Compiled successfully", TypeScript OK, 10 rutas prerenderizadas estáticamente.

## Gotchas

- El contrato `AsignacionOut` (flat) **no** incluye `numero_identificacion`; por eso se resuelve desde `GET /docente/estudiantes` en el cliente y se agrega el campo como opcional/defensivo en el tipo (por si el backend lo expone después).
- `getEstudiantes("")` y `getEstudiantes()` producen la misma URL; se usa queryKey `["docente","estudiantes", ""]` en la página y `["docente","estudiantes", q]` en el selector para compartir caché de React Query (una sola petición).
- `clasificacion_caso` y `condicion_final` son enums numéricos sin etiquetas definidas en los docs; se muestran como valor crudo para no inventar mapeos.
- Se mantiene `"use client"` y no se tocaron dependencias.
