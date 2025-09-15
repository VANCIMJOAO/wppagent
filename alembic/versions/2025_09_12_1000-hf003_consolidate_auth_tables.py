"""HF003: Consolidar auth_users e admin_users

Revision ID: hf003_consolidate_auth
Revises: 43cc0484d3a9
Create Date: 2025-09-12 10:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

revision = "hf003_consolidate_auth"
down_revision = "43cc0484d3a9"
branch_labels = None
depends_on = None


def upgrade():
    """HF003 - Consolidação IDEMPOTENTE das tabelas de autenticação"""
    connection = op.get_bind()

    # 1. Verificar se auth_users existe
    auth_users_exists = connection.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'auth_users' AND table_schema = 'public'
        )
    """
        )
    ).scalar()

    # 2. Verificar se admin_users existe
    admin_users_exists = connection.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'admin_users' AND table_schema = 'public'
        )
    """
        )
    ).scalar()

    print(
        f"HF003 - Status: auth_users={auth_users_exists}, admin_users={admin_users_exists}"
    )

    # 3. Criar backup da tabela admin_users se existir
    if admin_users_exists:
        try:
            connection.execute(
                text(
                    """
                CREATE TABLE admin_users_backup_hf003 AS 
                SELECT *, NOW() as backup_created_at FROM admin_users
            """
                )
            )
            print("HF003 - Backup admin_users criado: admin_users_backup_hf003")
        except Exception as e:
            print(f"HF003 - Warning: Backup já existe ou erro: {e}")

    # 4. Migrar dados de admin_users para auth_users se necessário
    if admin_users_exists and auth_users_exists:
        # Verificar se já foi migrado
        migrated_count = connection.execute(
            text(
                """
            SELECT COUNT(*) FROM auth_users 
            WHERE email IN (SELECT email FROM admin_users)
        """
            )
        ).scalar()

        if migrated_count == 0:
            # Verificar colunas disponíveis em admin_users
            admin_columns = connection.execute(
                text(
                    """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'admin_users'
            """
                )
            ).fetchall()
            admin_column_names = [col[0] for col in admin_columns]

            # Preparar SQL de inserção baseado nas colunas disponíveis
            if "name" in admin_column_names:
                name_field = "au.name"
            else:
                name_field = (
                    "SPLIT_PART(au.email, '@', 1)"  # Usar parte do email como nome
                )

            phone_field = "au.phone" if "phone" in admin_column_names else "NULL"

            # Migrar dados únicos de admin_users
            connection.execute(
                text(
                    f"""
                INSERT INTO auth_users (email, password_hash, name, role, phone, is_active, created_at, updated_at)
                SELECT 
                    au.email,
                    au.password_hash,
                    {name_field},
                    'admin' as role,
                    {phone_field},
                    au.is_active,
                    au.created_at,
                    au.updated_at
                FROM admin_users au
                WHERE au.email NOT IN (SELECT email FROM auth_users)
            """
                )
            )

            migrated = connection.execute(
                text(
                    """
                SELECT COUNT(*) FROM auth_users 
                WHERE role = 'admin' AND email IN (SELECT email FROM admin_users)
            """
                )
            ).scalar()

            print(f"HF003 - Migrados {migrated} admins para auth_users")

    # 5. Remover tabela admin_users após migração
    if admin_users_exists:
        try:
            connection.execute(text("DROP TABLE admin_users CASCADE"))
            print("HF003 - Tabela admin_users removida com sucesso")
        except Exception as e:
            print(f"HF003 - Warning: Erro ao remover admin_users: {e}")

    # 6. Criar índices otimizados para auth_users
    try:
        connection.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_auth_users_email_active 
            ON auth_users(email) WHERE is_active = true
        """
            )
        )

        connection.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_auth_users_role_active 
            ON auth_users(role) WHERE is_active = true  
        """
            )
        )
        print("HF003 - Índices otimizados criados")
    except Exception as e:
        print(f"HF003 - Warning: Índices já existem: {e}")


def downgrade():
    """HF003 - Rollback: Recriar admin_users se backup existir"""
    connection = op.get_bind()

    # Verificar se backup existe
    backup_exists = connection.execute(
        text(
            """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'admin_users_backup_hf003'
        )
    """
        )
    ).scalar()

    if backup_exists:
        # Recriar admin_users do backup
        connection.execute(
            text(
                """
            CREATE TABLE admin_users AS 
            SELECT id, email, password_hash, name, phone, is_active, created_at, updated_at
            FROM admin_users_backup_hf003
        """
            )
        )

        # Remover dados migrados de auth_users
        connection.execute(
            text(
                """
            DELETE FROM auth_users 
            WHERE role = 'admin' AND email IN (
                SELECT email FROM admin_users_backup_hf003
            )
        """
            )
        )

        print("HF003 - Rollback executado: admin_users restaurado")
    else:
        print("HF003 - Rollback impossível: backup não encontrado")
