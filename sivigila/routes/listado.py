from math import ceil

from fastapi import APIRouter, Depends, Request

from .. import db
from ..auth import require_permiso
from ..web import render

router = APIRouter()
permiso = require_permiso("ver_reportes")
POR_PAGINA = 50


def _contexto_resultados(request: Request) -> dict:
    q = request.query_params.get("q", "").strip()
    evento = request.query_params.get("evento") or None
    try:
        pagina = int(request.query_params.get("pagina", "1"))
    except ValueError:
        pagina = 1
    total = db.count_notificaciones(q, evento)
    paginas = max(1, ceil(total / POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    filas = db.list_notificaciones(q, evento, limite=POR_PAGINA, offset=(pagina - 1) * POR_PAGINA)
    return {"filas": filas, "total": total, "pagina": pagina, "paginas": paginas,
            "q": q, "evento": evento or ""}


@router.get("/listado")
def listado(request: Request, usuario=Depends(permiso)):
    ctx = _contexto_resultados(request)
    ctx.update(activo="listado", eventos=db.list_eventos())
    return render(request, "listado.html", ctx)


@router.get("/listado/resultados")
def resultados(request: Request, usuario=Depends(permiso)):
    return render(request, "_listado_resultados.html", _contexto_resultados(request))
