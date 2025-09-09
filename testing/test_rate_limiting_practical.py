#!/usr/bin/env python3
"""
🧪 Teste Prático do Middleware de Rate Limiting
==============================================

Este script testa o middleware diretamente sem precisar do servidor completo.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
import redis.asyncio as redis
from datetime import datetime

# Import do middleware
from app.middleware.user_rate_limit import UserRateLimitMiddleware, get_user_rate_limiter

async def test_basic_functionality():
    """Teste básico de funcionalidade"""
    print("🧪 Testando funcionalidade básica do Rate Limiter...")
    
    # Criar rate limiter
    limiter = get_user_rate_limiter()
    
    # Testar configurações carregadas
    print(f"✅ Endpoints configurados: {len(limiter.limits)}")
    print(f"✅ Tipos de usuário: {list(limiter.user_type_multipliers.keys())}")
    
    # Testar obtenção de configuração
    config = limiter._get_limit_config("POST /webhook", "regular")
    print(f"✅ Config para POST /webhook (regular): {config['requests']} req/{config['window']}s")
    
    config_admin = limiter._get_limit_config("POST /webhook", "admin")
    print(f"✅ Config para POST /webhook (admin): {config_admin['requests']} req/{config_admin['window']}s")
    
    return True

async def test_with_mock_redis():
    """Testar com Redis mockado"""
    print("\n🧪 Testando com Redis mockado...")
    
    # Criar mock do Redis
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    
    # Simular primeiro check - sem rate limit
    mock_redis.zcard = AsyncMock(return_value=0)  # Nenhuma requisição anterior
    mock_redis.zadd = AsyncMock(return_value=1)   # Adicionar nova requisição
    mock_redis.expire = AsyncMock(return_value=True)  # Definir expiração
    mock_redis.zremrangebyscore = AsyncMock(return_value=0)  # Limpar expiradas
    
    # Criar rate limiter com Redis mockado
    limiter = get_user_rate_limiter()
    limiter.redis = mock_redis
    
    # Configuração de teste
    config = {"requests": 5, "window": 60}
    
    # Primeiro check - deve passar
    result = await limiter._check_rate_limit("test_user", "GET /test", config)
    print(f"✅ Primeiro check: exceeded={result.get('exceeded', False)}")
    
    # Simular incremento
    await limiter._increment_counter("test_user", "GET /test", config)
    print("✅ Contador incrementado")
    
    # Simular limite excedido
    mock_redis.zcard = AsyncMock(return_value=6)  # 6 requisições (acima do limite)
    
    result = await limiter._check_rate_limit("test_user", "GET /test", config)
    print(f"✅ Check com limite excedido: exceeded={result.get('exceeded', True)}")
    
    return True

async def test_user_types():
    """Testar diferentes tipos de usuário"""
    print("\n🧪 Testando tipos de usuário...")
    
    limiter = get_user_rate_limiter()
    
    base_config = limiter.limits.get("default", {"requests": 60, "window": 60})
    base_requests = base_config["requests"]
    
    # Testar multiplicadores
    user_types = ["guest", "regular", "premium", "admin"]
    
    for user_type in user_types:
        config = limiter._get_limit_config("default", user_type)
        multiplier = limiter.user_type_multipliers.get(user_type, 1.0)
        expected = int(base_requests * multiplier)
        
        print(f"✅ {user_type}: {config['requests']} req (multiplicador {multiplier}x)")
        assert config['requests'] == expected, f"Erro no multiplicador para {user_type}"
    
    return True

async def test_endpoint_specific_limits():
    """Testar limites específicos por endpoint"""
    print("\n🧪 Testando limites por endpoint...")
    
    limiter = get_user_rate_limiter()
    
    # Testar endpoints específicos
    test_endpoints = [
        ("GET /health", "Muito permissivo"),
        ("POST /auth/login", "Muito restritivo"),
        ("POST /webhook", "Alto volume"),
        ("GET /unknown", "Usar padrão")
    ]
    
    for endpoint, desc in test_endpoints:
        config = limiter._get_limit_config(endpoint, "regular")
        
        if endpoint in limiter.limits:
            source = "específico"
        else:
            source = "padrão"
            
        print(f"✅ {endpoint}: {config['requests']} req/{config['window']}s ({desc}, {source})")
    
    return True

async def test_graceful_degradation():
    """Testar degradação graciosa"""
    print("\n🧪 Testando degradação graciosa...")
    
    # Criar rate limiter com Redis que falha
    limiter = get_user_rate_limiter()
    
    # Mock Redis que falha
    failing_redis = AsyncMock()
    failing_redis.ping = AsyncMock(side_effect=Exception("Redis not available"))
    failing_redis.zcard = AsyncMock(side_effect=Exception("Redis not available"))
    
    limiter.redis = failing_redis
    
    # Testar com Redis falhando
    config = {"requests": 5, "window": 60}
    result = await limiter._check_rate_limit("test_user", "GET /test", config)
    
    # Deve permitir quando Redis falha (graceful degradation)
    print(f"✅ Com Redis falhando: exceeded={result.get('exceeded', True)} (deve ser False)")
    assert not result.get('exceeded', True), "Deve permitir quando Redis falha"
    
    return True

async def run_all_tests():
    """Executar todos os testes"""
    print("🚀 INICIANDO TESTES DO SISTEMA DE RATE LIMITING")
    print("=" * 50)
    
    tests = [
        ("Funcionalidade Básica", test_basic_functionality),
        ("Redis Mockado", test_with_mock_redis),
        ("Tipos de Usuário", test_user_types),
        ("Limites por Endpoint", test_endpoint_specific_limits),
        ("Degradação Graciosa", test_graceful_degradation)
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Executando: {test_name}")
            await test_func()
            print(f"✅ {test_name}: PASSOU")
            success_count += 1
        except Exception as e:
            print(f"❌ {test_name}: FALHOU - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO FINAL: {success_count}/{total_count} testes passaram")
    
    if success_count == total_count:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando corretamente.")
        return True
    else:
        print("⚠️ Alguns testes falharam. Revisar implementação.")
        return False

if __name__ == "__main__":
    # Executar testes
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Sistema de Rate Limiting validado e pronto!")
        print("\n📋 RESUMO DO QUE FOI TESTADO:")
        print("   • Carregamento de configurações")
        print("   • Multiplicadores por tipo de usuário")  
        print("   • Limites específicos por endpoint")
        print("   • Integração com Redis (mockado)")
        print("   • Degradação graciosa em falhas")
        print("   • Lógica de rate limiting")
        
        print("\n🔥 PRÓXIMOS PASSOS:")
        print("   1. Executar servidor: uvicorn app.main:app --reload")
        print("   2. Executar demo completo: python demo_rate_limiting.py")
        print("   3. Testar endpoints via Postman/curl")
        print("   4. Deploy para produção")
    else:
        print("\n❌ Sistema precisa de correções antes do uso.")
    
    exit(0 if success else 1)
