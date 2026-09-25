import re

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.usuario import RolEnum

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    """Credenciales enviadas por el cliente en el login."""

    username: str
    password: str


class RegisterRequest(BaseModel):
    """Datos de registro de un estudiante (auto-login)."""

    email: str
    nombre_completo: str
    numero_identificacion: str
    rol: RolEnum = RolEnum.UPGD

    @field_validator("email")
    @classmethod
    def _validar_email(cls, value: str) -> str:
        email = value.strip()
        if not email:
            raise ValueError("El email no puede estar vacío")
        if not _EMAIL_REGEX.match(email):
            raise ValueError("El email no tiene un formato válido")
        return email

    @field_validator("nombre_completo")
    @classmethod
    def _validar_nombre_completo(cls, value: str) -> str:
        nombre = value.strip()
        if not nombre:
            raise ValueError("El nombre completo no puede estar vacío")
        return nombre

    @field_validator("numero_identificacion")
    @classmethod
    def _validar_numero_identificacion(cls, value: str) -> str:
        numero = value.strip()
        if not numero:
            raise ValueError("El número de identificación no puede estar vacío")
        return numero


class RolUpdateRequest(BaseModel):
    """Cambio de rol solicitado por un usuario autenticado."""

    rol: RolEnum


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
    numero_identificacion: str | None
    rol: RolEnum
    cod_upgd: str | None
    activo: bool


class LoginResponse(BaseModel):
    """Respuesta de /auth/login consumida por el frontend."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
