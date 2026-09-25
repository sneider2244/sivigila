# PROMPT PARA SUB-AGENTE DE CÓDIGO (DESARROLLO BACKEND SIVIGILA)

**Rol:** Eres un Ingeniero Backend Senior experto en Python, FastAPI, PostgreSQL y arquitectura RESTful para sistemas de salud pública.

**Objetivo:** Desarrollar el servicio API backend completo para el simulador SIVIGILA, alineado rigurosamente con los modelos de datos de las fichas oficiales y el sistema de roles SIVIGILA.

---

## Tareas Específicas a Ejecutar

### 1. Setup Inicial

- Crear la aplicación FastAPI en `app/main.py` con CORS habilitado para el frontend de Next.js.
- Configurar conexión asíncrona a PostgreSQL con SQLAlchemy 2.0 y soporte para migraciones con Alembic.

### 2. Módulo de Autenticación y RBAC (`app/api/v1/endpoints/auth.py`)

- Implementar POST `/api/v1/auth/login` recibiendo credenciales y retornando JWT token + datos del usuario (rol, cod_upgd, nombre).
- Implementar middleware de RBAC para validar acceso según los 6 roles SIVIGILA: `UPGD`, `UI`, `MUNICIPAL`, `DEPARTAMENTAL`, `NACIONAL`, `DOCENTE`.

### 3. Módulo Caracterización UPGD (`app/api/v1/endpoints/caracterizacion.py`)

- Basándote en el prototipo `caracterizacion.html`, crea las tablas y endpoints para:
  - GET `/api/v1/upgd/{cod_prestador}`: Consultar información institucional.
  - POST / PUT `/api/v1/upgd`: Guardar/Actualizar caracterización (Campos: Razón social, NIT, Nivel de complejidad, recursos disponibles como COVE, Unidad de Análisis, Internet, estado activa/inactiva).

### 4. Módulo Ficha Datos Básicos (`app/api/v1/endpoints/fichas_basicas.py`)

- Basándote en el prototipo `sivigila.html`, implementar:
  - POST `/api/v1/fichas/datos-basicos`: Crear nueva notificación individual.
  - GET `/api/v1/fichas/datos-basicos/{id}`: Obtener ficha básica.
  - GET `/api/v1/fichas/datos-basicos`: Listar fichas con filtros por `cod_evento`, `semana`, `anio`, `num_id` y `cod_upgd`.
  - Validar que un usuario con rol `UPGD` solo pueda ver/modificar fichas de su propia `cod_upgd`.

### 5. Módulo Datos Complementarios (`app/api/v1/endpoints/fichas_complementarias.py`)

- Basándote en el prototipo `datos-complementarios.html`, implementar:
  - POST `/api/v1/fichas/datos-complementarios`: Almacenar datos complementarios asociados a una ficha básica.
  - Utilizar validación Pydantic para el campo JSONB según el evento (ejemplo: validación de manifestaciones locales/sistémicas para accidente ofídico).

### 6. Catálogos Oficiales (`app/api/v1/endpoints/catalogos.py`)

- Endpoints de consulta para comboboxes: `/api/v1/catalogos/eventos`, `/api/v1/catalogos/departamentos`, `/api/v1/catalogos/municipios`.

---

## Criterios de Aceptación Técnicos

- Cobertura de tipos 100% con Pydantic v2.
- Respuestas HTTP estandarizadas: `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.
- Formato de fechas ISO 8601 (`YYYY-MM-DD`).
- Código formateado con Black/Ruff y totalmente documentado con docstrings tipo Google.
