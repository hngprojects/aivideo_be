"""Merge heads 34325fd8c1e1 and 5a8db3840d41

Revision ID: 76a6b1a73fa5
Revises: 5a8db3840d41
Create Date: 2024-08-14 15:59:35.000233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76a6b1a73fa5'
down_revision: Union[str, None] = '5a8db3840d41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
