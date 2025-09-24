"""Agrego tabla roles y relacion con usuario

Revision ID: db5975377962
Revises: e36cbef62332
Create Date: 2025-09-23 20:18:17.408036
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'db5975377962'
down_revision = 'e36cbef62332'
branch_labels = None
depends_on = None


def upgrade():
    # Creo la tabla roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre')
    )

    # Inserto un rol por defecto
    op.execute("INSERT INTO roles (id, nombre) VALUES (1, 'Usuario')")

    # Altero usuarios para agregar role_id
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.add_column(
            sa.Column('role_id', sa.Integer(), nullable=False, server_default='1')
        )
        batch_op.create_foreign_key(None, 'roles', ['role_id'], ['id'])
        batch_op.drop_column('rol')

    # Opcional: eliminar server_default después de la migración
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.alter_column('role_id', server_default=None)


def downgrade():
    # Revierto cambios
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rol', sa.TEXT(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('role_id')

    op.drop_table('roles')
