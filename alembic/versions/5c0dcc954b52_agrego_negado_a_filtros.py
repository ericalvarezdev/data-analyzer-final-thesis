"""agrego negado a filtros

Revision ID: 5c0dcc954b52
Revises: 7eed0f703dfb
Create Date: 2026-11-07 14:05:51.341134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c0dcc954b52'
down_revision: Union[str, Sequence[str], None] = '7eed0f703dfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
