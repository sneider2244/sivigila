# FP8 — Complementaria genérica + diseño de formularios + "Ver ficha" del docente

## Resumen

Se reemplazó el formulario ofídico (específico del evento 100) por una complementaria **genérica**, se creó el componente `Section` replicando el patrón visual de los mockups (badge numerado + título + subtítulo) y se rediseñó la vista "Ver ficha" del docente agrupando los campos en secciones y mostrando la complementaria.

## Archivos creados

- `front/src/components/ui/Section.tsx` — componente `Section` (`step?`, `title`, `subtitle?`, `children`).
- `front/src/components/ui/Section.module.scss` — `.card` (surface/border/radius/shadow), `.head`, `.badge` (40px, `$primary-soft`/`$primary-dark`), `.title`, `.subtitle`, `.body`.

## Archivos modificados

- `front/src/types/index.ts` — eliminados los tipos ofídicos (`ContenidoOfidico`, `DatosAccidente`, `ManifestacionesLocales`, `ManifestacionesSistemicas`, `Complicaciones`, `AtencionHospitalaria` y sus mappers). Se introdujo `ContenidoComplementario = Record<string, unknown>`, `FichaDatosComplementarios`/`Raw` con `contenido` genérico, `FichaDatosComplementariosOut`/`OutRaw` (con `id`) y los mappers `mapFichaDatosComplementarios`, `mapFichaDatosComplementariosToRaw`, `mapFichaDatosComplementariosOut`.
- `front/src/lib/fichas.ts` — import de `axios`; nueva función `getFichaDatosComplementarios(fichaBasicaId)` que devuelve `null` ante 404 (sin complementaria) y re-lanza el resto de errores.
- `front/src/app/(dashboard)/notificacion/datos-complementarios/page.tsx` — formulario genérico (ver detalle abajo).
- `front/src/app/(dashboard)/notificacion/datos-complementarios/datos-complementarios.module.scss` — se eliminaron `.section`/`.sectionTitle`/`.chips` (obsoletos) y se agregó `.textarea`. `.form` ahora es solo columna de secciones (sin fondo propio, lo aportan las `Section`).
- `front/src/app/(dashboard)/docente/escenarios/page.tsx` — `FichaResumen` agrupado en secciones; `FichaBasicaModal` ahora fetchea la complementaria y la renderiza.
- `front/src/app/(dashboard)/docente/escenarios/escenarios.module.scss` — `.fichaList`/`.fichaRow` reemplazados por `.fichaSections`, `.fichaGrid`, `.fichaItem` (grid label/valor de 2 columnas, 1 en `sm`).

## Forma genérica del `contenido`

El POST a `POST /api/v1/fichas/datos-complementarios` envía:

```json
{
  "ficha_basica_id": 123,
  "cod_evento": "100",
  "contenido": {
    "fecha_evento": "2026-02-21",
    "lugar": "...",
    "descripcion": "..."
  }
}
```

- `fecha_evento`, `lugar` y `descripcion` son opcionales (Zod `z.string().optional()`). Los vacíos se envían como `null`.
- `cod_evento` se precarga desde `useSearchParams()` (`cod_evento`), con fallback a la constante `COD_EVENTO = "100"`.
- `ficha_basica_id` se precarga desde `useSearchParams()` y se muestra en la sección "Ficha básica asociada" (`readOnly` cuando viene del query), conservando el banner de error si no está presente.
- Tras crear: si hay `asignacion_id` → `entregarEscenario(asignacion_id, ficha_basica_id)` + `router.replace('/mis-escenarios')`; si no, banner de éxito. Comportamiento preservado.

## Secciones de la complementaria

1. **01 — Ficha básica asociada**: `ficha_basica_id` (number, readOnly si viene del query).
2. **02 — Datos del evento**: `fecha_evento` (date), `lugar` (text) en grid de 2 columnas.
3. **03 — Hallazgos clínicos**: `descripcion` (textarea, lenguaje natural).

## Cómo se agrupa "Ver ficha" (docente)

`FichaResumen` usa `Section` con badge numerado y grid label/valor de 2 columnas:

- **01 — Identificación**: identificación (tipo + número), nombres, apellidos, sexo (M→Masculino, F→Femenino), fecha de nacimiento, edad.
- **02 — Evento y notificación**: código de evento, clasificación de caso, estado, fecha de notificación, año, semana epidemiológica, UPGD.
- **03 — Datos clínicos**: hospitalizado (Sí/No), condición final.
- **04 — Ubicación**: país, departamento, municipio, área de ocurrencia.
- **05 — Datos complementarios** (solo en modal): renderiza `contenido` como pares clave→valor.

Renderizado del `contenido` (genérico):
- `boolean` → "Sí" / "No".
- `string`/`number` → texto (vacío → "—").
- `null`/`undefined` → "—".
- objetos/arrays → `JSON.stringify`.
- Claves snake_case → etiqueta legible (`fecha_evento` → "Fecha evento").
- Sin complementaria (404 → `null`) o `contenido` vacío → "Sin datos complementarios".

## Lint / Build

- `npm run lint` → **OK** (sin salida de error).
- `npm run build` → **OK** (`next build`, Next 16.3.6 Turbopack; TypeScript OK; 10 rutas estáticas).

## Gotchas

- El frontend no usa `rg` (ripgrep) disponible; se usó la herramienta `grep` integrada. Sin impacto.
- `YNChip.tsx` **no existe** en el repo (solo `RadioYN.tsx`); no fue necesario para esta tarea.
- `contenido` pasa de un tipo fuertemente tipado (ofídico) a `Record<string, unknown>`, por lo que el mapeo de tipos/mappers se simplificó a passthrough. Cualquier evento futuro puede enviar su propio dict sin tocar el frontend.
- `getFichaDatosComplementarios` traga el 404 de forma controlada (devuelve `null`) para no disparar el estado de error del modal; otros errores se propagan al interceptor de axios (que solo reintenta 401).
- Los badges numerados son coherentes con los mockups (`01`, `02`, …). En el modal, la complementaria usa `05` tras las cuatro secciones de datos básicos.
- El `.form` de la complementaria dejó de tener fondo propio: ahora cada `Section` aporta su propia `.card`, siguiendo el lenguaje del mockup.
