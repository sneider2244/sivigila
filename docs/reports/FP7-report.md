# FP7 — Simplificar el flujo del escenario

## Estado

Completo. `npm run lint` y `npm run build` pasan sin errores.

## Archivos modificados

- `front/src/components/layout/NavigationTabs.tsx` — se eliminaron las pestañas de Caracterización / Datos Básicos / Datos Complementarios. Ahora muestra una sola pestaña según rol: `Mis escenarios` (no-DOCENTE) o `Docente` (DOCENTE).
- `front/src/app/(dashboard)/page.tsx` — home reducido a una sola tarjeta por rol (se quitaron `FICHA_CARDS`). Texto de "Gestión docente" actualizado (ya no menciona "evaluar").
- `front/src/app/(dashboard)/docente/escenarios/page.tsx` — `EscenarioForm` sin JSON (`datosEsperados` eliminado del schema, `superRefine`, defaults y submit); `descripcion` ahora es `<textarea>`; `codEvento` ahora es `<select>` poblado desde `GET /catalogos/eventos` (label "Nombre (código)", valor = `codigo`). `EscenarioCard` sin el bloque `<details>` "Datos esperados". `AsignacionRow` sin evaluación (`evaluarMutation`, `result`, `handleEvaluar`, `puedeEvaluar` eliminados); solo queda el botón "Ver ficha". Se eliminó la función `formatDetail`.
- `front/src/app/(dashboard)/docente/escenarios/escenarios.module.scss` — se quitó `font-family: monospace` de `.textarea` (ahora es texto en lenguaje natural). Las clases `.jsonDetails`, `.json` y `.resultado` quedaron sin uso en el JSX (no rompen lint/build).
- `front/src/lib/docente.ts` — `CrearEscenarioInput` sin `datosEsperados`; `createEscenario` ya no envía `datos_esperados`; se eliminó `evaluarFicha`.
- `front/src/lib/catalogos.ts` — **nuevo** cliente `getEventos()` para `GET /catalogos/eventos`.
- `front/src/types/index.ts` — `EscenarioClinico`/`EscenarioClinicoRaw`/`mapEscenarioClinico` sin `datosEsperados`/`datos_esperados`; se eliminó la interfaz `EvaluacionResult`; se agregó `CatalogoEvento`.
- `front/src/app/(dashboard)/notificacion/datos-basicos/page.tsx` — tras crear la ficha con `asignacion_id`, en vez de entregar inmediatamente redirige a datos-complementarios con `asignacion_id`, `ficha_basica_id` y `cod_evento`. Se quitó el import de `entregarEscenario`.
- `front/src/app/(dashboard)/notificacion/datos-complementarios/page.tsx` — lee `asignacion_id`, `ficha_basica_id` y `cod_evento` de `useSearchParams` (dentro de `<Suspense>`); precarga `ficha_basica_id` y usa `cod_evento` (con fallback `"100"`). Al crear la complementaria con `asignacion_id`, llama `entregarEscenario(asignacion_id, ficha_basica_id)` y redirige a `/mis-escenarios`; si no, banner de éxito.

## Nuevo flujo de escenario

```
Docente crea escenario (titulo, descripcion en lenguaje natural, evento, activo)
        → POST /docente/escenarios
        → Docente asigna estudiantes
        → Estudiante ve "Mis escenarios" y pulsa "Diligenciar"
        → /notificacion/datos-basicos?asignacion_id=&cod_evento=
        → POST /fichas/datos-basicos  (retorna ficha.id)
        → redirect a /notificacion/datos-complementarios?asignacion_id=&ficha_basica_id=&cod_evento=
        → POST /fichas/datos-complementarios (ficha_basica_id + cod_evento)
        → POST /estudiante/escenarios/{asignacion_id}/entregar { ficha_basica_id }
        → redirect a /mis-escenarios
```

## Lint / Build

```
$ npm run lint
> sivigila@0.1.0 lint
> eslint
(exit 0, sin warnings)

$ npm run build
> next build
✓ Compiled successfully in 3.3s
✓ Finished TypeScript in 5.6s
✓ Generating static pages (10/10)
Route: /notificacion/datos-complementarios → ○ (Static)
```

## Gotchas / Notas

1. **Contrato eventos**: `GET /catalogos/eventos` es público, pero la instancia `api` de axios inyecta `Authorization` si hay token (no rompe el endpoint). El tipo `CatalogoEvento` asume `{ codigo, nombre, descripcion }` directo, sin mapping snake→camel (el contrato ya usa esos nombres).
2. **Formulario complementario sigue siendo específico de ofídico** (evento 100): aunque `cod_evento` llega por query y se reenvía al backend, los campos de la ficha complementaria son fijos (agente agresor, manifestaciones, suero antiofídico). Si un escenario usa otro evento, el formulario no se adapta — pendiente de generalizar.
3. **Encadenado por query params**: se pasó de `fichaBasicaId` (camelCase) a `ficha_basica_id` (snake_case) en `datos-complementarios` para alinear con el resto de parámetros (`asignacion_id`, `cod_evento`). El texto del banner de error también se actualizó.
4. **`.textarea` reutilizado**: la descripción usa la clase `.textarea` que antes era para el JSON; se le quitó `font-family: monospace` para que sea legible como texto natural.
5. **Hydration**: el guard de rol lee `useUserStore` directamente (mismo patrón que `Topbar` y las páginas existentes). En SSR `user` es `null`; el HTML prerenderizado difiere hasta hidratar. No afecta lint/build.
6. **Campo `escenarioId`**: `EscenarioAsignacion` conserva `escenarioId` (ya no se usa en el JSX tras quitar la evaluación), pero se mantiene en el tipo porque el contrato lo incluye.
