# F3 — Formulario responsivo de Caracterización UPGD

## Estado

Completo. `npm run lint` pasa sin errores/warnings y `npm run build` genera un build de producción limpio.

## Archivos creados

| Archivo | Descripción |
|---------|-------------|
| `src/components/ui/Input.tsx` | Input tipado (`forwardRef`), reutiliza tokens SCSS, `aria-invalid` estiliza borde de error. |
| `src/components/ui/Input.module.scss` | Estilos del input (`@use` de `_variables`). |
| `src/components/ui/Select.tsx` | Select tipado (`forwardRef`), `appearance: none`. |
| `src/components/ui/Select.module.scss` | Estilos del select. |
| `src/components/ui/Field.tsx` | Wrapper `label` + control + `hint` + `error`. |
| `src/components/ui/Field.module.scss` | Estilos del wrapper de campo. |
| `src/components/ui/RadioYN.tsx` | Chip "Sí / No" (patrón del prototipo, adaptado a SCSS module). Compatible con `Controller` de RHF (`value` / `onChange`). |
| `src/components/ui/RadioYN.module.scss` | Chips pill con estado `:checked`. |
| `src/lib/upgd.ts` | Servicio `getUpgd`, `createUpgd`, `updateUpgd` sobre la instancia `api` + mappers. |
| `src/app/(dashboard)/layout.tsx` | Layout del route group `(dashboard)`: header institucional + `children`. Sin navegación completa. |
| `src/app/(dashboard)/layout.module.scss` | Estilos del layout (`@use` con ruta relativa de 2 niveles). |
| `src/app/(dashboard)/caracterizacion/page.tsx` | Formulario (RHF + Zod + axios). `"use client"`. |
| `src/app/(dashboard)/caracterizacion/caracterizacion.module.scss` | Estilos responsivos del formulario (`@include responsive(md)` y `responsive(sm)`). |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/types/index.ts` | Agrega `NivelComplejidad = 1 \| 2 \| 3 \| 4`, `UpgdCaracterizacion` (camelCase), `UpgdCaracterizacionRaw` (snake_case) y los mappers `mapUpgdCaracterizacion` / `mapUpgdCaracterizacionToRaw`. |

## Shape exacto consumido / producido

Contrato UPGD (JSON snake_case, tal como lo espera el backend):

```
cod_prestador:      string (12 chars)
razon_social:       string
nit:                string
nivel_complejidad:  int (1..4)
cove:               boolean
unidad_analisis:    boolean
internet:           boolean
activo:             boolean
departamento_codigo: string | null
municipio_codigo:   string | null
```

- `GET  /upgd/{cod_prestador}` → respuesta `UpgdCaracterizacionRaw` → `mapUpgdCaracterizacion` → dominio camelCase.
- `POST /upgd` → body `mapUpgdCaracterizacionToRaw(payload)`.
- `PUT  /upgd/{cod_prestador}` → body igual que POST (usado en modo edición).

Base URL: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`).

## Decisiones de UI / implementación

1. **Primitivas reutilizables en `components/ui/`**: `Input`, `Select`, `Field` (wrapper) y `RadioYN`. Todas sin `"use client"` (presentacionales, sin hooks) pero heredan el entorno cliente al ser importadas por la página. `Input`/`Select` usan `forwardRef` para compatibilidad con `register()` de RHF.
2. **Booleans como chips Sí/No** (`cove`, `unidad_analisis`, `internet`, `activo`): `RadioYN` implementa el patrón del prototipo (dos `<label>` con radio oculto + `<span>`). Se integran vía `Controller` porque el valor es `boolean` (no string). `activo` por defecto `true`.
3. **`nivel_complejidad` como `<Select>`** (1–4) con `setValueAs: (v) => (v === "" ? undefined : Number(v))`, así Zod recibe `number` y `undefined` cuando no se selecciona.
4. **Modo edición vía query param `?codPrestador=...`**: si existe, se hace `GET /upgd/{cod}` para precargar y el submit hace `PUT`; si no, `POST`. El campo `codPrestador` se deshabilita en edición (PK inmutable). Se usa `useSearchParams` dentro de un `<Suspense>` (requisito de Next 16 para prerender estático).
5. **Departamento/municipio**: selects con una lista mínima de códigos DANE reales (Antioquia/Bogotá/Valle + Medellín/Bogotá/Cali) como **placeholder**, porque el contrato UPGD no incluye endpoints de catálogo de división política. Se documenta como pendiente de reemplazar cuando exista `useCatalogos`.
6. **Responsive**: grid de 2 columnas que colapsa a 1 en `md` (880px); botón submit full-width en `sm` (560px), vía el mixin `responsive()`.

## Validación Zod (zod v4)

- `codPrestador`: `string.length(12)` (requerido por ser PK; el enunciado no lo listaba pero sin él el `POST` falla).
- `razonSocial`: `min(3)`.
- `nit`: `min(1)` (requerido).
- `nivelComplejidad`: `number({ error: "…" }).int().min(1).max(4)`.
- `cove` / `unidadAnalisis` / `internet` / `activo`: `boolean`.
- `departamentoCodigo` / `municipioCodigo`: `string.nullable()`.
- **Validación dependiente (soft)**: `superRefine` — si `nivelComplejidad >= 3` y `unidadAnalisis === false`, agrega issue en el path `unidadAnalisis`: "Una UPGD de nivel 3 o 4 debe contar con unidad de análisis".

Nota Zod v4: los params `required_error` / `invalid_type_error` ya no existen; se reemplazaron por `error` (`z.number({ error: "…" })`).

## Gotchas de Next 16 encontrados en F3

- **`react-hooks/set-state-in-effect`**: llamar `setState` de forma síncrona en el body de un `useEffect` rompe lint (cascading renders). El estado inicial de carga ya cubre el caso, así que se eliminaron `setLoading(true)` / `setLoadError(null)` del efecto y se dejaron solo en callbacks asíncronos.
- **`useSearchParams()` en componente cliente** exige `<Suspense>` durante el prerender estático; sin él el build falla con "should be wrapped in a suspense boundary".
- **Ruta relativa de `@use` SCSS depende de la profundidad**: `(dashboard)/layout.module.scss` está a 2 niveles (`../../styles/...`), mientras que `(dashboard)/caracterizacion/caracterizacion.module.scss` está a 3 (`../../../styles/...`).

## Salida de lint / build

`npm run lint`:

```
> sivigila@0.1.0 lint
> eslint
```

(exit 0, sin errores ni warnings)

`npm run build`:

```
▲ Next.js 16.3.6 (Turbopack)
✓ Compiled successfully
✓ Finished TypeScript
✓ Generating static pages (6/6)

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /caracterizacion
└ ○ /login
```

Build de producción limpio.

## Concerns

- **Catálogo de departamento/municipio es placeholder** (no hay endpoint en el contrato). Al existir `useCatalogos` debe reemplazarse y, probablemente, encadenar municipios al departamento seleccionado.
- **Backend aún no existe (Sprint 1)**: el POST/PUT/GET no se probó contra servidor real; solo tipado, lint y build. El manejo de errores usa `err.response?.data?.detail` (convención FastAPI); si el backend responde otro shape, ajustar en `onSubmit`.
- **`activo` se expone como chip Sí/No** con default `true`. Si el backend lo gestiona internamente (no lo recibe del form), habría que sacarlo de la UI y mandarlo fijo.
- **La ruta `/caracterizacion` es estática** (prerenderizada). Al integrar el guard de autenticación del dashboard (tareas posteriores) probablemente pase a ser dinámica o a vivir tras un middleware.
