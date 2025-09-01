"""merge heads

Revision ID: b1c39b2569a6
Revises: kb_001, d00d5d661a4f
Create Date: 2025-09-01 10:50:41.297331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c39b2569a6'
down_revision: Union[str, Sequence[str], None] = ('kb_001', 'd00d5d661a4f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
