#!/usr/bin/env python3
"""
Script de debug para testar localmente se a aplicação inicia corretamente
"""
import sys
import os
import subprocess
import time
import requests

# Simular ambiente Railway
os.environ['PORT'] = '8080'
os.environ['RAILWAY_ENVIRONMENT'] = 'production'
os.environ['RAILWAY_DETECTED'] = 'true'

# URLs de teste
test_urls = [
    'http://localhost:8080/ping',
    'http://localhost:8080/ready',
    'http://localhost:8080/alive',
    'http://localhost:8080/health',
    'http://localhost:8080/'
]

def start_server():
    """Inicia o servidor uvicorn localmente"""
    print("🚀 Iniciando servidor uvicorn com configurações Railway...")
    
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', '8080',
        '--log-level', 'debug',
        '--access-log',
        '--server-header'
    ]
    
    print(f"Comando: {' '.join(cmd)}")
    
    # Inicia em background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd='/home/vancim/whats_agent'
    )
    
    return process

def test_endpoints():
    """Testa os endpoints localmente"""
    print("\n🔍 Testando endpoints...")
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: {response.status_code} - {response.text[:100]}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {url}: {str(e)}")

def main():
    print("🐛 DEBUG STARTUP LOCAL - Simulando Railway")
    print("="*50)
    
    # Inicia servidor
    server_process = start_server()
    
    try:
        # Aguarda startup
        print("⏱️  Aguardando startup do servidor...")
        time.sleep(10)
        
        # Testa endpoints
        test_endpoints()
        
        # Mostra saída do servidor
        print("\n📋 Saída do servidor:")
        print("-" * 30)
        stdout, _ = server_process.communicate(timeout=5)
        print(stdout)
        
    except subprocess.TimeoutExpired:
        print("⚠️  Servidor ainda rodando, finalizando...")
        server_process.terminate()
        
        # Tenta testar mesmo assim
        test_endpoints()
        
        # Mostra saída parcial
        print("\n📋 Saída parcial do servidor:")
        print("-" * 30)
        try:
            stdout, _ = server_process.communicate(timeout=2)
            print(stdout)
        except:
            print("Não foi possível capturar saída")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        server_process.terminate()
    
    finally:
        if server_process.poll() is None:
            server_process.terminate()

if __name__ == "__main__":
    main()