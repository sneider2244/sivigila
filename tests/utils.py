from datetime import date, timedelta

CLAVE = "clave-segura-1"


def crear_usuario(db, username, rol="digitador", permisos=None):
    db.create_user(username, CLAVE, f"Usuario {username}", rol=rol, permisos=permisos)
    return db.get_user_by_username(username)


def crear_upgd(db, razon_social="Hospital de Prueba"):
    return db.upsert_upgd(
        {"cod_prestador": "110010000001", "razon_social": razon_social, "activa_sivigila": 1}
    )


def crear_ficha(db, upgd_id, usuario_id, **extra):
    datos = {
        "upgd_id": upgd_id,
        "codigo_evento": "210",
        "numero_id": "1000",
        "primer_nombre": "Ana",
        "primer_apellido": "Pérez",
        "estado_ficha": "En proceso",
        "fecha_notificacion": date.today().isoformat(),
    }
    datos.update(extra)
    return db.create_notificacion(datos, usuario_id)


def ficha_completa(**extra):
    """Formulario de ficha de Dengue (210) con todo lo que exige 'Terminar'."""
    hoy = date.today()
    datos = {
        "codigo_evento": "210",
        "tipo_id": "CC",
        "numero_id": "1032456789",
        "primer_nombre": "Ana",
        "primer_apellido": "Pérez",
        "sexo": "F",
        "fecha_nacimiento": (hoy - timedelta(days=365 * 30 + 10)).isoformat(),
        "fecha_inicio_sintomas": (hoy - timedelta(days=5)).isoformat(),
        "fecha_consulta": (hoy - timedelta(days=3)).isoformat(),
        "clasificacion_caso": "Probable",
        "condicion": "Vivo",
        "hospitalizado": "No",
        "comp__fiebre": "Sí",
        "comp__signos_alarma": "No",
        "comp__dolor_abdominal": "No",
        "comp__sangrado": "No",
        "comp__clasificacion_dengue": "Dengue sin signos de alarma",
        "comp__resultado_igm": "Pendiente",
    }
    datos.update(extra)
    return datos
