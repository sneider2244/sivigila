import re

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import auth, db
from ..auth import require_permiso
from ..web import redirigir, render

router = APIRouter()
permiso = require_permiso("gestionar_usuarios")
_FORMATO_USERNAME = re.compile(r"^[A-Za-z0-9._-]{3,30}$")


def _objetivo(actor, user_id: int):
    objetivo = db.get_user_by_id(user_id)
    if objetivo is None:
        raise HTTPException(status_code=404)
    if not db.puede_gestionar(actor, objetivo):
        raise auth.SinPermiso("No puedes gestionar a este usuario: su rol es igual o superior al tuyo.")
    return objetivo


def _permisos_de_form(form, actor, actuales: dict) -> dict:
    """
    Permisos pedidos en el formulario, limitados a los que tiene el actor: no puede dar
    un permiso que no tiene, ni quitarlo (ese conserva el valor actual del usuario).
    El super_admin no tiene límite.
    """
    permisos = {}
    for clave in db.PERMISOS_LABELS:
        pedido = form.get(f"perm_{clave}") == "1"
        if actor["rol"] == "super_admin" or db.tiene_permiso(actor, clave):
            permisos[clave] = pedido
        else:
            permisos[clave] = bool(actuales.get(clave, False))
    return permisos


def _render_form(request, actor, objetivo=None, valores=None, permisos=None, errores=None):
    asignables = db.roles_asignables(actor["rol"])
    if objetivo is not None and objetivo["rol"] not in asignables:
        asignables = asignables + [objetivo["rol"]]
    if valores is None:
        valores = ({"nombre_completo": objetivo["nombre_completo"], "rol": objetivo["rol"]}
                   if objetivo else {"rol": asignables[0]})
    if permisos is None:
        permisos = db.get_permisos(objetivo) if objetivo else db.permisos_por_defecto(valores["rol"])
    return render(request, "usuario_form.html", {
        "activo": "usuarios",
        "objetivo": objetivo,
        "valores": valores,
        "permisos_usuario": permisos,
        "permisos_labels": db.PERMISOS_LABELS,
        "roles": asignables,
        "errores": errores or {},
        "min_password": auth.MIN_PASSWORD,
    })


@router.get("/usuarios")
def lista(request: Request, usuario=Depends(permiso)):
    filas = [
        {"fila": u, "puede": db.puede_gestionar(usuario, u), "es_yo": u["id"] == usuario["id"]}
        for u in db.list_users()
    ]
    return render(request, "usuarios_lista.html", {
        "activo": "usuarios",
        "usuarios": filas,
        "puede_crear": bool(db.roles_asignables(usuario["rol"])),
        "mensaje": "Cambios guardados." if request.query_params.get("ok") else None,
    })


@router.get("/usuarios/permisos")
def permisos_por_rol(request: Request, rol: str = "", usuario=Depends(permiso)):
    return render(request, "_permisos.html", {
        "permisos_usuario": db.permisos_por_defecto(rol),
        "permisos_labels": db.PERMISOS_LABELS,
    })


@router.get("/usuarios/nuevo")
def nuevo_form(request: Request, usuario=Depends(permiso)):
    if not db.roles_asignables(usuario["rol"]):
        raise auth.SinPermiso("Tu rol no puede crear usuarios.")
    return _render_form(request, usuario)


@router.post("/usuarios/nuevo")
async def crear(request: Request, usuario=Depends(permiso)):
    if not db.roles_asignables(usuario["rol"]):
        raise auth.SinPermiso("Tu rol no puede crear usuarios.")
    form = await request.form()
    username = str(form.get("username", "")).strip()
    nombre = str(form.get("nombre_completo", "")).strip()
    password = str(form.get("password", ""))
    rol = str(form.get("rol", ""))
    permisos = _permisos_de_form(form, usuario, {})

    errores = {}
    if not username:
        errores["username"] = "Este campo es obligatorio."
    elif not _FORMATO_USERNAME.match(username):
        errores["username"] = "Usa de 3 a 30 letras, números, punto, guion o guion bajo."
    elif db.username_exists(username):
        errores["username"] = "Ese código de usuario ya existe."
    if not nombre:
        errores["nombre_completo"] = "Este campo es obligatorio."
    if len(password) < auth.MIN_PASSWORD:
        errores["password"] = f"Debe tener al menos {auth.MIN_PASSWORD} caracteres."
    if rol not in db.roles_asignables(usuario["rol"]):
        errores["rol"] = "No puedes asignar ese rol."
    if errores:
        valores = {"username": username, "nombre_completo": nombre,
                   "rol": rol if rol in db.ROLES_DISPONIBLES else db.roles_asignables(usuario["rol"])[0]}
        return _render_form(request, usuario, valores=valores, permisos=permisos, errores=errores)

    db.create_user(username, password, nombre, rol=rol, permisos=permisos,
                   creado_por=usuario["id"], debe_cambiar_password=True)
    db.log_action(usuario["id"], "CREA_USUARIO", username)
    return redirigir("/usuarios?ok=1")


@router.get("/usuarios/{user_id}/editar")
def editar_form(request: Request, user_id: int, usuario=Depends(permiso)):
    return _render_form(request, usuario, objetivo=_objetivo(usuario, user_id))


@router.post("/usuarios/{user_id}/editar")
async def editar(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    form = await request.form()
    nombre = str(form.get("nombre_completo", "")).strip()
    rol = str(form.get("rol", ""))
    permisos = _permisos_de_form(form, usuario, db.get_permisos(objetivo))

    errores = {}
    if not nombre:
        errores["nombre_completo"] = "Este campo es obligatorio."
    if rol not in db.roles_asignables(usuario["rol"]) and rol != objetivo["rol"]:
        errores["rol"] = "No puedes asignar ese rol."
    if errores:
        valores = {"nombre_completo": nombre, "rol": objetivo["rol"]}
        return _render_form(request, usuario, objetivo=objetivo, valores=valores,
                            permisos=permisos, errores=errores)

    db.update_user(user_id, nombre_completo=nombre, rol=rol, permisos=permisos)
    db.log_action(usuario["id"], "EDITA_USUARIO", f"id={user_id}")
    return redirigir("/usuarios?ok=1")


@router.post("/usuarios/{user_id}/activo")
async def cambiar_activo(request: Request, user_id: int, usuario=Depends(permiso)):
    _objetivo(usuario, user_id)
    if user_id == usuario["id"]:
        raise auth.SinPermiso("No puedes desactivarte a ti mismo.")
    form = await request.form()
    activo = form.get("activo") == "1"
    db.set_user_active(user_id, activo)
    db.log_action(usuario["id"], "ACTIVA_USUARIO" if activo else "DESACTIVA_USUARIO", f"id={user_id}")
    return redirigir("/usuarios?ok=1")


@router.get("/usuarios/{user_id}/password")
def password_form(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    return render(request, "usuario_password.html",
                  {"activo": "usuarios", "objetivo": objetivo, "error": None,
                   "min_password": auth.MIN_PASSWORD})


@router.post("/usuarios/{user_id}/password")
async def restablecer_password(request: Request, user_id: int, usuario=Depends(permiso)):
    objetivo = _objetivo(usuario, user_id)
    form = await request.form()
    password = str(form.get("password", ""))
    if len(password) < auth.MIN_PASSWORD:
        return render(request, "usuario_password.html", {
            "activo": "usuarios", "objetivo": objetivo, "min_password": auth.MIN_PASSWORD,
            "error": f"Debe tener al menos {auth.MIN_PASSWORD} caracteres.",
        })
    db.reset_password(user_id, password, debe_cambiar=True)
    db.log_action(usuario["id"], "RESET_PASSWORD", f"id={user_id}")
    return redirigir("/usuarios?ok=1")
