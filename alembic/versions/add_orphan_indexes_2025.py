"""Add orphan indexes 2025

Revision ID: add_orphan_indexes_2025
Revises: 
Create Date: 2025-09-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_orphan_indexes_2025'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add orphan indexes for 2025"""
    pass


def downgrade() -> None:
    """Remove orphan indexes for 2025"""
    pass