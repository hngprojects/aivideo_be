"""Final Merge of all heads

Revision ID: c5f21b9595f0
Revises: 17579f38e839
Create Date: 2024-08-14 19:25:17.081495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5f21b9595f0'
down_revision: Union[str, None] = '17579f38e839'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
