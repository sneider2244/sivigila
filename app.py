"""
SIVIGILA Moderno
================
Reinterpretación moderna e interactiva del flujo de notificación del
Sistema de Vigilancia en Salud Pública (SIVIGILA), con:
  - Login real (usuarios en SQLite, contraseñas con hash PBKDF2)
  - Interfaz gráfica moderna con CustomTkinter (tema oscuro/claro)
  - Caracterización de la UPGD
  - Notificación Individual: datos básicos + datos complementarios
    DINÁMICOS según el evento seleccionado (a diferencia del software
    original, aquí el formulario se genera solo)
  - Módulo de Laboratorios ligado a cada ficha
  - Listado/búsqueda de fichas y pequeño panel de indicadores

Ejecutar con:  python app.py
Requisitos:    pip install -r requirements.txt
"""

import json
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date

import customtkinter as ctk

import database as db

# ---------------------------------------------------------------------------
# Configuración visual global
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_PRIMARY = "#C8102E"      # rojo institucional (similar al de SIVIGILA)
COLOR_PRIMARY_HOVER = "#9E0C23"
COLOR_ACCENT = "#1F6FEB"
COLOR_BG = "#0F1115"
COLOR_CARD = "#181B21"
FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_LABEL = ("Segoe UI", 13)
FONT_SECTION = ("Segoe UI", 16, "bold")

SI_NO_OPCIONES = ["Sí", "No"]

ROL_LABELS = {
    "super_admin": "Super administrador",
    "admin": "Administrador",
    "digitador": "Digitador",
    "consulta": "Solo consulta",
}
ROL_COLORS = {
    "super_admin": "#8E24AA",
    "admin": "#1F6FEB",
    "digitador": "#2E7D32",
    "consulta": "#616161",
}


def hoy():
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Ventana principal / controlador de "páginas"
# ---------------------------------------------------------------------------

class SivigilaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SIVIGILA Moderno · Sistema de Vigilancia en Salud Pública")
        self.geometry("1180x740")
        self.minsize(1000, 650)
        self.configure(fg_color=COLOR_BG)

        self.current_user = None      # sqlite3.Row del usuario autenticado
        self.current_upgd_id = None   # UPGD activa de la sesión
        self.selected_notificacion_id = None

        db.init_db()

        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        self.show_frame(LoginFrame)

    def show_frame(self, frame_class, **kwargs):
        for widget in self.container.winfo_children():
            widget.destroy()
        frame = frame_class(self.container, self, **kwargs)
        frame.pack(fill="both", expand=True)
        return frame

    def logout(self):
        db.log_action(self.current_user["id"], "LOGOUT")
        self.current_user = None
        self.current_upgd_id = None
        self.show_frame(LoginFrame)


# ---------------------------------------------------------------------------
# Pantalla de LOGIN
# ---------------------------------------------------------------------------

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, app: SivigilaApp):
        super().__init__(parent, fg_color=COLOR_BG)
        self.app = app

        wrapper = ctk.CTkFrame(self, fg_color=COLOR_BG)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        card = ctk.CTkFrame(wrapper, fg_color=COLOR_CARD, corner_radius=18, width=420)
        card.pack()

        header = ctk.CTkFrame(card, fg_color=COLOR_PRIMARY, corner_radius=18,
                               height=110)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🩺  SIVIGILA", font=FONT_TITLE,
                     text_color="white").pack(pady=(22, 0))
        ctk.CTkLabel(header, text="Sistema de Vigilancia en Salud Pública · Moderno",
                     font=FONT_SUBTITLE, text_color="white").pack()

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", padx=36, pady=28)

        ctk.CTkLabel(body, text="Iniciar sesión", font=FONT_SECTION).pack(
            anchor="w", pady=(0, 14))

        ctk.CTkLabel(body, text="Código de usuario", font=FONT_LABEL).pack(anchor="w")
        self.user_entry = ctk.CTkEntry(body, placeholder_text="Ej: SIVIGILA", height=40)
        self.user_entry.pack(fill="x", pady=(4, 14))
        self.user_entry.insert(0, "SIVIGILA")

        ctk.CTkLabel(body, text="Contraseña", font=FONT_LABEL).pack(anchor="w")
        self.pass_entry = ctk.CTkEntry(body, placeholder_text="••••••••", show="•", height=40)
        self.pass_entry.pack(fill="x", pady=(4, 6))
        self.pass_entry.bind("<Return>", lambda e: self.do_login())

        self.error_label = ctk.CTkLabel(body, text="", text_color="#FF6B6B", font=FONT_LABEL)
        self.error_label.pack(anchor="w", pady=(0, 6))

        ctk.CTkButton(body, text="Continuar", height=42, fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER, font=("Segoe UI", 14, "bold"),
                      command=self.do_login).pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(body, text="Usuario demo: SIVIGILA   ·   Clave: sivigila2026",
                     font=("Segoe UI", 11), text_color="#888").pack(pady=(14, 0))

    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        user = db.get_user_by_username(username)
        if user and db.verify_password(password, user["password_hash"], user["salt"]):
            self.app.current_user = user
            db.log_action(user["id"], "LOGIN")
            self.app.show_frame(DashboardFrame)
        else:
            self.error_label.configure(text="Usuario o contraseña incorrectos.")


# ---------------------------------------------------------------------------
# Layout con barra lateral reutilizable
# ---------------------------------------------------------------------------

class BaseScreen(ctk.CTkFrame):
    """Frame con barra lateral de navegación + área de contenido."""

    NAV_ITEMS = [
        ("🏠  Panel principal", "dashboard", None),
        ("🏥  Caracterización", "caracterizacion", "gestionar_caracterizacion"),
        ("🧍  Notificación individual", "individual", "notificar_individual"),
        ("📋  Fichas registradas", "listado", "ver_reportes"),
        ("👥  Usuarios", "usuarios", "gestionar_usuarios"),
    ]

    def __init__(self, parent, app: SivigilaApp, active_key):
        super().__init__(parent, fg_color=COLOR_BG)
        self.app = app
        self.permisos = db.get_permisos(app.current_user)

        sidebar = ctk.CTkFrame(self, width=230, fg_color=COLOR_CARD, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="🩺 SIVIGILA", font=("Segoe UI", 20, "bold"),
                     text_color=COLOR_PRIMARY).pack(pady=(26, 4))
        ctk.CTkLabel(sidebar, text="Moderno", font=("Segoe UI", 12), text_color="#888").pack(pady=(0, 20))

        for label, key, permiso_req in self.NAV_ITEMS:
            if permiso_req and not self.permisos.get(permiso_req, False):
                continue  # oculta ítems del menú para los que el usuario no tiene permiso
            is_active = key == active_key
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w", height=42,
                fg_color=COLOR_PRIMARY if is_active else "transparent",
                hover_color=COLOR_PRIMARY_HOVER if is_active else "#242832",
                text_color="white",
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(fill="x", padx=14, pady=3)

        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        user = app.current_user
        user_box = ctk.CTkFrame(sidebar, fg_color="#20242C", corner_radius=10)
        user_box.pack(fill="x", padx=14, pady=14)
        ctk.CTkLabel(user_box, text=f"👤 {user['nombre_completo']}", font=("Segoe UI", 12, "bold"),
                     wraplength=190, justify="left").pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(user_box, text=f"Rol: {ROL_LABELS.get(user['rol'], user['rol'])}",
                     font=("Segoe UI", 11), text_color="#999").pack(anchor="w", padx=10, pady=(0, 8))
        ctk.CTkButton(sidebar, text="Cerrar sesión", fg_color="transparent",
                      hover_color="#3A1C22", text_color="#FF8080", height=34,
                      command=app.logout).pack(fill="x", padx=14, pady=(0, 16))

        self.content = ctk.CTkScrollableFrame(self, fg_color=COLOR_BG)
        self.content.pack(side="left", fill="both", expand=True, padx=26, pady=22)

    def navigate(self, key):
        mapping = {
            "dashboard": DashboardFrame,
            "caracterizacion": CaracterizacionFrame,
            "individual": IndividualFrame,
            "listado": ListadoFrame,
            "usuarios": UsuariosFrame,
        }
        self.app.show_frame(mapping[key])

    def sin_permiso(self, mensaje="No tienes permiso para acceder a esta sección."):
        ctk.CTkLabel(self.content, text="🔒  Acceso restringido", font=FONT_TITLE).pack(anchor="w")
        ctk.CTkLabel(self.content, text=mensaje, font=FONT_SUBTITLE,
                     text_color="#9AA0AA").pack(anchor="w", pady=(6, 0))

    def section_title(self, text, subtitle=None):
        ctk.CTkLabel(self.content, text=text, font=FONT_TITLE).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(self.content, text=subtitle, font=FONT_SUBTITLE,
                         text_color="#9AA0AA").pack(anchor="w", pady=(2, 18))
        else:
            ctk.CTkLabel(self.content, text="").pack(pady=(0, 6))


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

class DashboardFrame(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app, active_key="dashboard")
        self.section_title(
            f"Bienvenido(a), {app.current_user['nombre_completo'].split()[0]}",
            f"Semana epidemiológica actual · {datetime.now():%d/%m/%Y}"
        )

        # --- Tarjetas de acceso rápido (como el menú original, pero clicables) ---
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 24))

        items = [
            ("🏥", "Caracterización", "Configura la UPGD que notifica", CaracterizacionFrame,
             "gestionar_caracterizacion"),
            ("🧍", "Individual", "Diligencia fichas de vigilancia", IndividualFrame,
             "notificar_individual"),
            ("📋", "Fichas registradas", "Consulta, edita y filtra notificaciones", ListadoFrame,
             "ver_reportes"),
            ("👥", "Usuarios", "Crea usuarios y administra permisos", UsuariosFrame,
             "gestionar_usuarios"),
        ]
        items = [it for it in items if self.permisos.get(it[4], False)]
        for i, (icon, title, desc, target, _perm) in enumerate(items):
            card = ctk.CTkFrame(cards_frame, fg_color=COLOR_CARD, corner_radius=16,
                                 width=250, height=140)
            card.grid(row=0, column=i, padx=(0, 16), sticky="nsew")
            cards_frame.grid_columnconfigure(i, weight=1)
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 30)).pack(pady=(16, 0))
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 15, "bold")).pack()
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 11), text_color="#9AA0AA",
                         wraplength=210, justify="center").pack(pady=(2, 10))
            card.bind("<Button-1>", lambda e, t=target: self.navigate_to(t))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, t=target: self.navigate_to(t))

        # --- Indicadores ---
        ctk.CTkLabel(self.content, text="Casos notificados por evento", font=FONT_SECTION).pack(
            anchor="w", pady=(10, 10))
        stats = db.count_notificaciones_por_evento()
        stats_frame = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, corner_radius=16)
        stats_frame.pack(fill="x", pady=(0, 10))

        if not stats or all(s["total"] == 0 for s in stats):
            ctk.CTkLabel(stats_frame, text="Aún no hay fichas registradas.",
                         text_color="#9AA0AA").pack(padx=20, pady=20)
        else:
            max_total = max((s["total"] for s in stats), default=1) or 1
            for s in stats:
                row = ctk.CTkFrame(stats_frame, fg_color="transparent")
                row.pack(fill="x", padx=20, pady=6)
                ctk.CTkLabel(row, text=s["nombre"], font=FONT_LABEL, width=220,
                             anchor="w").pack(side="left")
                bar_bg = ctk.CTkFrame(row, fg_color="#242832", height=16, corner_radius=8)
                bar_bg.pack(side="left", fill="x", expand=True, padx=10)
                pct = max(0.04, s["total"] / max_total)
                bar = ctk.CTkFrame(bar_bg, fg_color=COLOR_PRIMARY, height=16, corner_radius=8)
                bar.place(relwidth=pct, relheight=1)
                ctk.CTkLabel(row, text=str(s["total"]), font=("Segoe UI", 13, "bold"),
                             width=30).pack(side="left")

        if not app.current_upgd_id and db.list_upgd():
            app.current_upgd_id = db.list_upgd()[0]["id"]
        if not db.list_upgd():
            warn = ctk.CTkFrame(self.content, fg_color="#3A2A12", corner_radius=12)
            warn.pack(fill="x", pady=(16, 0))
            ctk.CTkLabel(warn, text="⚠️  Aún no has configurado ninguna UPGD. Ve a "
                                     "'Caracterización' antes de notificar casos.",
                         text_color="#FFD27A", font=FONT_LABEL).pack(padx=16, pady=12, anchor="w")

    def navigate_to(self, target):
        self.app.show_frame(target)


# ---------------------------------------------------------------------------
# CARACTERIZACIÓN (UPGD)
# ---------------------------------------------------------------------------

class CaracterizacionFrame(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app, active_key="caracterizacion")
        if not self.permisos.get("gestionar_caracterizacion"):
            self.section_title("Caracterización de la UPGD")
            self.sin_permiso("Tu rol no tiene permiso para gestionar la caracterización. "
                              "Solicita acceso a un administrador.")
            return
        self.section_title("Caracterización de la UPGD",
                            "Configura la unidad notificadora: identificación, contacto y "
                            "recursos disponibles para la vigilancia epidemiológica.")

        form = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, corner_radius=16)
        form.pack(fill="x", pady=(0, 20))
        pad = dict(padx=20, pady=8)

        self.vars = {}

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=16)
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1)

        campos = [
            ("cod_prestador", "Código prestador", "entry"),
            ("subred", "Subred / seccional", "entry"),
            ("nit", "NIT", "entry"),
            ("razon_social", "Razón social", "entry"),
            ("direccion", "Dirección", "entry"),
            ("telefono", "Teléfono", "entry"),
            ("representante_legal", "Representante legal", "entry"),
            ("correo_electronico", "Correo electrónico", "entry"),
            ("responsable_notif", "Responsable de la notificación", "entry"),
            ("naturaleza_juridica", "Naturaleza jurídica", "combo",
             ["Privada sin ánimo de lucro", "Privada con ánimo de lucro", "Mixta", "Pública"]),
            ("nivel_complejidad", "Nivel de complejidad", "combo", ["I Nivel", "II Nivel", "III Nivel"]),
            ("tipo_unidad", "Tipo de unidad", "combo", ["UPGD", "UI", "Laboratorio"]),
            ("localidad_zona", "Localidad o zona (si aplica)", "entry"),
            ("estado", "Estado de la unidad", "combo", ["Activa", "Inactiva"]),
        ]

        self._build_field_grid(grid, campos, cols=2)

        ctk.CTkLabel(form, text="Recursos adicionales para la vigilancia epidemiológica",
                     font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(4, 8))

        recursos = ["unidad_analisis", "cove", "talento_humano", "computador",
                    "fax_modem", "correo_recurso", "internet", "telefax", "radio_telefono"]
        recursos_labels = {
            "unidad_analisis": "Unidad de análisis", "cove": "COVE",
            "talento_humano": "Talento humano disponible", "computador": "Computador",
            "fax_modem": "Fax/Módem", "correo_recurso": "Correo electrónico",
            "internet": "Internet", "telefax": "Telefax", "radio_telefono": "Radioteléfono",
        }
        recursos_frame = ctk.CTkFrame(form, fg_color="transparent")
        recursos_frame.pack(fill="x", padx=20, pady=(0, 16))
        self.checks = {}
        for i, key in enumerate(recursos):
            var = tk.BooleanVar(value=True)
            self.checks[key] = var
            cb = ctk.CTkCheckBox(recursos_frame, text=recursos_labels[key], variable=var,
                                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER)
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=6)

        ctk.CTkButton(form, text="💾  Guardar caracterización", height=44,
                      fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                      font=("Segoe UI", 14, "bold"),
                      command=self.guardar).pack(padx=20, pady=(4, 20), anchor="w")

        ctk.CTkLabel(self.content, text="UPGD configuradas", font=FONT_SECTION).pack(
            anchor="w", pady=(4, 10))
        self._render_upgd_list()

    def _build_field_grid(self, grid, campos, cols=2):
        row = col = 0
        for spec in campos:
            key, label = spec[0], spec[1]
            tipo = spec[2]
            wrap = ctk.CTkFrame(grid, fg_color="transparent")
            wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=6)
            ctk.CTkLabel(wrap, text=label, font=FONT_LABEL).pack(anchor="w")
            if tipo == "entry":
                w = ctk.CTkEntry(wrap, height=36)
            elif tipo == "combo":
                opciones = spec[3]
                w = ctk.CTkComboBox(wrap, values=opciones, height=36)
                w.set(opciones[0])
            w.pack(fill="x")
            self.vars[key] = w
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _render_upgd_list(self):
        rows = db.list_upgd()
        if not rows:
            ctk.CTkLabel(self.content, text="No hay UPGD registradas todavía.",
                         text_color="#9AA0AA").pack(anchor="w")
            return
        for r in rows:
            item = ctk.CTkFrame(self.content, fg_color=COLOR_CARD, corner_radius=12)
            item.pack(fill="x", pady=5)
            ctk.CTkLabel(item, text=f"🏥 {r['razon_social']}", font=("Segoe UI", 13, "bold")).pack(
                side="left", padx=16, pady=10)
            ctk.CTkLabel(item, text=f"NIT {r['nit'] or '-'} · {r['nivel_complejidad'] or '-'}",
                         text_color="#9AA0AA").pack(side="left", padx=10)
            active = r["id"] == self.app.current_upgd_id
            ctk.CTkButton(
                item, text="Usar en sesión" if not active else "✓ En uso",
                width=120, height=30,
                fg_color=COLOR_ACCENT if not active else "#2E7D32",
                command=lambda rid=r["id"]: self.set_active(rid),
            ).pack(side="right", padx=16, pady=8)

    def set_active(self, upgd_id):
        self.app.current_upgd_id = upgd_id
        self.app.show_frame(CaracterizacionFrame)

    def guardar(self):
        data = {}
        for key, widget in self.vars.items():
            data[key] = widget.get()
        for key, var in self.checks.items():
            data[key] = 1 if var.get() else 0
        if not data.get("razon_social") or not data.get("cod_prestador"):
            messagebox.showwarning("Datos incompletos",
                                    "Código prestador y Razón social son obligatorios.")
            return
        data["activa_sivigila"] = 1
        data["fecha_caracteriza"] = hoy()
        data["fecha_inicio_uso"] = hoy()
        new_id = db.upsert_upgd(data)
        self.app.current_upgd_id = new_id
        db.log_action(self.app.current_user["id"], "CREA_UPGD", data.get("razon_social"))
        messagebox.showinfo("Guardado", "Caracterización de la UPGD guardada correctamente.")
        self.app.show_frame(CaracterizacionFrame)


# ---------------------------------------------------------------------------
# NOTIFICACIÓN INDIVIDUAL (datos básicos + complementarios dinámicos + labs)
# ---------------------------------------------------------------------------

class IndividualFrame(BaseScreen):
    def __init__(self, parent, app, notificacion_id=None):
        super().__init__(parent, app, active_key="individual")

        if not self.permisos.get("notificar_individual") and not notificacion_id:
            self.section_title("Notificación individual")
            self.sin_permiso("Tu rol no tiene permiso para crear notificaciones. "
                              "Solicita acceso a un administrador.")
            return
        if notificacion_id and not self.permisos.get("editar_notificaciones") \
                and not self.permisos.get("notificar_individual"):
            self.section_title("Notificación individual")
            self.sin_permiso("Tu rol no tiene permiso para ver o editar esta ficha.")
            return

        if not app.current_upgd_id:
            self.section_title("Notificación individual")
            ctk.CTkLabel(self.content,
                         text="⚠️ Primero debes configurar y seleccionar una UPGD en "
                              "'Caracterización'.", text_color="#FFD27A").pack(anchor="w")
            return

        self.editing_id = notificacion_id
        record = db.get_notificacion(notificacion_id) if notificacion_id else None

        self.section_title(
            "Notificación individual" + (f" · Editando ficha #{notificacion_id}" if record else ""),
            "Página 1: datos básicos del paciente. Página 2: datos complementarios "
            "específicos del evento (se generan automáticamente)."
        )

        self.tabs = ctk.CTkTabview(self.content, fg_color=COLOR_CARD,
                                    segmented_button_selected_color=COLOR_PRIMARY,
                                    segmented_button_selected_hover_color=COLOR_PRIMARY_HOVER)
        self.tabs.pack(fill="both", expand=True)
        tab_basicos = self.tabs.add("1 · Datos básicos")
        tab_compl = self.tabs.add("2 · Datos complementarios")
        tab_labs = self.tabs.add("3 · Laboratorios")

        self.evento_field = None
        self.compl_widgets = {}
        self.compl_container = None

        self._build_datos_basicos(tab_basicos, record)
        self.compl_container = ctk.CTkFrame(tab_compl, fg_color="transparent")
        self.compl_container.pack(fill="both", expand=True, padx=10, pady=10)
        self._render_datos_complementarios(record)

        self._build_labs_tab(tab_labs, record)

        actions = ctk.CTkFrame(self.content, fg_color="transparent")
        actions.pack(fill="x", pady=16)
        ctk.CTkButton(actions, text="💾  Guardar ficha", height=44, fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER, font=("Segoe UI", 14, "bold"),
                      command=self.guardar).pack(side="left")
        ctk.CTkButton(actions, text="✅  Terminar", height=44, fg_color="#2E7D32",
                      hover_color="#1E5E23", font=("Segoe UI", 14, "bold"),
                      command=self.terminar).pack(side="left", padx=10)
        if record:
            ctk.CTkButton(actions, text="🗑  Eliminar ficha", height=44, fg_color="#7A1F1F",
                          hover_color="#591414",
                          command=self.eliminar).pack(side="left")

    # -- Página 1: datos básicos -------------------------------------------------
    def _build_datos_basicos(self, tab, record):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent", height=420)
        scroll.pack(fill="both", expand=True)
        self.b = {}

        eventos = db.list_eventos()
        evento_opciones = [f"{e['codigo']} - {e['nombre']}" for e in eventos]

        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="Evento de interés en salud pública", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.evento_field = ctk.CTkComboBox(top, values=evento_opciones, height=38, width=380,
                                             command=self._on_evento_change)
        default_evento = None
        if record:
            for opt in evento_opciones:
                if opt.startswith(record["codigo_evento"]):
                    default_evento = opt
        self.evento_field.set(default_evento or (evento_opciones[0] if evento_opciones else ""))
        self.evento_field.pack(anchor="w", pady=(4, 0))

        campos = [
            ("tipo_id", "Tipo de identificación", "combo", ["CC", "TI", "RC", "CE", "PA", "MS"]),
            ("numero_id", "Número de identificación", "entry"),
            ("primer_nombre", "Primer nombre", "entry"),
            ("segundo_nombre", "Segundo nombre", "entry"),
            ("primer_apellido", "Primer apellido", "entry"),
            ("segundo_apellido", "Segundo apellido", "entry"),
            ("telefono", "Teléfono", "entry"),
            ("fecha_nacimiento", "Fecha de nacimiento (AAAA-MM-DD)", "entry"),
            ("edad", "Edad", "entry"),
            ("unidad_edad", "Unidad de edad", "combo", ["Años", "Meses", "Días"]),
            ("sexo", "Sexo", "combo", ["F", "M", "I"]),
            ("nacionalidad", "Nacionalidad", "entry"),
            ("pais_procedencia", "País de procedencia", "entry"),
            ("departamento", "Departamento de ocurrencia", "entry"),
            ("municipio", "Municipio de ocurrencia", "entry"),
            ("area", "Área", "combo", ["Cabecera municipal", "Centro poblado", "Rural disperso"]),
            ("barrio", "Barrio", "entry"),
            ("vereda", "Vereda", "entry"),
            ("ocupacion", "Ocupación", "entry"),
            ("tipo_regimen", "Tipo de régimen", "combo", ["Contributivo", "Subsidiado", "Especial", "No asegurado"]),
            ("administradora", "Administradora (EPS)", "entry"),
            ("fuente", "Fuente de notificación", "combo", ["UPGD", "COVE", "Laboratorio", "Comunitaria"]),
            ("direccion_residencia", "Dirección de residencia", "entry"),
            ("fecha_consulta", "Fecha de consulta (AAAA-MM-DD)", "entry"),
            ("fecha_inicio_sintomas", "Fecha inicio de síntomas (AAAA-MM-DD)", "entry"),
            ("clasificacion_caso", "Clasificación del caso", "combo",
             ["Sospechoso", "Probable", "Confirmado por laboratorio",
              "Confirmado por clínica", "Confirmado por nexo epidemiológico"]),
            ("hospitalizado", "¿Hospitalizado?", "combo", SI_NO_OPCIONES),
            ("fecha_hospitalizacion", "Fecha hospitalización (AAAA-MM-DD)", "entry"),
            ("condicion", "Condición final", "combo", ["Vivo", "Fallecido"]),
            ("fecha_defuncion", "Fecha de defunción (AAAA-MM-DD)", "entry"),
            ("nombre_diligencia", "Nombre de quien diligencia la ficha", "entry"),
            ("telefono_diligencia", "Teléfono de quien diligencia", "entry"),
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)
        row = col = 0
        for spec in campos:
            key, label, tipo = spec[0], spec[1], spec[2]
            wrap = ctk.CTkFrame(grid, fg_color="transparent")
            wrap.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
            ctk.CTkLabel(wrap, text=label, font=("Segoe UI", 12)).pack(anchor="w")
            if tipo == "entry":
                w = ctk.CTkEntry(wrap, height=34)
            else:
                opciones = spec[3]
                w = ctk.CTkComboBox(wrap, values=opciones, height=34)
                w.set(opciones[0])
            if record and record[key] is not None:
                if tipo == "entry":
                    w.insert(0, str(record[key]))
                else:
                    w.set(str(record[key]))
            w.pack(fill="x")
            self.b[key] = w
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _evento_codigo_actual(self):
        val = self.evento_field.get()
        return val.split(" - ")[0].strip() if val else None

    def _on_evento_change(self, _value=None):
        self._render_datos_complementarios(None)

    # -- Página 2: datos complementarios (dinámicos) -----------------------------
    def _render_datos_complementarios(self, record):
        for w in self.compl_container.winfo_children():
            w.destroy()
        self.compl_widgets = {}

        codigo = self._evento_codigo_actual()
        evento = db.get_evento(codigo) if codigo else None
        if not evento:
            ctk.CTkLabel(self.compl_container, text="Selecciona un evento en la página 1.",
                         text_color="#9AA0AA").pack(anchor="w")
            return

        ctk.CTkLabel(self.compl_container, text=f"Formulario específico: {evento['nombre']}",
                     font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 12))

        existentes = {}
        if record and record["datos_complementarios"]:
            try:
                existentes = json.loads(record["datos_complementarios"])
            except (json.JSONDecodeError, TypeError):
                existentes = {}

        campos = json.loads(evento["campos_json"])
        grid = ctk.CTkFrame(self.compl_container, fg_color="transparent")
        grid.pack(fill="x")
        for c in range(2):
            grid.grid_columnconfigure(c, weight=1)
        row = col = 0
        for campo in campos:
            key, label, tipo = campo["key"], campo["label"], campo["tipo"]
            wrap = ctk.CTkFrame(grid, fg_color="transparent")
            wrap.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
            ctk.CTkLabel(wrap, text=label, font=("Segoe UI", 12)).pack(anchor="w")
            if tipo == "texto":
                w = ctk.CTkEntry(wrap, height=34)
                if key in existentes:
                    w.insert(0, existentes[key])
            elif tipo == "si_no":
                w = ctk.CTkComboBox(wrap, values=SI_NO_OPCIONES, height=34)
                w.set(existentes.get(key, "No"))
            elif tipo == "lista":
                opciones = campo["opciones"]
                w = ctk.CTkComboBox(wrap, values=opciones, height=34)
                w.set(existentes.get(key, opciones[0]))
            else:
                w = ctk.CTkEntry(wrap, height=34)
            w.pack(fill="x")
            self.compl_widgets[key] = w
            col += 1
            if col >= 2:
                col = 0
                row += 1

    # -- Página 3: laboratorios ----------------------------------------------------
    def _build_labs_tab(self, tab, record):
        wrap = ctk.CTkFrame(tab, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=10, pady=10)

        if not record:
            ctk.CTkLabel(wrap, text="Guarda primero la ficha (página 1) para poder "
                                     "registrar exámenes de laboratorio.",
                         text_color="#9AA0AA").pack(anchor="w")
            return

        form = ctk.CTkFrame(wrap, fg_color=COLOR_CARD, corner_radius=14)
        form.pack(fill="x", pady=(0, 14))
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=16)
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1)

        labels = ["Fecha toma (AAAA-MM-DD)", "Fecha recepción", "Muestra", "Prueba",
                  "Agente", "Resultado", "Fecha resultado", "Valor (si aplica)"]
        keys = ["fecha_toma", "fecha_recepcion", "muestra", "prueba",
                "agente", "resultado", "fecha_resultado", "valor"]
        self.lab_entries = {}
        for i, (lbl, key) in enumerate(zip(labels, keys)):
            box = ctk.CTkFrame(grid, fg_color="transparent")
            box.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="ew")
            ctk.CTkLabel(box, text=lbl, font=("Segoe UI", 12)).pack(anchor="w")
            e = ctk.CTkEntry(box, height=32)
            e.pack(fill="x")
            self.lab_entries[key] = e

        ctk.CTkButton(form, text="➕ Agregar resultado de laboratorio", height=36,
                      fg_color=COLOR_ACCENT,
                      command=lambda: self._agregar_lab(record["id"])).pack(
            anchor="w", padx=16, pady=(0, 16))

        ctk.CTkLabel(wrap, text="Resultados registrados", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(4, 8))
        self.labs_list_frame = ctk.CTkFrame(wrap, fg_color="transparent")
        self.labs_list_frame.pack(fill="x")
        self._refresh_labs_list(record["id"])

    def _refresh_labs_list(self, notificacion_id):
        for w in self.labs_list_frame.winfo_children():
            w.destroy()
        labs = db.list_laboratorios(notificacion_id)
        if not labs:
            ctk.CTkLabel(self.labs_list_frame, text="Sin resultados registrados aún.",
                         text_color="#9AA0AA").pack(anchor="w")
            return
        for lab in labs:
            row = ctk.CTkFrame(self.labs_list_frame, fg_color=COLOR_CARD, corner_radius=10)
            row.pack(fill="x", pady=4)
            texto = (f"🧪 {lab['prueba'] or '-'} · muestra: {lab['muestra'] or '-'} · "
                     f"resultado: {lab['resultado'] or '-'} · toma: {lab['fecha_toma'] or '-'}")
            ctk.CTkLabel(row, text=texto, font=("Segoe UI", 12)).pack(
                side="left", padx=14, pady=8)
            ctk.CTkButton(row, text="Eliminar", width=90, height=28, fg_color="#7A1F1F",
                          hover_color="#591414",
                          command=lambda lid=lab["id"], nid=notificacion_id: self._eliminar_lab(lid, nid)
                          ).pack(side="right", padx=10, pady=6)

    def _agregar_lab(self, notificacion_id):
        data = {k: e.get() for k, e in self.lab_entries.items()}
        if not data.get("prueba"):
            messagebox.showwarning("Falta información", "Indica al menos la prueba realizada.")
            return
        db.add_laboratorio(notificacion_id, data)
        for e in self.lab_entries.values():
            e.delete(0, "end")
        self._refresh_labs_list(notificacion_id)

    def _eliminar_lab(self, lab_id, notificacion_id):
        db.delete_laboratorio(lab_id)
        self._refresh_labs_list(notificacion_id)

    # -- Guardar / terminar / eliminar -------------------------------------------
    def _collect_data(self):
        data = {k: w.get() for k, w in self.b.items()}
        data["codigo_evento"] = self._evento_codigo_actual()
        data["fecha_notificacion"] = data.get("fecha_notificacion") or hoy()
        data["anio"] = datetime.now().year
        data["semana"] = int(datetime.now().strftime("%V"))
        data["upgd_id"] = self.app.current_upgd_id
        data["fecha_grabacion"] = hoy()
        compl = {k: w.get() for k, w in self.compl_widgets.items()}
        data["datos_complementarios"] = json.dumps(compl, ensure_ascii=False)
        return data

    def guardar(self, estado_final=None):
        if not self._evento_codigo_actual():
            messagebox.showwarning("Falta evento", "Selecciona el evento de interés en salud pública.")
            return None
        data = self._collect_data()
        if not data.get("numero_id") or not data.get("primer_nombre"):
            messagebox.showwarning("Datos incompletos",
                                    "Número de identificación y primer nombre son obligatorios.")
            return None
        if estado_final:
            data["estado_ficha"] = estado_final
        if self.editing_id:
            db.update_notificacion(self.editing_id, data)
            nid = self.editing_id
        else:
            data.setdefault("estado_ficha", "En proceso")
            nid = db.create_notificacion(data, self.app.current_user["id"])
            self.editing_id = nid
        db.log_action(self.app.current_user["id"], "GUARDA_FICHA", f"id={nid}")
        return nid

    def terminar(self):
        nid = self.guardar(estado_final="Terminada")
        if nid:
            messagebox.showinfo("Ficha terminada",
                                 "La ficha se guardó como TERMINADA y quedó lista para envío.")
            self.app.show_frame(ListadoFrame)

    def eliminar(self):
        if not self.editing_id:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar esta ficha de forma permanente?"):
            db.delete_notificacion(self.editing_id)
            self.app.show_frame(ListadoFrame)


# ---------------------------------------------------------------------------
# LISTADO / BÚSQUEDA DE FICHAS
# ---------------------------------------------------------------------------

class ListadoFrame(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app, active_key="listado")
        self.section_title("Fichas registradas", "Busca, filtra, edita o continúa el "
                                                   "diligenciamiento de una notificación.")

        toolbar = ctk.CTkFrame(self.content, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 14))

        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="Buscar por nombre, apellido o documento...",
                                          height=38, width=320)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        eventos = ["Todos"] + [f"{e['codigo']}" for e in db.list_eventos()]
        nombres = {e["codigo"]: e["nombre"] for e in db.list_eventos()}
        self.evento_filter_map = nombres
        display_values = ["Todos"] + [f"{c} - {nombres[c]}" for c in nombres]
        self.evento_filter = ctk.CTkComboBox(toolbar, values=display_values, height=38, width=260)
        self.evento_filter.set("Todos")
        self.evento_filter.pack(side="left", padx=10)

        ctk.CTkButton(toolbar, text="🔍 Buscar", height=38, fg_color=COLOR_ACCENT,
                      command=self.refresh).pack(side="left")
        if self.permisos.get("notificar_individual"):
            ctk.CTkButton(toolbar, text="➕ Nueva ficha", height=38, fg_color=COLOR_PRIMARY,
                          hover_color=COLOR_PRIMARY_HOVER,
                          command=lambda: app.show_frame(IndividualFrame)).pack(side="right")

        self.list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        texto = self.search_entry.get().strip()
        evento_val = self.evento_filter.get()
        codigo = evento_val.split(" - ")[0].strip() if evento_val != "Todos" else "Todos"
        rows = db.list_notificaciones(texto, codigo)

        if not rows:
            ctk.CTkLabel(self.list_frame, text="No se encontraron fichas con esos criterios.",
                         text_color="#9AA0AA").pack(anchor="w", pady=20)
            return

        for r in rows:
            item = ctk.CTkFrame(self.list_frame, fg_color=COLOR_CARD, corner_radius=12)
            item.pack(fill="x", pady=5)

            nombre = f"{r['primer_nombre'] or ''} {r['primer_apellido'] or ''}".strip() or "(sin nombre)"
            estado_color = "#2E7D32" if r["estado_ficha"] == "Terminada" else "#B8860B"

            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=16, pady=10)
            ctk.CTkLabel(info, text=f"🧍 {nombre}  ·  {r['tipo_id']} {r['numero_id']}",
                         font=("Segoe UI", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=f"Evento: {r['evento_nombre']}   ·   UPGD: {r['upgd_nombre']}   ·   "
                                     f"Notificado: {r['fecha_notificacion'] or '-'}",
                         font=("Segoe UI", 11), text_color="#9AA0AA").pack(anchor="w")

            badge = ctk.CTkLabel(item, text=r["estado_ficha"], fg_color=estado_color,
                                  corner_radius=8, text_color="white", font=("Segoe UI", 11, "bold"),
                                  width=90, height=26)
            badge.pack(side="left", padx=6)

            ctk.CTkButton(item, text="Abrir", width=90, height=30, fg_color=COLOR_ACCENT,
                          command=lambda rid=r["id"]: self.abrir(rid)).pack(side="right", padx=14, pady=8)

    def abrir(self, notificacion_id):
        self.app.show_frame(IndividualFrame, notificacion_id=notificacion_id)


# ---------------------------------------------------------------------------
# GESTIÓN DE USUARIOS (super admin / admin)
# ---------------------------------------------------------------------------

def roles_asignables(rol_actor):
    """Roles que un actor con 'rol_actor' puede asignar a otros usuarios."""
    if rol_actor == "super_admin":
        return db.ROLES_DISPONIBLES
    rango_actor = db.ROLES_JERARQUIA.get(rol_actor, 0)
    return [r for r, rango in db.ROLES_JERARQUIA.items() if rango < rango_actor]


class UsuariosFrame(BaseScreen):
    def __init__(self, parent, app):
        super().__init__(parent, app, active_key="usuarios")

        if not self.permisos.get("gestionar_usuarios"):
            self.section_title("Usuarios")
            self.sin_permiso("Tu rol no tiene permiso para administrar usuarios.")
            return

        self.section_title("Gestión de usuarios",
                            "Crea usuarios, asígnales un rol y personaliza sus permisos. "
                            "Solo puedes gestionar usuarios de rango igual o inferior al tuyo.")

        ctk.CTkButton(self.content, text="➕ Crear nuevo usuario", height=42,
                      fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                      font=("Segoe UI", 14, "bold"),
                      command=self.abrir_crear).pack(anchor="w", pady=(0, 18))

        self.lista_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.lista_frame.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        for w in self.lista_frame.winfo_children():
            w.destroy()
        for u in db.list_users():
            row = ctk.CTkFrame(self.lista_frame, fg_color=COLOR_CARD, corner_radius=12)
            row.pack(fill="x", pady=5)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=16, pady=10)
            nombre_line = ctk.CTkFrame(info, fg_color="transparent")
            nombre_line.pack(anchor="w")
            ctk.CTkLabel(nombre_line, text=f"👤 {u['nombre_completo']}",
                         font=("Segoe UI", 13, "bold")).pack(side="left")
            ctk.CTkLabel(nombre_line, text=ROL_LABELS.get(u["rol"], u["rol"]),
                         fg_color=ROL_COLORS.get(u["rol"], "#555"), text_color="white",
                         corner_radius=8, font=("Segoe UI", 10, "bold"),
                         width=140, height=22).pack(side="left", padx=10)
            if not u["activo"]:
                ctk.CTkLabel(nombre_line, text="INACTIVO", fg_color="#7A1F1F",
                             text_color="white", corner_radius=8, font=("Segoe UI", 10, "bold"),
                             width=80, height=22).pack(side="left")
            ctk.CTkLabel(info, text=f"Usuario: {u['username']}", font=("Segoe UI", 11),
                         text_color="#9AA0AA").pack(anchor="w")

            puede = db.puede_gestionar(self.app.current_user, u)
            es_yo_mismo = u["id"] == self.app.current_user["id"]

            acciones = ctk.CTkFrame(row, fg_color="transparent")
            acciones.pack(side="right", padx=12, pady=8)

            if puede:
                ctk.CTkButton(acciones, text="Editar", width=80, height=30, fg_color=COLOR_ACCENT,
                              command=lambda uid=u["id"]: self.abrir_editar(uid)).pack(side="left", padx=4)
                ctk.CTkButton(acciones, text="Clave", width=80, height=30, fg_color="#5C4B00",
                              command=lambda uid=u["id"]: self.abrir_reset_clave(uid)).pack(side="left", padx=4)
                if not es_yo_mismo:
                    texto = "Desactivar" if u["activo"] else "Activar"
                    color = "#7A1F1F" if u["activo"] else "#2E7D32"
                    ctk.CTkButton(acciones, text=texto, width=90, height=30, fg_color=color,
                                  command=lambda uid=u["id"], act=not u["activo"]: self.toggle_activo(uid, act)
                                  ).pack(side="left", padx=4)
            else:
                ctk.CTkLabel(acciones, text="🔒 Sin permisos sobre este usuario",
                             font=("Segoe UI", 11), text_color="#666").pack(padx=6)

    def toggle_activo(self, user_id, activo):
        db.set_user_active(user_id, activo)
        db.log_action(self.app.current_user["id"],
                       "ACTIVA_USUARIO" if activo else "DESACTIVA_USUARIO", f"id={user_id}")
        self.refresh()

    def abrir_crear(self):
        UserFormDialog(self, modo="crear")

    def abrir_editar(self, user_id):
        UserFormDialog(self, modo="editar", user_id=user_id)

    def abrir_reset_clave(self, user_id):
        ResetPasswordDialog(self, user_id)


class UserFormDialog(ctk.CTkToplevel):
    """Ventana emergente para crear o editar un usuario, con permisos granulares."""

    def __init__(self, parent_frame: UsuariosFrame, modo="crear", user_id=None):
        super().__init__(parent_frame)
        self.parent_frame = parent_frame
        self.app = parent_frame.app
        self.modo = modo
        self.user_id = user_id
        self.target_user = db.get_user_by_id(user_id) if user_id else None

        self.title("Crear usuario" if modo == "crear" else "Editar usuario")
        self.geometry("460x640")
        self.configure(fg_color=COLOR_BG)
        self.grab_set()  # modal

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="Crear nuevo usuario" if modo == "crear" else "Editar usuario",
                     font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 14))

        ctk.CTkLabel(scroll, text="Código de usuario", font=FONT_LABEL).pack(anchor="w")
        self.username_entry = ctk.CTkEntry(scroll, height=36)
        self.username_entry.pack(fill="x", pady=(4, 10))
        if self.target_user:
            self.username_entry.insert(0, self.target_user["username"])
            self.username_entry.configure(state="disabled")  # el username no se edita

        ctk.CTkLabel(scroll, text="Nombre completo", font=FONT_LABEL).pack(anchor="w")
        self.nombre_entry = ctk.CTkEntry(scroll, height=36)
        self.nombre_entry.pack(fill="x", pady=(4, 10))
        if self.target_user:
            self.nombre_entry.insert(0, self.target_user["nombre_completo"])

        if modo == "crear":
            ctk.CTkLabel(scroll, text="Contraseña inicial", font=FONT_LABEL).pack(anchor="w")
            self.password_entry = ctk.CTkEntry(scroll, height=36, show="•")
            self.password_entry.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(scroll, text="Rol", font=FONT_LABEL).pack(anchor="w")
        asignables = roles_asignables(self.app.current_user["rol"])
        if self.target_user and self.target_user["rol"] not in asignables:
            asignables = asignables + [self.target_user["rol"]]
        self.rol_combo = ctk.CTkComboBox(scroll, values=[ROL_LABELS[r] for r in asignables],
                                          height=36, command=self._on_rol_change)
        self._roles_orden = asignables
        rol_inicial = self.target_user["rol"] if self.target_user else asignables[0]
        self.rol_combo.set(ROL_LABELS.get(rol_inicial, rol_inicial))
        self.rol_combo.pack(fill="x", pady=(4, 14))

        ctk.CTkLabel(scroll, text="Permisos", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(4, 8))
        self.permiso_vars = {}
        permisos_iniciales = (db.get_permisos(self.target_user) if self.target_user
                               else db.permisos_por_defecto(rol_inicial))
        for key, label in db.PERMISOS_LABELS.items():
            var = tk.BooleanVar(value=permisos_iniciales.get(key, False))
            self.permiso_vars[key] = var
            ctk.CTkCheckBox(scroll, text=label, variable=var, fg_color=COLOR_PRIMARY,
                             hover_color=COLOR_PRIMARY_HOVER, wraplength=380,
                             justify="left").pack(anchor="w", pady=3)

        self.error_label = ctk.CTkLabel(scroll, text="", text_color="#FF6B6B")
        self.error_label.pack(anchor="w", pady=(10, 0))

        ctk.CTkButton(scroll, text="💾 Guardar", height=42, fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER, font=("Segoe UI", 14, "bold"),
                      command=self.guardar).pack(fill="x", pady=(16, 4))
        ctk.CTkButton(scroll, text="Cancelar", height=36, fg_color="transparent",
                      command=self.destroy).pack(fill="x")

    def _on_rol_change(self, _value):
        rol = self._rol_actual()
        defaults = db.permisos_por_defecto(rol)
        for key, var in self.permiso_vars.items():
            var.set(defaults.get(key, False))

    def _rol_actual(self):
        label = self.rol_combo.get()
        for r in self._roles_orden:
            if ROL_LABELS.get(r, r) == label:
                return r
        return self._roles_orden[0]

    def guardar(self):
        nombre = self.nombre_entry.get().strip()
        rol = self._rol_actual()
        permisos = {k: v.get() for k, v in self.permiso_vars.items()}

        if not nombre:
            self.error_label.configure(text="El nombre completo es obligatorio.")
            return

        if self.modo == "crear":
            username = self.username_entry.get().strip()
            password = self.password_entry.get()
            if not username or not password:
                self.error_label.configure(text="Usuario y contraseña son obligatorios.")
                return
            if len(password) < 6:
                self.error_label.configure(text="La contraseña debe tener al menos 6 caracteres.")
                return
            if db.username_exists(username):
                self.error_label.configure(text="Ese código de usuario ya existe.")
                return
            db.create_user(username, password, nombre, rol=rol, permisos=permisos,
                            creado_por=self.app.current_user["id"])
            db.log_action(self.app.current_user["id"], "CREA_USUARIO", username)
        else:
            db.update_user(self.user_id, nombre_completo=nombre, rol=rol, permisos=permisos)
            db.log_action(self.app.current_user["id"], "EDITA_USUARIO", f"id={self.user_id}")

        self.destroy()
        self.app.show_frame(UsuariosFrame)


class ResetPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent_frame: UsuariosFrame, user_id):
        super().__init__(parent_frame)
        self.parent_frame = parent_frame
        self.app = parent_frame.app
        self.user_id = user_id
        user = db.get_user_by_id(user_id)

        self.title("Restablecer contraseña")
        self.geometry("380x260")
        self.configure(fg_color=COLOR_BG)
        self.grab_set()

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(wrap, text=f"Nueva contraseña para {user['nombre_completo']}",
                     font=("Segoe UI", 14, "bold"), wraplength=340).pack(anchor="w", pady=(0, 14))
        self.pw_entry = ctk.CTkEntry(wrap, height=36, show="•", placeholder_text="Mínimo 6 caracteres")
        self.pw_entry.pack(fill="x")

        self.error_label = ctk.CTkLabel(wrap, text="", text_color="#FF6B6B")
        self.error_label.pack(anchor="w", pady=(8, 0))

        ctk.CTkButton(wrap, text="💾 Guardar nueva contraseña", height=40, fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER,
                      command=self.guardar).pack(fill="x", pady=(20, 6))
        ctk.CTkButton(wrap, text="Cancelar", height=34, fg_color="transparent",
                      command=self.destroy).pack(fill="x")

    def guardar(self):
        pw = self.pw_entry.get()
        if len(pw) < 6:
            self.error_label.configure(text="La contraseña debe tener al menos 6 caracteres.")
            return
        db.reset_password(self.user_id, pw)
        db.log_action(self.app.current_user["id"], "RESET_PASSWORD", f"id={self.user_id}")
        self.destroy()
        self.app.show_frame(UsuariosFrame)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = SivigilaApp()
    app.mainloop()
