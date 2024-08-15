"""Merging heads to fix multiple head issue

Revision ID: 27219c80768c
Revises: 2afb0259557d, b80680675943
Create Date: 2024-08-14 20:43:41.451108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27219c80768c'
down_revision: Union[str, None] = ('2afb0259557d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
