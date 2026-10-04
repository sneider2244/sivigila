import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import db
from ..auth import require_permiso
from ..catalogos import CAMPOS_BASICOS, CAMPOS_LAB, OBLIGATORIOS_GUARDAR
from ..validacion import comp_de_form, validar_ficha, validar_laboratorio
from ..web import redirigir, render, upgd_activa

router = APIRouter()

MENSAJES = {
    "guardada": "Ficha guardada correctamente.",
    "terminada": "La ficha se guardó como TERMINADA y quedó lista para envío.",
}


def _ficha_o_404(ficha_id: int):
    ficha = db.get_notificacion(ficha_id)
    if ficha is None:
        raise HTTPException(status_code=404)
    return ficha


def _comp_de_ficha(ficha) -> dict:
    if not ficha or not ficha["datos_complementarios"]:
        return {}
    try:
        return json.loads(ficha["datos_complementarios"])
    except (json.JSONDecodeError, TypeError):
        return {}


def _contexto_labs(request: Request, ficha, valores=None, errores=None) -> dict:
    usuario = request.state.usuario
    return {
        "ficha": ficha,
        "labs": db.list_laboratorios(ficha["id"]) if ficha else [],
        "puede_labs": ficha is not None and db.tiene_permiso(usuario, "gestionar_laboratorios"),
        "campos_lab": CAMPOS_LAB,
        "lab_valores": valores or {},
        "lab_errores": errores or {},
    }


def _render_ficha(request: Request, ficha=None, upgd=None, valores=None, comp_valores=None,
                  errores=None, mensaje=None):
    usuario = request.state.usuario
    eventos = db.list_eventos()
    if valores is None:
        valores = dict(ficha) if ficha else {}
    if comp_valores is None:
        comp_valores = _comp_de_ficha(ficha)
    codigo = valores.get("codigo_evento") or (eventos[0]["codigo"] if eventos else None)
    evento = db.get_evento(codigo) if codigo else None
    if upgd is None and ficha is not None:
        upgd = db.get_upgd(ficha["upgd_id"])
    ctx = {
        "activo": "fichas",
        "valores": valores,
        "comp_valores": comp_valores,
        "errores": errores or {},
        "eventos": eventos,
        "codigo_evento": codigo,
        "evento_nombre": evento["nombre"] if evento else None,
        "campos_basicos": CAMPOS_BASICOS,
        "campos_comp": json.loads(evento["campos_json"]) if evento else [],
        "obligatorios": OBLIGATORIOS_GUARDAR,
        "solo_lectura": ficha is not None and not db.tiene_permiso(usuario, "editar_notificaciones"),
        "upgd": upgd,
        "mensaje": mensaje,
    }
    ctx.update(_contexto_labs(request, ficha))
    return render(request, "ficha.html", ctx)


def _sin_upgd(request: Request):
    usuario = request.state.usuario
    puede = db.tiene_permiso(usuario, "gestionar_caracterizacion")
    return render(request, "error.html", {
        "activo": "fichas",
        "titulo": "Notificación individual",
        "mensaje": "Primero debes configurar y seleccionar una UPGD en «Caracterización».",
        "enlace": "/upgd" if puede else None,
        "enlace_texto": "Ir a Caracterización",
    })


@router.get("/fichas/nueva")
def nueva(request: Request, usuario=Depends(require_permiso("notificar_individual"))):
    upgd = upgd_activa(request)
    if upgd is None:
        return _sin_upgd(request)
    return _render_ficha(request, upgd=upgd)


@router.post("/fichas")
async def crear(request: Request, usuario=Depends(require_permiso("notificar_individual"))):
    upgd = upgd_activa(request)
    if upgd is None:
        return _sin_upgd(request)
    form = await request.form()
    hoy = date.today()
    evento = db.get_evento(str(form.get("codigo_evento", "")))
    datos, errores = validar_ficha(form, evento, completa=False, hoy=hoy)
    if errores:
        return _render_ficha(request, upgd=upgd, valores=dict(form),
                             comp_valores=comp_de_form(form), errores=errores)
    anio, semana, _ = hoy.isocalendar()
    datos.update(
        upgd_id=upgd["id"], fecha_notificacion=hoy.isoformat(), fecha_grabacion=hoy.isoformat(),
        anio=anio, semana=semana, estado_ficha="En proceso",
    )
    ficha_id = db.create_notificacion(datos, usuario["id"])
    db.log_action(usuario["id"], "GUARDA_FICHA", f"id={ficha_id}")
    return redirigir(f"/fichas/{ficha_id}?guardada=1")


@router.get("/fichas/campos")
def campos_complementarios(
    request: Request, codigo_evento: str = "",
    usuario=Depends(require_permiso("notificar_individual", "editar_notificaciones")),
):
    evento = db.get_evento(codigo_evento) if codigo_evento else None
    return render(request, "_complementarios.html", {
        "campos_comp": json.loads(evento["campos_json"]) if evento else [],
        "evento_nombre": evento["nombre"] if evento else None,
        "comp_valores": {},
        "errores": {},
        "solo_lectura": False,
    })


@router.get("/fichas/{ficha_id}")
def ver(request: Request, ficha_id: int, usuario=Depends(
        require_permiso("notificar_individual", "editar_notificaciones", "ver_reportes"))):
    ficha = _ficha_o_404(ficha_id)
    mensaje = next((m for clave, m in MENSAJES.items() if request.query_params.get(clave)), None)
    return _render_ficha(request, ficha=ficha, mensaje=mensaje)


async def _actualizar(request: Request, ficha_id: int, usuario, terminar: bool):
    ficha = _ficha_o_404(ficha_id)
    form = await request.form()
    evento = db.get_evento(str(form.get("codigo_evento", "")))
    datos, errores = validar_ficha(form, evento, completa=terminar, hoy=date.today())
    if errores:
        return _render_ficha(request, ficha=ficha, valores=dict(form),
                             comp_valores=comp_de_form(form), errores=errores)
    if terminar:
        datos["estado_ficha"] = "Terminada"
    db.update_notificacion(ficha_id, datos)
    db.log_action(usuario["id"], "TERMINA_FICHA" if terminar else "GUARDA_FICHA", f"id={ficha_id}")
    return redirigir(f"/fichas/{ficha_id}?{'terminada' if terminar else 'guardada'}=1")


@router.post("/fichas/{ficha_id}")
async def guardar(request: Request, ficha_id: int,
                  usuario=Depends(require_permiso("editar_notificaciones"))):
    return await _actualizar(request, ficha_id, usuario, terminar=False)


@router.post("/fichas/{ficha_id}/terminar")
async def terminar(request: Request, ficha_id: int,
                   usuario=Depends(require_permiso("editar_notificaciones"))):
    return await _actualizar(request, ficha_id, usuario, terminar=True)


@router.post("/fichas/{ficha_id}/eliminar")
def eliminar(request: Request, ficha_id: int,
             usuario=Depends(require_permiso("editar_notificaciones"))):
    _ficha_o_404(ficha_id)
    db.delete_notificacion(ficha_id)
    db.log_action(usuario["id"], "ELIMINA_FICHA", f"id={ficha_id}")
    return redirigir("/listado")


@router.post("/fichas/{ficha_id}/laboratorios")
async def agregar_laboratorio(request: Request, ficha_id: int,
                              usuario=Depends(require_permiso("gestionar_laboratorios"))):
    ficha = _ficha_o_404(ficha_id)
    form = await request.form()
    datos, errores = validar_laboratorio(form, date.today())
    if errores:
        return render(request, "_laboratorios.html",
                      _contexto_labs(request, ficha, valores=dict(form), errores=errores),
                      status_code=422)
    db.add_laboratorio(ficha_id, datos)
    db.log_action(usuario["id"], "AGREGA_LABORATORIO", f"ficha={ficha_id}")
    return render(request, "_laboratorios.html", _contexto_labs(request, ficha))


@router.post("/fichas/{ficha_id}/laboratorios/{lab_id}/eliminar")
def eliminar_laboratorio(request: Request, ficha_id: int, lab_id: int,
                         usuario=Depends(require_permiso("gestionar_laboratorios"))):
    ficha = _ficha_o_404(ficha_id)
    lab = db.get_laboratorio(lab_id)
    if lab is None or lab["notificacion_id"] != ficha_id:
        raise HTTPException(status_code=404)
    db.delete_laboratorio(lab_id)
    db.log_action(usuario["id"], "ELIMINA_LABORATORIO", f"ficha={ficha_id} lab={lab_id}")
    return render(request, "_laboratorios.html", _contexto_labs(request, ficha))
