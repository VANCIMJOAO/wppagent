"""merge_heads_for_pf002

Revision ID: 69bb14c78865
Revises: hf001_consolidate_drift, hf001_simplified_cleanup
Create Date: 2025-09-14 19:06:55.121540-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69bb14c78865'
down_revision = ('hf001_consolidate_drift', 'hf001_simplified_cleanup')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
