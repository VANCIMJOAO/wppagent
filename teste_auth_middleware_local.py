#!/usr/bin/env python3
"""
🔍 TESTE LOCAL - AuthMiddleware
Testa se a correção está funcionando localmente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth.middleware import AuthMiddleware

def test_auth_middleware():
    """Testa o AuthMiddleware localmente"""
    print("🔍 TESTE LOCAL - AuthMiddleware")
    print("=" * 50)
    
    # Criar instância do middleware
    middleware = AuthMiddleware(None)
    
    # Testar endpoints críticos
    critical_endpoints = ["/ping", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway", "/health"]
    
    print("📋 Testando endpoints críticos:")
    for endpoint in critical_endpoints:
        is_public = middleware._is_public_endpoint(endpoint)
        status = "✅" if is_public else "❌"
        print(f"   {status} {endpoint}: {'PÚBLICO' if is_public else 'PRIVADO'}")
    
    print("\n📋 Testando endpoints privados:")
    private_endpoints = ["/admin", "/users", "/api/private", "/dashboard"]
    
    for endpoint in private_endpoints:
        is_public = middleware._is_public_endpoint(endpoint)
        status = "✅" if not is_public else "❌"
        print(f"   {status} {endpoint}: {'PRIVADO' if not is_public else 'PÚBLICO'}")
    
    print("\n📋 Verificando configuração:")
    print(f"   public_endpoints: {len(middleware.public_endpoints)} endpoints")
    print(f"   /ping em public_endpoints: {'/ping' in middleware.public_endpoints}")
    print(f"   /emergency em public_endpoints: {'/emergency' in middleware.public_endpoints}")
    print(f"   /railway-health em public_endpoints: {'/railway-health' in middleware.public_endpoints}")

if __name__ == "__main__":
    test_auth_middleware()

