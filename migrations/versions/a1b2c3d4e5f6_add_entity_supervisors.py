"""add_entity_supervisors

Revision ID: a1b2c3d4e5f6
Revises: 4f8a3e2c1d5b
Create Date: 2026-05-14 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4f8a3e2c1d5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if 'entity_supervisors' not in inspect(conn).get_table_names():
        op.create_table('entity_supervisors',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('entity_type', 'entity_id', 'user_id', name='uq_entity_supervisor'),
        )


def downgrade() -> None:
    op.drop_table('entity_supervisors')
