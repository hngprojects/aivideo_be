"""Merge 17579f38e839 and 5d2400f416fb

Revision ID: 6882ebdc4078
Revises: 5d2400f416fb
Create Date: 2024-08-14 18:18:52.166826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6882ebdc4078'
down_revision: Union[str, None] = '5d2400f416fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
