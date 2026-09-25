# F5 — Formulario de Datos Complementarios (Accidente Ofídico)

## Estado

Completado. Lint OK, build OK.

## Archivos creados / modificados

| Archivo | Acción |
| --- | --- |
| `front/src/types/index.ts` | Modificado — tipos de dominio + mappers snake_case↔camelCase |
| `front/src/lib/fichas.ts` | Modificado — `createFichaDatosComplementarios` |
| `front/src/app/(dashboard)/notificacion/datos-complementarios/page.tsx` | Creado — formulario RHF + Zod |
| `front/src/app/(dashboard)/notificacion/datos-complementarios/datos-complementarios.module.scss` | Creado — SCSS module |

## Tipos agregados (`src/types/index.ts`)

- Dominio (camelCase): `DatosAccidente`, `ManifestacionesLocales`, `ManifestacionesSistemicas`, `Complicaciones`, `AtencionHospitalaria`, `ContenidoOfidico`, `FichaDatosComplementarios`.
- Raw (snake_case): `DatosAccidenteRaw`, `ManifestacionesLocalesRaw`, `ManifestacionesSistemicasRaw`, `ComplicacionesRaw`, `AtencionHospitalariaRaw`, `ContenidoOfidicoRaw`, `FichaDatosComplementariosRaw`.
- Mappers: `mapContenidoOfidico`, `mapContenidoOfidicoToRaw`, `mapFichaDatosComplementarios`, `mapFichaDatosComplementariosToRaw`.

Sigue el patrón ya existente para `FichaDatosBasicos` (interfaces Raw + dominio y un par de funciones de mapeo), con el sufijo `Raw` y `snake_case` en las propiedades de red.

## Chips Sí/No

- Se reutilizó `src/components/ui/RadioYN.tsx` (ya existía; no fue necesario crearlo).
- Para evitar 20 bloques `Controller` repetidos, se definió un helper local `YNChip` (tipado con `Control<...>` y `FieldPath<...>` de react-hook-form) que envuelve `Controller` + `RadioYN`. Cada ítem de las listas `MANIFESTACIONES_LOCALES`, `MANIFESTACIONES_SISTEMICAS` y `COMPLICACIONES` declara su `name` como literal (`as const` implícito en la unión) para preservar el tipado de los paths.
- Los booleanos se renderizan en un grid `.chips` (2 columnas → 1 columna en `md`).

## Validaciones (Zod v4)

- `fichaBasicaId`: `z.number({ error }).int().positive()` (obligatorio).
- `contenido.datosAccidente.fecha` / `.direccion`: `z.string().min(1, ...)`.
- `contenido.datosAccidente.agenteAgresor`: `z.number({ error }).int().min(1)`.
- `contenido.atencionHospitalaria.empleoSuero`: `z.number({ error }).int().min(1).max(2)` (Select Sí=1 / No=2).
- `contenido.atencionHospitalaria.dosis`: `z.number().int().nullable()`.
- 16 campos de manifestaciones + 4 de complicaciones: `z.boolean()` dentro de objetos anidados requeridos.
- `dosis` se muestra solo cuando `empleoSuero === 1` (via `useWatch`), igual que el patrón de campos condicionales de datos-básicos.

Nota Zod v4: se usó `{ error: "..." }` (no `required_error`), consistente con el resto del proyecto.

## `ficha_basica_id`

- Se lee del query param `?fichaBasicaId=<id>` (con `useSearchParams` dentro de `Suspense`).
- Si viene en la URL y es un entero positivo, precarga y deja el campo `readOnly`.
- Si falta, se muestra un banner de error y el usuario puede ingresarlo manualmente; el schema Zod lo hace obligatorio en submit.

## Shape exacto del POST

Endpoint: `POST /fichas/datos-complementarios` (base `NEXT_PUBLIC_API_URL`, `http://localhost:8000/api/v1`).

```json
{
  "ficha_basica_id": 123,
  "cod_evento": "100",
  "contenido": {
    "datos_accidente": { "fecha": "2026-09-25", "direccion": "...", "agente_agresor": 1 },
    "manifestaciones_locales": {
      "edema": false, "dolor": true, "eritema": false,
      "equimosis": false, "flictenas": false, "necrosis_local": false
    },
    "manifestaciones_sistemicas": {
      "nauseas": false, "vomito": false, "dolor_abdominal": false,
      "bradicardia": false, "hipotension": false, "sangrado": false
    },
    "complicaciones": {
      "celulitis": false, "necrosis": false,
      "insuficiencia_renal": false, "hipoxia": false
    },
    "atencion_hospitalaria": { "empleo_suero": 1, "dosis": 5 }
  }
}
```

- `agente_agresor` y `empleo_suero` son `int`; `dosis` es `int | null` (null cuando no se emplea suero).

## Lint / Build

```
$ npm run lint
> sivigila@0.1.0 lint
> eslint
(exit 0, sin warnings ni errores)
```

```
$ npm run build
▲ Next.js 16.3.6 (Turbopack)
✓ Compiled successfully in 3.0s
✓ Finished TypeScript in 4.2s ...
Route (app)
├ ○ /
├ ○ /_not-found
├ ○ /caracterizacion
├ ○ /login
├ ○ /notificacion/datos-basicos
└ ○ /notificacion/datos-complementarios
```

## Observaciones / decisiones

- `agente_agresor` se implementó como `Select` con catálogo educativo de géneros de serpientes (códigos 1–5). Si el backend espera un catálogo distinto, solo hay que ajustar `AGENTES_AGRESORES` en el page.
- `empleo_suero` se codificó como `1 = Sí`, `2 = No` (int, según contrato). Verificar que coincide con la convención del backend.
- `cod_evento` se fija en `"100"` como constante (no es campo de formulario), según contrato.
