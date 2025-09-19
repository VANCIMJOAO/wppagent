#!/usr/bin/env python3
"""
🔍 DEBUG AUTH MIDDLEWARE - Verificar Lógica de Endpoints Públicos
Testa especificamente se o AuthMiddleware está reconhecendo /ping como público
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth.middleware import AuthMiddleware

def test_auth_middleware():
    """Testa a lógica do AuthMiddleware"""
    print("🔍 DEBUG AUTH MIDDLEWARE - VERIFICAR LÓGICA")
    print("=" * 60)
    
    # Criar instância do middleware
    middleware = AuthMiddleware(app=None)
    
    # Testar endpoints
    test_endpoints = [
        "/ping",
        "/health",
        "/docs",
        "/meta/webhook/verify",
        "/meta/webhook",
        "/webhook",
        "/auth/login",
        "/admin/login",
        "/",
        "/metrics",
        "/cors/test"
    ]
    
    print("📋 TESTANDO ENDPOINTS PÚBLICOS:")
    print("-" * 40)
    
    for endpoint in test_endpoints:
        is_public = middleware._is_public_endpoint(endpoint)
        status = "✅" if is_public else "❌"
        print(f"   {status} {endpoint}: {'PÚBLICO' if is_public else 'PRIVADO'}")
    
    print("\n📋 VERIFICANDO CONFIGURAÇÃO:")
    print("-" * 40)
    
    print(f"   Total de endpoints públicos: {len(middleware.public_endpoints)}")
    print("   Endpoints públicos configurados:")
    for endpoint in sorted(middleware.public_endpoints):
        print(f"      - {endpoint}")
    
    print("\n📋 TESTANDO LÓGICA ESPECÍFICA:")
    print("-" * 40)
    
    # Testar lógica específica para /ping
    ping_tests = [
        "/ping",
        "/ping/",
        "/ping/test",
        "/ping?test=1",
        "/ping#test"
    ]
    
    for test_path in ping_tests:
        is_public = middleware._is_public_endpoint(test_path)
        status = "✅" if is_public else "❌"
        print(f"   {status} {test_path}: {'PÚBLICO' if is_public else 'PRIVADO'}")
    
    print("\n📋 TESTANDO LÓGICA DE PREFIXO:")
    print("-" * 40)
    
    # Testar lógica de prefixo
    prefix_tests = [
        ("/meta", "/meta/webhook/verify"),
        ("/meta/webhook", "/meta/webhook/verify"),
        ("/webhook", "/webhook/test"),
        ("/ping", "/ping/test")
    ]
    
    for prefix, full_path in prefix_tests:
        is_public = middleware._is_public_endpoint(full_path)
        status = "✅" if is_public else "❌"
        print(f"   {status} {full_path} (prefixo {prefix}): {'PÚBLICO' if is_public else 'PRIVADO'}")

def test_middleware_instantiation():
    """Testa se o middleware pode ser instanciado corretamente"""
    print("\n🔍 TESTANDO INSTANCIAÇÃO DO MIDDLEWARE:")
    print("-" * 40)
    
    try:
        middleware = AuthMiddleware(app=None)
        print("   ✅ AuthMiddleware instanciado com sucesso")
        
        # Verificar se os atributos estão corretos
        print(f"   ✅ public_endpoints: {len(middleware.public_endpoints)} endpoints")
        print(f"   ✅ jwt_manager: {middleware.jwt_manager is not None}")
        print(f"   ✅ two_factor: {middleware.two_factor is not None}")
        print(f"   ✅ rate_limiter: {middleware.rate_limiter is not None}")
        print(f"   ✅ secrets_manager: {middleware.secrets_manager is not None}")
        
    except Exception as e:
        print(f"   ❌ Erro ao instanciar AuthMiddleware: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

def main():
    """Executa todos os testes de debug"""
    print("🔍 DEBUG AUTH MIDDLEWARE - VERIFICAR LÓGICA")
    print("=" * 80)
    
    test_middleware_instantiation()
    test_auth_middleware()
    
    print("\n" + "=" * 80)
    print("🎉 DEBUG AUTH MIDDLEWARE CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()

