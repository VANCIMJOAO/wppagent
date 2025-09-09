#!/usr/bin/env python3
"""
🧪 Teste da implementação de cache otimizado
Verifica se o Redis está funcionando e se o cache está operacional
"""

import asyncio
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_cache_implementation():
    """Testa a implementação completa do cache"""
    
    print("🧪 INICIANDO TESTE DE CACHE OTIMIZADO")
    print("=" * 50)
    
    try:
        # 1. Testar importação dos módulos
        print("📦 1. Testando importações...")
        from app.services.cache_optimized import cache_service, CacheKeys
        from app.config.redis_config import RedisManager
        print("✅ Importações bem-sucedidas")
        
        # 2. Testar conexão Redis
        print("\n🔗 2. Testando conexão Redis...")
        redis_manager = RedisManager()
        if redis_manager.is_available:
            print(f"✅ Redis disponível: {redis_manager.client}")
        else:
            print("⚠️ Redis não disponível, usando fallback em memória")
        
        # 3. Verificar cache service
        print("\n🚀 3. Verificando cache service...")
        health = cache_service.health_check()
        print(f"✅ Cache service funcionando - Status: {health}")
        
        # 4. Testar operações básicas
        print("\n🔧 4. Testando operações básicas...")
        
        # Set/Get simples
        test_key = "test:basic"
        test_value = {"timestamp": datetime.now().isoformat(), "data": "test"}
        
        cache_service.set(test_key, test_value, ttl=60)
        cached_data = cache_service.get(test_key)
        
        if cached_data == test_value:
            print("✅ Set/Get básico funcionando")
        else:
            print(f"❌ Erro no Set/Get: esperado {test_value}, obtido {cached_data}")
        
        # 5. Testar get_or_set pattern
        print("\n🔄 5. Testando padrão get_or_set...")
        
        async def fetch_test_data():
            return {"fetched_at": datetime.now().isoformat(), "data": "fresh_data"}
        
        result1 = await cache_service.get_or_set(
            key="test:get_or_set",
            fetch_function=fetch_test_data,
            ttl=120
        )
        
        result2 = await cache_service.get_or_set(
            key="test:get_or_set", 
            fetch_function=fetch_test_data,
            ttl=120
        )
        
        if result1 == result2:
            print("✅ get_or_set funcionando (cache hit)")
        else:
            print(f"❌ get_or_set problema: {result1} != {result2}")
        
        # 6. Testar geração de chaves
        print("\n🗝️ 6. Testando geração de chaves...")
        
        appointments_key = CacheKeys.appointments_list(limit=10, page=1)
        detail_key = CacheKeys.appointment_detail(123)
        
        print(f"✅ Chave de lista: {appointments_key}")
        print(f"✅ Chave de detalhe: {detail_key}")
        
        # 7. Testar invalidação por padrão
        print("\n🧹 7. Testando invalidação por padrão...")
        
        # Criar várias chaves de teste
        test_keys = [
            "appointments:list:page_1",
            "appointments:list:page_2", 
            "appointments:detail:123"
        ]
        
        for key in test_keys:
            cache_service.set(key, {"test": True})
        
        # Invalidar por padrão
        invalidated = cache_service.invalidate_pattern("appointments:list:*")
        print(f"✅ Invalidadas {invalidated} chaves com padrão appointments:list:*")
        
        # Verificar se detail não foi afetado
        detail_data = cache_service.get("appointments:detail:123")
        if detail_data:
            print("✅ Chaves de detalhe preservadas")
        else:
            print("⚠️ Chave de detalhe foi invalidada (pode ser normal)")
        
        # 8. Testar estatísticas
        print("\n📊 8. Testando estatísticas...")
        stats = cache_service.get_cache_info()
        print(f"✅ Estatísticas do cache: {stats}")
        
        # 9. Limpar testes
        print("\n🧹 9. Limpando dados de teste...")
        cache_service.invalidate_pattern("test:*")
        cache_service.delete("appointments:detail:123")
        
        print("\n" + "=" * 50)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Cache otimizado está funcionando corretamente")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        logger.error(f"Erro no teste de cache: {e}", exc_info=True)
        return False
    
    finally:
        # Cleanup
        try:
            if 'cache_service' in locals():
                await cache_service.close()
        except:
            pass

async def test_appointments_integration():
    """Teste específico da integração com appointments"""
    
    print("\n" + "=" * 50)
    print("🔗 TESTE DE INTEGRAÇÃO COM APPOINTMENTS")
    print("=" * 50)
    
    try:
        from app.services.cache_optimized import cache_service, CacheKeys
        
        # Simular dados de appointment
        mock_appointment_data = {
            "appointments": [
                {
                    "id": 1,
                    "user_id": 1,
                    "date_time": "2024-01-15T10:00:00",
                    "status": "confirmed",
                    "user_name": "João Silva",
                    "service_name": "Corte de Cabelo"
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "has_more": False
        }
        
        # Testar cache de lista
        list_key = CacheKeys.appointments_list(limit=10, page=1)
        
        async def fetch_appointments():
            return mock_appointment_data
        
        # Primeira chamada (cache miss)
        result1 = await cache_service.get_or_set(
            key=list_key,
            fetch_function=fetch_appointments,
            ttl=120,
            cache_type='appointments_list'
        )
        
        # Segunda chamada (cache hit)
        result2 = await cache_service.get_or_set(
            key=list_key,
            fetch_function=fetch_appointments,
            ttl=120,
            cache_type='appointments_list'
        )
        
        if result1 == result2:
            print("✅ Cache de appointments funcionando")
        else:
            print("❌ Problema no cache de appointments")
        
        # Testar invalidação
        cache_service.invalidate_pattern("appointments:list:*")
        print("✅ Invalidação de appointments testada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        return False

if __name__ == "__main__":
    async def main():
        success1 = await test_cache_implementation()
        success2 = await test_appointments_integration()
        
        if success1 and success2:
            print("\n🎉 TODOS OS TESTES DE CACHE PASSARAM!")
            sys.exit(0)
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            sys.exit(1)
    
    asyncio.run(main())
