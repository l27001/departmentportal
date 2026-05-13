"""seed_all_roles

Revision ID: 4f8a3e2c1d5b
Revises: b5afe9b60f32
Create Date: 2026-05-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4f8a3e2c1d5b'
down_revision: Union[str, Sequence[str], None] = 'b5afe9b60f32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES = [
    (1, "Руководитель"),
    (2, "Документовед"),
    (3, "Сотрудник"),
    (4, "Ответственный"),
]


def upgrade() -> None:
    conn = op.get_bind()
    existing = {row[0] for row in conn.execute(
        sa.text("SELECT name FROM roles")
    ).fetchall()}
    for rid, name in ROLES:
        if name not in existing:
            op.execute(f"INSERT INTO roles (id, name) VALUES ({rid}, '{name}')")

    max_id = conn.execute(sa.text("SELECT MAX(id) FROM roles")).scalar()
    conn.execute(sa.text(f"ALTER SEQUENCE roles_id_seq RESTART WITH {max_id + 1}"))


def downgrade() -> None:
    names = [name for _, name in ROLES]
    op.execute("DELETE FROM roles WHERE name IN ('" + "','".join(names) + "')")
