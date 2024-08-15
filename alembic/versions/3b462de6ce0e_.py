"""empty message

Revision ID: 3b462de6ce0e
Revises: 2afb0259557d, f35492571c7a
Create Date: 2024-08-15 14:07:00.882133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b462de6ce0e'
down_revision: Union[str, None] = ('2afb0259557d', 'f35492571c7a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
