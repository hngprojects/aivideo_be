"""Merging multiple heads

Revision ID: ec8f02b74c2a
Revises: a2aee69efd58
Create Date: 2024-08-15 18:59:02.769951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec8f02b74c2a'
down_revision: Union[str, None] = 'a2aee69efd58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
