"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("salt", sa.String(length=64), nullable=False),
        sa.Column("nombre_completo", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("permisos", sa.JSON(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"]),
    )
    op.create_index("ix_usuarios_username", "usuarios", ["username"], unique=True)

    op.create_table(
        "upgd",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cod_prestador", sa.String(length=50), nullable=False),
        sa.Column("subred", sa.String(length=255), nullable=True),
        sa.Column("fecha_caracteriza", sa.Date(), nullable=True),
        sa.Column("fecha_inicio_uso", sa.Date(), nullable=True),
        sa.Column("razon_social", sa.String(length=255), nullable=False),
        sa.Column("nit", sa.String(length=50), nullable=True),
        sa.Column("direccion", sa.String(length=255), nullable=True),
        sa.Column("representante_legal", sa.String(length=255), nullable=True),
        sa.Column("correo_electronico", sa.String(length=255), nullable=True),
        sa.Column("responsable_notif", sa.String(length=255), nullable=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("fecha_constitucion", sa.Date(), nullable=True),
        sa.Column("naturaleza_juridica", sa.String(length=100), nullable=True),
        sa.Column("nivel_complejidad", sa.String(length=50), nullable=True),
        sa.Column("tipo_unidad", sa.String(length=50), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("localidad_zona", sa.String(length=255), nullable=True),
        sa.Column("notif_iad", sa.Boolean(), nullable=False),
        sa.Column("notif_iso", sa.Boolean(), nullable=False),
        sa.Column("notif_cab", sa.Boolean(), nullable=False),
        sa.Column("unidad_analisis", sa.Boolean(), nullable=False),
        sa.Column("cove", sa.Boolean(), nullable=False),
        sa.Column("talento_humano", sa.Boolean(), nullable=False),
        sa.Column("fax_modem", sa.Boolean(), nullable=False),
        sa.Column("correo_recurso", sa.Boolean(), nullable=False),
        sa.Column("internet", sa.Boolean(), nullable=False),
        sa.Column("telefax", sa.Boolean(), nullable=False),
        sa.Column("radio_telefono", sa.Boolean(), nullable=False),
        sa.Column("computador", sa.Boolean(), nullable=False),
        sa.Column("activa_sivigila", sa.Boolean(), nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "eventos",
        sa.Column("codigo", sa.String(length=10), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("campos_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("upgd_id", sa.Integer(), nullable=False),
        sa.Column("codigo_ficha", sa.String(length=50), nullable=True),
        sa.Column("ajuste", sa.Boolean(), nullable=False),
        sa.Column("fecha_grabacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("codigo_evento", sa.String(length=10), nullable=False),
        sa.Column("fecha_notificacion", sa.Date(), nullable=True),
        sa.Column("anio", sa.Integer(), nullable=True),
        sa.Column("semana", sa.Integer(), nullable=True),
        sa.Column("tipo_id", sa.String(length=10), nullable=True),
        sa.Column("numero_id", sa.String(length=50), nullable=True),
        sa.Column("primer_nombre", sa.String(length=100), nullable=True),
        sa.Column("segundo_nombre", sa.String(length=100), nullable=True),
        sa.Column("primer_apellido", sa.String(length=100), nullable=True),
        sa.Column("segundo_apellido", sa.String(length=100), nullable=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("edad", sa.Integer(), nullable=True),
        sa.Column("unidad_edad", sa.String(length=20), nullable=True),
        sa.Column("sexo", sa.String(length=5), nullable=True),
        sa.Column("nacionalidad", sa.String(length=100), nullable=True),
        sa.Column("pais_procedencia", sa.String(length=100), nullable=True),
        sa.Column("departamento", sa.String(length=100), nullable=True),
        sa.Column("municipio", sa.String(length=100), nullable=True),
        sa.Column("area", sa.String(length=50), nullable=True),
        sa.Column("localidad", sa.String(length=100), nullable=True),
        sa.Column("centro_poblado", sa.String(length=100), nullable=True),
        sa.Column("vereda", sa.String(length=100), nullable=True),
        sa.Column("barrio", sa.String(length=100), nullable=True),
        sa.Column("ocupacion", sa.String(length=150), nullable=True),
        sa.Column("tipo_regimen", sa.String(length=50), nullable=True),
        sa.Column("administradora", sa.String(length=150), nullable=True),
        sa.Column("pertenencia_etnica", sa.String(length=100), nullable=True),
        sa.Column("grupo_etnico", sa.String(length=100), nullable=True),
        sa.Column("fuente", sa.String(length=50), nullable=True),
        sa.Column("direccion_residencia", sa.String(length=255), nullable=True),
        sa.Column("fecha_consulta", sa.Date(), nullable=True),
        sa.Column("fecha_inicio_sintomas", sa.Date(), nullable=True),
        sa.Column("clasificacion_caso", sa.String(length=100), nullable=True),
        sa.Column("hospitalizado", sa.Boolean(), nullable=True),
        sa.Column("fecha_hospitalizacion", sa.Date(), nullable=True),
        sa.Column("condicion", sa.String(length=50), nullable=True),
        sa.Column("fecha_defuncion", sa.Date(), nullable=True),
        sa.Column("certificado_defuncion", sa.String(length=50), nullable=True),
        sa.Column("causa_basica", sa.String(length=255), nullable=True),
        sa.Column("nombre_diligencia", sa.String(length=255), nullable=True),
        sa.Column("telefono_diligencia", sa.String(length=50), nullable=True),
        sa.Column("datos_complementarios", sa.JSON(), nullable=True),
        sa.Column("estado_ficha", sa.String(length=20), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["upgd_id"], ["upgd.id"]),
        sa.ForeignKeyConstraint(["codigo_evento"], ["eventos.codigo"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuarios.id"]),
    )
    op.create_index("ix_notificaciones_upgd_id", "notificaciones", ["upgd_id"])
    op.create_index("ix_notificaciones_codigo_evento", "notificaciones", ["codigo_evento"])
    op.create_index("ix_notificaciones_numero_id", "notificaciones", ["numero_id"])
    op.create_index("ix_notificaciones_primer_apellido", "notificaciones", ["primer_apellido"])

    op.create_table(
        "laboratorios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notificacion_id", sa.Integer(), nullable=False),
        sa.Column("fecha_toma", sa.Date(), nullable=True),
        sa.Column("fecha_recepcion", sa.Date(), nullable=True),
        sa.Column("muestra", sa.String(length=150), nullable=True),
        sa.Column("prueba", sa.String(length=150), nullable=True),
        sa.Column("agente", sa.String(length=150), nullable=True),
        sa.Column("resultado", sa.String(length=150), nullable=True),
        sa.Column("fecha_resultado", sa.Date(), nullable=True),
        sa.Column("valor", sa.String(length=100), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["notificacion_id"], ["notificaciones.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_laboratorios_notificacion_id", "laboratorios", ["notificacion_id"])

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=50), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )


def downgrade() -> None:
    op.drop_table("auditoria")
    op.drop_index("ix_laboratorios_notificacion_id", table_name="laboratorios")
    op.drop_table("laboratorios")
    op.drop_index("ix_notificaciones_primer_apellido", table_name="notificaciones")
    op.drop_index("ix_notificaciones_numero_id", table_name="notificaciones")
    op.drop_index("ix_notificaciones_codigo_evento", table_name="notificaciones")
    op.drop_index("ix_notificaciones_upgd_id", table_name="notificaciones")
    op.drop_table("notificaciones")
    op.drop_table("eventos")
    op.drop_table("upgd")
    op.drop_index("ix_usuarios_username", table_name="usuarios")
    op.drop_table("usuarios")
