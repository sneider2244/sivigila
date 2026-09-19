# Dominio

Conocimiento extraído del legacy (`database.py`) para no tener que releerlo.

## Roles

Jerarquía estricta. Un usuario solo puede gestionar a usuarios de rango
**menor**; `super_admin` gestiona a todos.

| Rol | Rango | Descripción |
|-----|-------|-------------|
| `super_admin` | 3 | Todo, incluye gestionar otros admins |
| `admin` | 2 | Gestiona usuarios de rango menor, notifica, edita |
| `digitador` | 1 | Diligencia fichas, labs y caracterización |
| `consulta` | 0 | Solo lectura (indicadores y listado) |

## Permisos granulares

Además del rol, cada usuario tiene permisos individuales (JSON en `usuarios.permisos`).
Al cambiar el rol, se resetean a los defaults de ese rol.

| Clave | Default super_admin / admin / digitador / consulta |
|-------|----------------------------------------------------|
| `gestionar_usuarios` | ✅ / ✅ / ❌ / ❌ |
| `gestionar_caracterizacion` | ✅ / ✅ / ✅ / ❌ |
| `notificar_individual` | ✅ / ✅ / ✅ / ❌ |
| `editar_notificaciones` | ✅ / ✅ / ✅ / ❌ |
| `gestionar_laboratorios` | ✅ / ✅ / ✅ / ❌ |
| `ver_reportes` | ✅ / ✅ / ✅ / ✅ |

Regla de gestión: `super_admin` siempre puede; el resto solo si tiene
`gestionar_usuarios` **y** su rango es mayor al del objetivo.

## Estados de ficha

`EstadoFicha`: `EN_PROCESO` ("En proceso") → `TERMINADA` ("Terminada").
Guardar deja `EN_PROCESO`; Terminar deja `TERMINADA` (lista para envío).

## Campos dinámicos por evento

Cada evento define sus "datos complementarios" en `eventos.campos_json`:
lista de campos con `key`, `label`, `tipo`.

Tipos (`TipoCampo`):

| Tipo | Render | Extra |
|------|--------|-------|
| `texto` | input de texto | — |
| `si_no` | combo Sí/No | — |
| `lista` | combo | requiere `opciones` |

Eventos seed actuales: `205` Chagas, `100` Accidente Ofídico, `210` Dengue.

Los valores diligenciados se guardan como JSON en
`notificaciones.datos_complementarios`.

## Entidades

| Entidad | Tabla | Notas |
|---------|-------|-------|
| Usuario | `usuarios` | rol + permisos JSON + `activo` |
| UPGD | `upgd` | unidad notificadora; una activa por sesión |
| Evento | `eventos` | catálogo con formulario dinámico |
| Notificación | `notificaciones` | ficha individual del paciente |
| Laboratorio | `laboratorios` | N resultados por ficha (FK `ON DELETE CASCADE`) |
| Auditoría | `auditoria` | bitácora de acciones |

## Seeds iniciales

- `admin` / `Admin123!` → `super_admin`
- `SIVIGILA` / `sivigila2026` → `digitador`

> Rotar estas credenciales antes de producción. En el sistema web el admin se
> siembra desde variables de entorno.
