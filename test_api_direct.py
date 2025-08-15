#!/usr/bin/env python3
"""
🔧 TESTE API REST DIRETO
========================
Testa diretamente a API REST para verificar
se a formatação está funcionando
"""

import requests
import json

def test_api_direct():
    print("🔧 TESTE API REST DIRETO")
    print("=" * 40)
    
    # URL da API
    url = "https://wppagent-production.up.railway.app/chat"
    
    # Payload simulando uma mensagem
    payload = {
        "message": "Quais serviços vocês oferecem?",
        "phone": "15551536026",
        "business_id": 3
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"📡 Enviando para: {url}")
    print(f"📨 Mensagem: {payload['message']}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso!")
            print(f"🤖 Resposta: {data.get('response', 'N/A')[:300]}...")
            
            # Verificar se tem formatação
            response_text = data.get('response', '')
            if '💰' in response_text and '📋' in response_text:
                print("🎉 FORMATAÇÃO DETECTADA!")
            else:
                print("⚠️ Formatação não detectada")
                
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"📝 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_api_direct()
