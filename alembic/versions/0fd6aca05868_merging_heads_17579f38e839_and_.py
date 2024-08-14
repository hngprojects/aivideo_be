"""Merging heads 17579f38e839 and 4a83d4b5c037

Revision ID: 0fd6aca05868
Revises: 4a83d4b5c037
Create Date: 2024-08-14 19:22:00.959541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fd6aca05868'
down_revision: Union[str, None] = '4a83d4b5c037'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
