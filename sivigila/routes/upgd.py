from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import db
from ..auth import require_permiso
from ..catalogos import CAMPOS_UPGD, OBLIGATORIOS_UPGD, RECURSOS_UPGD
from ..validacion import validar_upgd
from ..web import redirigir, render, upgd_activa

router = APIRouter()
permiso = require_permiso("gestionar_caracterizacion")


def _upgd_o_404(upgd_id: int):
    upgd = db.get_upgd(upgd_id)
    if upgd is None:
        raise HTTPException(status_code=404)
    return upgd


def _form(request, upgd=None, valores=None, errores=None):
    return render(request, "upgd_form.html", {
        "activo": "upgd",
        "upgd": upgd,
        "valores": valores if valores is not None else (dict(upgd) if upgd else dict.fromkeys(RECURSOS_UPGD, 1)),
        "errores": errores or {},
        "campos": CAMPOS_UPGD,
        "obligatorios": OBLIGATORIOS_UPGD,
        "recursos": RECURSOS_UPGD,
    })


@router.get("/upgd")
def lista(request: Request, usuario=Depends(permiso)):
    return render(request, "upgd_lista.html", {
        "activo": "upgd",
        "upgds": db.list_upgd(),
        "upgd_activa": upgd_activa(request),
        "mensaje": "Caracterización guardada correctamente." if request.query_params.get("guardada") else None,
    })


@router.get("/upgd/nueva")
def nueva(request: Request, usuario=Depends(permiso)):
    return _form(request)


@router.post("/upgd/nueva")
async def crear(request: Request, usuario=Depends(permiso)):
    form = await request.form()
    hoy = date.today()
    datos, errores = validar_upgd(form, hoy)
    if errores:
        return _form(request, valores=dict(form), errores=errores)
    datos.update(activa_sivigila=1, fecha_caracteriza=hoy.isoformat(), fecha_inicio_uso=hoy.isoformat())
    nuevo_id = db.upsert_upgd(datos)
    request.session["upgd_id"] = nuevo_id
    db.log_action(usuario["id"], "CREA_UPGD", datos["razon_social"])
    return redirigir("/upgd?guardada=1")


@router.get("/upgd/{upgd_id}")
def editar_form(request: Request, upgd_id: int, usuario=Depends(permiso)):
    return _form(request, upgd=_upgd_o_404(upgd_id))


@router.post("/upgd/{upgd_id}")
async def editar(request: Request, upgd_id: int, usuario=Depends(permiso)):
    upgd = _upgd_o_404(upgd_id)
    form = await request.form()
    hoy = date.today()
    datos, errores = validar_upgd(form, hoy)
    if errores:
        return _form(request, upgd=upgd, valores=dict(form), errores=errores)
    datos["fecha_caracteriza"] = hoy.isoformat()
    db.upsert_upgd(datos, upgd_id)
    db.log_action(usuario["id"], "EDITA_UPGD", f"id={upgd_id}")
    return redirigir("/upgd?guardada=1")


@router.post("/upgd/{upgd_id}/activar")
def activar(request: Request, upgd_id: int, usuario=Depends(permiso)):
    _upgd_o_404(upgd_id)
    request.session["upgd_id"] = upgd_id
    return redirigir("/upgd")
