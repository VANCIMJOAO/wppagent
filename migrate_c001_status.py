#!/usr/bin/env python3
"""
C001: Migração de Status Enum - Unificação
=========================================

Atualiza valores de status existentes no banco para usar enum unificado:
- pendente → agendado  
- concluido → realizado
- Remove 'bloqueado' (se existir)
"""

import os
import sys
sys.path.append('/home/vancim/whats_agent')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

def migrate_status_enum():
    print("🔄 C001: Migração de Status Enum")
    print("=" * 40)
    print()
    
    # Conectar ao banco usando URL do Railway
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Verificar valores atuais
        print("📊 Verificando valores atuais...")
        result = db.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM appointments 
            GROUP BY status
        """)).fetchall()
        
        status_counts = [(row[0], row[1]) for row in result]
        
        print("\n📈 Status atuais no banco:")
        for status, count in status_counts:
            print(f"   {status}: {count} registros")
        
        # 2. Mapeamento de migração (incluindo valores encontrados)
        migration_map = {
            # Português (backend)
            'pendente': 'agendado',
            'concluido': 'realizado',
            'confirmado': 'confirmado',  
            'cancelado': 'cancelado',    
            'bloqueado': 'cancelado',     
            # Inglês (encontrado na produção)
            'pending': 'agendado',
            'confirmed': 'confirmado',
            'cancelled': 'cancelado',
            'completed': 'realizado',
            'blocked': 'cancelado',
            # Status inválidos
            'invalid_status': 'cancelado'
        }
        
        print(f"\n🔄 Mapeamento de migração:")
        for old, new in migration_map.items():
            print(f"   {old} → {new}")
        
        # 3. Executar migração
        print(f"\n⚡ Executando migração...")
        migration_results = {}
        
        for old_status, new_status in migration_map.items():
            if old_status != new_status:  # Só migra se diferente
                result = db.execute(text("""
                    UPDATE appointments 
                    SET status = :new_status 
                    WHERE status = :old_status
                """), {"new_status": new_status, "old_status": old_status})
                
                updated = result.rowcount
                
                if updated > 0:
                    migration_results[old_status] = {
                        "new_status": new_status,
                        "records_updated": updated
                    }
                    print(f"   ✅ {old_status} → {new_status}: {updated} registros")
        
        # 4. Commit das mudanças
        db.commit()
        print(f"\n✅ Migração commitada com sucesso!")
        
        # 5. Verificar resultado final
        print(f"\n📊 Verificando resultado final...")
        final_result = db.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM appointments 
            GROUP BY status
        """)).fetchall()
        
        final_status_counts = [(row[0], row[1]) for row in final_result]
        
        print("\n📈 Status finais no banco:")
        expected_statuses = ['agendado', 'confirmado', 'realizado', 'cancelado', 'pendente']
        for status, count in final_status_counts:
            icon = "✅" if status in expected_statuses else "❌"
            print(f"   {icon} {status}: {count} registros")
        
        # 6. Salvar relatório
        report = {
            "migration_date": datetime.now().isoformat(),
            "before": dict(status_counts),
            "after": dict(final_status_counts),
            "migration_map": migration_map,
            "results": migration_results,
            "success": True
        }
        
        with open('/home/vancim/whats_agent/c001_migration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Relatório salvo em: c001_migration_report.json")
        print(f"\n🎉 C001: Migração completa com sucesso!")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro na migração: {str(e)}")
        
        # Salvar relatório de erro
        error_report = {
            "migration_date": datetime.now().isoformat(),
            "error": str(e),
            "success": False
        }
        
        with open('/home/vancim/whats_agent/c001_migration_error.json', 'w') as f:
            json.dump(error_report, f, indent=2)
        
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = migrate_status_enum()
    exit(0 if success else 1)
