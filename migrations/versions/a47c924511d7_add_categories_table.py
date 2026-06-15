"""add categories table

Revision ID: a47c924511d7
Revises: c3daab576447
Create Date: 2026-06-15 16:56:39.958558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a47c924511d7'
down_revision: Union[str, Sequence[str], None] = 'c3daab576447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_CATEGORIES = [
    'нормативный',
    'учебный',
    'методический',
    'прочее',
]


def upgrade() -> None:
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    for name in DEFAULT_CATEGORIES:
        op.execute(f"INSERT INTO categories (name) VALUES ('{name}')")


def downgrade() -> None:
    op.drop_table('categories')
