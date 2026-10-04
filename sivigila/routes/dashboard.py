from datetime import date

from fastapi import APIRouter, Depends, Request

from .. import db
from ..auth import require_permiso
from ..web import render, upgd_activa

router = APIRouter()


@router.get("/")
def dashboard(request: Request, usuario=Depends(require_permiso("ver_reportes"))):
    stats = db.count_notificaciones_por_evento()
    maximo = max((s["total"] for s in stats), default=0)
    return render(request, "dashboard.html", {
        "activo": "dashboard",
        "stats": stats,
        "maximo": maximo or 1,
        "hay_casos": maximo > 0,
        "upgd": upgd_activa(request),
        "hoy": date.today(),
    })
