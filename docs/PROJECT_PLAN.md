# PROJECT PLAN: Simulador Educativo SIVIGILA

## Objetivos del Proyecto

Desarrollar un simulador web interactivo de SIVIGILA para el entrenamiento de personal de enfermería y salud pública, conservando la fidelidad técnica y funcional del sistema oficial con una experiencia de usuario (UI/UX) moderna, responsiva y accesible.

El simulador replica fielmente la lógica del sistema SIVIGILA (Sistema de Vigilancia en Salud Pública de Colombia), manteniendo la estructura oficial de captura de información: **Datos Básicos** (Ficha General), **Datos Complementarios** (Específicos por Evento) y **Caracterización UPGD**.

## Diagrama de Arquitectura

```
                          ┌─────────────────────────────────────────┐
                          │            Next.js Frontend             │
                          │   (SSR, SCSS Modules, React Hook Form)  │
                          └────────────────────┬────────────────────┘
                                               │  HTTPS / REST / WS
                                               ▼
                          ┌─────────────────────────────────────────┐
                          │         Python FastAPI Backend          │
                          │     (JWT Auth, RBAC Middleware, Pydantic)│
                          └──────┬───────────────────────────┬──────┘
                                 │                           │
                                 ▼                           ▼
                      ┌────────────────────┐      ┌────────────────────┐
                      │  PostgreSQL Database│      │  Redis Cache/Session│
                      │ (JSONB + Relational│      │ (Token Blacklist)  │
                      └────────────────────┘      └────────────────────┘
```

## Matriz de Roles y Control de Acceso (RBAC)

De acuerdo con la reglamentación del INS / SIVIGILA y las necesidades del simulador educativo:

| Rol SIVIGILA | Descripción en el Sistema Real | Alcance en el Simulador Educativo |
|--------------|--------------------------------|-----------------------------------|
| UPGD (Unidad Primaria Generadora de Datos) | IPS / Hospitales / Clínicas. Notifican casos de eventos de interés en salud pública. | Crear, editar y consultar fichas básicas y complementarias creadas por su propia UPGD. |
| UI (Unidad Informadora) | Entidades que identifican el evento pero no realizan manejo completo de la ficha. | Notificar casos preliminares y transferir a UPGD. |
| Municipal (Sec. Salud Municipal) | Consolida, valida, ajusta registros y vigila el silencio epidemiológico del municipio. | Revisar, aprobar o solicitar ajuste (Ajustes 0-6) a fichas de las UPGD de su municipio. |
| Departamental / Distrital | Supervisión territorial, control de calidad, consolidación departamental. | Auditar notificaciones territoriales, generar reportes epidemiológicos globales. |
| Nacional (INS / MinSalud) | Administrador central de la vigilancia del país. | Acceso global a estadísticas consolidadas y catálogos maestros. |
| Docente / Administrador (Exclusivo Simulador) | Gestiona casos de estudio y pruebas para los estudiantes. | Crear escenarios clínicos, simular brotes, asignar casos a estudiantes y evaluar el diligenciamiento. |

## Estrategia de Desarrollo En Paralelo

- **Frontend Team (Agente Principal):** Implementación de layouts Next.js (App Router), motor de formularios dinámicos con React Hook Form, gestión de estados y diseño en SCSS.
- **Backend Team (Sub-Agente Backend):** Construcción de API RESTful con FastAPI, esquemas Pydantic, motor de RBAC, modelos PostgreSQL (SQLAlchemy v2) y sembrado de catálogos oficiales (DIVIPOLA, Eventos SIVIGILA, CIE-10).

---

## Cronograma de Sprints (4 Sprints / 8 Semanas)

### Sprint 1: Fundamentos, Autenticación y Catálogos Maestros

- [ ] **Backend:** Modelo de usuarios, RBAC, JWT con Refresh Tokens, migración inicial con Alembic.
- [ ] **Backend:** Carga de catálogos oficiales (Departamentos, Municipios, Códigos de Eventos, Ocupaciones, Etnia).
- [ ] **Frontend:** Setup de Next.js (App Router), configuración de SCSS Modules y variables globales.
- [ ] **Frontend:** Módulo de Autenticación (Login, Selección de Rol y UPGD activa).

### Sprint 2: Caracterización de UPGD y Notificación Individual Básica

- [ ] **Backend:** CRUD de Caracterización de UPGD (`caracterizacion.html`).
- [ ] **Backend:** CRUD de Notificación Individual - Datos Básicos (`sivigila.html`).
- [ ] **Frontend:** Formulario responsivo de Caracterización de UPGD.
- [ ] **Frontend:** Formulario de Datos Básicos con validaciones dependientes (ej: Edad vs Unidad de Medida, Visibilidad condicional de identidad/orientación de género).

### Sprint 3: Datos Complementarios Dinámicos y Sistema de Ajustes

- [ ] **Backend:** Estructura JSONB para formularios complementarios específicos por código de evento (ej: Accidente Ofídico - Evento 100/820).
- [ ] **Backend:** Lógica de estados de fichas (Notificada, En Ajuste, Confirmada, Descartada) y trazabilidad.
- [ ] **Frontend:** Formulario de Datos Complementarios (`datos-complementarios.html`) con campos interactivos (chips de selección Sí/No, síntomas locales y sistémicos).
- [ ] **Frontend:** Actionbar sticky funcional con navegación por pestañas y modal de búsqueda de casos.

### Sprint 4: Módulo Docente/Simulación, Reportes y QA

- [ ] **Backend:** API para docentes: generación de escenarios clínicos simulados y evaluación automatizada de formularios.
- [ ] **Frontend:** Dashboard del Docente para revisión de diligenciamiento por parte de estudiantes.
- [ ] **Ambos:** Pruebas e integración end-to-end (E2E) con Playwright, auditoría de accesibilidad.
