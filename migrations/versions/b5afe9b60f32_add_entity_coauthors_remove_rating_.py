"""add_entity_coauthors

Revision ID: b5afe9b60f32
Revises: cf9762e6159d
Create Date: 2026-05-10 19:44:05.078780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'b5afe9b60f32'
down_revision: Union[str, Sequence[str], None] = 'cf9762e6159d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if 'entity_coauthors' not in inspect(conn).get_table_names():
        op.create_table('entity_coauthors',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('entity_type', 'entity_id', 'user_id', name='uq_entity_coauthor'),
        )


def downgrade() -> None:
    op.drop_table('entity_coauthors')
