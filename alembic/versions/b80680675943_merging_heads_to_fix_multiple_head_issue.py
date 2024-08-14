"""Merging heads to fix multiple head issue

Revision ID: b80680675943
Revises: 0fd6aca05868, c5f21b9595f0
Create Date: 2024-08-14 19:42:21.361484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b80680675943'
down_revision: Union[str, None] = ('0fd6aca05868', 'c5f21b9595f0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
