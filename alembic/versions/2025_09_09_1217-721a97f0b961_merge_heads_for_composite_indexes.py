"""merge_heads_for_composite_indexes

Revision ID: 721a97f0b961
Revises: d300a27c12cf, rbac_system_2025
Create Date: 2025-09-09 12:17:28.864535-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '721a97f0b961'
down_revision = ('d300a27c12cf', 'rbac_system_2025')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
