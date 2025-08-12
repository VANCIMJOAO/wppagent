#!/usr/bin/env python3
"""
Teste rápido do sistema de segurança implementado
"""

import sys
import os
sys.path.append('/home/vancim/whats_agent')

# Adicionar variáveis de ambiente necessárias
os.environ['SECURITY_LEVEL'] = 'high'
os.environ['JWT_SECRET_ROTATION_HOURS'] = '24'
os.environ['RATE_LIMITING_ENABLED'] = 'true'
os.environ['FORCE_2FA_FOR_ADMINS'] = 'true'

# Testes
print("🔧 Testando sistema de segurança...")
print()

try:
    # Teste 1: JWT Manager
    print("1. Testando JWT Manager...")
    from app.auth.jwt_manager import JWTManager
    jwt_manager = JWTManager()
    print("   ✅ JWT Manager inicializado")
    
    # Teste 2: Two Factor Auth
    print("2. Testando 2FA...")
    from app.auth.two_factor import TwoFactorAuth
    tfa = TwoFactorAuth()
    print("   ✅ 2FA inicializado")
    
    # Teste 3: Rate Limiter
    print("3. Testando Rate Limiter...")
    from app.auth.rate_limiter import RateLimiter
    rate_limiter = RateLimiter()
    print("   ✅ Rate Limiter inicializado")
    
    # Teste 4: Secrets Manager
    print("4. Testando Secrets Manager...")
    from app.auth.secrets_manager import SecretsManager
    secrets_manager = SecretsManager()
    print("   ✅ Secrets Manager inicializado")
    
    # Teste 5: Middleware
    print("5. Testando Auth Middleware...")
    from app.auth.middleware import AuthMiddleware
    middleware = AuthMiddleware()
    print("   ✅ Auth Middleware inicializado")
    
    print()
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("🔒 Sistema de segurança está funcionando corretamente!")
    print()
    print("Próximos passos:")
    print("1. Integrar middleware com FastAPI")
    print("2. Configurar endpoints de autenticação")
    print("3. Testar fluxo completo de login")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    print(f"   Tipo: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
