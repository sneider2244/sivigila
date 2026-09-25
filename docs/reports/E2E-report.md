# E2E Report — Playwright smoke tests + accessibility audit

Sprint 4 · Task **E2E**: "Pruebas e integración end-to-end (E2E) con Playwright, auditoría de accesibilidad".

Status: **DONE** (sin blockers; 5/5 tests pass, 1 violación serious de contraste detectada y reportada, no corregida).

---

## Archivos creados

| Ruta | Descripción |
|------|-------------|
| `e2e/package.json` | Proyecto npm independiente; deps `@playwright/test` + `@axe-core/playwright`; script `test`. |
| `e2e/playwright.config.ts` | Config: `testDir: ./tests`, `baseURL: http://localhost:3000`, `timeout: 30s`, `expect.timeout: 10s`, reporters `list` + `html`, proyecto `chromium` (Desktop Chrome). |
| `e2e/tests/health.spec.ts` | Smoke test del health check del backend (`GET http://localhost:8000/health`). |
| `e2e/tests/login.spec.ts` | Smoke tests del login (render del formulario + submit de credenciales válidas). |
| `e2e/tests/accessibility.spec.ts` | Auditoría de accesibilidad con `AxeBuilder` sobre `/login` y `/caracterizacion`; vuelca resultados a `/tmp/opencode/axe-violations.json`. |
| `docs/reports/E2E-report.md` | Este reporte. |

Versiones instaladas: `@playwright/test 1.63.0`, `@axe-core/playwright 4.13.0`, Chromium (Chrome for Testing 153.0.8010.12, playwright v1243 + headless shell).

---

## Comandos ejecutados

```bash
# 1. Setup de Playwright (en e2e/)
npm install
npx playwright install chromium

# 2. Levantar stack (Docker ya estaba corriendo y healthy; no se re-creó)
docker compose ps                      # postgres:16 healthy, redis:7 healthy
./.venv/bin/alembic upgrade head       # OK, sin migraciones pendientes
./.venv/bin/python -m app.db.seed      # Seed idempotente: docente/docente123 + catálogos + UPGD ejemplo

# 3. Servidores (background, logs a /tmp/opencode/)
#    Backend:  nohup ./.venv/bin/uvicorn app.main:app --port 8000 > /tmp/opencode/sivigila-backend.log 2>&1 &
#    Frontend: nohup npm run dev > /tmp/opencode/sivigila-frontend.log 2>&1 &
#    Verificación: curl http://localhost:8000/health -> 200 {"status":"ok"}
#                  curl http://localhost:3000        -> 200

# 4. Smoke tests
npx playwright test
```

Evidencia del estado real del stack antes de los tests:

- `docker compose ps`: `sivigila-postgres` (Up, healthy) y `sivigila-redis` (Up, healthy).
- `GET http://localhost:8000/health` → `200` `{"status":"ok"}`.
- `POST http://localhost:8000/api/v1/auth/login` (docente/docente123) → `200` con `access_token`/`refresh_token`/`usuario`.

---

## Resultado de los tests (`npx playwright test`)

```
Running 5 tests using 4 workers
  ✓  2 [chromium] › tests/health.spec.ts:3:5 › backend /health returns 200 {status:ok} (64ms)
  ✓  1 [chromium] › tests/login.spec.ts:3:5 › login page renders the form (5.5s)
  ✓  5 [chromium] › tests/login.spec.ts:12:5 › login submits valid credentials and navigates away from /login (6.4s)
  ✓  3 [chromium] › tests/accessibility.spec.ts:30:5 › accessibility audit: /login (6.5s)
  ✓  4 [chromium] › tests/accessibility.spec.ts:43:5 › accessibility audit: /caracterizacion (6.9s)

  5 passed (9.0s)
```

**5 passed / 0 failed.** El flujo completo de login funcionó (redirect fuera de `/login` sin error de autenticación), no fue necesario degradar a la aserción mínima.

---

## Auditoría de accesibilidad (axe-core)

Resumen por severidad:

| Página | Violations | Critical | Serious | Moderate | Minor |
|--------|-----------|----------|---------|----------|-------|
| `/login` | 0 | 0 | 0 | 0 | 0 |
| `/caracterizacion` | 2 | 0 | **1** | 2 nodos (1 regla) | 0 |

Top offenders (no corregidos, solo reportados):

1. **`color-contrast` — serious** (`/caracterizacion`)
   - Regla: elementos deben cumplir ratio mínimo WCAG 2 AA (4.5:1).
   - Nodo: `<p class="...subtitle">Registro de la información institucional de la unidad primaria generadora de datos.</p>`
   - Detalle: fg `#64748b` sobre bg `#f1f5f9`, ratio **4.34** (< 4.5), 14px peso normal.
   - Target: `.caracterizacion-module-scss-module__kRQRlW__subtitle`

2. **`region` — moderate** (`/caracterizacion`)
   - Regla: todo el contenido debe estar contenido en landmarks.
   - Nodos (2):
     - `<span class="Topbar-...__brand">SIVIGILA</span>` — target `.Topbar-...__brand`
     - `<div class="Topbar-...__user">…</div>` — target `.Topbar-...__user`

No se corrigió nada (scope de la tarea: solo reportar).

---

## Blockers / observaciones

- **Ninguno.** Descarga de Chromium OK, arranque de servidores OK, seed OK, tests verdes.
- Docker (Postgres16 + Redis7) ya estaba corriendo desde tareas previas y se dejó corriendo. No se re-creó.
- Los servidores de dev (uvicorn + `next dev`) se detuvieron al finalizar la tarea (ver Cleanup).

## Cleanup

- Detenidos los procesos `uvicorn` (backend) y `next dev` (frontend) lanzados para esta tarea.
- Docker se dejó corriendo (ya estaba up antes de la tarea).
- Nada commiteado (no se hizo `git commit`).
