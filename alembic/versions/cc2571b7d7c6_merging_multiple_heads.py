"""Merging multiple heads

Revision ID: cc2571b7d7c6
Revises: 76a6b1a73fa5
Create Date: 2024-08-14 16:08:26.192657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc2571b7d7c6'
down_revision: Union[str, None] = '76a6b1a73fa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
