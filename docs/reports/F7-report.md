# F7 — Dashboard del Docente

## Estado

Completo. `npm run lint` y `npm run build` pasan sin errores.

## Archivos creados / modificados

- `front/src/types/index.ts` — se agregaron los tipos `EscenarioClinico`, `EscenarioAsignacion`, `EvaluacionResult` (camelCase) junto con sus versiones raw (snake_case) y mappers `mapEscenarioClinico` / `mapEscenarioAsignacion`.
- `front/src/lib/docente.ts` — cliente HTTP para los endpoints del docente (`getEscenarios`, `createEscenario`, `asignarEscenario`, `getAsignaciones`, `evaluarFicha`) usando la instancia `api` de `@/lib/axios` (que ya inyecta el token y maneja refresh).
- `front/src/app/(dashboard)/docente/escenarios/page.tsx` — página del dashboard ("use client").
- `front/src/app/(dashboard)/docente/escenarios/escenarios.module.scss` — SCSS Module con tokens del proyecto (`@use` de `_variables.scss` y `_mixins.scss`) y responsive.

## Flujos

### Crear escenario
1. Formulario con `react-hook-form` + `zodResolver`.
2. Campos: `titulo`, `descripcion`, `codEvento`, `activo` (chip Sí/No vía `RadioYN`) y `datosEsperados` (textarea JSON).
3. El JSON se valida con Zod vía `superRefine`: debe parsear como un objeto (no array, no null). Si es inválido se muestra el error en el campo y no se envía.
4. Al enviar, se hace `JSON.parse` del textarea y se llama a `POST /docente/escenarios` con body snake_case (`cod_evento`, `datos_esperados`). Se invalida la query de escenarios y se resetea el formulario.

### Asignar escenario
1. Cada tarjeta de escenario tiene un input numérico (`estudiante_id`) y un botón "Asignar".
2. Se valida que el id sea entero positivo.
3. `POST /docente/escenarios/{id}/asignar` con `{ estudiante_id }` (mutation de react-query).
4. Al éxito se invalida la query de asignaciones y se limpia el input.

### Ver asignaciones / Evaluar
1. El botón "Ver asignaciones" hace `scrollIntoView` a la sección de asignaciones.
2. La sección lista `GET /docente/asignaciones` (query de react-query) mostrando escenario.titulo, estudiante (nombre + username) y `estado`.
3. Si la asignación tiene `ficha_basica_id`, se muestra el botón "Evaluar" que llama a `POST /docente/evaluar` con `{ ficha_basica_id, escenario_id }`.
4. El resultado (`puntaje`, `aciertos/total`, `detalle`) se muestra debajo de la fila; `detalle` se renderiza como JSON.

### Guard de rol
- Se lee `user` de `useUserStore`; si `user?.rol !== "DOCENTE"` se renderiza "Acceso solo para docentes".
- Las queries de escenarios/asignaciones usan `enabled: isDocente` para no disparar peticiones sin rol docente.

## Lint / Build

```
$ npm run lint
> eslint
(exit 0, sin warnings)

$ npm run build
✓ Compiled successfully
✓ Finished TypeScript
✓ Generating static pages (9/9)
Route: /docente/escenarios → ○ (Static)
```

## Preocupaciones / Notas

1. **Inconsistencia del contrato (`evaluar`)**: `POST /docente/evaluar` requiere `escenario_id`, pero `GET /docente/asignaciones` solo expone `escenario: { titulo }` (sin `id`). Se modeló `escenario.id` como opcional (`id?: number`) y el botón "Evaluar" solo se habilita cuando `ficha_basica_id` y `escenario.id` están presentes. Si el backend no devuelve `escenario.id`, el botón no aparecerá — conviene confirmar/ajustar el contrato del backend.
2. **Hydration**: el guard de rol lee `useUserStore` (persistido) directamente, igual que `Topbar` y `datos-basicos/page.tsx`. En SSR el usuario es `null`, por lo que el HTML prerenderizado muestra el mensaje de acceso denegado; al hidratar con un docente logueado hay un warning de hydration en dev (mismo comportamiento que las páginas existentes). No afecta lint/build.
3. `detalle` y `datos_esperados` se tipan como `unknown` porque el contrato no especifica su estructura; se renderizan como JSON.
