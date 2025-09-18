#!/usr/bin/env python3
"""
DEBUG MIDDLEWARE DIRETO - TESTE DE LÓGICA
========================================
Testa diretamente a lógica do middleware sem depender do Railway
"""

import sys
import os

# Adicionar path do projeto
sys.path.append('/home/vancim/whats_agent')

from app.auth.middleware import AuthMiddleware

def test_middleware_logic():
    """Testa a lógica do middleware diretamente"""
    
    print("🔍 TESTE DIRETO DA LÓGICA DO MIDDLEWARE")
    print("=" * 60)
    
    # Criar instância do middleware
    middleware = AuthMiddleware(app=None)
    
    # Endpoints de teste
    test_paths = [
        "/health",
        "/ping", 
        "/docs",
        "/meta",
        "/meta/webhook",
        "/meta/webhook/verify",
        "/debug",
        "/debug/public-endpoints",
        "/webhook",
        "/webhook/verify", 
        "/auth/login",
        "/admin/dashboard",  # Deveria ser privado
        "/users/profile"     # Deveria ser privado
    ]
    
    print(f"📋 Endpoints públicos configurados ({len(middleware.public_endpoints)}):")
    for endpoint in sorted(middleware.public_endpoints):
        print(f"   - {endpoint}")
    
    print(f"\n🧪 TESTE DE VERIFICAÇÃO DE ENDPOINTS:")
    print("-" * 60)
    
    for path in test_paths:
        is_public = middleware._is_public_endpoint(path)
        status = "✅ PÚBLICO" if is_public else "❌ PRIVADO"
        print(f"{path:<30} -> {status}")
        
        # Debug para endpoints problemáticos
        if "/meta" in path or "/debug" in path:
            print(f"   🔍 Debug para '{path}':")
            
            matches = []
            for public_path in middleware.public_endpoints:
                exact_match = path == public_path
                prefix_match = path.startswith(public_path + "/")
                
                if exact_match:
                    matches.append(f"Exact match: '{public_path}'")
                elif prefix_match:
                    matches.append(f"Prefix match: '{public_path}/'")
            
            if matches:
                for match in matches:
                    print(f"      ✅ {match}")
            else:
                print(f"      ❌ Nenhum match encontrado")
    
    print("\n" + "=" * 60)
    
    # Teste específico para meta webhook verify
    critical_path = "/meta/webhook/verify"
    is_critical_public = middleware._is_public_endpoint(critical_path)
    
    print(f"🎯 TESTE CRÍTICO: {critical_path}")
    print(f"   Resultado: {'✅ PÚBLICO' if is_critical_public else '❌ PRIVADO (PROBLEMA!)'}")
    
    if not is_critical_public:
        print("   🚨 ERRO: Este endpoint deveria ser público!")
        print("   🔧 Verificar configuração do middleware")
    else:
        print("   ✅ OK: Lógica do middleware está correta")
        print("   💡 Problema pode estar no deploy ou em outro middleware")
    
    return is_critical_public

if __name__ == "__main__":
    try:
        result = test_middleware_logic()
        if result:
            print("\n✅ LÓGICA DO MIDDLEWARE: OK")
            print("🔍 PRÓXIMO PASSO: Verificar deploy e outros middlewares")
        else:
            print("\n❌ LÓGICA DO MIDDLEWARE: PROBLEMA")
            print("🔧 PRÓXIMO PASSO: Corrigir configuração")
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()