# ARQUITECTURA BACKEND: Python (FastAPI) + PostgreSQL + RBAC

## Stack Tecnológico

- **Framework:** FastAPI (Python 3.12+)
- **ORM:** SQLAlchemy 2.0 (AsyncIO con `asyncpg`)
- **Migraciones:** Alembic
- **Validación y Datos:** Pydantic v2
- **Seguridad:** OAuth2 con JWT (Passlib / Argon2 para passwords, PyJWT)
- **Base de Datos:** PostgreSQL 16 (Uso intensivo de tipos JSONB para fichas complementarias dinámicas)
- **Cache/Sesiones:** Redis (token blacklist / sesiones)

---

## Estructura del Proyecto Python

```text
back/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py
│   │   │   │   ├── caracterizacion.py
│   │   │   │   ├── fichas_basicas.py
│   │   │   │   ├── fichas_complementarias.py
│   │   │   │   ├── catalogos.py
│   │   │   │   └── docente.py
│   │   │   └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── rbac.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── seed_data.py   # Datos iniciales: DIVIPOLA, Eventos SIVIGILA
│   ├── models/
│   │   ├── usuario.py
│   │   ├── upgd.py
│   │   ├── ficha_basica.py
│   │   ├── ficha_complementaria.py
│   │   └── catalogos.py
│   ├── schemas/
│   │   ├── usuario.py
│   │   ├── ficha_basica.py
│   │   └── complemento_ofidico.py
│   └── main.py
├── alembic/
└── pyproject.toml
```

## Modelo de Base de Datos (Relacional + JSONB)

### 1. Tabla de Usuarios y Roles

```python
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class RolEnum(str, enum.Enum):
    UPGD = "UPGD"
    UI = "UI"
    MUNICIPAL = "MUNICIPAL"
    DEPARTAMENTAL = "DEPARTAMENTAL"
    NACIONAL = "NACIONAL"
    DOCENTE = "DOCENTE"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    rol = Column(SQLEnum(RolEnum), nullable=False, default=RolEnum.UPGD)
    cod_upgd = Column(String(20), ForeignKey("upgd_caracterizacion.cod_prestador"), nullable=True)
    activo = Column(Boolean, default=True)

    upgd = relationship("UPGDCaracterizacion", back_populates="usuarios")
```

### 2. Tabla de Datos Básicos (`sivigila.html`)

```python
from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, JSON
from app.core.database import Base

class FichaDatosBasicos(Base):
    __tablename__ = "fichas_datos_basicos"

    id = Column(Integer, primary_key=True, index=True)
    cod_upgd = Column(String(20), nullable=False, index=True)
    subindice = Column(String(5), default="01")
    cod_evento = Column(String(10), nullable=False, index=True)
    f_grabacion = Column(Date, nullable=False)
    f_notificacion = Column(Date, nullable=False)
    anio = Column(Integer, nullable=False)
    semana_epidemiologica = Column(Integer, nullable=False)

    # Identificación Paciente
    tipo_id = Column(String(5), nullable=False)
    num_id = Column(String(20), nullable=False, index=True)
    primer_nombre = Column(String(50), nullable=False)
    segundo_nombre = Column(String(50), nullable=True)
    primer_apellido = Column(String(50), nullable=False)
    segundo_apellido = Column(String(50), nullable=True)
    telefono = Column(String(20), nullable=True)
    f_nacimiento = Column(Date, nullable=False)
    edad = Column(Integer, nullable=False)
    und_med_edad = Column(Integer, nullable=False) # 1: Años, 2: Meses, 3: Días
    sexo = Column(String(1), nullable=False) # M / F
    identidad_genero = Column(Integer, default=1)
    orientacion_sexual = Column(Integer, default=1)

    # Ubicación y Demografía
    pais_ocurrencia = Column(String(50), default="COLOMBIA")
    dpto_ocurrencia = Column(String(5), nullable=False)
    muni_ocurrencia = Column(String(5), nullable=False)
    area_ocurrencia = Column(Integer, nullable=False) # 1: Cabecera, 2: Centro Pob, 3: Rural

    # Grupos Poblacionales (Almacenados como Flags o JSONB)
    grupos_poblacionales = Column(JSON, nullable=False, default={})
    # Ej: {"gestante": True, "semanas_gestacion": 24, "desplazado": False, ...}

    # Datos Clínicos
    clasificacion_caso = Column(Integer, nullable=False) # 1: Sospechoso, 2: Probable, 3: Confirmado, 4: Descartado
    hospitalizado = Column(Boolean, default=False)
    condicion_final = Column(Integer, default=1) # 1: Vivo, 2: Muerto

    # Control de Auditoría del Simulador
    creado_por_usuario_id = Column(Integer, ForeignKey("usuarios.id"))
```

### 3. Datos Complementarios (Almacenamiento Híbrido JSONB)

```python
class FichaDatosComplementarios(Base):
    __tablename__ = "fichas_datos_complementarios"

    id = Column(Integer, primary_key=True, index=True)
    ficha_basica_id = Column(Integer, ForeignKey("fichas_datos_basicos.id"), nullable=False, unique=True)
    cod_evento = Column(String(10), nullable=False)

    # JSONB dinámico para acomodar cualquier ficha complementaria (ej. Accidente Ofídico, Dengue, Chagas)
    contenido = Column(JSON, nullable=False)
    # Estructura del JSON de acuerdo a datos-complementarios.html:
    # {
    #   "datos_accidente": { "fecha": "2026-02-21", "direccion": "CRA 23 SUR 9-87", "agente_agresor": 17 },
    #   "manifestaciones_locales": { "edema": true, "dolor": true, "eritema": false, ... },
    #   "manifestaciones_sistemicas": { "nauseas": false, "bradicardia": false, ... },
    #   "complicaciones": { "celulitis": false, "necrosis": false, "hipoxia": true },
    #   "atencion_hospitalaria": { "empleo_suero": 2, "dosis": null }
    # }
```

## Control de Accesos mediante Middleware Decorador

```python
from fastapi import HTTPException, status, Depends
from app.core.security import get_current_user
from app.models.usuario import Usuario, RolEnum

class RequiereRol:
    def __init__(self, roles_permitidos: list[RolEnum]):
        self.roles_permitidos = roles_permitidos

    def __call__(self, usuario_actual: Usuario = Depends(get_current_user)):
        if usuario_actual.rol not in self.roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No posee los permisos necesarios para realizar esta operación en SIVIGILA."
            )
        return usuario_actual
```
