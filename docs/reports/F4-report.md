# F4 — Formulario de Datos Básicos (notificación individual)

## Estado

Completado. `npm run lint` OK · `npm run build` OK.

## Archivos creados / modificados

| Archivo | Acción |
| --- | --- |
| `front/src/types/index.ts` | Modificado: tipos `FichaDatosBasicos`, `FichaDatosBasicosRaw`, `GruposPoblacionales`, `GruposPoblacionalesRaw`, enums literales (`Sexo`, `UnidadMedidaEdad`, `AreaOcurrencia`, `ClasificacionCaso`, `CondicionFinal`) y mappers `mapFichaDatosBasicos` / `mapFichaDatosBasicosToRaw` (más los de grupos poblacionales). |
| `front/src/lib/fichas.ts` | Creado: `createFichaDatosBasicos` (POST `/fichas/datos-basicos`), patrón idéntico a `lib/upgd.ts`. |
| `front/src/app/(dashboard)/notificacion/datos-basicos/page.tsx` | Creado: formulario completo (RHF + Zod, `"use client"`). |
| `front/src/app/(dashboard)/notificacion/datos-basicos/datos-basicos.module.scss` | Creado: SCSS module con tokens del proyecto. |

Componentes UI reutilizados: `Field`, `Input`, `Select`, `RadioYN` (sin crear nuevos componentes UI). Las fechas usan `<Input type="date">` nativo; los booleanos (`hospitalizado`, `gruposPoblacionales.gestante`, `gruposPoblacionales.desplazado`) usan el chip `RadioYN` Sí/No ya existente.

## Validaciones dependientes (Zod v4)

Implementadas con `.superRefine` sobre el schema `datosBasicosSchema` (mismo patrón que `caracterizacionSchema` en F3). Todas emiten `z.ZodIssueCode.custom` con `path` anidado para que RHF mapee el error al campo correcto:

| Regla | Issue `path` |
| --- | --- |
| `identidadGenero === 5` (Otro) ⇒ `otraIdentidad` requerido | `["gruposPoblacionales", "otraIdentidad"]` |
| `gestante === true` ⇒ `semanasGestacion` requerido | `["gruposPoblacionales", "semanasGestacion"]` |
| `hospitalizado === true` ⇒ `fHospitalizacion` requerido | `["gruposPoblacionales", "fHospitalizacion"]` |
| `condicionFinal === 2` (Muerto) ⇒ `fDefuncion` + `certificado` requeridos | `["gruposPoblacionales", "fDefuncion"]` y `["gruposPoblacionales", "certificado"]` |

La revelación/ocultamiento de campos condicionales se hace con `useWatch`:

- `identidadGenero` → muestra el input "¿Cuál identidad de género?" cuando `=== 5`.
- `gruposPoblacionales.gestante` → muestra "Semanas de gestación" cuando `true`.
- `hospitalizado` → muestra "Fecha de hospitalización" cuando `true`.
- `condicionFinal` → muestra "Fecha de defunción" + "Nº certificado" cuando `=== 2`.

Detalle importante: aunque los campos ocultos se desmonten del DOM, su valor persiste en RHF; para evitar enviar restos inválidos se limpian con `setValueAs` (`"" → null`) y, en `onSubmit`, se trimean y pasan a `null` los vacíos (`otraIdentidad`, `certificado`, `segundoNombre`, `segundoApellido`, `telefono`).

Errores inline vía `Field`/`RadioYN` (`error={errors.gruposPoblacionales?.otraIdentidad?.message}`, etc.).

## Payload exacto (POST `/fichas/datos-basicos`, snake_case)

```json
{
  "cod_upgd": "123456789012",
  "subindice": "01",
  "cod_evento": "210",
  "f_grabacion": "2026-09-25",
  "f_notificacion": "2026-09-25",
  "anio": 2026,
  "semana_epidemiologica": 39,
  "tipo_id": "CC",
  "num_id": "1234567890",
  "primer_nombre": "María",
  "segundo_nombre": null,
  "primer_apellido": "Pérez",
  "segundo_apellido": null,
  "telefono": "3001234567",
  "f_nacimiento": "1990-05-10",
  "edad": 36,
  "und_med_edad": 1,
  "sexo": "F",
  "identidad_genero": 1,
  "orientacion_sexual": 1,
  "pais_ocurrencia": "COLOMBIA",
  "dpto_ocurrencia": "05",
  "muni_ocurrencia": "05001",
  "area_ocurrencia": 1,
  "grupos_poblacionales": {
    "gestante": true,
    "semanas_gestacion": 24,
    "desplazado": false,
    "otra_identidad": null,
    "f_hospitalizacion": null,
    "f_defuncion": null,
    "certificado": null
  },
  "clasificacion_caso": 3,
  "hospitalizado": false,
  "condicion_final": 1
}
```

Notas sobre el payload:

- Fechas en `YYYY-MM-DD` (valor directo de `<input type="date">`).
- Campos opcionales que quedan vacíos se serializan como `null` (no `""`).
- `subindice` fijo `"01"`, `pais_ocurrencia` por defecto `"COLOMBIA"`.
- `cod_upgd` se pre-carga desde `useUserStore.user.codUpgd` (rol UPGD) y es editable.

## Validación: lint y build

```
$ npm run lint
> sivigila@0.1.0 lint
> eslint
(exit 0, sin warnings/errors)

$ npm run build
> next build
▲ Next.js 16.3.6 (Turbopack)
✓ Compiled successfully in 1336ms
✓ Finished TypeScript in 4.2s
✓ Generating static pages using 7 workers (7/7)
Route (app)
┌ ○ /notificacion/datos-basicos  (Static)
```

## Gotchas / decisiones

1. **Ruta SCSS**: el `@use` de `variables`/`mixins` desde `datos-basicos/` requiere `../../../../styles/...` (4 niveles), no 3 como en `caracterizacion/`. El primer `build` falló con `Can't find stylesheet to import` por usar 3 niveles; corregido.
2. **Zod v4**: `required_error`/`invalid_type_error` fueron removidos; se usa el parámetro `error` en `z.number({ error })`, `z.enum(["M","F"], { error })`, `z.string().min(...)`. Verificado contra `node_modules/zod/v4/core/api.d.ts` (`error?: string` en `Params`).
3. **Números**: los `<Select>` numéricos usan `setValueAs` (`"" → undefined`) y `z.number().int().min().max()`, replicando el patrón de `nivelComplejidad` en F3; en `onSubmit` se castea al enum literal (`UnidadMedidaEdad`, `AreaOcurrencia`, `ClasificacionCaso`, `CondicionFinal`). `edad`/`semanaEpidemiologica` arrancan `undefined` vía `DeepPartial` de RHF (no disparan error al montar).
4. **Catálogos placeholder**: `DEPARTAMENTOS`, `MUNICIPIOS`, `TIPOS_ID`, `identidadGenero`/`orientacionSexual` son listas estáticas locales a la espera del endpoint `catalogos` (`useCatalogos`). Los valores numéricos (`identidad_genero`, `orientacion_sexual`, `area_ocurrencia`, `clasificacion_caso`, `condicion_final`) siguen la semántica del backend (`docs/BACKEND_ARCH.md`): `area_ocurrencia` 1 Cabecera/2 Centro poblado/3 Rural; `clasificacion_caso` 1 Sospechoso/2 Probable/3 Confirmado/4 Descartado; `condicion_final` 1 Vivo/2 Muerto; `und_med_edad` 1 Años/2 Meses/3 Días.
5. **`identidad_genero === 5` (Otro)** como gatillo de `otra_identidad`, coherente con `docs/FRONTEND_ARCH.md` ("identGenero == '5' (Otro)").
6. **No se hace redirect** tras éxito: se muestra banner de éxito (el endpoint aún no devuelve navegación; navegar a datos-complementarios se deja para F5). Se maneja loading (`isSubmitting`), error (detalle del backend vía `axios.isAxiosError` → `err.response?.data?.detail`) y éxito.
7. **Sin comentarios de IA / commits**: no se commiteó nada, no se agregó atribución.
