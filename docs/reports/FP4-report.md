# FP4 — Reporte: Acceso (dos modos), registro, home, guard y selector de rol

## Estado

Completado. `npm run lint` y `npm run build` pasan sin errores.

## Archivos creados

- `front/src/components/layout/AuthGuard.tsx` — Guard de auth client-side con hidratación segura.
- `front/src/app/(dashboard)/page.tsx` — Home con saludo y tarjetas de módulos según rol.
- `front/src/app/(dashboard)/page.module.scss` — Estilos del home (tokens del proyecto).

## Archivos modificados

- `front/src/lib/auth.ts` — `mapUsuario` exportado; `numero_identificacion` en `UsuarioRaw`; nuevas `register()` y `updateRol()`.
- `front/src/types/index.ts` — `numeroIdentificacion` en `Usuario`; nueva constante `ROLES_NO_DOCENTE` y tipo `RolNoDocente`.
- `front/src/store/useUserStore.ts` — nuevo action `setUser`; persist con `skipHydration: true`.
- `front/src/hooks/useAuth.ts` — expone `register` y `changeRol`.
- `front/src/app/(auth)/login/page.tsx` — reescrito: selector de modo, login por modo, formulario de registro.
- `front/src/app/(auth)/login/login.module.scss` — nuevos `.modes`, `.mode`, `.modeActive`, `.select`, `.switchLink`.
- `front/src/app/(dashboard)/layout.tsx` — envuelve Actionbar + children en `<AuthGuard>`.
- `front/src/components/layout/NavigationTabs.tsx` — pestañas según rol.
- `front/src/components/layout/Topbar.tsx` — selector de rol dinámico (solo no-DOCENTE).
- `front/src/components/layout/Topbar.module.scss` — estilos del selector de rol.
- `front/src/app/page.tsx` — ELIMINADO (placeholder).

## Flujo de login / registro

### Login (dos modos)

`(auth)/login/page.tsx` renderiza un `LoginForm` con un selector de modo (`Estudiante | Docente`) y un `RegisterForm` que se alterna por estado local `vista`.

- Modo **Estudiante**: campos `email` + `numeroIdentificacion` → `login(email, numeroIdentificacion)`.
- Modo **Docente**: campos `username` + `password` → `login(username, password)`.

El schema es un `z.discriminatedUnion("modo", ...)`: la rama estudiante valida email con formato, la rama docente solo no-vacío. El `modo` viaja como campo (input hidden registrado) y los tabs hacen `setValue("modo", next, { shouldValidate: true })`. Al enviar, ambos modos terminan llamando `login(values.username, values.password)` porque en estudiante `username=email` y `password=identificación`.

Tras éxito: `router.replace("/")`. Errores: 401 → mensaje específico por modo; otro → genérico.

### Registro

`RegisterForm` con `email`, `nombreCompleto`, `numeroIdentificacion` y selector de rol (`ROLES_NO_DOCENTE`, 5 roles, default `UPGD`). Llama `register({ email, nombreCompleto, numeroIdentificacion, rol })` → `POST /auth/register` (snake_case) → `mapLoginResponse` → `setSession` → `router.replace("/")`.

Errores: 409 → "Ya existe un usuario con ese email."; 422 → `detail` del backend (p. ej. rol DOCENTE o datos inválidos); otro → genérico.

### Selector de rol (Topbar)

Para no-DOCENTE se muestra un `<select>` con los 5 roles (`value = user.rol`). `onChange` → `changeRol(nuevoRol)` → `PATCH /auth/me` → `setUser(updated)` en el store. Estado `changingRol` (disabled) y `rolError` simple. Para DOCENTE no se muestra (solo texto `rol · codUpgd`).

## Hidratación del guard

`AuthGuard` es un client component envuelto en el layout server de `(dashboard)`.

Problema detectado y resuelto: zustand `persist` usa por defecto `createJSONStorage(() => window.localStorage)`. En el servidor (prerender/SSR) `window` no existe → `createJSONStorage` devuelve `undefined` → el middleware `persist` retorna **antes** de asignar `api.persist`, por lo que `useUserStore.persist` es `undefined` en el server. Acceder a `useUserStore.persist.onFinishHydration` crasheaba el prerender con `TypeError: Cannot read properties of undefined`.

Solución:
1. `skipHydration: true` en `useUserStore` para que no hidrate automáticamente y el server no intente acceder a storage.
2. En `AuthGuard` se usa `useSyncExternalStore` con `subscribeToHydration` / `getHydrationSnapshot` / `getServerHydrationSnapshot`:
   - `subscribe` usa `useUserStore.persist?.onFinishHydration(cb)` con fallback `() => {}` (server-safe).
   - `getSnapshot` = `useUserStore.persist?.hasHydrated() ?? false`.
   - `getServerSnapshot` = `false` siempre (evita mismatch de hidratación).
3. Un `useEffect` llama `useUserStore.persist?.rehydrate()` una vez montado el cliente (los effects no corren en el server).
4. Otro `useEffect` redirige a `/login` solo cuando `hydrated && (!user || !accessToken)`.

Render: si no hidratado → `null`; si hidratado y sin sesión → `null` (redirigiendo); si hay sesión → `children`.

Se evitó el patrón `setMounted(true)` dentro de un effect porque `eslint-plugin-react-hooks` (v6, regla `react-hooks/set-state-in-effect`) lo marca como error; `useSyncExternalStore` no dispara esa regla.

## Resultados

- `npm run lint`: sin errores.
- `npm run build`: compila y genera 9 páginas estáticas sin errores.

## Gotchas

- `useUserStore.persist` es `undefined` en SSR (ver arriba): nunca acceder sin optional chaining ni sin `skipHydration`.
- `react-hooks/set-state-in-effect` prohíbe `setState` síncrono en el body de un effect; usar `useSyncExternalStore` para suscribirse a la hidratación.
- La ruta `/mis-escenarios` (tarjeta "Mis escenarios" y pestaña) apunta a una página que aún no existe (Fase 5). El link 404 hasta que se implemente esa fase; no rompe lint/build.
- zod v4: `z.enum` acepta la tupla `as const` de `ROLES_NO_DOCENTE`; `z.discriminatedUnion` por el campo `modo`.
- El mapeo `numero_identificacion` → `numeroIdentificacion` se agregó a `Usuario`/`mapUsuario` porque `UsuarioOut` del backend ya lo incluye (Fase 1).
