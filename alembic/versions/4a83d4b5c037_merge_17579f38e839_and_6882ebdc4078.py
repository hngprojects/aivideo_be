"""Merge 17579f38e839 and 6882ebdc4078

Revision ID: 4a83d4b5c037
Revises: 6882ebdc4078
Create Date: 2024-08-14 18:20:27.572058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a83d4b5c037'
down_revision: Union[str, None] = '6882ebdc4078'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
