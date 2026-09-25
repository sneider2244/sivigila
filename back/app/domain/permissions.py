from app.domain.enums import Rol

ROLES_JERARQUIA: dict[Rol, int] = {
    Rol.SUPER_ADMIN: 3,
    Rol.ADMIN: 2,
    Rol.DIGITADOR: 1,
    Rol.CONSULTA: 0,
}

PERMISOS_DEFAULT: dict[Rol, dict[str, bool]] = {
    Rol.SUPER_ADMIN: {
        "gestionar_usuarios": True,
        "gestionar_caracterizacion": True,
        "notificar_individual": True,
        "editar_notificaciones": True,
        "gestionar_laboratorios": True,
        "ver_reportes": True,
    },
    Rol.ADMIN: {
        "gestionar_usuarios": True,
        "gestionar_caracterizacion": True,
        "notificar_individual": True,
        "editar_notificaciones": True,
        "gestionar_laboratorios": True,
        "ver_reportes": True,
    },
    Rol.DIGITADOR: {
        "gestionar_usuarios": False,
        "gestionar_caracterizacion": True,
        "notificar_individual": True,
        "editar_notificaciones": True,
        "gestionar_laboratorios": True,
        "ver_reportes": True,
    },
    Rol.CONSULTA: {
        "gestionar_usuarios": False,
        "gestionar_caracterizacion": False,
        "notificar_individual": False,
        "editar_notificaciones": False,
        "gestionar_laboratorios": False,
        "ver_reportes": True,
    },
}

PERMISOS_LABELS: dict[str, str] = {
    "gestionar_usuarios": "Gestionar usuarios (crear, editar, permisos)",
    "gestionar_caracterizacion": "Gestionar caracterización de UPGD",
    "notificar_individual": "Crear notificaciones individuales",
    "editar_notificaciones": "Editar / terminar / eliminar fichas",
    "gestionar_laboratorios": "Gestionar resultados de laboratorio",
    "ver_reportes": "Ver panel de indicadores y reportes",
}


def rango(rol: Rol) -> int:
    return ROLES_JERARQUIA.get(rol, 0)


def permisos_por_defecto(rol: Rol) -> dict[str, bool]:
    return dict(PERMISOS_DEFAULT.get(rol, PERMISOS_DEFAULT[Rol.CONSULTA]))


def roles_asignables(actor_rol: Rol) -> list[Rol]:
    if actor_rol == Rol.SUPER_ADMIN:
        return list(ROLES_JERARQUIA.keys())
    rango_actor = rango(actor_rol)
    return [rol for rol, r in ROLES_JERARQUIA.items() if r < rango_actor]


def puede_gestionar(
    actor_rol: Rol,
    actor_permisos: dict[str, bool],
    objetivo_rol: Rol,
) -> bool:
    if not actor_permisos.get("gestionar_usuarios", False):
        return False
    if actor_rol == Rol.SUPER_ADMIN:
        return True
    return rango(actor_rol) > rango(objetivo_rol)
