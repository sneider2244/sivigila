"""estados_y_trazabilidad

Revision ID: a67a6cf60073
Revises: 5210c2ca17b8
Create Date: 2026-09-25 00:48:00.752056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a67a6cf60073'
down_revision: Union[str, Sequence[str], None] = '5210c2ca17b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Enum de estados compartido por `fichas_datos_basicos.estado` y las dos columnas
# de `fichas_trazabilidad`. Se crea una sola vez explícitamente.
estado_ficha = postgresql.ENUM(
    'NOTIFICADA', 'EN_AJUSTE', 'CONFIRMADA', 'DESCARTADA',
    name='estado_ficha',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    estado_ficha.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'fichas_datos_basicos',
        sa.Column(
            'estado',
            estado_ficha,
            server_default='NOTIFICADA',
            nullable=False,
        ),
    )

    op.create_table(
        'fichas_trazabilidad',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ficha_basica_id', sa.Integer(), nullable=False),
        sa.Column('estado_anterior', estado_ficha, nullable=False),
        sa.Column('estado_nuevo', estado_ficha, nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('ajuste', sa.Integer(), nullable=True),
        sa.Column('observacion', sa.String(length=500), nullable=True),
        sa.Column('f_cambio', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['ficha_basica_id'],
            ['fichas_datos_basicos.id'],
            name='fk_fichas_trazabilidad_ficha_basica',
        ),
        sa.ForeignKeyConstraint(
            ['usuario_id'],
            ['usuarios.id'],
            name='fk_fichas_trazabilidad_usuario',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_fichas_trazabilidad_ficha_basica_id'),
        'fichas_trazabilidad',
        ['ficha_basica_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_fichas_trazabilidad_ficha_basica_id'),
        table_name='fichas_trazabilidad',
    )
    op.drop_table('fichas_trazabilidad')
    op.drop_column('fichas_datos_basicos', 'estado')
    estado_ficha.drop(op.get_bind(), checkfirst=True)
