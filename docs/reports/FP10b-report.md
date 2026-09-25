# FP10b — Reporte

## Resumen

Tarea dividida en dos bloques implementados sobre el frontend Next.js 16 (App Router):

- **A.** Detalle de escenario docente: tabs (`asignaciones` / `asignar`) + consulta por `id` con `getEscenario`.
- **B.** Guardado parcial con *resume* y *borrador* en `localStorage`, más el flujo de estados `ASIGNADO → EN_PROGRESO → COMPLETADO`.

`npm run lint` y `npm run build` pasan sin errores.

## Archivos creados / modificados

### Creados

- `src/hooks/useFormDraft.ts` — hook genérico de borradores en `localStorage`.

### Modificados

- `src/lib/docente.ts` — añadido `getEscenario(id)`.
- `src/lib/estudiante.ts` — añadido `progresarEscenario(asignacionId, fichaBasicaId)`.
- `src/app/(dashboard)/docente/escenarios/[id]/page.tsx` — `getEscenario` por id + tabs.
- `src/app/(dashboard)/docente/escenarios/[id]/detalle.module.scss` — estilos `.tabs`, `.tab`, `.tabActive`.
- `src/app/(dashboard)/notificacion/datos-basicos/page.tsx` — `progresarEscenario` + `useFormDraft`.
- `src/app/(dashboard)/notificacion/datos-complementarios/page.tsx` — `useFormDraft`.
- `src/app/(dashboard)/mis-escenarios/page.tsx` — acciones según estado.

## Cómo funciona `useFormDraft`

Firma: `useFormDraft<T>(key: string | null, values: T, restore: (v: T) => void)`.

Devuelve `{ clear }`.

- **Restore (mount):** un `useEffect` con dep `[key]` lee `localStorage.getItem(key)`; si existe, hace `restore(JSON.parse(raw))`. `restore` se guarda en un `useRef` y se sincroniza en un `useEffect` propio (patrón requerido por la regla `react-hooks/refs` de React 19, que prohíbe mutar refs durante el render).
- **Autosave (debounced):** un segundo `useEffect` con dep `[key, values]` programa un `setTimeout` de ~300 ms que hace `setItem(key, JSON.stringify(values))`; el cleanup cancela el timer pendiente. Un flag `firstSaveRef` evita guardar los `defaultValues` en el primer render (antes del `restore`).
- **`clear()`:** `useCallback` que hace `removeItem(key)`.
- **SSR-safe:** cada rama chequea `typeof window === "undefined"` antes de tocar `localStorage`, y todo el I/O va en `try/catch` (draft corrupto, cuota excedida, etc. se ignoran silenciosamente).

Uso en las páginas: la clave es `sivigila-draft-basica-${asignacionId}` (o `-complementaria-`) y solo cuando existe `asignacion_id`; si no hay, se pasa `null` y no se persiste nada. Los valores actuales se capturan con `useWatch({ control })` y `restore` ejecuta `reset(parsed)`.

## Flujo de estados

```
ASIGNADO ──(Diligenciar)──▶ datos-basicos ──createFichaBasicos + progresarEscenario──▶ EN_PROGRESO
EN_PROGRESO ──(Continuar)──▶ datos-complementarios ──createComplementarios + entregarEscenario──▶ COMPLETADO
COMPLETADO ──▶ "Entregado" (sin acción)
```

- `mis-escenarios` decide la acción por `asignacion.estado`:
  - `ASIGNADO` → botón "Diligenciar" → `/notificacion/datos-basicos?asignacion_id=&cod_evento=`.
  - `EN_PROGRESO` → botón "Continuar" → `/notificacion/datos-complementarios?asignacion_id=&ficha_basica_id=&cod_evento=` (usa `asignacion.fichaBasicaId`).
  - `COMPLETADO` → span "Entregado".
- En `datos-basicos`, al crear la ficha con `esEntrega` (hay `asignacion_id`): se llama `progresarEscenario(asignacionId, fichaCreada.id)` (marca `EN_PROGRESO`), se hace `clearDraft()` y se redirige a complementarios con `asignacion_id`, `ficha_basica_id` y `cod_evento`.
- En `datos-complementarios`, tras `entregarEscenario` (marca `COMPLETADO`), se hace `clearDraft()` y se redirige a `/mis-escenarios`.

## Lint / Build

```
npm run lint
> eslint
(0 errores, 0 warnings)
```

```
npm run build
> next build
✓ Compiled successfully
✓ Finished TypeScript
✓ Generating static pages (11/11)
```

## Gotchas

- `useWatch({ control })` (sin `name`) devuelve `DeepPartialSkipArrayKey<T>`, no `T`; se castea `as DatosBasicosFormValues` / `as DatosComplementariosFormValues` al pasarlo al hook.
- La regla `react-hooks/refs` (eslint-plugin-react-hooks v6, React 19) prohíbe mutar `ref.current` durante el render; el "último `restore`" se sincroniza dentro de un `useEffect`, no en el cuerpo del hook.
- `JSON.stringify` descarta los campos `undefined` (p.ej. `semanaEpidemiologica`, `edad` cuando están vacíos); al restaurar con `reset(parsed)` esos campos caen de nuevo a sus `defaultValues`, que es el comportamiento deseado.
- `getEscenario` lanza AxiosError en 404; react-query lo expone como `isError`, que se usa para mostrar "Escenario no encontrado".
- El `EstudianteSelector` ya invalidaba `["docente", "escenarios", escenario.id, "asignaciones"]` en su `onSuccess`, por lo que el contador de la pestaña "Asignaciones (N)" se refresca tras una asignación bulk sin cambios extra.
