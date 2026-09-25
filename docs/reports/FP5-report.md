# FP5 — Reporte: "Mis escenarios" del estudiante + flujo diligenciar → entregar

## Estado

**Completado.** `npm run lint` OK (sin warnings/errores) y `npm run build` OK (compila TypeScript + prerender estático, incluyendo la nueva ruta `/mis-escenarios`).

## Archivos creados

- `front/src/lib/estudiante.ts` — `getMisEscenarios()` y `entregarEscenario()`.
- `front/src/app/(dashboard)/mis-escenarios/page.tsx` — listado de asignaciones del estudiante.
- `front/src/app/(dashboard)/mis-escenarios/mis-escenarios.module.scss` — estilos con tokens.

## Archivos modificados

- `front/src/types/index.ts`
- `front/src/lib/fichas.ts`
- `front/src/app/(dashboard)/notificacion/datos-basicos/page.tsx`

## Detalle por archivo

### 1. `types/index.ts`
Añadidos (respetando la convención `*Raw` snake_case + mapper camelCase):

- `EstadoAsignacion = "ASIGNADO" | "EN_PROGRESO" | "COMPLETADO"`.
- `EscenarioEstudiante` / `EscenarioEstudianteRaw` + `mapEscenarioEstudiante`.
- `EstudianteAsignacion` / `EstudianteAsignacionRaw` + `mapEstudianteAsignacion`.

Además (necesario para el paso 4, no listado explícitamente en el enunciado pero implícito en "retorna la ficha con su `id`"):

- `FichaDatosBasicosOutRaw extends FichaDatosBasicosRaw` con `id` y `creado_por_usuario_id` (el `FichaDatosBasicosRaw` existente **no** puede llevar `id` obligatorio porque `mapFichaDatosBasicosToRaw` lo construye para el POST, que no lo incluye).
- `FichaDatosBasicosOut extends FichaDatosBasicos` con `id` y `creadoPorUsuarioId` + `mapFichaDatosBasicosOut`.

### 2. `lib/estudiante.ts` (nuevo)

```ts
getMisEscenarios(): Promise<EstudianteAsignacion[]>
  → GET /estudiante/escenarios → data.map(mapEstudianteAsignacion)

entregarEscenario(asignacionId, fichaBasicaId): Promise<void>
  → POST /estudiante/escenarios/{asignacion_id}/entregar
  → body { ficha_basica_id: number }
```

### 3. `lib/fichas.ts`
`createFichaDatosBasicos` ahora retorna `FichaDatosBasicosOut` (antes `FichaDatosBasicos`), capturando el `id` del POST `/fichas/datos-basicos`. Ningún otro llamador se ve afectado (el único uso previo ignoraba el retorno).

### 4. `mis-escenarios/page.tsx`
- `useQuery({ queryKey: ["estudiante","escenarios"], queryFn: getMisEscenarios })`.
- Estado vacío: `"Aún no tenés escenarios asignados."`.
- Card por asignación: título, descripción, `Evento: <cod_evento>` y badge por estado:
  - `COMPLETADO` → badge verde "Completado" + texto "Entregado" (sin botón).
  - `EN_PROGRESO` → badge ámbar "En progreso".
  - `ASIGNADO` → badge gris "Asignado".
- Botón "Diligenciar" (solo si `estado !== "COMPLETADO"`) → `Link` a `/notificacion/datos-basicos?asignacion_id=<id>&cod_evento=<cod_evento>`.

### 5. `datos-basicos/page.tsx`
- Envolví el formulario en `<Suspense>` (requerido por `useSearchParams` en App Router/Next 16) y renombré el componente a `DatosBasicosForm`; el default export es `DatosBasicosPage` con Suspense (mismo patrón que `caracterizacion/page.tsx`).
- Leo `useSearchParams()`: `asignacion_id` y `cod_evento`.
- Precargo `codEvento` en `defaultValues` si `cod_evento` viene en la query.
- En `onSubmit`, tras `createFichaDatosBasicos`:
  - Si `asignacion_id` es un entero > 0 → `entregarEscenario(asignacionId, fichaCreada.id)` y `router.replace("/mis-escenarios")` (sin banner de éxito; el éxito se refleja en el listado).
  - Si no → comportamiento actual (banner de éxito).

## Flujo diligenciar → entregar (exacto)

1. Estudiante entra a `/mis-escenarios` → `GET /api/v1/estudiante/escenarios` (JWT vía interceptor de axios).
2. Pulsa "Diligenciar" en una asignación con `estado != COMPLETADO` → navega a
   `/notificacion/datos-basicos?asignacion_id=<id>&cod_evento=<cod_evento>`.
3. El formulario precarga `cod_evento` en el campo "Evento".
4. Al enviar: `POST /api/v1/fichas/datos-basicos` con el payload mapeado (snake_case).
5. Respuesta incluye `id` de la ficha creada (`FichaDatosBasicosOut`).
6. `POST /api/v1/estudiante/escenarios/{asignacion_id}/entregar` con `{ ficha_basica_id: id }`.
7. `router.replace("/mis-escenarios")` → el listado muestra la asignación como `COMPLETADO`/`Entregado`.

## Payloads

`POST /estudiante/escenarios/{asignacion_id}/entregar`:
```json
{ "ficha_basica_id": 123 }
```

`POST /fichas/datos-basicos` (sin cambios, vía `mapFichaDatosBasicosToRaw`).

## Lint / Build

```
$ npm run lint
> eslint
(exit 0, sin salida = sin errores ni warnings)

$ npm run build
✓ Compiled successfully in 3.4s
✓ Finished TypeScript in 5.1s
✓ Generating static pages (10/10)
Route (app): incluye /mis-escenarios (○ Static)
```

## Gotchas / decisiones

- **`id` en la ficha creada**: el contrato `POST /fichas/datos-basicos` retorna la ficha con `id`, pero `FichaDatosBasicos`/`FichaDatosBasicosRaw` del frontend no lo modelaban. No agregué `id` obligatorio a `FichaDatosBasicosRaw` porque `mapFichaDatosBasicosToRaw` (payload del POST) lo construye sin `id`; en su lugar creé `FichaDatosBasicosOutRaw`/`FichaDatosBasicosOut` con `id` + `creado_por_usuario_id` (el backend `FichaDatosBasicosOut` los incluye siempre).
- **`useSearchParams` + Suspense**: Next 16 App Router exige envolver en `<Suspense>` el componente que usa `useSearchParams` (mismo patrón ya presente en `caracterizacion/page.tsx`). Sin ello el build falla en prerender estático.
- **Navegación con `Link` (no `router.push`)**: usé `next/link` con objeto `href` para el botón "Diligenciar" (idiomático y evita un componente client extra para el click). Para el redirect post-entrega usé `router.replace` (evita dejar la URL con query params en el historial).
- **`router.replace` en vez de `push`**: al entregar, `replace("/mis-escenarios")` evita que "atrás" vuelva a un formulario con `asignacion_id` ya entregada.
- **Complementarios no tocados** (según consigna): el vínculo de datos complementarios al escenario queda como pulido posterior.

## Concerns

- `entregarEscenario` no valida errores de red localmente; un fallo del POST de entrega cae en el `catch` genérico del form y muestra el `detail` del backend como banner de error. Aceptable para este flujo educativo.
- El `defaultValues` de `codEvento` usa el valor del query en el primer render; si el usuario cambiara el query param sin recargar, no se re-sincroniza (irrelevante en la práctica porque siempre se navega a esta ruta desde un clic).
