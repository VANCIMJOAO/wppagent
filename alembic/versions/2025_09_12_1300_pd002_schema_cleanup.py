"""PD002: Limpeza de tabelas órfãs com safety checks

Revision ID: pd002_schema_cleanup
Revises: pd001_performance_idx
Create Date: 2025-09-12 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'pd002_schema_cleanup'
down_revision = 'pd001_performance_idx'
branch_labels = None
depends_on = None


def upgrade():
    """PD002 - Limpar tabelas órfãs com verificações de segurança"""
    connection = op.get_bind()
    
    print("🧹 PD002 - Iniciando limpeza de schema órfão com safety checks")
    
    # Lista de tabelas órfãs para remoção
    orphan_tables = [
        'admin_users_backup_hf003',  # Backup HF003 não mais necessário
        'login_attempts',            # Sistema de login antigo
        'login_sessions',            # Sistema de login antigo  
        'refresh_tokens',            # Referência quebrada
        'available_slots',           # Não referenciada por FK
        'blocked_times'              # Não referenciada por FK
    ]
    
    removed_tables = []
    backup_tables = []
    skipped_tables = []
    
    for table_name in orphan_tables:
        try:
            # 1. Verificar se tabela existe
            exists = connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                )
            """)).scalar()
            
            if not exists:
                print(f"  ⏭️  Tabela {table_name} não existe, pulando...")
                skipped_tables.append(f"{table_name} (não existe)")
                continue
                
            # 2. Verificar se tem dados (backup se > 0)
            count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"  📊 Tabela {table_name}: {count} registros encontrados")
            
            # 3. Criar backup se tem dados importantes (exceto já é backup)
            if count > 0 and not table_name.endswith('_backup_hf003'):
                backup_name = f"{table_name}_backup_pd002"
                
                # Verificar se backup já existe
                backup_exists = connection.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = '{backup_name}' AND table_schema = 'public'
                    )
                """)).scalar()
                
                if not backup_exists:
                    connection.execute(text(f"""
                        CREATE TABLE {backup_name} AS 
                        SELECT *, NOW() as backup_created_at FROM {table_name}
                    """))
                    backup_tables.append(backup_name)
                    print(f"  💾 Backup criado: {backup_name}")
                else:
                    print(f"  ⚠️  Backup {backup_name} já existe, pulando criação")
            
            # 4. Verificar dependências FK (safety check)
            fk_dependencies = connection.execute(text(f"""
                SELECT constraint_name, table_name 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND (table_name = '{table_name}' OR constraint_name LIKE '%{table_name}%')
            """)).fetchall()
            
            # Verificar se outras tabelas referenciam esta
            referenced_by = connection.execute(text(f"""
                SELECT 
                    tc.table_name as referencing_table,
                    ccu.table_name as referenced_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu 
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND ccu.table_name = '{table_name}'
            """)).fetchall()
            
            if referenced_by:
                print(f"  ⚠️  WARNING: Tabela {table_name} é referenciada por outras tabelas:")
                for ref in referenced_by:
                    print(f"      - {ref[0]} -> {ref[1]}")
                skipped_tables.append(f"{table_name} (tem FKs)")
                continue
            
            # 5. Verificar se tem constraints que podem impedir DROP
            constraints = connection.execute(text(f"""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = '{table_name}'
                AND constraint_type IN ('FOREIGN KEY', 'CHECK')
            """)).fetchall()
            
            # 6. Remover constraints FK primeiro se existirem
            for constraint in constraints:
                if constraint[1] == 'FOREIGN KEY':
                    try:
                        connection.execute(text(f"""
                            ALTER TABLE {table_name} DROP CONSTRAINT {constraint[0]} CASCADE
                        """))
                        print(f"  🔗 Constraint FK removida: {constraint[0]}")
                    except Exception as e:
                        print(f"  ⚠️  Erro ao remover constraint {constraint[0]}: {e}")
            
            # 7. Remover tabela com CASCADE para limpar índices/constraints restantes
            connection.execute(text(f"DROP TABLE {table_name} CASCADE"))
            removed_tables.append(table_name)
            print(f"  ✅ Tabela {table_name} removida com sucesso")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {table_name}: {e}")
            skipped_tables.append(f"{table_name} (erro: {str(e)[:50]}...)")
            # Continue com próxima tabela, não falhe toda migração
    
    # Relatório final
    print("\n📋 PD002 - Relatório de Limpeza de Schema:")
    print(f"  ✅ Tabelas removidas ({len(removed_tables)}): {removed_tables}")
    print(f"  💾 Backups criados ({len(backup_tables)}): {backup_tables}")
    print(f"  ⏭️  Tabelas puladas ({len(skipped_tables)}): {skipped_tables}")
    
    # Verificar tamanho do schema após limpeza
    remaining_tables = connection.execute(text("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)).scalar()
    
    print(f"  📊 Tabelas restantes no schema: {remaining_tables}")
    print("🧹 PD002 - Limpeza de schema concluída com sucesso!")


def downgrade():
    """PD002 - Rollback: recriar tabelas dos backups se existirem"""
    connection = op.get_bind()
    
    print("🔄 PD002 - Iniciando rollback: restaurando tabelas de backups")
    
    # Verificar se existem backups PD002 para restaurar
    backup_tables = connection.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name LIKE '%_backup_pd002' AND table_schema = 'public'
    """)).fetchall()
    
    restored_tables = []
    
    for backup_table in backup_tables:
        backup_name = backup_table[0]
        original_name = backup_name.replace('_backup_pd002', '')
        
        try:
            # Verificar se tabela original já existe
            exists = connection.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{original_name}' AND table_schema = 'public'
                )
            """)).scalar()
            
            if exists:
                print(f"  ⚠️  Tabela {original_name} já existe, pulando rollback")
                continue
            
            # Verificar se backup tem dados
            count = connection.execute(text(f"SELECT COUNT(*) FROM {backup_name}")).scalar()
            print(f"  📊 Backup {backup_name}: {count} registros para restaurar")
            
            if count == 0:
                print(f"  ⏭️  Backup {backup_name} vazio, pulando restauração")
                continue
            
            # Recriar tabela original do backup (sem coluna backup_created_at)
            columns = connection.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{backup_name}' 
                AND column_name != 'backup_created_at'
                ORDER BY ordinal_position
            """)).fetchall()
            
            # Construir CREATE TABLE baseado nas colunas do backup
            column_definitions = []
            for col in columns:
                col_def = f"{col[0]} {col[1]}"
                if col[2] == 'NO':
                    col_def += " NOT NULL"
                if col[3]:
                    col_def += f" DEFAULT {col[3]}"
                column_definitions.append(col_def)
            
            if column_definitions:
                create_sql = f"""
                    CREATE TABLE {original_name} (
                        {', '.join(column_definitions)}
                    )
                """
                connection.execute(text(create_sql))
                
                # Copiar dados do backup para tabela original
                connection.execute(text(f"""
                    INSERT INTO {original_name} 
                    SELECT {', '.join([col[0] for col in columns])}
                    FROM {backup_name}
                """))
                
                restored_tables.append(original_name)
                print(f"  ✅ Tabela {original_name} restaurada de {backup_name}")
            
        except Exception as e:
            print(f"  ❌ Erro no rollback de {original_name}: {e}")
    
    print(f"\n🔄 PD002 - Rollback concluído. Tabelas restauradas: {restored_tables}")
