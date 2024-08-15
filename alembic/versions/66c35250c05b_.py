"""empty message

Revision ID: 66c35250c05b
Revises: 3b462de6ce0e, 764d60fda655
Create Date: 2024-08-15 17:32:35.894514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66c35250c05b'
down_revision: Union[str, None] = ('3b462de6ce0e', '764d60fda655')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
