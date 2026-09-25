from app.schemas.catalogo import (
    DepartamentoOut,
    EtniaOut,
    EventoOut,
    MunicipioOut,
    OcupacionOut,
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
from app.schemas.upgd import (
    UPGDCaracterizacionCreate,
    UPGDCaracterizacionOut,
    UPGDCaracterizacionUpdate,
)
from app.schemas.usuario import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenResponse,
    UsuarioOut,
)

__all__ = [
    "DepartamentoOut",
    "EtniaOut",
    "EventoOut",
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
    "TokenResponse",
    "UPGDCaracterizacionCreate",
    "UPGDCaracterizacionOut",
    "UPGDCaracterizacionUpdate",
    "UsuarioOut",
]
