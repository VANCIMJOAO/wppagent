"""
Adicionar tabelas para sistema dinâmico

Revision ID: 002_dynamic_system
Revises: 001_initial
Create Date: 2025-07-29 21:20:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_dynamic_system'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela company_info
    op.create_table('company_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('slogan', sa.String(length=500), nullable=True),
        sa.Column('about_us', sa.Text(), nullable=True),
        sa.Column('whatsapp_number', sa.String(length=20), nullable=True),
        sa.Column('phone_secondary', sa.String(length=20), nullable=True),
        sa.Column('email_contact', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('street_address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=50), server_default='Brasil'),
        sa.Column('instagram', sa.String(length=255), nullable=True),
        sa.Column('facebook', sa.String(length=255), nullable=True),
        sa.Column('linkedin', sa.String(length=255), nullable=True),
        sa.Column('welcome_message', sa.Text(), server_default='Olá! 👋 Bem-vindo à nossa empresa! Como posso ajudá-lo hoje?'),
        sa.Column('auto_response_enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_info_id'), 'company_info', ['id'], unique=False)

    # Criar tabela message_templates
    op.create_table('message_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('template_key', sa.String(length=100), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=True),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('available_variables', sa.JSON(), server_default='[]'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_templates_id'), 'message_templates', ['id'], unique=False)

    # Criar tabela bot_configurations
    op.create_table('bot_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('min_advance_booking_hours', sa.Integer(), server_default='2'),
        sa.Column('max_advance_booking_days', sa.Integer(), server_default='30'),
        sa.Column('auto_confirm_bookings', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('slot_duration_minutes', sa.Integer(), server_default='30'),
        sa.Column('break_between_appointments_minutes', sa.Integer(), server_default='0'),
        sa.Column('send_confirmation_messages', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('send_reminder_messages', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('reminder_hours_before', sa.Integer(), server_default='24'),
        sa.Column('max_retries_data_collection', sa.Integer(), server_default='3'),
        sa.Column('timeout_minutes_user_response', sa.Integer(), server_default='30'),
        sa.Column('enable_human_handoff', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('require_email', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('require_phone_confirmation', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('require_full_name', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bot_configurations_id'), 'bot_configurations', ['id'], unique=False)

    # Criar tabela available_slots
    op.create_table('available_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('slot_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('is_available', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('is_blocked', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('blocked_reason', sa.String(length=255), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('slot_time', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_available_slots_id'), 'available_slots', ['id'], unique=False)

    # Criar tabela customer_data_collection
    op.create_table('customer_data_collection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('collection_status', sa.String(length=20), server_default='incomplete'),
        sa.Column('has_name', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('has_email', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('has_phone', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('name_attempts', sa.Integer(), server_default='0'),
        sa.Column('email_attempts', sa.Integer(), server_default='0'),
        sa.Column('phone_attempts', sa.Integer(), server_default='0'),
        sa.Column('collection_method', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_data_collection_id'), 'customer_data_collection', ['id'], unique=False)

    # Criar tabela conversation_contexts
    op.create_table('conversation_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('current_state', sa.String(length=50), server_default='initial'),
        sa.Column('previous_state', sa.String(length=50), nullable=True),
        sa.Column('temp_data', sa.JSON(), server_default='{}'),
        sa.Column('collected_data', sa.JSON(), server_default='{}'),
        sa.Column('booking_data', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('awaiting_response', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('awaiting_response_for', sa.String(length=100), nullable=True),
        sa.Column('state_changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_contexts_id'), 'conversation_contexts', ['id'], unique=False)


def downgrade():
    # Remover tabelas na ordem reversa
    op.drop_index(op.f('ix_conversation_contexts_id'), table_name='conversation_contexts')
    op.drop_table('conversation_contexts')
    
    op.drop_index(op.f('ix_customer_data_collection_id'), table_name='customer_data_collection')
    op.drop_table('customer_data_collection')
    
    op.drop_index(op.f('ix_available_slots_id'), table_name='available_slots')  
    op.drop_table('available_slots')
    
    op.drop_index(op.f('ix_bot_configurations_id'), table_name='bot_configurations')
    op.drop_table('bot_configurations')
    
    op.drop_index(op.f('ix_message_templates_id'), table_name='message_templates')
    op.drop_table('message_templates')
    
    op.drop_index(op.f('ix_company_info_id'), table_name='company_info')
    op.drop_table('company_info')
