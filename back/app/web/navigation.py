NAV_ITEMS = [
    {
        "key": "dashboard",
        "label": "Panel principal",
        "icon": "🏠",
        "href": "/",
        "permission": None,
    },
    {
        "key": "caracterizacion",
        "label": "Caracterización",
        "icon": "🏥",
        "href": "/upgd",
        "permission": "gestionar_caracterizacion",
    },
    {
        "key": "individual",
        "label": "Notificación individual",
        "icon": "🧍",
        "href": "/notificaciones/nueva",
        "permission": "notificar_individual",
    },
    {
        "key": "listado",
        "label": "Fichas registradas",
        "icon": "📋",
        "href": "/notificaciones",
        "permission": "ver_reportes",
    },
    {
        "key": "usuarios",
        "label": "Usuarios",
        "icon": "👥",
        "href": "/usuarios",
        "permission": "gestionar_usuarios",
    },
]
