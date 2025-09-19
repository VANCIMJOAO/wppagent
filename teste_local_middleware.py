#!/usr/bin/env python3
"""
🧪 TESTE LOCAL MIDDLEWARE - Verificar Correção Localmente
Testa a reordenação dos middlewares localmente
"""

import subprocess
import time
import requests
import signal
import os
from datetime import datetime

def testar_localmente():
    """Testa a aplicação localmente"""
    print("🧪 TESTE LOCAL MIDDLEWARE - VERIFICAR CORREÇÃO")
    print("=" * 60)
    
    # Iniciar servidor local
    print("🚀 Iniciando servidor local...")
    
    try:
        # Iniciar uvicorn em background
        process = subprocess.Popen([
            "python", "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguardar servidor inicializar
        print("⏳ Aguardando servidor inicializar...")
        time.sleep(10)
        
        # Testar endpoints
        base_url = "http://localhost:8000"
        
        print("\n📋 TESTANDO ENDPOINTS LOCAIS:")
        print("-" * 40)
        
        # Teste 1: /ping
        try:
            response = requests.get(f"{base_url}/ping", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} GET /ping: {response.status_code}")
            if response.status_code != 200:
                print(f"      Content: {response.text[:100]}...")
        except Exception as e:
            print(f"   ❌ GET /ping: ERRO - {str(e)}")
        
        # Teste 2: /health
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} GET /health: {response.status_code}")
        except Exception as e:
            print(f"   ❌ GET /health: ERRO - {str(e)}")
        
        # Teste 3: /docs
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} GET /docs: {response.status_code}")
        except Exception as e:
            print(f"   ❌ GET /docs: ERRO - {str(e)}")
        
        # Teste 4: /meta/webhook/verify
        try:
            response = requests.post(f"{base_url}/meta/webhook/verify", json={}, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} POST /meta/webhook/verify: {response.status_code}")
            if response.status_code != 200:
                print(f"      Content: {response.text[:100]}...")
        except Exception as e:
            print(f"   ❌ POST /meta/webhook/verify: ERRO - {str(e)}")
        
        # Teste 5: Múltiplas requisições para /ping (testar rate limiting)
        print("\n📋 TESTANDO RATE LIMITING:")
        print("-" * 40)
        
        for i in range(5):
            try:
                response = requests.get(f"{base_url}/ping", timeout=5)
                status = "✅" if response.status_code == 200 else "❌"
                print(f"   {status} Requisição {i+1} /ping: {response.status_code}")
                
                if response.status_code == 429:
                    try:
                        content = response.json()
                        print(f"      Rate limit: {content}")
                    except:
                        pass
                
                time.sleep(1)  # Aguardar 1 segundo entre requisições
                
            except Exception as e:
                print(f"   ❌ Requisição {i+1} /ping: ERRO - {str(e)}")
        
        print("\n✅ TESTE LOCAL CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro ao testar localmente: {str(e)}")
    
    finally:
        # Parar servidor
        try:
            process.terminate()
            process.wait(timeout=5)
            print("🛑 Servidor local parado")
        except:
            try:
                process.kill()
                print("🛑 Servidor local forçado a parar")
            except:
                print("⚠️ Não foi possível parar o servidor local")

def main():
    """Executa teste local"""
    print("🧪 TESTE LOCAL MIDDLEWARE - VERIFICAR CORREÇÃO")
    print("=" * 80)
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    testar_localmente()
    
    print("\n" + "=" * 80)
    print("🎉 TESTE LOCAL CONCLUÍDO!")
    print("=" * 80)

if __name__ == "__main__":
    main()

