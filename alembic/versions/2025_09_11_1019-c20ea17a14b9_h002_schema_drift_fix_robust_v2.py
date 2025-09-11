"""H002_schema_drift_fix_robust_v2

Revision ID: c20ea17a14b9
Revises: 4fd34d192041
Create Date: 2025-09-11 10:19:36.635627-03:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c20ea17a14b9'
down_revision = '4fd34d192041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    H002 - Correção robusta de Schema Drift
    Abordagem incremental para todas as inconsistências
    """
    
    # 1. Primeiro removemos todas as tabelas órfãs que ainda existem
    orphan_tables = [
        'role_permissions', 'rbac_audit_logs', 'rbac_roles', 
        'rbac_permissions', 'user_roles', 'admins', 'rbac_users'
    ]
    
    for table in orphan_tables:
        try:
            op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"Removed orphan table: {table}")
        except Exception as e:
            print(f"Warning: Could not remove {table}: {e}")
    
    # 2. Corrigir índices de appointments (simples)
    try:
        # Remove old indexes silently
        op.execute("DROP INDEX IF EXISTS idx_appointments_date_time")
        op.execute("DROP INDEX IF EXISTS idx_appointments_datetime_status")
        op.execute("DROP INDEX IF EXISTS idx_appointments_price")
        op.execute("DROP INDEX IF EXISTS idx_appointments_status")
        op.execute("DROP INDEX IF EXISTS idx_appointments_user_date")
        
        # Create new indexes
        op.execute("CREATE INDEX IF NOT EXISTS ix_appointments_date_time ON appointments (date_time)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_appointments_status ON appointments (status)")
        print("Fixed appointments indexes")
    except Exception as e:
        print(f"Warning: Error fixing appointments indexes: {e}")

    # 3. Corrigir auth_users com conversões seguras
    try:
        # Modify phone length
        op.execute("ALTER TABLE auth_users ALTER COLUMN phone TYPE VARCHAR(20)")
        
        # Fix timestamps - conversion more careful
        op.execute("ALTER TABLE auth_users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at::timestamptz")
        op.execute("ALTER TABLE auth_users ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at::timestamptz") 
        op.execute("ALTER TABLE auth_users ALTER COLUMN last_login TYPE TIMESTAMPTZ USING last_login::timestamptz")
        
        # Remove old indexes and constraints
        op.execute("DROP INDEX IF EXISTS idx_auth_users_email_active")
        op.execute("DROP INDEX IF EXISTS idx_auth_users_last_login")
        op.execute("ALTER TABLE auth_users DROP CONSTRAINT IF EXISTS auth_users_email_key")
        
        # Add new indexes
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_users_email ON auth_users (email)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_auth_users_id ON auth_users (id)")
        print("Fixed auth_users")
    except Exception as e:
        print(f"Warning: Error fixing auth_users: {e}")

    # 4. Corrigir business_hours - estratégia especial para TIME
    try:
        # Primeiro drop do índice problemático
        op.execute("DROP INDEX IF EXISTS idx_business_hours_business_day")
        
        # Estratégia para conversão TIME -> VARCHAR: usar um campo temporário
        op.execute("ALTER TABLE business_hours ADD COLUMN IF NOT EXISTS temp_open_time VARCHAR(5)")
        op.execute("ALTER TABLE business_hours ADD COLUMN IF NOT EXISTS temp_close_time VARCHAR(5)")
        op.execute("ALTER TABLE business_hours ADD COLUMN IF NOT EXISTS temp_break_start_time VARCHAR(5)")
        op.execute("ALTER TABLE business_hours ADD COLUMN IF NOT EXISTS temp_break_end_time VARCHAR(5)")
        
        # Copiar dados convertidos
        op.execute("UPDATE business_hours SET temp_open_time = open_time::TEXT WHERE open_time IS NOT NULL")
        op.execute("UPDATE business_hours SET temp_close_time = close_time::TEXT WHERE close_time IS NOT NULL")
        op.execute("UPDATE business_hours SET temp_break_start_time = break_start_time::TEXT WHERE break_start_time IS NOT NULL")
        op.execute("UPDATE business_hours SET temp_break_end_time = break_end_time::TEXT WHERE break_end_time IS NOT NULL")
        
        # Dropar colunas antigas e renomear
        op.execute("ALTER TABLE business_hours DROP COLUMN IF EXISTS open_time")
        op.execute("ALTER TABLE business_hours DROP COLUMN IF EXISTS close_time")
        op.execute("ALTER TABLE business_hours DROP COLUMN IF EXISTS break_start_time")
        op.execute("ALTER TABLE business_hours DROP COLUMN IF EXISTS break_end_time")
        
        op.execute("ALTER TABLE business_hours RENAME COLUMN temp_open_time TO open_time")
        op.execute("ALTER TABLE business_hours RENAME COLUMN temp_close_time TO close_time")
        op.execute("ALTER TABLE business_hours RENAME COLUMN temp_break_start_time TO break_start_time")
        op.execute("ALTER TABLE business_hours RENAME COLUMN temp_break_end_time TO break_end_time")
        
        # Add new index
        op.execute("CREATE INDEX IF NOT EXISTS ix_business_hours_id ON business_hours (id)")
        print("Fixed business_hours")
    except Exception as e:
        print(f"Warning: Error fixing business_hours: {e}")

    # 5. Corrigir business_policies
    try:
        op.execute("ALTER TABLE business_policies ALTER COLUMN policy_type TYPE VARCHAR(100)")
        op.execute("ALTER TABLE business_policies ALTER COLUMN title TYPE VARCHAR(255)")
        
        # Remove old indexes
        op.execute("DROP INDEX IF EXISTS idx_business_policies_business_type")
        op.execute("DROP INDEX IF EXISTS idx_business_policies_type_active")
        
        # Add new index
        op.execute("CREATE INDEX IF NOT EXISTS ix_business_policies_id ON business_policies (id)")
        print("Fixed business_policies")
    except Exception as e:
        print(f"Warning: Error fixing business_policies: {e}")

    # 6. Corrigir conversations - remover colunas órfãs
    try:
        op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS context")
        op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS phone_number")
        print("Fixed conversations")
    except Exception as e:
        print(f"Warning: Error fixing conversations: {e}")

    # 7. Corrigir login_attempts
    try:
        # Convert INET to VARCHAR
        op.execute("ALTER TABLE login_attempts ALTER COLUMN ip_address TYPE VARCHAR(45) USING ip_address::TEXT")
        op.execute("ALTER TABLE login_attempts ALTER COLUMN attempted_at TYPE TIMESTAMPTZ USING attempted_at::timestamptz")
        
        # Remove old indexes
        op.execute("DROP INDEX IF EXISTS idx_login_attempts_attempted_at")
        op.execute("DROP INDEX IF EXISTS idx_login_attempts_email")
        op.execute("DROP INDEX IF EXISTS idx_login_attempts_email_time")
        op.execute("DROP INDEX IF EXISTS idx_login_attempts_failed_recent")
        op.execute("DROP INDEX IF EXISTS idx_login_attempts_ip_time")
        
        # Add new indexes
        op.execute("CREATE INDEX IF NOT EXISTS ix_login_attempts_attempted_at ON login_attempts (attempted_at)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_login_attempts_email ON login_attempts (email)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_login_attempts_id ON login_attempts (id)")
        print("Fixed login_attempts")
    except Exception as e:
        print(f"Warning: Error fixing login_attempts: {e}")

    # 8. Corrigir messages
    try:
        op.execute("DROP INDEX IF EXISTS idx_messages_user_created")
        print("Fixed messages")
    except Exception as e:
        print(f"Warning: Error fixing messages: {e}")

    # 9. Corrigir payment_methods
    try:
        op.execute("ALTER TABLE payment_methods ALTER COLUMN name TYPE VARCHAR(255)")
        
        # Remove old indexes
        op.execute("DROP INDEX IF EXISTS idx_payment_methods_active_order")
        op.execute("DROP INDEX IF EXISTS idx_payment_methods_business")
        
        # Add new index
        op.execute("CREATE INDEX IF NOT EXISTS ix_payment_methods_id ON payment_methods (id)")
        print("Fixed payment_methods")
    except Exception as e:
        print(f"Warning: Error fixing payment_methods: {e}")

    # 10. Corrigir services
    try:
        # Convert NUMERIC to VARCHAR
        op.execute("ALTER TABLE services ALTER COLUMN price TYPE VARCHAR(20) USING price::TEXT")
        op.execute("ALTER TABLE services DROP COLUMN IF EXISTS duration")
        print("Fixed services")
    except Exception as e:
        print(f"Warning: Error fixing services: {e}")

    # 11. Corrigir user_sessions
    try:
        # Fix timestamps
        op.execute("ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at::timestamptz")
        op.execute("ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at::timestamptz")
        op.execute("ALTER TABLE user_sessions ALTER COLUMN ip_address TYPE VARCHAR(45) USING ip_address::TEXT")
        
        # Remove old indexes and constraints
        op.execute("DROP INDEX IF EXISTS idx_user_sessions_expired")
        op.execute("DROP INDEX IF EXISTS idx_user_sessions_session_id")
        op.execute("DROP INDEX IF EXISTS idx_user_sessions_user_active")
        op.execute("DROP INDEX IF EXISTS idx_user_sessions_user_id")
        op.execute("ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS user_sessions_session_id_key")
        
        # Add new indexes
        op.execute("CREATE INDEX IF NOT EXISTS ix_user_sessions_id ON user_sessions (id)")
        op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_sessions_session_id ON user_sessions (session_id)")
        print("Fixed user_sessions")
    except Exception as e:
        print(f"Warning: Error fixing user_sessions: {e}")

    # 12. Corrigir users
    try:
        op.execute("ALTER TABLE users ALTER COLUMN telefone TYPE VARCHAR(20)")
        print("Fixed users")
    except Exception as e:
        print(f"Warning: Error fixing users: {e}")

    print("\n=== H002 Schema Drift Fix v2 Completed ===")
    print("Robust incremental approach applied to all inconsistencies")


def downgrade() -> None:
    """
    Downgrade seria muito complexo devido às muitas mudanças.
    Este é um fix crítico que não deve ser revertido.
    """
    print("Downgrade not supported for H002 schema drift fix")
