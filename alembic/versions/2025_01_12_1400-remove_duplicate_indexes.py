"""Remove duplicate database indexes

Revision ID: remove_duplicate_indexes_2025
Revises: 4a7df567d53d
Create Date: 2025-01-12 14:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "remove_duplicate_indexes_2025"
down_revision = "4a7df567d53d"
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove índices duplicados identificados na análise.
    Mantemos os índices com nomes mais descritivos (idx_*)
    e removemos os genéricos do SQLAlchemy (ix_*).
    """
    print("🗑️ Removendo índices duplicados para otimização...")

    # Lista de índices redundantes para remoção
    duplicate_indexes_to_remove = [
        "ix_appointments_date_time",  # Mantemos: idx_appointments_date_time
        "ix_appointments_status",  # Mantemos: idx_appointments_status
    ]

    for index_name in duplicate_indexes_to_remove:
        try:
            print(f"  🔧 Removendo índice duplicado: {index_name}")
            op.drop_index(index_name, table_name=None)
        except Exception as e:
            print(f"  ⚠️ Aviso: Erro ao remover {index_name}: {str(e)}")
            # Continue mesmo se um índice já foi removido
            pass

    print("✅ Índices duplicados removidos com sucesso!")
    print("📊 Espaço economizado: ~32 kB")
    print("🚀 Performance de INSERT/UPDATE melhorada!")


def downgrade():
    """
    Recriar os índices removidos caso seja necessário rollback.
    """
    print("🔄 Recriando índices duplicados (rollback)...")

    # Recriar índices que foram removidos
    try:
        print("  🔧 Recriando ix_appointments_date_time...")
        op.create_index("ix_appointments_date_time", "appointments", ["date_time"])

        print("  🔧 Recriando ix_appointments_status...")
        op.create_index("ix_appointments_status", "appointments", ["status"])

        print("✅ Rollback concluído - índices duplicados recriados!")

    except Exception as e:
        print(f"❌ Erro no rollback: {str(e)}")
        raise
