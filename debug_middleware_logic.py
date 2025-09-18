#!/usr/bin/env python3
"""
DEBUG MIDDLEWARE - Testar lógica de endpoints públicos
"""

def test_public_endpoint_logic():
    """Testa a lógica de verificação de endpoints públicos"""
    
    public_endpoints = {
        "/health",
        "/ping",
        "/docs", 
        "/openapi.json",
        "/webhook",
        "/webhook/test",
        "/meta",
        "/meta/webhook", 
        "/api/v1/webhooks",
        "/auth/login",
        "/admin/login",
        "/admin/create-initial-admin",
        "/admin/debug-admin",
        "/admin/debug-jwt",
        "/auth/register",
        "/metrics",
        "/metrics/system",
        "/cors/test",
        "/cors/debug",
        "/appointments/test",
        "/",
    }
    
    test_paths = [
        "/health",
        "/ping", 
        "/docs",
        "/meta",
        "/meta/webhook",
        "/meta/webhook/verify",
        "/webhook",
        "/webhook/verify",
        "/webhook/test",
        "/unknown/path"
    ]
    
    print("TESTE DE LÓGICA DE ENDPOINTS PÚBLICOS")
    print("=" * 50)
    
    def is_public_endpoint(path: str) -> bool:
        """Replica a lógica do middleware"""
        for public_path in public_endpoints:
            if path == public_path or path.startswith(public_path + "/"):
                return True
        return False
    
    for path in test_paths:
        result = is_public_endpoint(path)
        status = "✅ PÚBLICO" if result else "❌ PRIVADO"
        print(f"{path:<25} -> {status}")
        
        # Debug detalhado para paths problemáticos
        if "/meta" in path:
            print(f"   Debug: checking against public endpoints...")
            for public_path in public_endpoints:
                if path == public_path:
                    print(f"   -> Exact match with '{public_path}'")
                elif path.startswith(public_path + "/"):
                    print(f"   -> Prefix match with '{public_path}/' (path starts with '{public_path}/')")
    
    print("\n" + "=" * 50)
    print("ANÁLISE:")
    
    # Verificar casos específicos
    meta_webhook_verify = "/meta/webhook/verify"
    print(f"\nTestando '{meta_webhook_verify}':")
    
    for public_path in public_endpoints:
        exact_match = meta_webhook_verify == public_path
        prefix_match = meta_webhook_verify.startswith(public_path + "/")
        
        if exact_match or prefix_match:
            print(f"✅ Match com '{public_path}' - Exact: {exact_match}, Prefix: {prefix_match}")
    
    # Verificar se /meta/webhook/verify deveria ser público
    should_be_public = is_public_endpoint(meta_webhook_verify)
    print(f"\n/meta/webhook/verify é público? {should_be_public}")

if __name__ == "__main__":
    test_public_endpoint_logic()