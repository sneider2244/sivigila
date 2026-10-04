"""Punto de entrada web: uvicorn sivigila.main:app --reload"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import auth, db
from .routes import dashboard, fichas, login, upgd
from .web import es_htmx, redirigir, render

logger = logging.getLogger("sivigila")

CLAVE_DESARROLLO = "solo-para-desarrollo-local-cambiame"
TITULOS_ERROR = {403: "Acceso restringido", 404: "No encontrado", 405: "Acción no permitida"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


def create_app() -> FastAPI:
    secret = os.environ.get("SIVIGILA_SECRET_KEY")
    if not secret:
        logger.warning(
            "SIVIGILA_SECRET_KEY no está definida: se usa una clave de desarrollo. "
            "No uses esta configuración fuera de tu máquina."
        )
        secret = CLAVE_DESARROLLO

    app = FastAPI(
        title="SIVIGILA Moderno",
        lifespan=lifespan,
        dependencies=[Depends(auth.verificar_csrf)],
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret,
        session_cookie="sivigila_sesion",
        max_age=8 * 3600,
        same_site="lax",
        https_only=os.environ.get("SIVIGILA_COOKIE_SECURE") == "1",
    )
    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

    for modulo in (login, dashboard, upgd, fichas):
        app.include_router(modulo.router)

    _registrar_errores(app)
    return app


def _registrar_errores(app: FastAPI):
    @app.exception_handler(auth.NoAutenticado)
    async def _no_autenticado(request: Request, exc: auth.NoAutenticado):
        if es_htmx(request):
            return Response(status_code=401, headers={"HX-Redirect": "/login"})
        return redirigir("/login")

    @app.exception_handler(auth.DebeCambiarPassword)
    async def _debe_cambiar(request: Request, exc: auth.DebeCambiarPassword):
        if es_htmx(request):
            return Response(status_code=401, headers={"HX-Redirect": "/cambiar-password"})
        return redirigir("/cambiar-password")

    @app.exception_handler(auth.SinPermiso)
    async def _sin_permiso(request: Request, exc: auth.SinPermiso):
        return render(request, "error.html",
                      {"titulo": "Acceso restringido", "mensaje": exc.mensaje}, status_code=403)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        titulo = TITULOS_ERROR.get(exc.status_code, f"Error {exc.status_code}")
        if exc.status_code == 403:
            mensaje = exc.detail
        elif exc.status_code == 404:
            mensaje = "La página o el registro que buscas no existe."
        else:
            mensaje = "No se pudo completar la acción."
        return render(request, "error.html", {"titulo": titulo, "mensaje": mensaje},
                      status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _error_no_controlado(request: Request, exc: Exception):
        # Solo método, ruta y tipo de excepción: nunca el mensaje, que podría traer datos del paciente.
        logger.error("Error no controlado en %s %s: %s",
                     request.method, request.url.path, type(exc).__name__)
        return render(request, "error.html", {
            "titulo": "Algo salió mal",
            "mensaje": "Ocurrió un error inesperado. Intenta de nuevo; si persiste, avisa al administrador.",
        }, status_code=500)


app = create_app()
