# FP10a — Normalización de anchos (1200px) y grillas (3 columnas)

**Status:** COMPLETED
**Build:** `npm run build` OK (Next.js 16.3.6 / Turbopack, compiló el SCSS sin errores)
**Lint:** `npm run lint` OK (sin errores)

## Archivos cambiados

| Archivo | Cambio | Valor final |
| ------- | ------ | ----------- |
| `src/styles/_variables.scss` | Nueva variable | `$container-max: 1200px;` |
| `src/app/(dashboard)/mis-escenarios/mis-escenarios.module.scss` | `.page` max-width 760px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/notificacion/datos-complementarios/datos-complementarios.module.scss` | `.page` 760px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/caracterizacion/caracterizacion.module.scss` | `.page` 760px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/notificacion/datos-basicos/datos-basicos.module.scss` | `.page` 760px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/docente/escenarios/escenarios.module.scss` | `.page` 860px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/docente/escenarios/nuevo/nuevo.module.scss` | `.page` 860px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/docente/escenarios/[id]/detalle.module.scss` | `.page` 860px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/page.module.scss` | `.page` 960px → variable | `max-width: $container-max;` |
| `src/app/(dashboard)/notificacion/datos-basicos/datos-basicos.module.scss` | `.grid` 2→3 col responsive | `repeat(3,1fr)` / md `repeat(2,1fr)` / sm `1fr` |
| `src/app/(dashboard)/notificacion/datos-complementarios/datos-complementarios.module.scss` | `.grid` 2→3 col responsive | `repeat(3,1fr)` / md `repeat(2,1fr)` / sm `1fr` |
| `src/app/(dashboard)/caracterizacion/caracterizacion.module.scss` | `.grid` 2→3 col responsive | `repeat(3,1fr)` / md `repeat(2,1fr)` / sm `1fr` |
| `src/components/docente/FichaBasicaModal.module.scss` | `.modal` 560px → variable | `max-width: $container-max;` |
| `src/components/docente/FichaBasicaModal.module.scss` | `.fichaGrid` 2→3 col responsive | `repeat(3,1fr)` / md `repeat(2,1fr)` / sm `1fr` |

## Notas

- `login.module.scss` (400px) y `SearchModal.module.scss` (520px) no se tocaron, tal como se indicó.
- La grilla del home (`page.module.scss` `.grid`) usa `repeat(auto-fill, minmax(220px, 1fr))` y NO es una grilla de formulario, por lo que se dejó intacta (solo se amplió su contenedor a 1200px).

## Estructura distinta a la esperada

Ninguna. Todos los archivos tenían exactamente la estructura prevista (`.page` con `max-width` + `.grid` con `1fr 1fr` y `@include responsive(md)`).
