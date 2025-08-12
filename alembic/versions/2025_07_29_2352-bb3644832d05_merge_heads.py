"""merge_heads

Revision ID: bb3644832d05
Revises: 002_dynamic_system, 4af292c63277
Create Date: 2025-07-29 23:52:53.808953-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb3644832d05'
down_revision = ('002_dynamic_system', '4af292c63277')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
