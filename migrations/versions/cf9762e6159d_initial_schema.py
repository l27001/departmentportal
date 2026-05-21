"""Create all tables from current models (squashed initial migration)

Revision ID: cf9762e6159d
Revises: 
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'cf9762e6159d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(name: str) -> bool:
    conn = op.get_bind()
    return name in inspect(conn).get_table_names()


def upgrade() -> None:
    from app import create_app
    from extensions import db

    app = create_app()
    with app.app_context():
        conn = op.get_bind()
        db.metadata.create_all(conn)


def downgrade() -> None:
    from app import create_app
    from extensions import db

    app = create_app()
    with app.app_context():
        conn = op.get_bind()
        for table_name, table in reversed(list(db.metadata.tables.items())):
            if table_name.startswith('alembic'):
                continue
            table.drop(conn, checkfirst=True)
