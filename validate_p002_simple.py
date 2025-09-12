#!/usr/bin/env python3
"""
✅ P002: Script de validação simplificado - Índice composto messages

Problema: Índice composto ausente na tabela messages
Solução: CREATE INDEX messages_conv_dir_created ON messages (conversation_id, direction, created_at)
Meta: Dashboard conversations query < 100ms
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_p002():
    """Validação simplificada do P002"""
    
    print("🚀 Validando P002 - Índice composto messages")
    print("=" * 50)
    
    db_url = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "problem": "P002: Índice composto ausente na tabela messages",
        "solution": "CREATE INDEX messages_conv_dir_created ON messages (conversation_id, direction, created_at)",
        "target": "Dashboard conversations query < 100ms",
        "tests": [],
        "status": "unknown"
    }
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Test 1: Verificar se índice existe
        print("\n📊 Teste 1: Verificando se índice foi criado...")
        index_query = """
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'messages' 
        AND indexname = 'messages_conv_dir_created'
        """
        index_result = await conn.fetch(index_query)
        index_exists = bool(index_result)
        
        if index_exists:
            print(f"   ✅ Índice encontrado: {index_result[0]['indexname']}")
            print(f"   📝 Definição: {index_result[0]['indexdef']}")
        else:
            print("   ❌ Índice não encontrado!")
        
        results["tests"].append({
            "name": "Index existence",
            "status": "pass" if index_exists else "fail",
            "found": index_exists,
            "definition": index_result[0]['indexdef'] if index_exists else None
        })
        
        # Test 2: Estatísticas da tabela
        print("\n📊 Teste 2: Estatísticas da tabela...")
        stats_query = """
        SELECT 
            COUNT(*) as total_messages,
            COUNT(DISTINCT conversation_id) as unique_conversations,
            COUNT(DISTINCT direction) as unique_directions
        FROM messages
        """
        stats = await conn.fetchrow(stats_query)
        
        print(f"   📄 Total mensagens: {stats['total_messages']}")
        print(f"   💬 Conversas únicas: {stats['unique_conversations']}")
        print(f"   📋 Direções únicas: {stats['unique_directions']}")
        
        results["tests"].append({
            "name": "Table statistics",
            "status": "pass",
            "total_messages": stats['total_messages'],
            "unique_conversations": stats['unique_conversations'],
            "unique_directions": stats['unique_directions']
        })
        
        # Test 3: Performance de queries típicas
        print("\n📊 Teste 3: Performance de queries do dashboard...")
        
        queries = [
            ("Lista mensagens conversa", "SELECT id, direction, content FROM messages WHERE conversation_id = 10 ORDER BY created_at ASC LIMIT 50"),
            ("Mensagens de entrada", "SELECT id, content FROM messages WHERE conversation_id = 10 AND direction = 'in' ORDER BY created_at DESC LIMIT 20"),
            ("Última mensagem", "SELECT id, content FROM messages WHERE conversation_id = 10 ORDER BY created_at DESC LIMIT 1"),
        ]
        
        performance_results = []
        for name, query in queries:
            print(f"   🔍 Testando: {name}")
            
            start_time = time.time()
            result = await conn.fetch(query)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            print(f"      ⏱️  Tempo: {execution_time:.2f}ms")
            print(f"      📄 Resultados: {len(result)} linhas")
            
            performance_results.append({
                "name": name,
                "execution_time_ms": round(execution_time, 2),
                "rows_returned": len(result),
                "status": "pass" if execution_time < 100 else "warning"
            })
        
        results["tests"].extend(performance_results)
        
        # Test 4: Verificar se PostgreSQL está usando o índice correto
        print("\n📊 Teste 4: Verificando uso do índice...")
        explain_query = """
        EXPLAIN (FORMAT TEXT) 
        SELECT id, direction, content 
        FROM messages 
        WHERE conversation_id = 10 AND direction = 'in' 
        ORDER BY created_at ASC 
        LIMIT 10
        """
        
        explain_result = await conn.fetch(explain_query)
        explain_text = "\n".join([row[0] for row in explain_result])
        
        using_new_index = "messages_conv_dir_created" in explain_text
        print(f"   📊 Usando novo índice: {'✅ SIM' if using_new_index else '⚠️ NÃO'}")
        print(f"   📝 Plano de execução:")
        for line in explain_text.split('\n'):
            print(f"      {line}")
        
        results["tests"].append({
            "name": "Index usage verification",
            "status": "pass" if using_new_index else "warning",
            "using_new_index": using_new_index,
            "execution_plan": explain_text
        })
        
        # Calcular status geral
        avg_performance = sum(t["execution_time_ms"] for t in performance_results) / len(performance_results)
        target_met = avg_performance < 100
        
        results["performance_summary"] = {
            "average_execution_time_ms": round(avg_performance, 2),
            "target_met": target_met,
            "index_created": index_exists,
            "postgresql_using_index": using_new_index
        }
        
        # Status final
        if not index_exists:
            results["status"] = "fail"
        elif not target_met:
            results["status"] = "fail"
        elif not using_new_index:
            results["status"] = "warning"  # Index exists but not being used
        else:
            results["status"] = "pass"
        
        await conn.close()
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"❌ Erro durante validação: {e}")
    
    # Save results
    with open("p002_validation_simple.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print(f"\n📋 RESUMO P002:")
    print(f"   Problema: {results['problem']}")
    print(f"   Solução: {results['solution']}")
    
    if "performance_summary" in results:
        perf = results["performance_summary"]
        print(f"   📊 Performance média: {perf['average_execution_time_ms']}ms")
        print(f"   🎯 Meta < 100ms: {'✅ ATINGIDA' if perf['target_met'] else '❌ NÃO ATINGIDA'}")
        print(f"   📊 Índice criado: {'✅ SIM' if perf['index_created'] else '❌ NÃO'}")
        print(f"   🔍 PostgreSQL usando índice: {'✅ SIM' if perf['postgresql_using_index'] else '⚠️ NÃO'}")
    
    status_emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌", "error": "❌"}
    print(f"\n{status_emoji.get(results['status'], '❓')} STATUS FINAL: {results['status'].upper()}")
    
    if results['status'] == 'pass':
        print("🎉 P002 CONCLUÍDO COM SUCESSO!")
    elif results['status'] == 'warning':
        print("⚠️ P002 implementado mas PostgreSQL ainda não está usando o novo índice")
        print("💡 Isso é normal - o otimizador escolhe o melhor índice baseado nas estatísticas")
    elif results['status'] == 'fail':
        print("❌ P002 falhou - verificar implementação")
    
    return results

if __name__ == "__main__":
    asyncio.run(validate_p002())
