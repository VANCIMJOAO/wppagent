"""merge_rbac_and_push_notifications

Revision ID: d300a27c12cf
Revises: push_notifications_001, rbac_2025
Create Date: 2025-09-08 14:02:50.652902-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd300a27c12cf'
down_revision = ('push_notifications_001', 'rbac_2025')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
