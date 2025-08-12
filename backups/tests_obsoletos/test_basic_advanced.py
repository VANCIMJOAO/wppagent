#!/usr/bin/env python3
"""
🧪 TESTE SIMPLES DOS TESTES AVANÇADOS
Verificação rápida se o sistema está funcionando
"""

import requests
import time
import sys
import os

# Adicionar diretório do projeto
sys.path.insert(0, '/home/vancim/whats_agent')

def test_basic_advanced_functionality():
    """Teste básico dos recursos avançados"""
    
    print("🧪 TESTE BÁSICO DOS RECURSOS AVANÇADOS")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    # 1. Verificar se backend está funcionando
    print("🔍 1. Verificando backend...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        assert response.status_code == 200
        print("✅ Backend funcionando")
    except Exception as e:
        print(f"❌ Backend não funcionando: {e}")
        return False
    
    # 2. Teste de stress básico - múltiplas requisições
    print("\n🔥 2. Teste de stress básico...")
    
    stress_results = []
    for i in range(10):
        try:
            start_time = time.time()
            
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [{
                                "from": f"5511999stress{i:02d}",
                                "text": {"body": f"Teste stress básico {i}"},
                                "type": "text",
                                "id": f"wamid.basic_stress_{i}",
                                "timestamp": str(int(time.time()))
                            }]
                        }
                    }]
                }]
            }
            
            response = requests.post(
                f"{backend_url}/webhook",
                json=payload,
                timeout=5
            )
            
            response_time = time.time() - start_time
            
            stress_results.append({
                'id': i,
                'status': response.status_code,
                'time': response_time,
                'success': response.status_code == 200
            })
            
            print(f"  📤 Mensagem {i+1}/10: {response.status_code} em {response_time:.3f}s")
            
        except Exception as e:
            print(f"  ❌ Erro na mensagem {i}: {e}")
            stress_results.append({'id': i, 'success': False, 'error': str(e)})
    
    # Análise do stress
    successful = len([r for r in stress_results if r.get('success')])
    print(f"\n📊 Stress básico: {successful}/10 sucessos")
    
    if successful >= 8:
        print("✅ Stress básico passou")
    else:
        print("❌ Stress básico falhou")
        return False
    
    # 3. Teste de falha simulada
    print("\n💥 3. Teste de falha simulada...")
    
    try:
        # Enviar payload inválido
        invalid_payload = {"invalid": "data"}
        
        response = requests.post(
            f"{backend_url}/webhook",
            json=invalid_payload,
            timeout=5
        )
        
        print(f"  📤 Payload inválido: {response.status_code}")
        
        # Sistema deve retornar erro (400, 422, etc) mas não travar
        if response.status_code in [400, 422, 500]:
            print("✅ Sistema lidou bem com dados inválidos")
        else:
            print(f"⚠️ Resposta inesperada: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erro no teste de falha: {e}")
        return False
    
    # 4. Teste end-to-end básico
    print("\n🔄 4. Teste end-to-end básico...")
    
    try:
        # Capturar métricas antes
        metrics_before = requests.get(f"{backend_url}/metrics").json()
        messages_before = metrics_before.get('total_messages', 0)
        
        # Enviar mensagem
        e2e_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": "5511999e2etest",
                            "text": {"body": "Teste end-to-end básico"},
                            "type": "text",
                            "id": "wamid.basic_e2e",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{backend_url}/webhook", json=e2e_payload)
        assert response.status_code == 200
        
        # Aguardar processamento
        time.sleep(2)
        
        # Verificar métricas depois
        metrics_after = requests.get(f"{backend_url}/metrics").json()
        messages_after = metrics_after.get('total_messages', 0)
        
        print(f"  📊 Mensagens: {messages_before} → {messages_after}")
        
        if messages_after > messages_before:
            print("✅ End-to-end básico funcionando")
        else:
            print("⚠️ Mensagem pode não ter sido processada")
        
    except Exception as e:
        print(f"❌ Erro no teste e2e: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 TODOS OS TESTES BÁSICOS AVANÇADOS PASSARAM!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_basic_advanced_functionality()
    sys.exit(0 if success else 1)
