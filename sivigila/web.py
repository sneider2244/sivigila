"""Helpers compartidos por las rutas: render con contexto común, redirects, UPGD activa."""

from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from . import auth, db
from .catalogos import ROL_LABELS

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Orden en que se elige la pantalla de inicio según los permisos del usuario.
PANTALLAS_INICIO = [
    ("ver_reportes", "/"),
    ("notificar_individual", "/fichas/nueva"),
    ("gestionar_caracterizacion", "/upgd"),
    ("gestionar_usuarios", "/usuarios"),
]


def render(request: Request, plantilla: str, contexto: dict | None = None, status_code: int = 200):
    usuario = getattr(request.state, "usuario", None)
    ctx = {
        "usuario": usuario,
        "permisos": db.get_permisos(usuario) if usuario else {},
        "csrf_token": auth.obtener_csrf(request),
        "rol_labels": ROL_LABELS,
    }
    ctx.update(contexto or {})
    return templates.TemplateResponse(request, plantilla, ctx, status_code=status_code)


def redirigir(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def es_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def primera_pantalla(usuario) -> str:
    for permiso, url in PANTALLAS_INICIO:
        if db.tiene_permiso(usuario, permiso):
            return url
    return "/sin-acceso"


def upgd_activa(request: Request):
    """UPGD de la sesión; si no hay (o ya no existe), toma la primera registrada."""
    upgd_id = request.session.get("upgd_id")
    upgd = db.get_upgd(upgd_id) if upgd_id else None
    if upgd is None:
        todas = db.list_upgd()
        upgd = todas[0] if todas else None
        if upgd is not None:
            request.session["upgd_id"] = upgd["id"]
        else:
            request.session.pop("upgd_id", None)
    return upgd
