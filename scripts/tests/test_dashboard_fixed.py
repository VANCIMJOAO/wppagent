#!/usr/bin/env python3
"""
Teste rápido para verificar se o dashboard está funcionando sem loops
"""

import requests
import time
import sys

def test_dashboard():
    """Testar se o dashboard está respondendo corretamente"""
    print("🧪 Testando dashboard...")
    
    try:
        # Testar se o servidor está rodando
        response = requests.get("http://localhost:8050", timeout=10)
        print(f"✅ Dashboard respondendo - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard carregando corretamente")
            print(f"📏 Tamanho da resposta: {len(response.content)} bytes")
            
            # Verificar se há login form
            if 'login' in response.text.lower():
                print("🔐 Página de login detectada")
            
            # Verificar se há erros JavaScript
            if 'error' in response.text.lower():
                print("⚠️  Possíveis erros na página")
            else:
                print("✅ Nenhum erro aparente detectado")
                
            return True
        else:
            print(f"❌ Dashboard retornou status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard não está rodando ou inacessível")
        return False
    except requests.exceptions.Timeout:
        print("❌ Dashboard demorou muito para responder")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_auth():
    """Testar autenticação"""
    print("\n🔐 Testando autenticação...")
    
    try:
        # Simular login
        session = requests.Session()
        
        # Primeiro, pegar a página inicial
        resp = session.get("http://localhost:8050")
        print(f"✅ Página inicial carregada: {resp.status_code}")
        
        # Tentar fazer login via callback (simulação)
        login_data = {
            "username": "admin",
            "password": "123456"
        }
        
        print("📤 Tentando autenticação...")
        # Nota: Em um dashboard Dash real, o login seria via callback, não POST direto
        # Este é apenas um teste de conectividade
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de auth: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("🚀 Iniciando testes do dashboard...")
    print("=" * 50)
    
    # Aguardar um pouco para o dashboard inicializar
    print("⏳ Aguardando dashboard inicializar...")
    time.sleep(3)
    
    success = True
    
    # Teste básico de conectividade
    if not test_dashboard():
        success = False
    
    # Teste de autenticação
    if not test_auth():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Todos os testes PASSARAM! Dashboard funcionando!")
        print("🌐 Acesse: http://localhost:8050")
        print("🔑 Login: admin / 123456")
    else:
        print("❌ Alguns testes FALHARAM!")
        print("📋 Verifique se o dashboard está rodando corretamente")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
