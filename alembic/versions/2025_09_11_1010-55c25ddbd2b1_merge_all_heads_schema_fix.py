"""merge_all_heads_schema_fix

Revision ID: 55c25ddbd2b1
Revises: remove_duplicate_indexes_2025, remove_duplicate_admin_2025
Create Date: 2025-09-11 10:10:05.306247-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55c25ddbd2b1'
down_revision = ('remove_duplicate_indexes_2025', 'remove_duplicate_admin_2025')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
