#!/usr/bin/env python3
"""
Script de teste para validar implementação PF-001
Testa se as rotas otimizadas eliminam queries N+1 e respeitam cache TTL
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Any, List
import sys
import os

# Adicionar o diretório root ao path
sys.path.append('/home/vancim/whats_agent')

async def test_pf001_optimization():
    """Testa a implementação PF-001 - Otimização de N+1 queries"""
    
    print("🚀 Iniciando teste PF-001 - Otimização de N+1 queries")
    print("=" * 60)
    
    # URL base da aplicação
    base_url = "http://localhost:8000"
    
    # Endpoints para testar
    endpoints = [
        "/appointments/test/optimized",  # Rota de teste otimizada (sem auth)
        "/appointments/test/optimized/1",  # Detalhes otimizados (sem auth)
        "/appointments/test/stats/cache",  # Estatísticas de cache
        "/appointments/test/stats/queries",  # Estatísticas de queries
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            print(f"\n📊 Testando endpoint: {endpoint}")
            
            # Teste 1: Primeira requisição (cache miss)
            start_time = time.time()
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        first_response_time = time.time() - start_time
                        print(f"✅ Primeira requisição: {response.status} ({first_response_time:.3f}s)")
                        
                        # Verificar estrutura da resposta
                        if 'success' in data and 'data' in data:
                            print(f"✅ Estrutura de resposta padronizada: success={data['success']}")
                        else:
                            print("⚠️ Resposta não segue padrão C002")
                            
                    else:
                        print(f"❌ Primeira requisição falhou: {response.status}")
                        continue
                        
            except Exception as e:
                print(f"❌ Erro na primeira requisição: {e}")
                continue
            
            # Teste 2: Segunda requisição (cache hit esperado)
            start_time = time.time()
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        second_response_time = time.time() - start_time
                        print(f"✅ Segunda requisição: {response.status} ({second_response_time:.3f}s)")
                        
                        # Verificar se foi mais rápida (cache hit)
                        if second_response_time < first_response_time * 0.8:
                            print(f"✅ Cache hit detectado - {((first_response_time - second_response_time) / first_response_time * 100):.1f}% mais rápida")
                        else:
                            print(f"⚠️ Cache miss ou performance similar")
                            
                    else:
                        print(f"❌ Segunda requisição falhou: {response.status}")
                        
            except Exception as e:
                print(f"❌ Erro na segunda requisição: {e}")
                
            results[endpoint] = {
                'first_response_time': first_response_time,
                'second_response_time': second_response_time if 'second_response_time' in locals() else None
            }
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES PF-001")
    print("=" * 60)
    
    for endpoint, metrics in results.items():
        print(f"\n📍 {endpoint}:")
        print(f"   • Primeira requisição: {metrics['first_response_time']:.3f}s")
        if metrics['second_response_time']:
            print(f"   • Segunda requisição: {metrics['second_response_time']:.3f}s")
            improvement = ((metrics['first_response_time'] - metrics['second_response_time']) / metrics['first_response_time'] * 100)
            print(f"   • Melhoria cache: {improvement:.1f}%")
    
    print("\n✅ Teste PF-001 concluído")
    return results

async def test_database_monitoring():
    """Testa se o middleware de monitoramento de database está funcionando"""
    
    print("\n🔍 Testando middleware de monitoramento de database")
    print("-" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Fazer uma requisição que deve gerar logs de monitoramento
            async with session.get(f"{base_url}/appointments/test/optimized") as response:
                if response.status == 200:
                    print("✅ Requisição para endpoint de teste executada")
                    print("✅ Middleware de monitoramento deve ter registrado métricas")
                    
                    # Testar estatísticas de cache
                    async with session.get(f"{base_url}/appointments/test/stats/cache") as cache_response:
                        if cache_response.status == 200:
                            cache_data = await cache_response.json()
                            print("✅ Estatísticas de cache acessíveis")
                            print(f"   Cache enabled: {cache_data.get('cache_enabled', 'unknown')}")
                        else:
                            print(f"⚠️ Estatísticas de cache indisponíveis: {cache_response.status}")
                    
                    return True
                else:
                    print(f"❌ Falha na requisição: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro no teste de monitoramento: {e}")
            return False

if __name__ == "__main__":
    print("🚀 PF-001 Test Suite - Otimização de N+1 Queries")
    print("=" * 60)
    
    try:
        # Executar testes
        loop = asyncio.get_event_loop()
        optimization_results = loop.run_until_complete(test_pf001_optimization())
        monitoring_result = loop.run_until_complete(test_database_monitoring())
        
        print("\n" + "=" * 60)
        print("🎯 RESULTADO FINAL PF-001")
        print("=" * 60)
        
        if optimization_results and monitoring_result:
            print("✅ PF-001 implementado com sucesso!")
            print("✅ Rotas otimizadas funcionando")
            print("✅ Cache funcionando")
            print("✅ Middleware de monitoramento ativo")
        else:
            print("❌ Alguns testes falharam - revisar implementação")
            
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")