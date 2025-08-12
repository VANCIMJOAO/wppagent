#!/usr/bin/env python3
"""
Debug do JWT Manager
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth import JWTManager
import json

def main():
    print("🔍 Debug do JWT Manager...")
    
    try:
        # Inicializar JWTManager
        jwt_manager = JWTManager()
        print("✅ JWTManager inicializado")
        
        # Criar token
        print("\n📝 Criando token de acesso...")
        token = jwt_manager.create_access_token(
            user_id="admin",
            role="admin",
            permissions=[]
        )
        print(f"✅ Token criado: {token[:50]}...")
        
        # Verificar token
        print("\n🔍 Verificando token...")
        payload = jwt_manager.verify_token(token)
        print(f"✅ Token válido!")
        print(f"📄 Payload: {json.dumps(payload, indent=2, default=str)}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
