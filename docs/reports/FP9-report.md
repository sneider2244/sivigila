# FP9 — Separar el área docente en tres páginas (lista / crear / detalle)

## Resumen

Se reestructuró la página monolítica `/docente/escenarios` (que contenía formulario de creación, selector de estudiantes, tarjetas de escenarios, asignaciones globales y modal de ficha) en **tres rutas independientes**, extrayendo a su vez los componentes reutilizables a `src/components/docente/`.

## Rutas y flujo

| Ruta | Archivo | Qué hace |
|------|---------|----------|
| `/docente/escenarios` | `src/app/(dashboard)/docente/escenarios/page.tsx` | Lista de escenarios como tarjetas (título, descripción, evento, badge activo/inactivo). Cada tarjeta es un `Link` al detalle. Botón "Crear escenario" → `/docente/escenarios/nuevo`. Estado vacío "No hay escenarios creados todavía." |
| `/docente/escenarios/nuevo` | `src/app/(dashboard)/docente/escenarios/nuevo/page.tsx` | `EscenarioForm` extraído (titulo, descripcion textarea, cod_evento select desde `/catalogos/eventos`, activo `RadioYN`). Al crear con éxito → `router.replace('/docente/escenarios/{id}')`. Botón "Volver". |
| `/docente/escenarios/[id]` | `src/app/(dashboard)/docente/escenarios/[id]/page.tsx` | Header (título, descripción, evento, badge), sección "Asignar estudiantes" (`EstudianteSelector`), sección "Asignaciones (N)" con las asignaciones del escenario. |

Flujo de creación → detalle: `createEscenario` retorna el escenario con `id`; en `onSuccess` se invalida `["docente","escenarios"]` y se redirige al detalle del id creado.

## Archivos creados

- `front/src/components/docente/EstudianteSelector.tsx` + `EstudianteSelector.module.scss` — selector reutilizable (buscador + checkboxes + bulk assign). Invalida `["docente","escenarios",{id},"asignaciones"]` al asignar.
- `front/src/components/docente/FichaBasicaModal.tsx` + `FichaBasicaModal.module.scss` — agrupa `FichaBasicaModal`, `FichaResumen`, `FichaItem`, `DatosComplementariosResumen` y los helpers `humanizarEtiqueta`/`formatValorComplementario`.
- `front/src/app/(dashboard)/docente/escenarios/nuevo/page.tsx` + `nuevo.module.scss`.
- `front/src/app/(dashboard)/docente/escenarios/[id]/page.tsx` + `detalle.module.scss`.

## Archivos modificados

- `front/src/app/(dashboard)/docente/escenarios/page.tsx` — reescrita como lista.
- `front/src/app/(dashboard)/docente/escenarios/escenarios.module.scss` — reducido a estilos de lista/cards.
- `front/src/lib/docente.ts` — eliminado `getAsignaciones` global; añadido `getAsignacionesPorEscenario(escenarioId)` (pega `GET /docente/escenarios/{id}/asignaciones`). `evaluarFicha` ya no existía (se quitó en FP7).
- `front/src/types/index.ts` — en `EscenarioAsignacion`/`Raw`/`mapEscenarioAsignacion` se reemplazó `numeroIdentificacion`/`numero_identificacion` por `estudianteNumeroIdentificacion`/`estudiante_numero_identificacion`, alineado al nuevo contrato del endpoint de asignaciones.

## Cómo se muestra la lista de ~100 asignaciones

La sección "Asignaciones (N)" itera el arreglo devuelto por `GET /docente/escenarios/{id}/asignaciones` (el backend ya lo ordena por nombre). Se renderiza un `<ul>` con una fila por asignación: nombre + username, identificación (`· CC {n}` si existe), badge de estado y botón "Ver ficha" solo si `ficha_basica_id != null`. El contador `N` usa `asignaciones.length` directamente (sin paginación, apto para ~100 ítems; la fila es liviana y el modal de ficha solo se monta bajo demanda). El `EstudianteSelector` mantiene su propia lista acotada a `max-height` con scroll para el buscador.

## Lint / Build

- `npm run lint` → **OK** (sin salida).
- `npm run build` → **OK** (`next build`, Next 16.3.6 Turbopack; TypeScript OK). Rutas generadas:
  - `/docente/escenarios` (static)
  - `/docente/escenarios/nuevo` (static)
  - `/docente/escenarios/[id]` (dynamic, `ƒ`)

## Gotchas

- El contrato backend **no** documenta un `GET /docente/escenarios/{id}` individual, por lo que el detalle obtiene el escenario reutilizando `getEscenarios()` y filtrando por id (opción que habilita explícitamente la tarea) en lugar de exponer un helper `getEscenario(id)` contra un endpoint inexistente.
- `useParams()` (client component) se usa para leer `id` y se valida con `Number.isInteger` antes de habilitar la query de asignaciones, evitando llamadas con id inválido (`NaN`).
- `createEscenario` no se resetea: al ser página nueva se monta limpia; tras éxito se redirige (no hay reuso del form).
- Los estilos antes concentrados en `escenarios.module.scss` se repartieron entre los módulos de cada página y de los componentes compartidos (`components/docente/*`), con `@use` de `variables`/`mixins` siguiendo la convención del repo. Pequeña duplicación de tokens utilitarios (`.button`, `.buttonGhost`, `.banner`, `.errorBanner`, `.successBanner`) es intencional para mantener el patrón de CSS Modules por archivo.
- La pestaña "Docente" (`NavigationTabs`) sigue apuntando a `/docente/escenarios`, y `pathname.startsWith('/docente/escenarios/')` mantiene el estado activo en `nuevo` y `[id]` sin cambios.
- `getAsignaciones` global quedó eliminado; no hay referencias colgantes (solo quedan `numeroIdentificacion` en `EstudianteDocente` y en `auth.ts`, que son tipos distintos y no se tocaron).
