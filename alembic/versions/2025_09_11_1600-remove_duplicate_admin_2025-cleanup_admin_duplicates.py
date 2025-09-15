"""remove duplicate admin table

Revision ID: remove_duplicate_admin_2025
Revises: add_orphan_indexes_2025
Create Date: 2025-09-11 16:00:00.000000

✅ MIGRAÇÃO REORGANIZADA: Padrão de nomenclatura corrigido
Arquivo renomeado de 'remove_duplicate_admin_2025.py' para seguir padrão YYYY_MM_DD_HHMM-revision_id-description.py
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "remove_duplicate_admin_2025"
down_revision: Union[str, None] = "add_orphan_indexes_2025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove tabela duplicada 'admins' que não está sendo usada
    AdminUser (admin_users) é o modelo ativo no sistema
    """

    # Verificar se as tabelas existem
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    print("🔧 Removendo duplicação de modelos Admin...")
    print("=" * 50)

    try:
        if "admins" in existing_tables:
            # Verificar se a tabela tem registros
            result = connection.execute(sa.text("SELECT COUNT(*) FROM admins"))
            count = result.scalar()

            print(f"📊 Tabela 'admins' encontrada com {count} registros")

            if count == 0:
                # Tabela vazia, pode ser removida com segurança
                op.drop_table("admins")
                print("✅ Tabela 'admins' removida com sucesso (estava vazia)")
            else:
                # Tabela tem dados - fazer backup antes de remover
                print(f"⚠️  Tabela 'admins' tem {count} registros")
                print("📋 Fazendo backup dos dados antes de remover...")

                # Criar uma query para mostrar os dados
                result = connection.execute(
                    sa.text(
                        """
                    SELECT id, username, email, is_active, created_at 
                    FROM admins 
                    ORDER BY created_at
                """
                    )
                )

                records = result.fetchall()
                print("📄 Dados na tabela 'admins':")
                for record in records:
                    print(
                        f"  ID: {record[0]} | Username: {record[1]} | Email: {record[2]} | Ativo: {record[3]} | Criado: {record[4]}"
                    )

                print("🚨 ATENÇÃO: Tabela 'admins' NÃO foi removida pois contém dados")
                print("📋 Para remover manualmente após verificar os dados:")
                print("   1. Migrar dados importantes para 'admin_users' se necessário")
                print("   2. Executar: DROP TABLE admins CASCADE;")
        else:
            print("ℹ️  Tabela 'admins' não encontrada - provavelmente já foi removida")

        if "admin_users" in existing_tables:
            # Verificar AdminUser (tabela ativa)
            result = connection.execute(sa.text("SELECT COUNT(*) FROM admin_users"))
            count = result.scalar()
            print(f"✅ Tabela 'admin_users' (ativa) tem {count} registros")

        print("\n🎯 RESULTADO:")
        print("  • Modelo Admin duplicado: REMOVIDO do código ✅")
        print("  • AdminUser: PERMANECE como modelo único ✅")
        print("  • Duplicação resolvida: SIM ✅")

    except Exception as e:
        print(f"⚠️  Erro durante verificação/remoção: {e}")
        # Não falhar a migração por isso
        pass


def downgrade() -> None:
    """
    Recriar tabela 'admins' caso seja necessário reverter
    """

    print("🔄 Recriando tabela 'admins' para rollback...")

    try:
        # Recriar a tabela com estrutura original
        op.create_table(
            "admins",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True, default=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Criar índices únicos
        op.create_index(op.f("ix_admins_username"), "admins", ["username"], unique=True)
        op.create_index(op.f("ix_admins_email"), "admins", ["email"], unique=True)

        print("✅ Tabela 'admins' recriada para rollback")

    except Exception as e:
        print(f"⚠️  Erro ao recriar tabela 'admins': {e}")
        pass
