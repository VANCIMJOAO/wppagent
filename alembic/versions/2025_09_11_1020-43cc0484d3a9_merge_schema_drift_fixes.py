"""merge_schema_drift_fixes

Revision ID: 43cc0484d3a9
Revises: 7ed1cc4d4764, c20ea17a14b9
Create Date: 2025-09-11 10:20:47.089693-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43cc0484d3a9'
down_revision = ('7ed1cc4d4764', 'c20ea17a14b9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
