"""add rbac system tables

Revision ID: rbac_2025
Revises: 2025_09_08_1600-add_refresh_tokens  
Create Date: 2025-01-11 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision: str = 'rbac_2025'
down_revision: Union[str, None] = 'add_refresh_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rbac_roles table
    op.create_table('rbac_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role_type', sa.Enum('SYSTEM', 'CUSTOM', name='roletype'), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=False, default=False),
        sa.Column('can_be_deleted', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rbac_roles_name'), 'rbac_roles', ['name'], unique=True)

    # Create rbac_permissions table
    op.create_table('rbac_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('permission_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('DASHBOARD', 'APPOINTMENTS', 'CONVERSATIONS', 'CLIENTS', 'REPORTS', 'SYSTEM', name='permissioncategory'), nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=False),
        sa.Column('requires_2fa', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rbac_permissions_permission_type'), 'rbac_permissions', ['permission_type'], unique=True)

    # Create rbac_users table
    op.create_table('rbac_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('requires_2fa', sa.Boolean(), nullable=False, default=False),
        sa.Column('two_factor_secret', sa.String(length=32), nullable=True),
        sa.Column('backup_codes', sa.JSON(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rbac_users_username'), 'rbac_users', ['username'], unique=True)
    op.create_index(op.f('ix_rbac_users_email'), 'rbac_users', ['email'], unique=True)

    # Create role_permissions association table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['rbac_permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['rbac_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['rbac_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # Create user_roles association table
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['rbac_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['rbac_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['rbac_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create audit_logs table
    op.create_table('rbac_audit_logs',
        sa.Column('id', UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['rbac_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rbac_audit_logs_timestamp'), 'rbac_audit_logs', ['timestamp'])
    op.create_index(op.f('ix_rbac_audit_logs_user_id'), 'rbac_audit_logs', ['user_id'])


def downgrade() -> None:
    # Drop all RBAC tables in reverse order
    op.drop_table('rbac_audit_logs')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('rbac_users')
    op.drop_table('rbac_permissions')
    op.drop_table('rbac_roles')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS roletype CASCADE')
    op.execute('DROP TYPE IF EXISTS permissioncategory CASCADE')  
    op.execute('DROP TYPE IF EXISTS risklevel CASCADE')
