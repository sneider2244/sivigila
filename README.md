# SIVIGILA Moderno 🩺

Versión moderna e interactiva del flujo mostrado en tus capturas de pantalla
del Software SIVIGILA (login → caracterización → notificación individual →
datos complementarios → laboratorio → terminar), construida en **Python**
con:

- **CustomTkinter** → interfaz gráfica moderna (tema oscuro, tarjetas,
  botones redondeados, barra lateral de navegación).
- **SQLite** → base de datos local, sin necesidad de instalar un servidor.
- **Login real** → usuarios guardados en base de datos con contraseñas
  cifradas (PBKDF2-SHA256 + salt, sin contraseñas en texto plano).
- **Formularios dinámicos** → a diferencia del software original, la
  página de "Datos complementarios" se genera automáticamente según el
  evento que elijas (ya vienen configurados Chagas, Accidente Ofídico y
  Dengue, y puedes agregar más eventos en `database.py`).

## 1. Instalación

Requiere Python 3.9 o superior.

```bash
cd sivigila_moderno
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Ejecutar

```bash
python app.py
```

Al iniciar por primera vez se crea automáticamente el archivo `sivigila.db`
con dos usuarios de prueba:

| Usuario    | Contraseña     | Rol                |
|------------|----------------|--------------------|
| `admin`    | `Admin123!`    | Super administrador|
| `SIVIGILA` | `sivigila2026` | Digitador          |

> ⚠️ Cambia estas contraseñas antes de usar el sistema con datos reales
> (inicia sesión como `admin` → menú **Usuarios** → botón **Clave**).

## 3. Roles y permisos

El sistema ahora tiene 4 roles con una jerarquía clara:

| Rol                  | Puede...                                                        |
|-----------------------|------------------------------------------------------------------|
| **Super administrador** | Todo, incluyendo crear/editar/desactivar a cualquier usuario, incluso otros administradores. |
| **Administrador**       | Notificar, editar caracterización/laboratorios, y gestionar usuarios de rango *digitador* o *consulta* (no puede tocar a otros admins). |
| **Digitador**            | Diligenciar y editar fichas, laboratorios y caracterización. No administra usuarios. |
| **Consulta**             | Solo ve el panel de indicadores y el listado de fichas (modo lectura). |

Además de los roles, cada usuario tiene **permisos granulares** (checkboxes)
que puedes personalizar individualmente desde **Usuarios → Editar**:
gestionar usuarios, gestionar caracterización, notificar, editar/terminar
fichas, gestionar laboratorios y ver reportes. Al cambiar el rol de un
usuario, los permisos se resetean a los valores por defecto de ese rol,
pero luego puedes ajustarlos uno por uno.

### Cómo crear un nuevo usuario (como super administrador o administrador)

1. Inicia sesión con una cuenta que tenga el permiso "Gestionar usuarios"
   (por defecto, `admin`).
2. Ve al menú lateral **👥 Usuarios**.
3. Clic en **➕ Crear nuevo usuario**, completa código, nombre, contraseña
   inicial y rol. Los permisos se autocompletan según el rol elegido — puedes
   marcarlos o desmarcarlos manualmente.
4. Desde la misma pantalla puedes **Editar**, **Activar/Desactivar** o
   **restablecer la Clave** de cualquier usuario que esté en tu jerarquía o
   por debajo (un administrador no puede modificar a otro administrador ni
   al super administrador; el super administrador sí puede gestionar a
   todos).

## 4. Flujo de uso (equivalente al del manual)

1. **Login** con código de usuario y contraseña.
2. **Caracterización**: registra la UPGD (razón social, NIT, responsable,
   recursos disponibles) y selecciónala como activa para la sesión.
3. **Notificación individual**:
   - Pestaña 1 — Datos básicos del paciente (iguales para todas las fichas).
   - Pestaña 2 — Datos complementarios (el formulario cambia según el
     evento que elijas: Chagas, Accidente Ofídico, Dengue, etc.).
   - Pestaña 3 — Laboratorios (agrega uno o varios resultados a la ficha).
4. **Guardar** deja la ficha "En proceso"; **Terminar** la marca como
   "Terminada" y lista para envío.
5. **Fichas registradas**: buscador y filtro por evento, con indicador de
   estado y acceso directo para editar cada ficha.
6. **Panel principal**: accesos rápidos + gráfico de barras con el número
   de casos notificados por evento.

## 5. Estructura del proyecto

```
sivigila_moderno/
├── app.py           # Interfaz gráfica (CustomTkinter) y navegación
├── database.py       # Esquema SQLite, seguridad de contraseñas y CRUD
├── requirements.txt
├── README.md
└── sivigila.db        # Se crea automáticamente al ejecutar por primera vez
```

## 6. Cómo agregar un nuevo evento con su propio formulario

En `database.py`, dentro de `EVENTOS_DEFAULT`, agrega un bloque como:

```python
{
    "codigo": "220",
    "nombre": "Leptospirosis",
    "campos": [
        {"key": "fiebre", "label": "Fiebre", "tipo": "si_no"},
        {"key": "mialgias", "label": "Mialgias", "tipo": "si_no"},
        {"key": "resultado", "label": "Resultado de laboratorio", "tipo": "lista",
         "opciones": ["Positivo", "Negativo", "Pendiente"]},
    ],
},
```

Tipos de campo soportados: `texto`, `si_no`, `lista` (con `opciones`).
La próxima vez que ejecutes la app (con una base de datos nueva) el
formulario de "Datos complementarios" para ese evento se generará solo.

## 7. Notas de seguridad

- Las contraseñas nunca se guardan en texto plano: se usa
  `hashlib.pbkdf2_hmac` con 200.000 iteraciones y una sal aleatoria por
  usuario.
- Toda la información queda en tu propio computador (`sivigila.db`); no se
  envía a ningún servidor externo. Si necesitas trabajo en red/multiusuario
  real, este proyecto es una buena base para migrar a PostgreSQL/MySQL más
  adelante.
