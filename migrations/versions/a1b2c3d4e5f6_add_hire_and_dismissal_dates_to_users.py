"""Add hire_date and dismissal_date to users

Revision ID: a1b2c3d4e5f6
Revises: 9977775ed120
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '9977775ed120'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('hire_date', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('dismissal_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('users', 'dismissal_date')
    op.drop_column('users', 'hire_date')
