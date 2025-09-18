#!/usr/bin/env python3
"""
TESTE DIRETO DA META WHATSAPP API
=================================
Testa diretamente a API da Meta para verificar se as credenc    try:
        response = requests.post(f"{railway_url}/webhook/test", 
                               json=webhook_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook processado com sucesso!")
        else:
            print("❌ Webhook com problema - verificar autenticação")
    except Exception as e:
        print(f"❌ Erro: {e}")uncionando
"""

import requests
import json
from datetime import datetime

# Suas credenciais Meta
META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPS1qkBjfZAnI8qdXInJ3Lxgc7IAn35PvZAAhdeRELACQTUspzTFViQ6OfzzjqbzS9ZCutlTTTTzNmz8ezkeGtCkGtyxujzcN67ZBEKzriS79jlXxbqoZBw3f0MAMTOZCVKpeq2fTbUd6f4h2tvoCAXSLb9vPf1C0EQXyvKZA3986WNYeZA4vrfanZBLJyVLppTnjVupAGZAyOfRaey3ebfWz4CeLCEK5JbfjXQCNQGhT8dx0gQZAAZDZD"
META_PHONE_NUMBER_ID = "728348237027885"

def test_meta_api_direct():
    """Testa diretamente a API da Meta"""
    print("🔍 TESTANDO DIRETAMENTE A API DA META WHATSAPP")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {META_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Teste 1: Verificar informações do phone number
    print("\n📱 Teste 1: Verificando informações do número...")
    url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Número verificado: {data.get('display_phone_number', 'N/A')}")
            print(f"📋 Status: {data.get('status', 'N/A')}")
            print(f"📊 Quality Rating: {data.get('quality_rating', 'N/A')}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 2: Verificar webhook
    print("\n🔗 Teste 2: Verificando configuração de webhook...")
    webhook_url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}/webhooks"
    
    try:
        response = requests.get(webhook_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhooks configurados: {len(data.get('data', []))}")
            for webhook in data.get('data', []):
                print(f"  📍 URL: {webhook.get('callback_url', 'N/A')}")
                print(f"  🔔 Eventos: {webhook.get('fields', [])}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 3: Enviar mensagem de teste (para um número válido)
    print("\n📤 Teste 3: Testando envio de mensagem...")
    message_url = f"https://graph.facebook.com/v18.0/{META_PHONE_NUMBER_ID}/messages"
    
    # Use seu próprio número para teste
    test_message = {
        "messaging_product": "whatsapp",
        "to": "5511999999999",  # Substitua por um número válido para teste
        "type": "text",
        "text": {
            "body": f"Teste direto da Meta API - {datetime.now().strftime('%H:%M:%S')}"
        }
    }
    
    try:
        response = requests.post(message_url, json=test_message, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            print(f"✅ Mensagem enviada! ID: {message_id}")
        else:
            print(f"❌ Erro no envio: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 4: Verificar permissões do token
    print("\n🔐 Teste 4: Verificando permissões do token...")
    me_url = "https://graph.facebook.com/v18.0/me"
    
    try:
        response = requests.get(me_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ App ID: {data.get('id', 'N/A')}")
            print(f"📋 Nome: {data.get('name', 'N/A')}")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

def test_railway_webhook_endpoint():
    """Testa o endpoint de webhook do Railway"""
    print("\n\n🚂 TESTANDO ENDPOINT DE WEBHOOK DO RAILWAY")
    print("=" * 60)
    
    railway_url = "https://wppagent-production-app-production.up.railway.app"
    
    # Teste 1: Verificação como o Meta faz
    print("\n✅ Teste 1: Verificação de webhook (como Meta faz)...")
    verify_params = {
        "hub.mode": "subscribe", 
        "hub.verify_token": "your_verify_token_here",  # Token atual no Railway
        "hub.challenge": "12345"  # Deve ser número para int() funcionar
    }
    
    try:
        response = requests.get(f"{railway_url}/webhook/verify", params=verify_params, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200 and "12345" in response.text:
            print("✅ Webhook verification funcionando!")
        else:
            print("❌ Webhook verification com problema")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 2: Envio de webhook como Meta enviaria
    print("\n📱 Teste 2: Enviando webhook como Meta enviaria...")
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": META_PHONE_NUMBER_ID
                    },
                    "messages": [{
                        "id": f"wamid.test_{int(datetime.now().timestamp())}",
                        "from": "5511999999999",
                        "timestamp": str(int(datetime.now().timestamp())),
                        "text": {"body": "Teste direto de webhook"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        response = requests.post(f"{railway_url}/api/v1/webhooks/whatsapp", 
                               json=webhook_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook processado com sucesso!")
        else:
            print("❌ Webhook com problema - verificar autenticação")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🔥 TESTE DIRETO DAS APIS - DIAGNÓSTICO COMPLETO")
    print("=" * 80)
    
    test_meta_api_direct()
    test_railway_webhook_endpoint()
    
    print("\n" + "=" * 80)
    print("🎯 DIAGNÓSTICO CONCLUÍDO!")
    print("✨ Verifique os resultados acima para identificar problemas específicos")
    print("=" * 80)