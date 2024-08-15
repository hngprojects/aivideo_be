"""Merging heads

Revision ID: 5d2400f416fb
Revises: 34325fd8c1e1
Create Date: 2024-08-14 18:14:28.954783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d2400f416fb'
down_revision: Union[str, None] = '34325fd8c1e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
