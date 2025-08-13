#!/usr/bin/env python3
"""
Script temporário para debug do webhook secret
"""
import os
import sys

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, '/home/vancim/whats_agent')

try:
    from app.config import settings
    from app.services.whatsapp_security import WhatsAppSecurityService
    
    print("🔍 Debug Webhook Secret Configuration")
    print("=" * 50)
    
    # Verificar settings
    webhook_secret_raw = settings.whatsapp_webhook_secret
    print(f"Settings webhook_secret type: {type(webhook_secret_raw)}")
    print(f"Settings webhook_secret exists: {bool(webhook_secret_raw)}")
    
    if webhook_secret_raw:
        if hasattr(webhook_secret_raw, 'get_secret_value'):
            secret_value = webhook_secret_raw.get_secret_value()
            print(f"Secret value length: {len(secret_value)}")
            print(f"Secret value (first 8 chars): {secret_value[:8]}...")
            print(f"Secret value (last 8 chars): ...{secret_value[-8:]}")
        else:
            print(f"Secret value length: {len(webhook_secret_raw)}")
            print(f"Secret value (first 8 chars): {webhook_secret_raw[:8]}...")
    
    # Verificar service
    service = WhatsAppSecurityService()
    print(f"\nService webhook_secret type: {type(service.webhook_secret)}")
    print(f"Service webhook_secret exists: {bool(service.webhook_secret)}")
    
    if service.webhook_secret:
        print(f"Service secret length: {len(service.webhook_secret)}")
        print(f"Service secret (first 8 chars): {service.webhook_secret[:8]}...")
        print(f"Service secret (last 8 chars): ...{service.webhook_secret[-8:]}")
    
    # Verificar variável de ambiente
    env_secret = os.getenv('WHATSAPP_WEBHOOK_SECRET')
    print(f"\nENV WHATSAPP_WEBHOOK_SECRET exists: {bool(env_secret)}")
    if env_secret:
        print(f"ENV secret length: {len(env_secret)}")
        print(f"ENV secret (first 8 chars): {env_secret[:8]}...")
        print(f"ENV secret (last 8 chars): ...{env_secret[-8:]}")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
