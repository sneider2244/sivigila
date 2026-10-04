"""Sesión, CSRF, usuario actual, permisos por ruta y bloqueo de login."""

import secrets
import time

from fastapi import Depends, HTTPException, Request

from . import db

MIN_PASSWORD = 6
MAX_INTENTOS = 5
VENTANA_SEG = 600   # se cuentan los fallos de los últimos 10 minutos
BLOQUEO_SEG = 600   # y se bloquea el username 10 minutos

_fallos: dict[str, list[float]] = {}
_bloqueados: dict[str, float] = {}

METODOS_CON_CSRF = {"POST", "PUT", "PATCH", "DELETE"}
RUTAS_SIN_CAMBIO_OBLIGATORIO = {"/cambiar-password", "/logout"}


class NoAutenticado(Exception):
    """No hay sesión válida: se redirige a /login."""


class DebeCambiarPassword(Exception):
    """El usuario debe cambiar su contraseña antes de seguir."""


class SinPermiso(Exception):
    def __init__(self, mensaje="No tienes permiso para acceder a esta sección."):
        super().__init__(mensaje)
        self.mensaje = mensaje


# --- Bloqueo por intentos fallidos (en memoria del proceso) -----------------

def _ahora() -> float:
    return time.monotonic()


def _clave(username: str) -> str:
    return username.strip().lower()


def reiniciar_intentos():
    _fallos.clear()
    _bloqueados.clear()


def esta_bloqueado(username: str) -> bool:
    hasta = _bloqueados.get(_clave(username))
    if hasta is None:
        return False
    if _ahora() < hasta:
        return True
    _bloqueados.pop(_clave(username), None)
    return False


def registrar_fallo(username: str):
    clave, ahora = _clave(username), _ahora()
    recientes = [t for t in _fallos.get(clave, []) if ahora - t < VENTANA_SEG]
    recientes.append(ahora)
    if len(recientes) >= MAX_INTENTOS:
        _bloqueados[clave] = ahora + BLOQUEO_SEG
        recientes = []
    _fallos[clave] = recientes


def limpiar_intentos(username: str):
    _fallos.pop(_clave(username), None)


# --- CSRF y sesión -----------------------------------------------------------

def obtener_csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def verificar_csrf(request: Request):
    """Dependencia global: todo POST/PUT/PATCH/DELETE debe traer el token de la sesión."""
    if request.method not in METODOS_CON_CSRF:
        return
    enviado = request.headers.get("X-CSRF-Token")
    if not enviado:
        formulario = await request.form()
        enviado = formulario.get("csrf_token")
    esperado = request.session.get("csrf_token")
    if not esperado or not enviado or not secrets.compare_digest(str(enviado), esperado):
        raise HTTPException(
            status_code=403,
            detail="La sesión expiró o el formulario no es válido. Recarga la página e intenta de nuevo.",
        )


def iniciar_sesion(request: Request, usuario):
    request.session.clear()  # evita reutilizar una sesión previa (fijación de sesión)
    request.session["user_id"] = usuario["id"]
    request.session["csrf_token"] = secrets.token_urlsafe(32)


def cerrar_sesion(request: Request):
    request.session.clear()


# --- Usuario actual y permisos -----------------------------------------------

def usuario_actual(request: Request):
    """Relee el usuario en cada petición: si lo desactivan, pierde la sesión de inmediato."""
    user_id = request.session.get("user_id")
    usuario = db.get_user_by_id(user_id) if user_id else None
    if usuario is None or not usuario["activo"]:
        request.session.clear()
        raise NoAutenticado()
    request.state.usuario = usuario
    if usuario["debe_cambiar_password"] and request.url.path not in RUTAS_SIN_CAMBIO_OBLIGATORIO:
        raise DebeCambiarPassword()
    return usuario


def require_permiso(*claves: str):
    """Dependencia que exige al menos uno de los permisos indicados."""

    def dependencia(request: Request, usuario=Depends(usuario_actual)):
        if not any(db.tiene_permiso(usuario, c) for c in claves):
            db.log_action(
                usuario["id"], "ACCESO_DENEGADO",
                f"{request.method} {request.url.path} requiere {'|'.join(claves)}",
            )
            raise SinPermiso()
        return usuario

    return dependencia
