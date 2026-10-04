from fastapi import APIRouter, Depends, Request

from .. import auth, db
from ..web import primera_pantalla, redirigir, render

router = APIRouter()


@router.get("/login")
def login_form(request: Request):
    user_id = request.session.get("user_id")
    usuario = db.get_user_by_id(user_id) if user_id else None
    if usuario is not None and usuario["activo"]:
        return redirigir(primera_pantalla(usuario))
    return render(request, "login.html")


@router.post("/login")
async def login(request: Request):
    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))

    if auth.esta_bloqueado(username):
        db.log_action(None, "LOGIN_BLOQUEADO", username)
        return render(request, "login.html", {
            "error": "Demasiados intentos fallidos. Espera 10 minutos e intenta de nuevo.",
            "username": username,
        }, status_code=429)

    usuario = db.get_user_by_username(username) if username else None
    if usuario is None or not db.verify_password(password, usuario["password_hash"], usuario["salt"]):
        auth.registrar_fallo(username)
        db.log_action(None, "LOGIN_FALLIDO", username)
        return render(request, "login.html", {
            "error": "Usuario o contraseña incorrectos.",
            "username": username,
        }, status_code=401)

    auth.limpiar_intentos(username)
    auth.iniciar_sesion(request, usuario)
    db.log_action(usuario["id"], "LOGIN")
    if usuario["debe_cambiar_password"]:
        return redirigir("/cambiar-password")
    return redirigir(primera_pantalla(usuario))


@router.post("/logout")
def logout(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        db.log_action(user_id, "LOGOUT")
    auth.cerrar_sesion(request)
    return redirigir("/login")


@router.get("/sin-acceso")
def sin_acceso(request: Request, usuario=Depends(auth.usuario_actual)):
    return render(request, "error.html", {
        "titulo": "Sin secciones habilitadas",
        "mensaje": "Tu usuario no tiene ninguna sección habilitada. "
                   "Pide a un administrador que te asigne permisos.",
    })


@router.get("/cambiar-password")
def cambiar_password_form(request: Request, usuario=Depends(auth.usuario_actual)):
    return render(request, "cambiar_password.html",
                  {"obligatorio": bool(usuario["debe_cambiar_password"]), "errores": {}})


@router.post("/cambiar-password")
async def cambiar_password(request: Request, usuario=Depends(auth.usuario_actual)):
    form = await request.form()
    actual = str(form.get("actual", ""))
    nueva = str(form.get("nueva", ""))
    confirmacion = str(form.get("confirmacion", ""))

    errores = {}
    if not db.verify_password(actual, usuario["password_hash"], usuario["salt"]):
        errores["actual"] = "La contraseña actual no es correcta."
    if len(nueva) < auth.MIN_PASSWORD:
        errores["nueva"] = f"Debe tener al menos {auth.MIN_PASSWORD} caracteres."
    elif nueva == actual:
        errores["nueva"] = "Debe ser distinta de la actual."
    if nueva != confirmacion:
        errores["confirmacion"] = "No coincide con la nueva contraseña."
    if errores:
        return render(request, "cambiar_password.html",
                      {"obligatorio": bool(usuario["debe_cambiar_password"]), "errores": errores})

    db.reset_password(usuario["id"], nueva, debe_cambiar=False)
    db.log_action(usuario["id"], "CAMBIA_PASSWORD")
    return redirigir(primera_pantalla(usuario))
