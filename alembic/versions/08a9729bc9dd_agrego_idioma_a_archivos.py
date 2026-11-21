"""agrego idioma a archivos

Revision ID: 08a9729bc9dd
Revises: 5c0dcc954b52
Create Date: 2026-11-07 16:35:39.275650

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08a9729bc9dd'
down_revision: Union[str, Sequence[str], None] = '5c0dcc954b52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('archivos_subidos', sa.Column('idioma', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('archivos_subidos', 'idioma')