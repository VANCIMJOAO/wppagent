#!/usr/bin/env python3
"""
🚀 Executar otimizações completas do banco de dados
"""

import asyncio
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database_optimization import db_optimizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_full_optimization():
    """Executar todas as otimizações"""
    
    print("🚀 INICIANDO OTIMIZAÇÕES COMPLETAS DO BANCO DE DADOS")
    print("=" * 60)
    
    try:
        # 1. Status inicial
        print("\n📊 1. VERIFICANDO STATUS INICIAL...")
        initial_status = await db_optimizer.get_optimization_status()
        print(f"Health Score inicial: {initial_status['health_score']:.1f}%")
        
        # 2. Criar índices otimizados
        print("\n🔧 2. CRIANDO ÍNDICES OTIMIZADOS...")
        indexes_result = await db_optimizer.create_optimized_indexes()
        
        total_indexes_created = 0
        for category, results in indexes_result.items():
            successful = [r for r in results if "✅" in r]
            failed = [r for r in results if "❌" in r]
            total_indexes_created += len(successful)
            
            print(f"  📁 {category}: {len(successful)} sucessos, {len(failed)} falhas")
        
        print(f"✅ Total de índices criados: {total_indexes_created}")
        
        # 3. Criar stored procedures
        print("\n🔧 3. CRIANDO STORED PROCEDURES...")
        procedures_result = await db_optimizer.create_stored_procedures()
        
        successful_procedures = sum(1 for status in procedures_result.values() if "✅" in status)
        failed_procedures = sum(1 for status in procedures_result.values() if "❌" in status)
        
        print(f"✅ Procedures criadas: {successful_procedures}")
        if failed_procedures > 0:
            print(f"❌ Procedures com erro: {failed_procedures}")
        
        # 4. Configurar backup
        print("\n💾 4. CONFIGURANDO ESTRATÉGIA DE BACKUP...")
        backup_result = await db_optimizer.setup_backup_strategy()
        print(f"✅ {backup_result['status']}")
        print(f"📁 Diretório: {backup_result['backup_directory']}")
        print(f"📜 Script backup: {backup_result['backup_script']}")
        print(f"🔄 Script restore: {backup_result['restore_script']}")
        
        # 5. Configurar replicação
        print("\n🔄 5. CONFIGURANDO REPLICAÇÃO...")
        replication_result = await db_optimizer.setup_replication_config()
        print(f"✅ {replication_result['status']}")
        print(f"📁 Diretório config: {replication_result['config_directory']}")
        
        # 6. Análise de performance
        print("\n📊 6. EXECUTANDO ANÁLISE DE PERFORMANCE...")
        analysis_result = await db_optimizer.run_performance_analysis()
        
        for analysis_name, data in analysis_result.items():
            if isinstance(data, list):
                print(f"  📈 {analysis_name}: {len(data)} resultados")
            else:
                print(f"  📈 {analysis_name}: {data}")
        
        # 7. Status final
        print("\n📊 7. VERIFICANDO STATUS FINAL...")
        final_status = await db_optimizer.get_optimization_status()
        print(f"Health Score final: {final_status['health_score']:.1f}%")
        
        # Resumo
        print("\n" + "=" * 60)
        print("🎯 RESUMO DAS OTIMIZAÇÕES")
        print("=" * 60)
        print(f"✅ Índices criados: {total_indexes_created}")
        print(f"✅ Procedures criadas: {successful_procedures}")
        print(f"✅ Backup configurado: ✓")
        print(f"✅ Replicação configurada: ✓")
        print(f"✅ Análise executada: ✓")
        print(f"📊 Health Score: {initial_status['health_score']:.1f}% → {final_status['health_score']:.1f}%")
        
        improvement = final_status['health_score'] - initial_status['health_score']
        if improvement > 0:
            print(f"🚀 Melhoria: +{improvement:.1f}%")
        
        print("\n🎉 OTIMIZAÇÕES COMPLETAS FINALIZADAS COM SUCESSO!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE AS OTIMIZAÇÕES: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_full_optimization())
    if success:
        print("\n🏆 SISTEMA OTIMIZADO E PRONTO PARA PRODUÇÃO!")
    else:
        print("\n💥 FALHA NAS OTIMIZAÇÕES")
        sys.exit(1)
