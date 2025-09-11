"""Remove duplicate admin 2025

Revision ID: remove_duplicate_admin_2025
Revises: add_orphan_indexes_2025
Create Date: 2025-09-11 15:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_duplicate_admin_2025'
down_revision = 'add_orphan_indexes_2025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove duplicate admin entries for 2025"""
    pass


def downgrade() -> None:
    """Restore duplicate admin entries for 2025"""
    pass