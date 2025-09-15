"""add_push_notifications_tables

Revision ID: push_notifications_001
Revises: add_performance_indexes
Create Date: 2025-01-11 19:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "push_notifications_001"
down_revision = "d08ef6b15ecb"  # add_performance_indexes
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create push notifications tables"""

    # Create push_subscriptions table
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "admin_user_id",
            sa.Integer(),
            sa.ForeignKey("admin_users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("endpoint", sa.String(500), nullable=False, unique=True),
        sa.Column("p256dh_key", sa.String(255), nullable=False),
        sa.Column("auth_key", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), default=True, index=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # Create push_notifications table (log)
    op.create_table(
        "push_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            sa.ForeignKey("push_subscriptions.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("data", sa.JSON()),
        sa.Column("status", sa.String(50), default="sent"),
        sa.Column("error_message", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop push notifications tables"""
    op.drop_table("push_notifications")
    op.drop_table("push_subscriptions")
