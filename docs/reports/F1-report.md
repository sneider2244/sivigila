# Task F1 — Scaffold reorganization + styling + deps

**Status:** DONE
**Date:** 2026-09-25
**Scope:** `front/` only (no feature logic, no login UI)

---

## 1. Files created

### Styles (`src/styles/`)
| File | Content |
|------|---------|
| `src/styles/_variables.scss` | Colors institucionales, `$radius: 14px` (exact values from `docs/FRONTEND_ARCH.md`) |
| `src/styles/_mixins.scss` | `@mixin responsive($canvas)` (sm 560px / md 880px) |
| `src/styles/_base.scss` | Reset + global rules, uses `$text`, `$bg`, Inter font stack |
| `src/styles/main.scss` | Entry point: `@use 'variables'; @use 'mixins'; @use 'base';` |

### Placeholders
| File | Content |
|------|---------|
| `src/types/index.ts` | `Rol` union type, `User`, `UPGD`, `Caso` interfaces |
| `src/store/useUserStore.ts` | Minimal zustand store (`user`, `setUser`) |
| `src/store/useCasoStore.ts` | Minimal zustand store (`upgdSeleccionada`, `borrador`) |
| `src/lib/axios.ts` | `axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1" })` |

### Empty directories (with `.gitkeep`)
`src/hooks/`, `src/components/ui/`, `src/components/forms/`, `src/components/layout/`

## 2. Files moved

| From | To |
|------|----|
| `app/favicon.ico` | `src/app/favicon.ico` |
| `app/layout.tsx` | `src/app/layout.tsx` (rewritten) |
| `app/page.tsx` | `src/app/page.tsx` (rewritten) |
| `app/globals.css` | **deleted** (replaced by `src/styles/main.scss`) |
| `app/page.module.css` | **deleted** (replaced by minimal placeholder page) |

Root `app/` was fully removed so Next picks up `src/app/` (a leftover root `app/` would shadow `src/app/`).

## 3. Files modified

| File | Change |
|------|--------|
| `tsconfig.json` | `paths`: `"@/*": ["./*"]` → `"@/*": ["./src/*"]` |
| `src/app/layout.tsx` | Import `@/styles/main.scss` (replaces `./globals.css`); removed `next/font/google` (Geist); `lang="es"`; metadata → SIVIGILA |
| `src/app/page.tsx` | Minimal placeholder heading; removed `next/image` + public SVGs |
| `package.json` / `package-lock.json` | deps added (below) |

## 4. Versions installed

### Runtime (`dependencies`)
| Package | Version |
|---------|---------|
| `react-hook-form` | 7.88.0 |
| `zod` | 4.6.5 |
| `@hookform/resolvers` | 5.9.1 |
| `zustand` | 5.0.15 |
| `@tanstack/react-query` | 5.103.2 (pinned `^5` per arch "React Query v5") |
| `axios` | 1.20.0 |

### Dev (`devDependencies`)
| Package | Version |
|---------|---------|
| `sass` | 1.105.0 |

0 vulnerabilities reported by npm audit.

## 5. Next 16 gotchas discovered (IMPORTANT)

1. **`next lint` removed.** `next build` no longer runs linting. `package.json` already wired `"lint": "eslint"` (ESLint Flat Config via `eslint.config.mjs`), so `npm run lint` invokes ESLint directly.
2. **Turbopack is the default** for both `next dev` and `next build` (no `--turbopack` flag needed). Build output shows `Next.js 16.3.6 (Turbopack)`.
3. **Modern Sass API (sass-loader v16).** Legacy `@import` is deprecated; partials were wired with `@use`. Turbopack does **not** support the legacy `~` tilde prefix for `node_modules` Sass imports.
4. **`LayoutProps<"/">` global type helper** (typed routes) is generated during build via `next typegen` — it needs no import. Kept as-is from the scaffold; type-checks clean after the `src/` move.
5. **Async Request APIs are fully async** — `params`/`searchParams`/`cookies()`/`headers()` return Promises; synchronous access was removed. Not hit by F1 (no dynamic routes yet), but relevant for F2+.
6. **`src/app` is ignored if a root `app/` still exists.** The root `app/` had to be deleted, not just copied.
7. **`next/font/google` (Geist) removed.** Inter is the spec'd typeface (`docs/FRONTEND_ARCH.md`). Using a system Inter stack in `_base.scss` also avoids a network font fetch during `next build`.
8. **`next/image` defaults changed** (`imageSizes` no longer includes 16px; `qualities` now only `[75]`). Irrelevant to F1 — removed `next/image` usage from the placeholder page.
9. **`next dev` and `next build` use separate output dirs** (`next dev` → `.next/dev`), enabling concurrent runs; a lockfile prevents double instances.

## 6. Verification output

### `npm run lint`
```
> sivigila@0.1.0 lint
> eslint

```
Exit code 0 — no errors/warnings.

### `npm run build`
```
▲ Next.js 16.3.6 (Turbopack)
✓ Running next.config.ts took 164ms
  Creating an optimized production build ...
✓ Compiled successfully in 7.4s
  Running TypeScript ...
  Finished TypeScript in 3.4s ...
  Collecting page data using 5 workers ...
✓ Generating static pages using 5 workers (4/4) in 869ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
└ ○ /_not-found

○  (Static)  prerendered as static content
```
Exit code 0 — clean production build.

## 7. Deviations (with justification)

1. **Responsive mixin placed in `_mixins.scss`, not `_variables.scss`.** `docs/FRONTEND_ARCH.md` shows a single code block titled `_variables.scss` that contains both variables and the mixin, but its directory listing assigns "Responsive break-points" to `_mixins.scss`. Followed the directory listing (the more granular source of truth). Values are byte-for-byte identical to the spec.
2. **Removed `next/font/google` (Geist) in favor of a system Inter stack.** The spec specifies Inter (`tipografía Inter`); Geist is a create-next-app artifact. Also removes build-time network dependency.
3. **Simplified `page.tsx` placeholder** (dropped `next/image` + public SVGs) and deleted `page.module.css`/`globals.css`. This is scaffold cleanup, not feature logic; the page is a placeholder until Task F2.
4. **`.gitkeep` added** to the four empty directories so they persist as part of the target structure (empty dirs are not tracked by git).
5. **`NEXT_PUBLIC_API_URL` default set to `http://localhost:8000/api/v1`**, matching the backend route prefix documented in `docs/BACKEND_SUBAGENT_PROMPT.md`.

Nothing was committed; all changes remain in the working tree.
