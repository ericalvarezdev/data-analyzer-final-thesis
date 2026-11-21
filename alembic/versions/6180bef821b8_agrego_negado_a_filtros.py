"""agrego negado a filtros

Revision ID: 6180bef821b8
Revises: 5c0dcc954b52
Create Date: 2026-11-07 16:27:34.517207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6180bef821b8'
down_revision: Union[str, Sequence[str], None] = '5c0dcc954b52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
