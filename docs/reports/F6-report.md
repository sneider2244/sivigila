# F6 — Actionbar sticky + navegación por pestañas + modal de búsqueda de casos

## Resumen

Se implementó la barra de acción (Actionbar) sticky dentro del layout `(dashboard)`, con
navegación por pestañas, cabecera con usuario + logout y un modal de búsqueda de casos que
consulta `GET /fichas/datos-basicos`.

## Archivos creados

- `front/src/components/layout/Actionbar.tsx` — contenedor sticky que compone `Topbar` + `NavigationTabs`.
- `front/src/components/layout/Actionbar.module.scss` — `position: sticky; top: 0; z-index: 50` + sombra inferior.
- `front/src/components/layout/Topbar.tsx` — marca SIVIGILA, usuario (`nombreCompleto`, `rol`, `codUpgd`), botón "Buscar casos" y "Cerrar sesión".
- `front/src/components/layout/Topbar.module.scss` — franja primary + responsive (wrap en `sm`).
- `front/src/components/layout/NavigationTabs.tsx` — pestañas con `Link` + `usePathname` para resaltar la activa.
- `front/src/components/layout/NavigationTabs.module.scss` — pestañas con indicador inferior activo.
- `front/src/components/ui/SearchModal.tsx` — modal de búsqueda (estado local + `api` de axios).
- `front/src/components/ui/SearchModal.module.scss` — overlay fixed + modal responsivo.

## Archivos modificados

- `front/src/types/index.ts` — nuevo tipo `EstadoFicha` (`"NOTIFICADA" | "EN_AJUSTE" | "CONFIRMADA" | "DESCARTADA"`), campo `estado` en `FichaDatosBasicos`/`FichaDatosBasicosRaw` y sus mappers.
- `front/src/app/(dashboard)/notificacion/datos-basicos/page.tsx` — agrega `estado: "NOTIFICADA"` al payload de creación.
- `front/src/app/(dashboard)/layout.tsx` — reemplaza el `<header>` por `<Actionbar />`.
- `front/src/app/(dashboard)/layout.module.scss` — elimina `.header`/`.brand` (ahora viven en el Topbar).

## Cómo funciona

### Sticky
`Actionbar.module.scss` aplica `position: sticky; top: 0; z-index: 50`. La Actionbar es hija
directa de `.shell` (`display: flex; flex-direction: column; min-height: 100vh`), así que se
mantiene fija al tope del viewport mientras el contenido principal scrollea.

### Pestañas
`NavigationTabs` usa `usePathname()` (`next/navigation`, Client Component). Marca como activa la
pestaña cuya ruta coincide exactamente o por prefijo (`pathname === href || startsWith(href + "/")`)
y aplica `aria-current="page"`. Las rutas: `/caracterizacion`, `/notificacion/datos-basicos`,
`/notificacion/datos-complementarios`.

### Topbar / HeaderUPGD
`Topbar` lee el usuario desde `useUserStore` (campo `user` con `nombreCompleto`, `rol`, `codUpgd`).
`Cerrar sesión` ejecuta `useAuth().logout` (limpia la sesión persistida) y redirige a `/login` con
`router.replace`. `Buscar casos` monta el `SearchModal`.

### Modal de búsqueda
- Input `num_id` (obligatorio) y `cod_evento` (opcional); búsqueda por botón o `Enter`.
- Consulta `api.get("/fichas/datos-basicos", { params })` con `num_id` y, opcionalmente, `cod_evento`.
- Tolera respuestas array directo o envueltas en `{ data: [...] }`.
- Muestra `num_id`, `primer_nombre`, `primer_apellido`, `cod_evento` y `estado`.
- Al hacer click en un resultado navega a `/notificacion/datos-basicos?numId=<id>` y cierra el modal.
- Cierra con `Escape` (listener en `document`) o click en el backdrop (stopPropagation en el modal).

## Verificación

- `npm run lint` → **PASS** (sin errores ni warnings).
- `npm run build` → **PASS** (compilación y TypeScript OK; 8 páginas estáticas generadas).

```
Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /caracterizacion
├ ○ /login
├ ○ /notificacion/datos-basicos
└ ○ /notificacion/datos-complementarios
```

## Observaciones / riesgos

- `_base.scss` define `html, body { overflow-x: hidden; }`. Esto puede, en algunos navegadores,
  alterar el comportamiento de `position: sticky` (crea un contexto de scroll). No se modificó para
  no exceder el alcance; si la barra no quedara fija visualmente, revisar esa regla.
- La respuesta real del endpoint de búsqueda puede venir envuelta (p. ej. `{ data: [...] }` o
  paginada); el modal maneja `Array.isArray` y `data.data` como fallback, pero si el backend paginara
  habría que ajustar el mapeo.
- `estado` se agregó como campo requerido de la ficha y se envía `"NOTIFICADA"` al crear; si el
  backend lo auto-asigna y rechaza el campo, habría que hacerlo opcional en el payload.
