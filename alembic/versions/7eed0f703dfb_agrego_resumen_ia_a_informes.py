"""Agrego resumen ia a informes

Revision ID: 7eed0f703dfb
Revises: 697ba0fcaaff
Create Date: 2026-10-25 17:19:57.529804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7eed0f703dfb'
down_revision: Union[str, Sequence[str], None] = '697ba0fcaaff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('informes_generados', sa.Column('resumen_ia', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('informes_generados', 'resumen_ia')