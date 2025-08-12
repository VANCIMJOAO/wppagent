#!/usr/bin/env python3
"""
Debug dos módulos de autenticação
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_modules():
    print("🔍 Testando módulos...")
    
    try:
        from app.auth import TwoFactorAuth
        twofa = TwoFactorAuth()
        print("✅ TwoFactorAuth inicializado")
        
        # Testar geração de secret
        secret = twofa.generate_secret()
        print(f"✅ Secret gerado: {secret[:10]}...")
        
    except Exception as e:
        print(f"❌ Erro com TwoFactorAuth: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from app.auth import SecretsManager
        secrets_manager = SecretsManager()
        print("✅ SecretsManager inicializado")
        
        # Testar listagem
        secrets = secrets_manager.list_secrets()
        print(f"✅ Secrets listados: {len(secrets)} encontrados")
        
    except Exception as e:
        print(f"❌ Erro com SecretsManager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_modules()
