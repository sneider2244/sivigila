from pydantic import BaseModel, ConfigDict

from app.models.usuario import RolEnum


class LoginRequest(BaseModel):
    """Credenciales enviadas por el cliente en el login."""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh token enviado para rotar la sesión."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Par de tokens JWT emitidos tras login o refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    """Representación pública de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nombre_completo: str
    rol: RolEnum
    cod_upgd: str | None
    activo: bool


class LoginResponse(BaseModel):
    """Respuesta de /auth/login consumida por el frontend."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
