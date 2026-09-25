# ARQUITECTURA FRONTEND: Next.js + SCSS + SSR

## Stack Tecnológico

- **Framework:** Next.js 16 (App Router con Server Side Rendering) — React 19
- **Estilos:** SCSS Modules + Variables CSS nativas (`caracterizacion.css`)
- **Gestión de Formularios:** React Hook Form + Zod (para validaciones de esquema epidemiológico)
- **Gestión de Estado Global:** Zustand (para estado de la sesión, UPGD seleccionada y borradores)
- **HTTP Client:** TanStack Query (React Query v5) + Axios

> **Nota:** el scaffold actual (`create-next-app`) vive bajo `front/` con `app/` en la raíz.
> La estructura objetivo usa `src/` y se reorganiza durante el Sprint 1.

---

## Estructura de Directorios

```text
front/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   │       └── page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── caracterizacion/
│   │   │   │   └── page.tsx
│   │   │   ├── notificacion/
│   │   │   │   ├── datos-basicos/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── datos-complementarios/
│   │   │   │       └── page.tsx
│   │   │   └── docente/
│   │   │       └── escenarios/
│   │   │           └── page.tsx
│   │   ├── api/             # BFF o reescritura de headers si aplica
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/              # Input, Select, CheckChip, RadioGroup, Actionbar
│   │   ├── forms/           # FormularioDatosBasicos, FormularioComplementario
│   │   └── layout/          # Topbar, HeaderUPGD, NavigationTabs
│   ├── hooks/               # useSivigilaForm, useAuth, useCatalogos
│   ├── styles/
│   │   ├── _variables.scss  # Colores institucional, tipografía Inter, radios
│   │   ├── _mixins.scss     # Responsive break-points, grids
│   │   ├── _base.scss       # Reset y reglas globales
│   │   └── main.scss        # Punto de entrada de estilos
│   ├── lib/                 # Axios instance, validaciones Zod
│   ├── types/               # TypeScript interfaces para SIVIGILA
│   └── store/               # Zustand stores (useUserStore, useCasoStore)
```

## Sistema de Estilos SCSS (`src/styles/_variables.scss`)

A partir del prototipo proporcionado (`caracterizacion.css`):

```scss
// Variables basadas en el diseño del prototipo oficial
$primary: #154d8a;
$primary-dark: #0f3a6b;
$primary-soft: #e3edf9;
$accent-yellow: #ffcc29;
$danger: #dc2626;
$bg: #f1f5f9;
$surface: #ffffff;
$border: #e2e8f0;
$text: #0f172a;
$text-soft: #64748b;
$radius: 14px;

@mixin responsive($canvas) {
  @if $canvas == sm {
    @media only screen and (max-width: 560px) { @content; }
  }
  @else if $canvas == md {
    @media only screen and (max-width: 880px) { @content; }
  }
}
```

## Componentes Clave

### Control "Sí / No" Estilo Chip (`src/components/ui/RadioYN.tsx`)

Inspirado en la interfaz de manifestaciones clínicas del prototipo (`caracterizacion.html` / `datos-complementarios.html`):

```tsx
interface RadioYNProps {
  name: string;
  label: string;
  value: boolean;
  onChange: (val: boolean) => void;
}

export const RadioYN = ({ name, label, value, onChange }: RadioYNProps) => {
  return (
    <div className="recurso">
      <p>{label}</p>
      <div className="yn">
        <label className="chip-sm">
          <input
            type="radio"
            name={name}
            checked={value === true}
            onChange={() => onChange(true)}
          />
          <span>Sí</span>
        </label>
        <label className="chip-sm">
          <input
            type="radio"
            name={name}
            checked={value === false}
            onChange={() => onChange(false)}
          />
          <span>No</span>
        </label>
      </div>
    </div>
  );
};
```

## Validaciones y Lógica Condicional Frontend

Se debe garantizar que los campos deshabilitados en el prototipo (`disabled`) se activen dinámicamente mediante react-hook-form y Zod:

- Si `identGenero == '5'` (Otro), se habilita el campo `otraIdentidad`.
- Si `pEtnica > '0'` (Indígena/Afro/ROM), se habilita el campo `grupoEtnico`.
- Si `hospitalizado == 'SI'`, el campo `fHospitalizacion` es obligatorio.
- Si `condicion == '2'` (Muerto), los campos `fDefuncion` y `certificado` se vuelven requeridos.
