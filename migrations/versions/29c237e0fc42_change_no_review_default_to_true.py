"""change no_review default to True

Revision ID: 29c237e0fc42
Revises: 4243ac7f3cf0
Create Date: 2026-05-06 15:33:16.293546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29c237e0fc42'
down_revision: Union[str, Sequence[str], None] = '4243ac7f3cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('tasks', 'no_review', server_default=sa.text('true'))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('tasks', 'no_review', server_default=sa.text('false'))
