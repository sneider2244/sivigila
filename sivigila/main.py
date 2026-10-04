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
from .routes import dashboard, fichas, listado, login, upgd, usuarios
from .web import es_htmx, redirigir, render

logger = logging.getLogger("sivigila")

CLAVE_DESARROLLO = "solo-para-desarrollo-local-cambiame"
TITULOS_ERROR = {403: "Acceso restringido", 404: "No encontrado", 405: "Acción no permitida"}


class FiltroDatosSensibles(logging.Filter):
    """
    Quita de los logs de uvicorn lo que puede traer datos de pacientes (Ley 1581):
    la query string de cada petición (la búsqueda del listado va por GET) y el mensaje
    y traceback de las excepciones (se deja solo el tipo).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access" and isinstance(record.args, tuple) and len(record.args) >= 3:
            args = list(record.args)
            args[2] = str(args[2]).split("?", 1)[0]
            record.args = tuple(args)
        if record.exc_info:
            tipo = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            record.msg = f"{record.getMessage()}: {tipo}"
            record.args = ()
            record.exc_info = None
            record.exc_text = None
        return True


def _instalar_filtro_de_logs():
    for nombre in ("uvicorn.access", "uvicorn.error"):
        registro = logging.getLogger(nombre)
        if not any(isinstance(f, FiltroDatosSensibles) for f in registro.filters):
            registro.addFilter(FiltroDatosSensibles())


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

    for modulo in (login, dashboard, upgd, fichas, listado, usuarios):
        app.include_router(modulo.router)

    _registrar_errores(app)
    _instalar_filtro_de_logs()
    return app


def _pagina_error(request: Request, titulo: str, mensaje: str, status_code: int):
    respuesta = render(request, "error.html", {"titulo": titulo, "mensaje": mensaje},
                       status_code=status_code)
    if es_htmx(request):
        # htmx descarta las respuestas 4xx/5xx: se pide recargar la página completa para que
        # la persona vea el error (o un formulario con token CSRF nuevo).
        respuesta.headers["HX-Refresh"] = "true"
    return respuesta


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
        return _pagina_error(request, "Acceso restringido", exc.mensaje, 403)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        titulo = TITULOS_ERROR.get(exc.status_code, f"Error {exc.status_code}")
        if exc.status_code == 403:
            mensaje = exc.detail
        elif exc.status_code == 404:
            mensaje = "La página o el registro que buscas no existe."
        else:
            mensaje = "No se pudo completar la acción."
        return _pagina_error(request, titulo, mensaje, exc.status_code)

    @app.exception_handler(Exception)
    async def _error_no_controlado(request: Request, exc: Exception):
        # Solo método, ruta y tipo de excepción: nunca el mensaje, que podría traer datos del paciente.
        logger.error("Error no controlado en %s %s: %s",
                     request.method, request.url.path, type(exc).__name__)
        return _pagina_error(
            request, "Algo salió mal",
            "Ocurrió un error inesperado. Intenta de nuevo; si persiste, avisa al administrador.", 500,
        )


app = create_app()
