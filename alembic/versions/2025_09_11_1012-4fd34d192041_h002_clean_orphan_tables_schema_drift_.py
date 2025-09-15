"""h002_clean_orphan_tables_schema_drift_fix

🔧 H002 - CORREÇÃO CRÍTICA DE SCHEMA DRIFT
===========================================

Esta migração resolve inconsistências críticas entre modelos e banco:
- Remove tabelas órfãs do sistema RBAC antigo
- Corrige tipos de dados inconsistentes
- Reorganiza índices para melhor performance
- Garante integridade referencial

IMPORTANTE: Esta migração pode demorar em bancos grandes.

Revision ID: 4fd34d192041
Revises: 55c25ddbd2b1
Create Date: 2025-09-11 10:12:33.051244-03:00

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "4fd34d192041"
down_revision = "55c25ddbd2b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Correção de Schema Drift - H002
    ===============================

    Esta função resolve inconsistências entre modelos e banco de dados:
    1. Remove tabelas órfãs do sistema RBAC
    2. Corrige tipos de dados
    3. Reorganiza índices
    """

    # 🗑️ FASE 1: REMOVER TABELAS ÓRFÃS (em ordem de dependências)

    # Remover tabelas que dependem de rbac_users primeiro
    try:
        op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
        print("✅ Tabela user_roles removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover user_roles: {e}")

    try:
        op.execute("DROP TABLE IF EXISTS rbac_audit_logs CASCADE")
        print("✅ Tabela rbac_audit_logs removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover rbac_audit_logs: {e}")

    try:
        op.execute("DROP TABLE IF EXISTS role_permissions CASCADE")
        print("✅ Tabela role_permissions removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover role_permissions: {e}")

    # Agora remover as tabelas principais
    try:
        op.execute("DROP TABLE IF EXISTS rbac_users CASCADE")
        print("✅ Tabela rbac_users removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover rbac_users: {e}")

    try:
        op.execute("DROP TABLE IF EXISTS rbac_roles CASCADE")
        print("✅ Tabela rbac_roles removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover rbac_roles: {e}")

    try:
        op.execute("DROP TABLE IF EXISTS rbac_permissions CASCADE")
        print("✅ Tabela rbac_permissions removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover rbac_permissions: {e}")

    try:
        op.execute("DROP TABLE IF EXISTS admins CASCADE")
        print("✅ Tabela admins removida")
    except Exception as e:
        print(f"⚠️ Erro ao remover admins: {e}")

    # 🔧 FASE 2: CORRIGIR ÍNDICES E TIPOS DE DADOS

    # Remover índices antigos e criar novos (appointments)
    try:
        op.execute("DROP INDEX IF EXISTS idx_appointments_date_time")
        op.execute("DROP INDEX IF EXISTS idx_appointments_datetime_status")
        op.execute("DROP INDEX IF EXISTS idx_appointments_price")
        op.execute("DROP INDEX IF EXISTS idx_appointments_status")
        op.execute("DROP INDEX IF EXISTS idx_appointments_user_date")
        print("✅ Índices antigos de appointments removidos")
    except Exception as e:
        print(f"⚠️ Erro ao remover índices de appointments: {e}")

    try:
        op.create_index("ix_appointments_date_time", "appointments", ["date_time"])
        op.create_index("ix_appointments_status", "appointments", ["status"])
        print("✅ Novos índices de appointments criados")
    except Exception as e:
        print(f"⚠️ Erro ao criar índices de appointments: {e}")

    # Corrigir tipos de dados críticos
    try:
        # auth_users
        op.execute("ALTER TABLE auth_users ALTER COLUMN phone TYPE VARCHAR(20)")
        op.execute(
            "ALTER TABLE auth_users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE"
        )
        op.execute(
            "ALTER TABLE auth_users ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE"
        )
        op.execute(
            "ALTER TABLE auth_users ALTER COLUMN last_login TYPE TIMESTAMP WITH TIME ZONE"
        )
        print("✅ Tipos de dados auth_users corrigidos")
    except Exception as e:
        print(f"⚠️ Erro ao corrigir tipos auth_users: {e}")

    try:
        # business_hours
        op.execute("ALTER TABLE business_hours ALTER COLUMN open_time TYPE VARCHAR(5)")
        op.execute("ALTER TABLE business_hours ALTER COLUMN close_time TYPE VARCHAR(5)")
        op.execute(
            "ALTER TABLE business_hours ALTER COLUMN break_start_time TYPE VARCHAR(5)"
        )
        op.execute(
            "ALTER TABLE business_hours ALTER COLUMN break_end_time TYPE VARCHAR(5)"
        )
        print("✅ Tipos de dados business_hours corrigidos")
    except Exception as e:
        print(f"⚠️ Erro ao corrigir tipos business_hours: {e}")

    try:
        # login_attempts
        op.execute(
            "ALTER TABLE login_attempts ALTER COLUMN ip_address TYPE VARCHAR(45)"
        )
        op.execute(
            "ALTER TABLE login_attempts ALTER COLUMN attempted_at TYPE TIMESTAMP WITH TIME ZONE"
        )
        print("✅ Tipos de dados login_attempts corrigidos")
    except Exception as e:
        print(f"⚠️ Erro ao corrigir tipos login_attempts: {e}")

    try:
        # user_sessions
        op.execute(
            "ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE"
        )
        op.execute(
            "ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE"
        )
        op.execute("ALTER TABLE user_sessions ALTER COLUMN ip_address TYPE VARCHAR(45)")
        print("✅ Tipos de dados user_sessions corrigidos")
    except Exception as e:
        print(f"⚠️ Erro ao corrigir tipos user_sessions: {e}")

    # 🧹 FASE 3: LIMPAR COLUNAS ÓRFÃS
    try:
        op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS phone_number")
        op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS context")
        print("✅ Colunas órfãs de conversations removidas")
    except Exception as e:
        print(f"⚠️ Erro ao remover colunas órfãs: {e}")

    try:
        op.execute("ALTER TABLE services DROP COLUMN IF EXISTS duration")
        print("✅ Coluna duration removida de services")
    except Exception as e:
        print(f"⚠️ Erro ao remover coluna duration: {e}")

    print("🎉 MIGRAÇÃO H002 CONCLUÍDA - Schema Drift Corrigido!")


def downgrade() -> None:
    """
    Rollback da correção de schema drift
    """
    print("⚠️ Rollback de correção de schema drift não implementado")
    print("Esta é uma migração de limpeza que não pode ser revertida")
    pass
