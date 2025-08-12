#!/usr/bin/env python3
"""
🧪 TESTE DE CONEXÃO SSL COM POSTGRESQL
=====================================
"""

import asyncio
import asyncpg
import psycopg2
import ssl
from datetime import datetime

async def test_ssl_connection():
    """Testa conexão SSL com PostgreSQL"""
    print("🔐 TESTE DE CONEXÃO SSL - POSTGRESQL")
    print("=" * 50)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # URLs de teste (ajustar conforme necessário)
    test_connections = [
        {
            'name': 'PostgreSQL SSL Async',
            'url': 'postgresql://whatsapp_app:PASSWORD@localhost:5432/whatsapp_agent?sslmode=require',
            'type': 'async'
        },
        {
            'name': 'PostgreSQL SSL Sync',
            'url': 'postgresql://whatsapp_app:PASSWORD@localhost:5432/whatsapp_agent?sslmode=require',
            'type': 'sync'
        }
    ]
    
    results = []
    
    for test in test_connections:
        print(f"🔄 Testando: {test['name']}")
        
        try:
            if test['type'] == 'async':
                # Teste assíncrono
                conn = await asyncpg.connect(test['url'])
                
                # Verificar SSL
                ssl_info = await conn.fetchrow("SELECT ssl_is_used();")
                version = await conn.fetchval("SELECT version();")
                
                print(f"   ✅ Conectado via SSL: {ssl_info['ssl_is_used']}")
                print(f"   📋 Versão: {version[:50]}...")
                
                await conn.close()
                results.append(True)
                
            else:
                # Teste síncrono
                conn = psycopg2.connect(test['url'])
                cursor = conn.cursor()
                
                # Verificar SSL
                cursor.execute("SELECT ssl_is_used();")
                ssl_used = cursor.fetchone()[0]
                
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                
                print(f"   ✅ Conectado via SSL: {ssl_used}")
                print(f"   📋 Versão: {version[:50]}...")
                
                conn.close()
                results.append(True)
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append(False)
        
        print()
    
    # Resultado final
    passed = sum(results)
    total = len(results)
    
    print("📊 RESULTADO DOS TESTES SSL")
    print("-" * 30)
    print(f"   Passou: {passed}/{total}")
    
    if passed == total:
        print("   🎉 Todos os testes SSL passaram!")
        return 0
    else:
        print("   ⚠️ Alguns testes SSL falharam")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(test_ssl_connection()))
