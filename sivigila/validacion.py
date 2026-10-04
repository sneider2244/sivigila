"""Validación de formularios: fechas, listas cerradas y campos dinámicos por evento."""

import re
from datetime import date

from .catalogos import CAMPOS_UPGD, OBLIGATORIOS_UPGD, RECURSOS_UPGD, SI_NO

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
