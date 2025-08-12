#!/usr/bin/env python3
"""
🧪 Teste Simples e Direto da API
Teste básico que funciona apenas com o backend rodando
"""

import requests
import time
import json
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config.test_settings import *
from app.database import SessionLocal
from app.models.database import User, Message


def test_backend_health():
    """🏥 Teste simples de health check"""
    print("🏥 Testando health check...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        
        print(f"✅ Health check OK: {data}")
        return True
        
    except Exception as e:
        print(f"❌ Health check falhou: {e}")
        return False


def test_webhook_simple():
    """📱 Teste simples do webhook"""
    print("📱 Testando webhook...")
    
    # Payload simples do WhatsApp
    payload = {
        "entry": [{
            "id": "PHONE_NUMBER_ID_TEST",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999887766",
                        "phone_number_id": "PHONE_NUMBER_ID_TEST"
                    },
                    "contacts": [{
                        "profile": {"name": "Teste Simples"},
                        "wa_id": "5511999000000"
                    }],
                    "messages": [{
                        "from": "5511999000000",
                        "id": f"wamid.test_simple_{int(time.time())}",
                        "timestamp": str(int(time.time())),
                        "text": {"body": "Olá, este é um teste simples"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        print(f"📱 Webhook response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook processado com sucesso")
            
            # Aguardar um pouco para processamento
            time.sleep(3)
            
            # Verificar se dados foram salvos
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.wa_id == "5511999000000").first()
                if user:
                    print(f"✅ Usuário criado: {user.nome}")
                    
                    messages = session.query(Message).filter(Message.user_id == user.id).all()
                    print(f"📨 Mensagens encontradas: {len(messages)}")
                else:
                    print("⚠️ Usuário não foi criado no banco")
                    
            finally:
                session.close()
            
            return True
        else:
            print(f"❌ Webhook falhou: {response.status_code}")
            try:
                print(f"Response: {response.text}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return False


def test_database_connection():
    """🗄️ Teste de conexão com banco"""
    print("🗄️ Testando conexão com banco...")
    
    try:
        session = SessionLocal()
        from sqlalchemy import text
        
        # Teste simples
        result = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"✅ Banco conectado - {result} usuários na tabela")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return False


def run_all_simple_tests():
    """🚀 Executa todos os testes simples"""
    print("🧪 EXECUTANDO TESTES SIMPLES")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_backend_health),
        ("Database Connection", test_database_connection), 
        ("Webhook", test_webhook_simple)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Executando: {test_name}")
        start_time = time.time()
        
        try:
            success = test_func()
            duration = time.time() - start_time
            
            results.append({
                'test': test_name,
                'success': success,
                'duration': duration
            })
            
            print(f"{'✅' if success else '❌'} {test_name} - {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            results.append({
                'test': test_name,
                'success': False,
                'duration': duration,
                'error': str(e)
            })
            print(f"❌ {test_name} - Erro: {e}")
    
    # Relatório final
    print(f"\n📊 RELATÓRIO DOS TESTES SIMPLES")
    print("=" * 40)
    
    successful = len([r for r in results if r['success']])
    total = len(results)
    
    print(f"🧪 Total: {total}")
    print(f"✅ Sucessos: {successful}")
    print(f"❌ Falhas: {total - successful}")
    print(f"📈 Taxa de sucesso: {successful/total*100:.1f}%")
    
    total_time = sum(r['duration'] for r in results)
    print(f"⏱️ Tempo total: {total_time:.2f}s")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['test']}: {result['duration']:.2f}s")
    
    return successful == total


if __name__ == "__main__":
    print("🧪 TESTES SIMPLES DO WHATSAPP AGENT")
    print("=" * 50)
    print("📋 Estes testes verificam funcionalidades básicas")
    print("🎯 Requisitos: Backend rodando em localhost:8000")
    print()
    
    # Verificar se backend está rodando
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend detectado - iniciando testes")
            success = run_all_simple_tests()
            
            if success:
                print("\n🎉 TODOS OS TESTES PASSARAM!")
                sys.exit(0)
            else:
                print("\n❌ ALGUNS TESTES FALHARAM!")
                sys.exit(1)
        else:
            print(f"❌ Backend não saudável: {response.status_code}")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend não está rodando em localhost:8000")
        print("💡 Execute primeiro: python app/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao verificar backend: {e}")
        sys.exit(1)
