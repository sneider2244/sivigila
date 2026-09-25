"""Endpoints de autenticación: login, refresh, logout y usuario actual."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import blacklist_token, is_blacklisted
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    token_remaining_ttl,
    verify_password,
)
from app.models.usuario import RolEnum, Usuario
from app.schemas.usuario import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    RolUpdateRequest,
    TokenResponse,
    UsuarioOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_CREDENCIALES_INVALIDAS = "Credenciales inválidas"
_COD_UPGD_DEMO = "150010123456"
_DOCENTE_NO_DISPONIBLE = "El rol DOCENTE no está disponible"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    """Autentica un usuario y emite access + refresh tokens."""
    user = await db.scalar(select(Usuario).where(Usuario.username == payload.username))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_CREDENCIALES_INVALIDAS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return LoginResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
        token_type="bearer",
        usuario=UsuarioOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Rota la sesión: revoca el refresh token actual y emite un nuevo par."""
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    username = data.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    if await is_blacklisted(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    user = await db.scalar(select(Usuario).where(Usuario.username == username))
    if user is None or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    await blacklist_token(payload.refresh_token, token_remaining_ttl(payload.refresh_token))

    return TokenResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    current_user: Usuario = Depends(get_current_user),
    access_token: str = Depends(oauth2_scheme),
) -> dict[str, str]:
    """Cierra la sesión revocando el refresh token y el access token actual."""
    await blacklist_token(payload.refresh_token, token_remaining_ttl(payload.refresh_token))
    await blacklist_token(access_token, token_remaining_ttl(access_token))
    return {"detail": "Sesión cerrada"}


@router.get("/me", response_model=UsuarioOut)
async def me(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Retorna el usuario autenticado actual."""
    return current_user


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """Registra un estudiante y emite tokens (auto-login)."""
    if payload.rol == RolEnum.DOCENTE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_DOCENTE_NO_DISPONIBLE,
        )

    existing = await db.scalar(select(Usuario).where(Usuario.username == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    user = Usuario(
        username=payload.email,
        hashed_password=get_password_hash(payload.numero_identificacion),
        nombre_completo=payload.nombre_completo,
        numero_identificacion=payload.numero_identificacion,
        rol=payload.rol,
        cod_upgd=_COD_UPGD_DEMO,
        activo=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return LoginResponse(
        access_token=create_access_token(user.username),
        refresh_token=create_refresh_token(user.username),
        token_type="bearer",
        usuario=UsuarioOut.model_validate(user),
    )


@router.patch("/me", response_model=UsuarioOut)
async def update_me(
    payload: RolUpdateRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Actualiza el rol del usuario autenticado (nunca a DOCENTE)."""
    if payload.rol == RolEnum.DOCENTE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_DOCENTE_NO_DISPONIBLE,
        )

    current_user.rol = payload.rol
    await db.commit()
    await db.refresh(current_user)
    return current_user
