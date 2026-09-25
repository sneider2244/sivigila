from app.schemas.catalogo import (
    DepartamentoOut,
    EtniaOut,
    EventoOut,
    MunicipioOut,
    OcupacionOut,
)
from app.schemas.docente import (
    AsignacionCreate,
    AsignacionOut,
    EscenarioCreate,
    EscenarioOut,
    EvaluacionDetalle,
    EvaluacionResult,
    EvaluarRequest,
)
from app.schemas.ficha_basica import (
    FichaDatosBasicosCreate,
    FichaDatosBasicosOut,
    FichaDatosBasicosUpdate,
)
from app.schemas.ficha_complementaria import (
    FichaDatosComplementariosCreate,
    FichaDatosComplementariosOut,
    FichaDatosComplementariosUpdate,
)
from app.schemas.trazabilidad import EstadoTransitionRequest, TrazabilidadOut
from app.schemas.upgd import (
    UPGDCaracterizacionCreate,
    UPGDCaracterizacionOut,
    UPGDCaracterizacionUpdate,
)
from app.schemas.usuario import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    RolUpdateRequest,
    TokenResponse,
    UsuarioOut,
)

__all__ = [
    "AsignacionCreate",
    "AsignacionOut",
    "DepartamentoOut",
    "EtniaOut",
    "EstadoTransitionRequest",
    "EventoOut",
    "EscenarioCreate",
    "EscenarioOut",
    "EvaluacionDetalle",
    "EvaluacionResult",
    "EvaluarRequest",
    "FichaDatosBasicosCreate",
    "FichaDatosBasicosOut",
    "FichaDatosBasicosUpdate",
    "FichaDatosComplementariosCreate",
    "FichaDatosComplementariosOut",
    "FichaDatosComplementariosUpdate",
    "LoginRequest",
    "LoginResponse",
    "MunicipioOut",
    "OcupacionOut",
    "RefreshRequest",
    "RegisterRequest",
    "RolUpdateRequest",
    "TokenResponse",
    "TrazabilidadOut",
    "UPGDCaracterizacionCreate",
    "UPGDCaracterizacionOut",
    "UPGDCaracterizacionUpdate",
    "UsuarioOut",
]
