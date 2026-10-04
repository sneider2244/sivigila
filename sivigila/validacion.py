"""Validación de formularios: fechas, listas cerradas y campos dinámicos por evento."""

import json
import re
from datetime import date

from .catalogos import (
    CAMPOS_BASICOS, CAMPOS_LAB, CAMPOS_UPGD, OBLIGATORIOS_GUARDAR, OBLIGATORIOS_TERMINAR,
    OBLIGATORIOS_UPGD, PREFIJO_COMP, RECURSOS_UPGD, SI_NO,
)

_FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parsear_fecha(valor: str) -> date:
    """Convierte 'AAAA-MM-DD' en date. Lanza ValueError si el formato no es ese."""
    if not _FORMATO_FECHA.match(valor):
        raise ValueError(f"Formato de fecha no válido: {valor!r}")
    return date.fromisoformat(valor)


def validar_campos(campos, form, obligatorios, hoy: date):
    """
    Valida los campos definidos en `campos` contra lo enviado en `form`.
    Devuelve (datos, errores): datos con None en los vacíos; errores {clave: mensaje}.
    """
    datos, errores = {}, {}
    for c in campos:
        clave = c["key"]
        valor = str(form.get(clave) or "").strip()
        if not valor:
            datos[clave] = None
            if clave in obligatorios:
                errores[clave] = "Este campo es obligatorio."
            continue
        if c["tipo"] == "fecha":
            try:
                fecha = parsear_fecha(valor)
            except ValueError:
                errores[clave] = "Fecha no válida. Usa el formato AAAA-MM-DD."
                continue
            if fecha > hoy:
                errores[clave] = "La fecha no puede ser posterior a hoy."
                continue
        elif c["tipo"] in ("lista", "si_no"):
            opciones = c.get("opciones") or SI_NO
            if valor not in opciones:
                errores[clave] = "Selecciona una opción de la lista."
                continue
        datos[clave] = valor
    return datos, errores


def validar_upgd(form, hoy: date):
    datos, errores = validar_campos(CAMPOS_UPGD, form, OBLIGATORIOS_UPGD, hoy)
    for clave in RECURSOS_UPGD:
        datos[clave] = 1 if form.get(clave) else 0
    return datos, errores


# Orden lógico de las fechas clínicas de la ficha (solo se compara entre las que vengan llenas).
ORDEN_FECHAS = [
    ("fecha_nacimiento", "fecha de nacimiento"),
    ("fecha_inicio_sintomas", "fecha de inicio de síntomas"),
    ("fecha_consulta", "fecha de consulta"),
]


def calcular_edad(nacimiento: date, referencia: date):
    """Edad en años; si es menor de un año, en meses; si es menor de un mes, en días."""
    anios = referencia.year - nacimiento.year - (
        (referencia.month, referencia.day) < (nacimiento.month, nacimiento.day)
    )
    if anios >= 1:
        return anios, "Años"
    meses = (referencia.year - nacimiento.year) * 12 + referencia.month - nacimiento.month
    if referencia.day < nacimiento.day:
        meses -= 1
    if meses >= 1:
        return meses, "Meses"
    return (referencia - nacimiento).days, "Días"


def comp_de_form(form) -> dict:
    return {k[len(PREFIJO_COMP):]: v for k, v in form.items() if k.startswith(PREFIJO_COMP)}


def _validar_orden_fechas(datos, errores):
    anterior = None
    for clave, nombre in ORDEN_FECHAS:
        valor = datos.get(clave)
        if not valor or clave in errores:
            continue
        if anterior and valor < anterior[1]:  # fechas ISO: el orden de texto es el cronológico
            errores[clave] = f"No puede ser anterior a la {anterior[0]}."
        else:
            anterior = (nombre, valor)


def validar_ficha(form, evento, completa: bool, hoy: date):
    """
    Valida la ficha individual. `completa=True` es para "Terminar": exige todos los
    obligatorios de básicos y todos los complementarios del evento.
    """
    obligatorios = OBLIGATORIOS_GUARDAR | (OBLIGATORIOS_TERMINAR if completa else set())
    datos, errores = validar_campos(CAMPOS_BASICOS, form, obligatorios, hoy)

    if evento is None:
        errores["codigo_evento"] = "Selecciona el evento de interés en salud pública."
        campos_comp = []
    else:
        datos["codigo_evento"] = evento["codigo"]
        campos_comp = json.loads(evento["campos_json"])

    if completa:
        if datos.get("hospitalizado") == "Sí" and not datos.get("fecha_hospitalizacion") \
                and "fecha_hospitalizacion" not in errores:
            errores["fecha_hospitalizacion"] = "Obligatoria si el paciente fue hospitalizado."
        if datos.get("condicion") == "Fallecido" and not datos.get("fecha_defuncion") \
                and "fecha_defuncion" not in errores:
            errores["fecha_defuncion"] = "Obligatoria si el paciente falleció."

    _validar_orden_fechas(datos, errores)

    claves_validas = {c["key"] for c in campos_comp}
    enviados = comp_de_form(form)
    desconocidas = sorted(set(enviados) - claves_validas)
    if desconocidas:
        errores["general"] = (
            "El formulario trae campos que no corresponden al evento: " + ", ".join(desconocidas) + "."
        )
    comp, errores_comp = validar_campos(
        campos_comp, enviados, claves_validas if completa else set(), hoy
    )
    errores.update({PREFIJO_COMP + k: v for k, v in errores_comp.items()})
    datos["datos_complementarios"] = json.dumps(
        {k: v for k, v in comp.items() if v is not None}, ensure_ascii=False
    )

    if datos.get("fecha_nacimiento") and "fecha_nacimiento" not in errores:
        datos["edad"], datos["unidad_edad"] = calcular_edad(parsear_fecha(datos["fecha_nacimiento"]), hoy)
    else:
        datos["edad"], datos["unidad_edad"] = None, None
    return datos, errores


def validar_laboratorio(form, hoy: date):
    return validar_campos(CAMPOS_LAB, form, {"prueba"}, hoy)
