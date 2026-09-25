# F2 — Módulo de autenticación (login + estado de sesión + wiring HTTP)

## Estado

Completo. `npm run lint` pasa y `npm run build` genera un build de producción limpio.

## Archivos creados / modificados

Creados:

- `front/src/lib/auth.ts` — tipos "raw" del backend (snake_case), mapper `mapLoginResponse` y función `login(username, password)`.
- `front/src/hooks/useAuth.ts` — hook thin-wrapper sobre el store + servicio de login.
- `front/src/lib/queryClient.ts` — `getQueryClient()` (una instancia por render de servidor, reutilizada en el browser).
- `front/src/app/providers.tsx` — componente cliente que envuelve `children` con `QueryClientProvider`.
- `front/src/app/(auth)/login/page.tsx` — página de login (React Hook Form + Zod).
- `front/src/app/(auth)/login/login.module.scss` — estilos de la página usando las variables SCSS institucionales.

Modificados:

- `front/src/types/index.ts` — reemplaza `User` por `Usuario`, agrega `LoginResponse`.
- `front/src/store/useUserStore.ts` — store Zustand con `user`/`accessToken`/`refreshToken`, `setSession`, `setTokens`, `clearSession`, persistencia a `localStorage`.
- `front/src/lib/axios.ts` — interceptores de request/response con refresh.
- `front/src/app/layout.tsx` — envuelve el árbol con `<Providers>`.

## Shape exacto consumido

Petición de login (POST `http://localhost:8000/api/v1/auth/login`):

```json
{ "username": "jdoe", "password": "secreto123" }
```

Respuesta del backend (snake_case), tal cual se consume:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "1",
    "username": "jdoe",
    "nombre_completo": "John Doe",
    "rol": "UPGD",
    "cod_upgd": "1001",
    "activo": true
  }
}
```

El mapper `mapLoginResponse` convierte a camelCase:

```ts
{
  accessToken, refreshToken, tokenType,
  user: { id, username, nombreCompleto, rol, codUpgd, activo }
}
```

## Manejo del refresh

- **Request interceptor:** adjunta `Authorization: Bearer <accessToken>` tomado de `useUserStore.getState()`.
- **Response interceptor:** ante un `401` que **no** provenga de `/auth/login` ni `/auth/refresh`, y que **no** sea ya un retry (`_retry`), intenta refrescar el token:
  1. Si no hay `refreshToken`, limpia la sesión y rechaza.
  2. Llama `POST /auth/refresh` con `{ "refresh_token": <refreshToken> }` usando una instancia `axios` cruda (no `api`) para evitar reentrar al interceptor. Se espera respuesta `{ "access_token": "..." }`.
  3. Las llamadas concurrentes se deduplican con una única `refreshPromise` en vuelo.
  4. Con el nuevo token, actualiza el store (`setTokens`), reescribe el header `Authorization` y reintenta la petición original **una** vez.
  5. Si el refresh falla, limpia la sesión y rechaza.

- El flag `_retry` evita bucles infinitos de reintento.

## Gotchas de Next 16 encontrados

- **`next lint` eliminado.** `npm run lint` ejecuta ESLint (flat config `eslint.config.mjs`) directamente; `next build` ya no corre linting.
- **Turbopack por defecto** en `dev` y `build` (sin flag). La ruta de SCSS no usa prefijo `~`.
- **Sass moderno:** se usa `@use "..." as *;` en `login.module.scss`, nunca `@import`, igual que el resto del setup F1 (`_base.scss`).
- **`LayoutProps<'/'>`** es un helper global tipado (sin import); se conserva en `layout.tsx`.
- **Client components** llevan `"use client"` donde usan hooks/estado (`login/page.tsx`, `useAuth.ts`, `useUserStore.ts`, `providers.tsx`).
- La navegación post-login usa `useRouter().replace("/")` (event handler, no `redirect()`).

## Salida de lint / build

`npm run lint`:

```
> sivigila@0.1.0 lint
> eslint
```

(sin errores ni warnings)

`npm run build`:

```
▲ Next.js 16.3.6 (Turbopack)
✓ Compiled successfully
✓ Finished TypeScript
✓ Generating static pages (5/5)
Route (app)
┌ ○ /
├ ○ /_not-found
└ ○ /login
```

Build de producción limpio.

## Notas / concerns

- El backend aún no existe (Sprint 1), así que el login no se probó contra un servidor real; solo se validó tipado, lint y build. La contractura se fijó según lo especificado.
- Se asumió que `/auth/refresh` responde `{ "access_token": "..." }` (opcional `refresh_token`). Si el backend rota el refresh token o usa otro shape, ajustar `refreshAccessToken` en `axios.ts` y `setTokens` en el store.
- La redirección post-login va a `/` (home), que hoy es una página estática de placeholder; el dashboard real corresponde a tareas posteriores.
