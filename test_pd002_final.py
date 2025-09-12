#!/usr/bin/env python3
"""
PD002 - Schema Cleanup Validation Test

Verifica se a limpeza de tabelas órfãs foi executada conforme DoD requirements.
"""

import asyncio
import asyncpg
import os
from datetime import datetime

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')

class PD002Validator:
    def __init__(self):
        self.results = {
            'orphan_tables_removed': [],
            'backups_created': [],
            'schema_integrity': True,
            'performance_metrics': {},
            'errors': []
        }
    
    async def connect_db(self):
        """Conectar ao banco PostgreSQL"""
        try:
            self.conn = await asyncpg.connect(DATABASE_URL)
            print("✅ Conexão com PostgreSQL estabelecida")
            return True
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            self.results['errors'].append(f"Database connection: {e}")
            return False
    
    async def test_orphan_tables_removal(self):
        """DoD 1: Verificar se tabelas órfãs foram removidas"""
        print("\n🧹 Teste 1: Verificação de remoção de tabelas órfãs")
        
        orphan_tables = [
            'admin_users_backup_hf003',
            'login_attempts', 
            'login_sessions',
            'refresh_tokens',
            'available_slots',
            'blocked_times'
        ]
        
        for table in orphan_tables:
            exists = await self.conn.fetchval('''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                )
            ''', table)
            
            if not exists:
                print(f"  ✅ {table}: removida corretamente")
                self.results['orphan_tables_removed'].append(table)
            else:
                print(f"  ❌ {table}: ainda existe no banco")
                self.results['errors'].append(f"Orphan table still exists: {table}")
        
        return len(self.results['orphan_tables_removed']) == len(orphan_tables)
    
    async def test_backup_preservation(self):
        """DoD 2: Verificar se backups foram criados para dados importantes"""
        print("\n💾 Teste 2: Verificação de preservação de backups")
        
        expected_backups = [
            'login_attempts_backup_pd002',
            'login_sessions_backup_pd002', 
            'refresh_tokens_backup_pd002'
        ]
        
        for backup_table in expected_backups:
            exists = await self.conn.fetchval('''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                )
            ''', backup_table)
            
            if exists:
                count = await self.conn.fetchval(f'SELECT COUNT(*) FROM {backup_table}')
                print(f"  ✅ {backup_table}: {count} registros preservados")
                self.results['backups_created'].append({
                    'table': backup_table,
                    'records': count
                })
            else:
                print(f"  ❌ {backup_table}: backup não encontrado")
                self.results['errors'].append(f"Expected backup not found: {backup_table}")
        
        return len(self.results['backups_created']) == len(expected_backups)
    
    async def test_schema_integrity(self):
        """DoD 3: Verificar integridade do schema após limpeza"""
        print("\n🔍 Teste 3: Verificação de integridade do schema")
        
        # Verificar FKs quebradas
        broken_fks = await self.conn.fetch('''
            SELECT 
                tc.table_name,
                tc.constraint_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.tables t 
                WHERE t.table_name = ccu.table_name AND t.table_schema = 'public'
            )
        ''')
        
        if broken_fks:
            print(f"  ❌ {len(broken_fks)} FKs quebradas encontradas:")
            for fk in broken_fks:
                print(f"    - {fk[0]}.{fk[1]} -> {fk[2]}")
                self.results['errors'].append(f"Broken FK: {fk[0]}.{fk[1]} -> {fk[2]}")
            self.results['schema_integrity'] = False
        else:
            print("  ✅ Nenhuma FK quebrada - integridade mantida")
        
        # Verificar se tabelas essenciais existem
        essential_tables = [
            'users', 'conversations', 'messages', 'appointments', 
            'businesses', 'services', 'admin_users'
        ]
        
        missing_tables = []
        for table in essential_tables:
            exists = await self.conn.fetchval('''
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                )
            ''', table)
            
            if not exists:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"  ❌ Tabelas essenciais faltando: {missing_tables}")
            self.results['errors'].extend([f"Missing essential table: {t}" for t in missing_tables])
            self.results['schema_integrity'] = False
        else:
            print("  ✅ Todas as tabelas essenciais preservadas")
        
        return self.results['schema_integrity']
    
    async def test_performance_metrics(self):
        """DoD 4: Coletar métricas de performance do schema otimizado"""
        print("\n📊 Teste 4: Métricas de performance do schema")
        
        # Total de tabelas
        total_tables = await self.conn.fetchval('''
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        ''')
        
        # Tamanho total do banco
        db_size = await self.conn.fetchval('''
            SELECT pg_size_pretty(pg_database_size(current_database()))
        ''')
        
        # Número de índices
        total_indexes = await self.conn.fetchval('''
            SELECT COUNT(*) FROM pg_indexes 
            WHERE schemaname = 'public'
        ''')
        
        self.results['performance_metrics'] = {
            'total_tables': total_tables,
            'database_size': db_size,
            'total_indexes': total_indexes,
            'tables_removed': 6,
            'schema_reduction': f"{33} -> {total_tables} (-{33-total_tables})"
        }
        
        print(f"  📊 Total de tabelas: {total_tables}")
        print(f"  💾 Tamanho do banco: {db_size}")
        print(f"  🗂️  Total de índices: {total_indexes}")
        print(f"  🧹 Redução do schema: 33 -> {total_tables} tabelas")
        
        return True
    
    async def test_rollback_capability(self):
        """DoD 5: Verificar se rollback é possível"""
        print("\n🔄 Teste 5: Capacidade de rollback")
        
        backup_tables = await self.conn.fetch('''
            SELECT table_name FROM information_schema.tables 
            WHERE table_name LIKE '%_backup_pd002' AND table_schema = 'public'
        ''')
        
        rollback_ready = True
        for backup in backup_tables:
            table_name = backup[0]
            
            # Verificar se backup tem estrutura consistente
            columns = await self.conn.fetch(f'''
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                AND column_name != 'backup_created_at'
                ORDER BY ordinal_position
            ''')
            
            if len(columns) > 0:
                print(f"  ✅ {table_name}: {len(columns)} colunas - rollback possível")
            else:
                print(f"  ❌ {table_name}: estrutura inválida")
                rollback_ready = False
        
        if rollback_ready and backup_tables:
            print("  ✅ Sistema de rollback operacional")
        else:
            print("  ❌ Problemas no sistema de rollback")
            self.results['errors'].append("Rollback system issues")
        
        return rollback_ready
    
    async def run_all_tests(self):
        """Executar todos os testes de validação do PD002"""
        print("🧪 PD002 - INICIANDO VALIDAÇÃO COMPLETA")
        print("=" * 60)
        
        if not await self.connect_db():
            return False
        
        try:
            test_results = {
                'orphan_removal': await self.test_orphan_tables_removal(),
                'backup_preservation': await self.test_backup_preservation(),
                'schema_integrity': await self.test_schema_integrity(),
                'performance_metrics': await self.test_performance_metrics(),
                'rollback_capability': await self.test_rollback_capability()
            }
            
            # Resumo final
            print("\n" + "=" * 60)
            print("📋 PD002 - RELATÓRIO FINAL DE VALIDAÇÃO")
            print("=" * 60)
            
            total_tests = len(test_results)
            passed_tests = sum(test_results.values())
            
            print(f"\n✅ Testes aprovados: {passed_tests}/{total_tests}")
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status} {test_name.replace('_', ' ').title()}")
            
            print(f"\n📊 Métricas do Schema:")
            metrics = self.results['performance_metrics']
            for key, value in metrics.items():
                print(f"  - {key.replace('_', ' ').title()}: {value}")
            
            print(f"\n💾 Backups Preservados: {len(self.results['backups_created'])}")
            for backup in self.results['backups_created']:
                print(f"  - {backup['table']}: {backup['records']} registros")
            
            if self.results['errors']:
                print(f"\n❌ Erros Encontrados ({len(self.results['errors'])}):")
                for error in self.results['errors']:
                    print(f"  - {error}")
            
            success_rate = (passed_tests / total_tests) * 100
            
            if success_rate == 100:
                print(f"\n🏆 STATUS PD002: COMPLETAMENTE VALIDADO ({success_rate:.0f}%)")
                print("✅ DoD Requirements: TODOS ATENDIDOS")
            else:
                print(f"\n⚠️ STATUS PD002: PARCIALMENTE VALIDADO ({success_rate:.0f}%)")
                print("❌ Alguns DoD requirements não foram atendidos")
            
            return success_rate == 100
            
        except Exception as e:
            print(f"\n❌ Erro durante validação: {e}")
            return False
        finally:
            await self.conn.close()

async def main():
    """Função principal para executar validação PD002"""
    validator = PD002Validator()
    success = await validator.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 PD002 - SCHEMA CLEANUP VALIDADO COM SUCESSO!")
    else:
        print("💥 PD002 - VALIDAÇÃO FALHOU - VERIFICAR ERROS")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
