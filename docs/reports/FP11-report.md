# FP11 — Descripción del caso + visor de ficha / resumen post-entrega

## Estado

Completado. `npm run lint` y `npm run build` pasan sin errores.

## Objetivos

1. Mostrar la descripción del caso en los formularios (banner).
2. Permitir al estudiante ver sus respuestas (modal desde "Mis escenarios" + página de resumen post-entrega).

---

## A. Banner del caso en los formularios

### Archivos

- `src/lib/estudiante.ts` — añadido `getMiEscenario(asignacionId)`.
  - `GET /estudiante/escenarios/{id}` → mapeado con `mapEstudianteAsignacion`.
- `src/components/ficha/CaseBanner.tsx` (nuevo) — componente cliente.
  - `useQuery` con `queryKey: ["estudiante", "escenario", asignacionId]`.
  - `enabled` solo cuando `asignacionId` es entero positivo.
  - Si no hay datos (`!data`) retorna `null` (fallback discreto: no rompe).
- `src/components/ficha/CaseBanner.module.scss` (nuevo).
  - Fondo `$primary-soft`, borde izquierdo 4px `$primary`.
  - Título "Caso: {titulo}" en bold (`$primary-dark`), descripción debajo.

### Integración

- `src/app/(dashboard)/notificacion/datos-basicos/page.tsx`:
  - Renderiza `<CaseBanner asignacionId={asignacionId} />` justo debajo del header, solo cuando `esEntrega` (asignación válida).
- `src/app/(dashboard)/notificacion/datos-complementarios/page.tsx`:
  - Renderiza `<CaseBanner asignacionId={asignacionId} />` debajo del header cuando `asignacionId != null`.

---

## B. Visor de ficha compartido (migración de FichaBasicaModal)

### Archivos

- `src/components/ficha/FichaViewer.tsx` (nuevo) — contenido migrado desde `FichaBasicaModal.tsx`.
  - `FichaViewer({ fichaBasicaId })`: queries de básica + complementaria y render de secciones (`FichaResumen` y `DatosComplementariosResumen`). Sin overlay.
  - `FichaViewerModal({ fichaBasicaId, onClose })`: overlay + header + `<FichaViewer />`.
  - Se mantuvieron las secciones Identificación / Evento / Clínico / Ubicación / Complementarios tal cual.
- `src/components/ficha/FichaViewer.module.scss` (nuevo) — SCSS migrado tal cual.

### Migración del consumidor

- `src/app/(dashboard)/docente/escenarios/[id]/page.tsx`:
  - Import cambiado a `import { FichaViewerModal } from "@/components/ficha/FichaViewer"`.
  - Uso de `<FichaViewerModal ... />` en `AsignacionRow`.

### Eliminados

- `src/components/docente/FichaBasicaModal.tsx`
- `src/components/docente/FichaBasicaModal.module.scss`

Verificado: `grep FichaBasicaModal` no devuelve ninguna referencia restante.

---

## C. Resumen post-entrega

### Archivos

- `src/app/(dashboard)/notificacion/resumen/page.tsx` (nuevo).
  - `useSearchParams` envuelto en `<Suspense>` (requisito Next 16).
  - Lee `ficha_basica_id`; si es válido renderiza `<FichaViewer />` a página completa.
  - Botón/link "Volver a mis escenarios" → `/mis-escenarios`.
  - Si no hay `ficha_basica_id` válido, mensaje de error simple.
- `src/app/(dashboard)/notificacion/resumen/resumen.module.scss` (nuevo).

### Redirección

- `src/app/(dashboard)/notificacion/datos-complementarios/page.tsx`:
  - Tras `entregarEscenario(...)` exitoso, redirige a
    `/notificacion/resumen?ficha_basica_id=<id>&asignacion_id=<id>`
    (antes era `/mis-escenarios`).

---

## D. "Ver mi ficha" en Mis escenarios

### Archivo

- `src/app/(dashboard)/mis-escenarios/page.tsx`:
  - Añadido estado local `verFicha` en `AsignacionCard`.
  - Cuando `asignacion.fichaBasicaId != null` (aplica a `COMPLETADO` y `EN_PROGRESO`), se muestra botón "Ver mi ficha" que abre `<FichaViewerModal>`.
  - Se mantienen las acciones actuales ("Diligenciar" / "Continuar" / "Entregado").
- `src/app/(dashboard)/mis-escenarios/mis-escenarios.module.scss`:
  - Añadido estilo `.buttonGhost` (consistente con el usado en el detalle de escenario docente).

---

## Salida de lint / build

### `npm run lint`

```
> sivigila@0.1.0 lint
> eslint
```

Sin warnings ni errores (salida vacía = OK).

### `npm run build`

```
✓ Compiled successfully in 5.2s
Finished TypeScript in 5.5s
✓ Generating static pages using 7 workers (12/12)
```

La nueva ruta aparece correctamente en el output:

```
└ ○ /notificacion/resumen
```

---

## Gotchas / notas

- **`useSearchParams` exige `<Suspense>`** (Next 16): la página de resumen envuelve el componente que usa `useSearchParams` en `<Suspense>`, igual que las páginas de `datos-basicos` y `datos-complementarios` existentes.
- **`CaseBanner` es tolerante a fallos**: si el `GET` falla o no devuelve datos, retorna `null` (no rompe el formulario). No muestra estado de error para no contaminar el flujo de llenado.
- **Contrato del endpoint**: `getMiEscenario` mapea `EstudianteAsignacionRaw` (que ya incluye `escenario.descripcion`), por lo que no fue necesario tocar tipos.
- **El `FichaViewer` no es un overlay**: permite reutilizarlo a página completa (resumen) y dentro del modal sin duplicar las queries.
- **Nada de `datos_esperados`**: el endpoint de estudiante no expone la solución, por lo que el visor solo muestra lo que el estudiante registró (básica + complementaria).

## Archivos tocados (resumen)

Creados:
- `src/components/ficha/CaseBanner.tsx`
- `src/components/ficha/CaseBanner.module.scss`
- `src/components/ficha/FichaViewer.tsx`
- `src/components/ficha/FichaViewer.module.scss`
- `src/app/(dashboard)/notificacion/resumen/page.tsx`
- `src/app/(dashboard)/notificacion/resumen/resumen.module.scss`

Modificados:
- `src/lib/estudiante.ts`
- `src/app/(dashboard)/notificacion/datos-basicos/page.tsx`
- `src/app/(dashboard)/notificacion/datos-complementarios/page.tsx`
- `src/app/(dashboard)/docente/escenarios/[id]/page.tsx`
- `src/app/(dashboard)/mis-escenarios/page.tsx`
- `src/app/(dashboard)/mis-escenarios/mis-escenarios.module.scss`

Eliminados:
- `src/components/docente/FichaBasicaModal.tsx`
- `src/components/docente/FichaBasicaModal.module.scss`
