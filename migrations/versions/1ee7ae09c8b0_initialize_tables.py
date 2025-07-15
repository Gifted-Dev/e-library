"""initialize tables

Revision ID: 1ee7ae09c8b0
Revises: 8beb8e27e13b
Create Date: 2025-07-15 17:31:05.042545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ee7ae09c8b0'
down_revision: Union[str, Sequence[str], None] = '8beb8e27e13b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
