"""Final merge of heads

Revision ID: 17579f38e839
Revises: cc2571b7d7c6
Create Date: 2024-08-14 16:09:32.432785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17579f38e839'
down_revision: Union[str, None] = 'cc2571b7d7c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
