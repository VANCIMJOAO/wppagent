#!/usr/bin/env python3
"""
H005: Monitor de Deploy PWA
Aguarda o deploy completar e testa o PWA
"""

import requests
import time
import json

def check_deployment_status():
    """Verifica se o deploy foi completado"""
    url = "https://wppagent-production-app-production.up.railway.app"
    
    print("🚀 Aguardando deploy do H005...")
    print("=" * 40)
    
    max_attempts = 20  # 10 minutos (30s cada)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{url}/manifest.json", timeout=10)
            
            if response.status_code == 200:
                print("✅ Deploy completado! Manifest.json acessível")
                return True
            elif response.status_code == 401:
                print(f"⏳ Tentativa {attempt + 1}/{max_attempts}: Ainda em deploy (401)...")
            else:
                print(f"⏳ Tentativa {attempt + 1}/{max_attempts}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"⏳ Tentativa {attempt + 1}/{max_attempts}: Conexão falhou")
            
        attempt += 1
        time.sleep(30)  # Aguarda 30 segundos
        
    print("❌ Timeout: Deploy não completou em 10 minutos")
    return False

def test_service_worker():
    """Testa se o service worker está acessível"""
    url = "https://wppagent-production-app-production.up.railway.app/sw-h005.js"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            if "H005" in content:
                print("✅ Service Worker H005 implantado com sucesso!")
                return True
            else:
                print("❌ Service Worker sem identificação H005")
                return False
        else:
            print(f"❌ Service Worker não acessível: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar Service Worker: {e}")
        return False

def main():
    print("🔄 H005: Monitoramento de Deploy PWA")
    print("=" * 50)
    print()
    
    # Aguarda deploy
    if check_deployment_status():
        print()
        print("🧪 Testando Service Worker...")
        if test_service_worker():
            print()
            print("🎉 H005: PWA implantado com sucesso!")
            print()
            print("📱 Próximos passos:")
            print("1. Execute: ./test_h005_automated.py")
            print("2. Execute: ./test_h005_manual.sh")
            print("3. Teste instalação do PWA no navegador")
            return True
        else:
            print("❌ Service Worker não funcionando")
            return False
    else:
        print("❌ Deploy não completou")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
