# docs/superpowers — cómo se hizo la migración a web

Esta carpeta guarda el diseño y el plan con los que se migró SIVIGILA de app de escritorio
(CustomTkinter) a app web (FastAPI + Jinja2 + HTMX + SQLite). Se generaron con
**Superpowers**, un conjunto de *skills* para Claude Code que obliga a seguir un proceso:
primero se acuerda el diseño, luego se escribe el plan y solo después se programa, siempre
con tests escritos antes del código.

## Archivos

| Archivo | Qué es | Cuándo leerlo |
|---|---|---|
| [`specs/2026-10-03-sivigila-web-design.md`](specs/2026-10-03-sivigila-web-design.md) | **Especificación**: qué se construye y por qué. Decisiones de stack, permisos por ruta, pantallas, validaciones, errores y tests. Es la fuente de verdad: si el código y la spec no coinciden, se discute contra la spec. | Antes de cambiar el comportamiento de la app. |
| [`plans/2026-10-03-sivigila-web.md`](plans/2026-10-03-sivigila-web.md) | **Plan de implementación**: 11 tareas en orden, cada una con su test, el código completo y su commit. Es histórico: describe cómo se llegó al código, no cómo está hoy (después hubo arreglos de revisión y de QA, ver abajo). | Para entender el porqué de una parte del código o retomar el mismo estilo de trabajo. |

## El proceso que se siguió

| Paso | Skill de Superpowers | Resultado |
|---|---|---|
| 1. Análisis del repo | — (dos subagentes en paralelo) | Qué hace la app, cómo correrla y riesgos encontrados. |
| 2. Diseño | `brainstorming` | Preguntas una a una (usuarios, despliegue, alcance), tres secciones de diseño aprobadas y la spec escrita y revisada. |
| 3. Plan | `writing-plans` | Plan de 11 tareas con interfaces entre tareas y una sección "Review Focus" con los casos que más fácil se escapan. |
| 4. Implementación | `executing-plans` + `test-driven-development` | Cada tarea: test que falla → código → test que pasa → commit. Un registro de avance por tarea. |
| 5. Revisión de toda la rama | `requesting-code-review` (revisor independiente) | 2 hallazgos críticos y 5 importantes, todos corregidos con su test (ver abajo). |
| 6. Validación en navegador | agente `goe:qa-playwright` | Recorrido completo de 11 puntos en el navegador; 3 hallazgos corregidos. |

## Hallazgos corregidos después del plan

**Revisión de código** (`tests/test_hallazgos_revision.py`):

- Una base de la versión de escritorio no obligaba a cambiar las claves por defecto. Ahora la
  migración marca a todos los usuarios existentes para cambio de clave.
- Un admin con permisos limitados podía crear usuarios con más permisos que él. Ahora solo
  puede dar o quitar los permisos que él mismo tiene.
- Cerrar sesión o cambiar la clave no invalidaba una cookie copiada. Ahora cada usuario tiene
  una versión de sesión que se incrementa en esos casos.
- Guardar una ficha "Terminada" la dejaba "Terminada" aunque quedara incompleta. Ahora vuelve
  a "En proceso".
- La búsqueda distinguía tildes y mayúsculas, y `%` o `_` actuaban como comodines. Ahora
  "perez" encuentra "PÉREZ" y los comodines se buscan como texto.
- Los errores en peticiones HTMX (403, token vencido, 500) no se veían. Ahora el servidor pide
  recargar la página (`HX-Refresh`).
- Los logs de uvicorn guardaban la búsqueda (con documentos) y el detalle de las excepciones.
  Ahora un filtro quita la query string y deja solo el tipo de error.

**QA en navegador** (`tests/test_hallazgos_qa.py`):

- Se sembraba un segundo usuario (`SIVIGILA`) con clave publicada. Ahora una base nueva solo
  crea `admin`.
- En celular el listado se desbordaba y la barra lateral ocupaba media pantalla. Ahora las
  tablas se desplazan dentro de su recuadro y la barra es compacta.
- Recargar después de un "Terminar" o "Guardar" fallido daba 405. Ahora redirige a la ficha.

## Decisiones tomadas durante la implementación

- `requirements-dev.txt` usa `httpx2` en vez de `httpx`: Starlette 1.7 marca `httpx` como
  deprecado en el cliente de pruebas.
- Un admin limitado no puede dar ni quitar un permiso que él no tiene; ese permiso conserva el
  valor actual del usuario editado.
- La migración obliga a cambiar la clave a **todos** los usuarios de una base vieja, no solo a
  los sembrados, porque no hay forma de saber qué claves son débiles.
- Los datos de prueba de los tests son inventados y están marcados `# datos sintéticos`
  (política de datos de paciente de la organización).

## Pendientes conocidos

Decisiones de producto:

- Con solo el permiso `notificar_individual` se puede abrir cualquier ficha por su número en
  la URL, pero no se puede editar la propia. Así lo define la spec; se podría limitar a las
  fichas propias y permitir editarlas mientras estén "En proceso".
- No hay separación de fichas por UPGD (la spec asume una sola institución).
- La edad se calcula con la fecha del día en que se guarda.
- El bloqueo de login (5 intentos) vive en memoria y se pierde al reiniciar.

Menores, sin corregir:

- `/fichas/abc` responde con un error técnico en JSON en vez de la página 404.
- Un super_admin puede quitarse a sí mismo el rol y dejar el sistema sin super_admin.
- `/cambiar-password` no limita los intentos contra la clave actual.
- Si alguien escribe su clave en el campo de usuario, el intento fallido la guarda en la
  auditoría.
- La pestaña con errores no lleva marca, "Quitar" laboratorio no pide confirmación, el rol por
  defecto al crear usuario es "Super administrador" y la ficha no avisa cuando está en solo
  lectura.

Del repo:

- Por ahora no hay `.gitignore` y `sivigila.db` está versionada. En cuanto la base tenga fichas
  reales no puede ir en un commit (Ley 1581): hay que volver a ignorarla antes.

## Cómo seguir trabajando así

Con Claude Code y el plugin Superpowers instalado, un cambio nuevo empieza pidiendo el diseño
(skill `brainstorming`). El resultado va a `specs/` y el plan a `plans/`, con fecha en el
nombre del archivo. La implementación se hace tarea por tarea con TDD. La suite corre con
`python -m pytest` desde la raíz del repo.
