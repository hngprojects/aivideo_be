"""empty message

Revision ID: 67a7708dda66
Revises: 27219c80768c, ec8f02b74c2a
Create Date: 2024-08-15 18:59:26.975235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67a7708dda66'
down_revision: Union[str, None] = ('27219c80768c', 'ec8f02b74c2a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
