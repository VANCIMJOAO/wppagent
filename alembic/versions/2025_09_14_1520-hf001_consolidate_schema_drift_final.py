"""HF-001: Consolidate schema drift final

Revision ID: hf001_consolidate_drift
Revises: pd001_performance_idx
Create Date: 2025-09-14 15:20:05.613706-03:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'hf001_consolidate_drift'
down_revision = 'pd001_performance_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HF-001: Consolidar schema drift - ordem correta para evitar dependências
    
    # 1. Primeiro remover tabelas de backup e índices órfãos (se existirem)
    try:
        op.drop_table('login_attempts_backup_pd002')
    except:
        pass
    try:
        op.drop_table('login_sessions_backup_pd002')
    except:
        pass 
    try:
        op.drop_table('refresh_tokens_backup_pd002')
    except:
        pass
    
    # 2. Remover índices antes das tabelas
    op.drop_index('idx_role_permissions_permission', table_name='role_permissions', if_exists=True)
    op.drop_index('idx_role_permissions_role_assigned', table_name='role_permissions', if_exists=True)
    op.drop_index('idx_user_roles_expires', table_name='user_roles', if_exists=True)
    op.drop_index('idx_user_roles_user_assigned', table_name='user_roles', if_exists=True)
    op.drop_index('idx_rbac_audit_action_resource', table_name='rbac_audit_logs', if_exists=True)
    op.drop_index('idx_rbac_audit_user_time', table_name='rbac_audit_logs', if_exists=True)
    op.drop_index('ix_rbac_audit_logs_timestamp', table_name='rbac_audit_logs', if_exists=True)
    op.drop_index('ix_rbac_audit_logs_user_id', table_name='rbac_audit_logs', if_exists=True)
    op.drop_index('ix_rbac_users_email', table_name='rbac_users', if_exists=True)
    op.drop_index('ix_rbac_users_username', table_name='rbac_users', if_exists=True)
    
    # 3. Remover tabelas filhas primeiro (que têm foreign keys)
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('rbac_audit_logs')
    
    # 4. Depois remover tabelas pai
    op.drop_table('rbac_roles')
    op.drop_table('rbac_permissions')
    op.drop_table('rbac_users')
    op.drop_index('idx_appointments_business_datetime', table_name='appointments')
    op.drop_index('idx_appointments_date_time', table_name='appointments')
    op.drop_index('idx_appointments_datetime_status', table_name='appointments')
    op.drop_index('idx_appointments_price', table_name='appointments')
    op.drop_index('idx_appointments_status', table_name='appointments')
    op.drop_index('idx_appointments_user_date', table_name='appointments')
    op.drop_index('idx_appointments_user_status_date', table_name='appointments')
    op.create_index(op.f('ix_appointments_date_time'), 'appointments', ['date_time'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)
    op.alter_column('auth_users', 'phone',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=20),
               existing_nullable=True)
    op.alter_column('auth_users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('auth_users', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('auth_users', 'last_login',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.drop_constraint('auth_users_email_key', 'auth_users', type_='unique')
    op.drop_index('idx_auth_users_email_active', table_name='auth_users')
    op.drop_index('idx_auth_users_last_login', table_name='auth_users', postgresql_where='(last_login IS NOT NULL)')
    op.drop_index('idx_auth_users_role_active', table_name='auth_users', postgresql_where='(is_active = true)')
    op.create_index(op.f('ix_auth_users_email'), 'auth_users', ['email'], unique=True)
    op.create_index(op.f('ix_auth_users_id'), 'auth_users', ['id'], unique=False)
    op.alter_column('business_hours', 'open_time',
               existing_type=postgresql.TIME(),
               type_=sa.String(length=5),
               existing_nullable=True)
    op.alter_column('business_hours', 'close_time',
               existing_type=postgresql.TIME(),
               type_=sa.String(length=5),
               existing_nullable=True)
    op.alter_column('business_hours', 'break_start_time',
               existing_type=postgresql.TIME(),
               type_=sa.String(length=5),
               existing_nullable=True)
    op.alter_column('business_hours', 'break_end_time',
               existing_type=postgresql.TIME(),
               type_=sa.String(length=5),
               existing_nullable=True)
    op.drop_index('idx_business_hours_business_day', table_name='business_hours')
    op.create_index(op.f('ix_business_hours_id'), 'business_hours', ['id'], unique=False)
    op.create_foreign_key(None, 'business_hours', 'businesses', ['business_id'], ['id'])
    op.alter_column('business_policies', 'policy_type',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=100),
               existing_nullable=False)
    op.alter_column('business_policies', 'title',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.drop_index('idx_business_policies_business_type', table_name='business_policies')
    op.drop_index('idx_business_policies_type_active', table_name='business_policies')
    op.create_index(op.f('ix_business_policies_id'), 'business_policies', ['id'], unique=False)
    op.create_foreign_key(None, 'business_policies', 'businesses', ['business_id'], ['id'])
    op.drop_index('idx_conversations_status_last_message', table_name='conversations', postgresql_where="((status)::text = ANY ((ARRAY['active'::character varying, 'pending'::character varying])::text[]))")
    op.drop_index('idx_conversations_user_last_message', table_name='conversations')
    op.drop_column('conversations', 'phone_number')
    op.drop_column('conversations', 'context')
    op.drop_index('idx_messages_conversation_count', table_name='messages', postgresql_where="((direction)::text = 'in'::text)")
    op.drop_index('idx_messages_conversation_created', table_name='messages')
    op.drop_index('idx_messages_user_created', table_name='messages')
    op.drop_index('messages_conv_dir_created', table_name='messages')
    op.alter_column('payment_methods', 'name',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=255),
               existing_nullable=False)
    op.drop_index('idx_payment_methods_active_order', table_name='payment_methods')
    op.drop_index('idx_payment_methods_business', table_name='payment_methods')
    op.create_index(op.f('ix_payment_methods_id'), 'payment_methods', ['id'], unique=False)
    op.create_foreign_key(None, 'payment_methods', 'businesses', ['business_id'], ['id'])
    op.create_foreign_key(None, 'push_subscriptions', 'admin_users', ['admin_user_id'], ['id'])
    op.alter_column('services', 'price',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.String(length=20),
               existing_nullable=True)
    op.drop_index('idx_services_business_active', table_name='services', postgresql_where='(is_active = true)')
    op.drop_column('services', 'duration')
    op.alter_column('user_sessions', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('user_sessions', 'expires_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)
    op.alter_column('user_sessions', 'ip_address',
               existing_type=postgresql.INET(),
               type_=sa.String(length=45),
               existing_nullable=True)
    op.drop_index('idx_user_sessions_expired', table_name='user_sessions', postgresql_where='(is_active = true)')
    op.drop_index('idx_user_sessions_session_id', table_name='user_sessions')
    op.drop_index('idx_user_sessions_user_active', table_name='user_sessions', postgresql_where='(user_id IS NOT NULL)')
    op.drop_index('idx_user_sessions_user_id', table_name='user_sessions')
    op.drop_constraint('user_sessions_session_id_key', 'user_sessions', type_='unique')
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_id'), 'user_sessions', ['session_id'], unique=True)
    op.drop_constraint('user_sessions_user_id_fkey', 'user_sessions', type_='foreignkey')
    op.create_foreign_key(None, 'user_sessions', 'users', ['user_id'], ['id'])
    op.alter_column('users', 'telefone',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=20),
               existing_nullable=True)
    op.drop_index('idx_users_telefone', table_name='users')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_users_telefone', 'users', ['telefone'], unique=False)
    op.alter_column('users', 'telefone',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
    op.drop_constraint(None, 'user_sessions', type_='foreignkey')
    op.create_foreign_key('user_sessions_user_id_fkey', 'user_sessions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_user_sessions_session_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.create_unique_constraint('user_sessions_session_id_key', 'user_sessions', ['session_id'], postgresql_nulls_not_distinct=False)
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active', sa.text('expires_at DESC')], unique=False, postgresql_where='(user_id IS NOT NULL)')
    op.create_index('idx_user_sessions_session_id', 'user_sessions', ['session_id'], unique=False)
    op.create_index('idx_user_sessions_expired', 'user_sessions', ['expires_at'], unique=False, postgresql_where='(is_active = true)')
    op.alter_column('user_sessions', 'ip_address',
               existing_type=sa.String(length=45),
               type_=postgresql.INET(),
               existing_nullable=True)
    op.alter_column('user_sessions', 'expires_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False)
    op.alter_column('user_sessions', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.add_column('services', sa.Column('duration', sa.INTEGER(), server_default=sa.text('60'), autoincrement=False, nullable=True))
    op.create_index('idx_services_business_active', 'services', ['business_id', 'is_active'], unique=False, postgresql_where='(is_active = true)')
    op.alter_column('services', 'price',
               existing_type=sa.String(length=20),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.drop_constraint(None, 'push_subscriptions', type_='foreignkey')
    op.drop_constraint(None, 'payment_methods', type_='foreignkey')
    op.drop_index(op.f('ix_payment_methods_id'), table_name='payment_methods')
    op.create_index('idx_payment_methods_business', 'payment_methods', ['business_id', 'is_active'], unique=False)
    op.create_index('idx_payment_methods_active_order', 'payment_methods', ['business_id', 'is_active', 'display_order'], unique=False)
    op.alter_column('payment_methods', 'name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
    op.create_index('messages_conv_dir_created', 'messages', ['conversation_id', 'direction', 'created_at'], unique=False)
    op.create_index('idx_messages_user_created', 'messages', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_messages_conversation_created', 'messages', ['conversation_id', sa.text('created_at DESC')], unique=False)
    op.create_index('idx_messages_conversation_count', 'messages', ['conversation_id'], unique=False, postgresql_where="((direction)::text = 'in'::text)")
    op.add_column('conversations', sa.Column('context', sa.TEXT(), server_default=sa.text("'{}'::text"), autoincrement=False, nullable=True))
    op.add_column('conversations', sa.Column('phone_number', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.create_index('idx_conversations_user_last_message', 'conversations', ['user_id', sa.text('last_message_at DESC')], unique=False)
    op.create_index('idx_conversations_status_last_message', 'conversations', ['status', sa.text('last_message_at DESC')], unique=False, postgresql_where="((status)::text = ANY ((ARRAY['active'::character varying, 'pending'::character varying])::text[]))")
    op.drop_constraint(None, 'business_policies', type_='foreignkey')
    op.drop_index(op.f('ix_business_policies_id'), table_name='business_policies')
    op.create_index('idx_business_policies_type_active', 'business_policies', ['business_id', 'policy_type', 'is_active'], unique=False)
    op.create_index('idx_business_policies_business_type', 'business_policies', ['business_id', 'policy_type', 'is_active'], unique=False)
    op.alter_column('business_policies', 'title',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
    op.alter_column('business_policies', 'policy_type',
               existing_type=sa.String(length=100),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
    op.drop_constraint(None, 'business_hours', type_='foreignkey')
    op.drop_index(op.f('ix_business_hours_id'), table_name='business_hours')
    op.create_index('idx_business_hours_business_day', 'business_hours', ['business_id', 'day_of_week'], unique=False)
    op.alter_column('business_hours', 'break_end_time',
               existing_type=sa.String(length=5),
               type_=postgresql.TIME(),
               existing_nullable=True)
    op.alter_column('business_hours', 'break_start_time',
               existing_type=sa.String(length=5),
               type_=postgresql.TIME(),
               existing_nullable=True)
    op.alter_column('business_hours', 'close_time',
               existing_type=sa.String(length=5),
               type_=postgresql.TIME(),
               existing_nullable=True)
    op.alter_column('business_hours', 'open_time',
               existing_type=sa.String(length=5),
               type_=postgresql.TIME(),
               existing_nullable=True)
    op.drop_index(op.f('ix_auth_users_id'), table_name='auth_users')
    op.drop_index(op.f('ix_auth_users_email'), table_name='auth_users')
    op.create_index('idx_auth_users_role_active', 'auth_users', ['role'], unique=False, postgresql_where='(is_active = true)')
    op.create_index('idx_auth_users_last_login', 'auth_users', [sa.text('last_login DESC')], unique=False, postgresql_where='(last_login IS NOT NULL)')
    op.create_index('idx_auth_users_email_active', 'auth_users', ['email', 'is_active'], unique=False)
    op.create_unique_constraint('auth_users_email_key', 'auth_users', ['email'], postgresql_nulls_not_distinct=False)
    op.alter_column('auth_users', 'last_login',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.alter_column('auth_users', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('auth_users', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.alter_column('auth_users', 'phone',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)
    op.drop_index(op.f('ix_appointments_status'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_date_time'), table_name='appointments')
    op.create_index('idx_appointments_user_status_date', 'appointments', ['user_id', 'status', sa.text('date_time DESC')], unique=False)
    op.create_index('idx_appointments_user_date', 'appointments', ['user_id', 'date_time'], unique=False)
    op.create_index('idx_appointments_status', 'appointments', ['status'], unique=False)
    op.create_index('idx_appointments_price', 'appointments', ['price'], unique=False)
    op.create_index('idx_appointments_datetime_status', 'appointments', ['date_time', 'status'], unique=False)
    op.create_index('idx_appointments_date_time', 'appointments', ['date_time'], unique=False)
    op.create_index('idx_appointments_business_datetime', 'appointments', ['business_id', sa.text('date_time DESC')], unique=False)
    op.create_table('rbac_users',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('rbac_users_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('full_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('password_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('is_verified', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('requires_2fa', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('two_factor_secret', sa.VARCHAR(length=32), autoincrement=False, nullable=True),
    sa.Column('backup_codes', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('last_login', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('login_attempts', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('locked_until', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='rbac_users_pkey'),
    sa.UniqueConstraint('email', name='rbac_users_email_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    sa.UniqueConstraint('username', name='rbac_users_username_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_rbac_users_username', 'rbac_users', ['username'], unique=False)
    op.create_index('ix_rbac_users_email', 'rbac_users', ['email'], unique=False)
    op.create_table('user_roles',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('assigned_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('assigned_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['assigned_by'], ['rbac_users.id'], name='user_roles_assigned_by_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['role_id'], ['rbac_roles.id'], name='user_roles_role_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['rbac_users.id'], name='user_roles_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'role_id', name='user_roles_pkey')
    )
    op.create_index('idx_user_roles_user_assigned', 'user_roles', ['user_id', sa.text('assigned_at DESC')], unique=False)
    op.create_index('idx_user_roles_expires', 'user_roles', ['expires_at'], unique=False)
    op.create_table('refresh_tokens_backup_pd002',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('token_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('admin_user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('is_revoked', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('backup_created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True)
    )
    op.create_table('rbac_permissions',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('rbac_permissions_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('permission_type', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('category', postgresql.ENUM('DASHBOARD', 'APPOINTMENTS', 'CONVERSATIONS', 'CLIENTS', 'REPORTS', 'SYSTEM', name='permissioncategory'), autoincrement=False, nullable=False),
    sa.Column('risk_level', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), autoincrement=False, nullable=False),
    sa.Column('requires_2fa', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='rbac_permissions_pkey'),
    sa.UniqueConstraint('permission_type', name='rbac_permissions_permission_type_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_table('rbac_audit_logs',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('action', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('resource_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('resource_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('details', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=45), autoincrement=False, nullable=True),
    sa.Column('user_agent', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('success', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('timestamp', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['rbac_users.id'], name='rbac_audit_logs_user_id_fkey', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name='rbac_audit_logs_pkey')
    )
    op.create_index('ix_rbac_audit_logs_user_id', 'rbac_audit_logs', ['user_id'], unique=False)
    op.create_index('ix_rbac_audit_logs_timestamp', 'rbac_audit_logs', ['timestamp'], unique=False)
    op.create_index('idx_rbac_audit_user_time', 'rbac_audit_logs', ['user_id', sa.text('timestamp DESC')], unique=False, postgresql_where='(user_id IS NOT NULL)')
    op.create_index('idx_rbac_audit_action_resource', 'rbac_audit_logs', ['action', 'resource_type', sa.text('timestamp DESC')], unique=False)
    op.create_table('rbac_roles',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('rbac_roles_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('role_type', postgresql.ENUM('SYSTEM', 'CUSTOM', 'SUPER_ADMIN', 'ADMIN', 'MANAGER', 'USER', 'GUEST', 'OPERATOR', 'VIEWER', name='roletype'), autoincrement=False, nullable=True),
    sa.Column('is_system_role', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('can_be_deleted', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='rbac_roles_pkey'),
    sa.UniqueConstraint('name', name='rbac_roles_name_key', postgresql_include=[], postgresql_nulls_not_distinct=False),
    postgresql_ignore_search_path=False
    )
    op.create_table('login_sessions_backup_pd002',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('session_token', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('admin_user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=45), autoincrement=False, nullable=True),
    sa.Column('user_agent', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('backup_created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True)
    )
    op.create_table('role_permissions',
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('permission_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('assigned_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('assigned_by', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['assigned_by'], ['rbac_users.id'], name='role_permissions_assigned_by_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['permission_id'], ['rbac_permissions.id'], name='role_permissions_permission_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['rbac_roles.id'], name='role_permissions_role_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_id', 'permission_id', name='role_permissions_pkey')
    )
    op.create_index('idx_role_permissions_role_assigned', 'role_permissions', ['role_id', sa.text('assigned_at DESC')], unique=False)
    op.create_index('idx_role_permissions_permission', 'role_permissions', ['permission_id', sa.text('assigned_at DESC')], unique=False)
    op.create_table('login_attempts_backup_pd002',
    sa.Column('id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('ip_address', postgresql.INET(), autoincrement=False, nullable=True),
    sa.Column('success', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('attempted_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('error_message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('backup_created_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
