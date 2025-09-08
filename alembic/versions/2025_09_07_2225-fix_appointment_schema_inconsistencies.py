"""Fix appointment schema inconsistencies

Revision ID: fix_appointment_schema
Revises: latest
Create Date: 2025-09-07 22:17:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers
revision = 'fix_appointment_schema'
down_revision = '115422716842'  # add_admin_authentication_system
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema fixes for appointments table"""
    
    # 🔧 1. UNIFICAR CAMPOS DE PREÇO
    # =================================
    
    # Primeiro, criar coluna temporária para consolidar preços
    op.add_column('appointments', sa.Column('price_temp', sa.Numeric(10, 2), nullable=True))
    
    # Consolidar dados: price_at_booking tem prioridade, senão usa price
    op.execute("""
        UPDATE appointments 
        SET price_temp = COALESCE(price_at_booking, price, 0.00)
        WHERE price_temp IS NULL
    """)
    
    # Remover colunas antigas
    op.drop_column('appointments', 'price_at_booking')
    op.drop_column('appointments', 'price')
    
    # Renomear coluna temporária para price
    op.alter_column('appointments', 'price_temp', new_column_name='price')
    
    # Adicionar constraint de não-nulo e default
    op.alter_column('appointments', 'price', nullable=False, server_default='0.00')
    
    
    # 🔧 2. PADRONIZAR CAMPO DURAÇÃO  
    # ================================
    
    # Adicionar nova coluna duration_minutes
    op.add_column('appointments', sa.Column('duration_minutes', sa.Integer(), nullable=True, default=60))
    
    # Migrar dados da coluna duration
    op.execute("""
        UPDATE appointments 
        SET duration_minutes = COALESCE(duration, 60)
        WHERE duration_minutes IS NULL
    """)
    
    # Remover coluna antiga
    op.drop_column('appointments', 'duration')
    
    # Tornar duration_minutes não-nulo
    op.alter_column('appointments', 'duration_minutes', nullable=False, server_default='60')
    
    
    # 🔧 3. MELHORAR CAMPOS EXISTENTES
    # =================================
    
    # Melhorar precision do campo price se necessário
    op.alter_column('appointments', 'price', type_=sa.Numeric(10, 2))
    
    # Garantir que end_time seja calculado automaticamente (trigger SQL)
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_appointment_end_time()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Calcular end_time automaticamente baseado em date_time + duration_minutes
            IF NEW.date_time IS NOT NULL AND NEW.duration_minutes IS NOT NULL THEN
                NEW.end_time = NEW.date_time + (NEW.duration_minutes || ' minutes')::INTERVAL;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        DROP TRIGGER IF EXISTS appointment_end_time_trigger ON appointments;
        CREATE TRIGGER appointment_end_time_trigger
            BEFORE INSERT OR UPDATE ON appointments
            FOR EACH ROW
            EXECUTE FUNCTION calculate_appointment_end_time();
    """)
    
    # Recalcular todos os end_time existentes
    op.execute("""
        UPDATE appointments 
        SET end_time = date_time + (duration_minutes || ' minutes')::INTERVAL
        WHERE date_time IS NOT NULL AND duration_minutes IS NOT NULL
    """)
    
    
    # 🔧 4. ADICIONAR ÍNDICES PARA PERFORMANCE
    # =========================================
    
    op.create_index('idx_appointments_date_time', 'appointments', ['date_time'])
    op.create_index('idx_appointments_status', 'appointments', ['status'])
    op.create_index('idx_appointments_user_date', 'appointments', ['user_id', 'date_time'])
    op.create_index('idx_appointments_price', 'appointments', ['price'])


def downgrade():
    """Reverter alterações do schema"""
    
    # Remover índices
    op.drop_index('idx_appointments_price')
    op.drop_index('idx_appointments_user_date')
    op.drop_index('idx_appointments_status')
    op.drop_index('idx_appointments_date_time')
    
    # Remover trigger
    op.execute("DROP TRIGGER IF EXISTS appointment_end_time_trigger ON appointments")
    op.execute("DROP FUNCTION IF EXISTS calculate_appointment_end_time()")
    
    # Reverter campos
    op.add_column('appointments', sa.Column('duration', sa.Integer(), default=60))
    op.add_column('appointments', sa.Column('price_at_booking', sa.Numeric()))
    
    # Migrar dados de volta
    op.execute("UPDATE appointments SET duration = duration_minutes")
    op.execute("UPDATE appointments SET price_at_booking = price")
    
    # Remover colunas novas
    op.drop_column('appointments', 'duration_minutes')
    op.alter_column('appointments', 'price', server_default=None)
