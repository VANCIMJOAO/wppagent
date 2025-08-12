#!/usr/bin/env python3
"""
Debug direto do TwoFactorAuth
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_2fa():
    print("🔍 Testando TwoFactorAuth diretamente...")
    
    try:
        from app.auth import TwoFactorAuth
        twofa = TwoFactorAuth()
        print("✅ TwoFactorAuth inicializado")
        
        # Testar geração de secret
        user_id = "admin"
        secret = twofa.generate_secret(user_id)
        print(f"✅ Secret gerado: {secret[:10]}...")
        
        # Testar geração de QR code
        qr_code = twofa.generate_qr_code(user_id, f"{user_id}@whatsapp-agent.com", secret)
        print(f"✅ QR Code gerado: {len(qr_code)} caracteres")
        print(f"📱 QR Code prefix: {qr_code[:50]}...")
        
        return {"secret": secret, "qr_code": qr_code[:100] + "..."}
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_2fa()
    if result:
        print("🎉 2FA funcionando!")
        print(f"Secret: {result['secret']}")
    else:
        print("❌ 2FA com problemas")
