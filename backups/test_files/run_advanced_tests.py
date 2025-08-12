"""
🚀 EXECUTAR TESTES AVANÇADOS
Suite completa de testes avançados para WhatsApp Agent
"""

import pytest
import sys
import os
from datetime import datetime
import json

# Adicionar diretório do projeto ao Python path
sys.path.insert(0, '/home/vancim/whats_agent')

def run_advanced_tests():
    """Executar todos os testes avançados"""
    
    print("🚀 INICIANDO TESTES AVANÇADOS DO WHATSAPP AGENT")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Configurar pytest com verbosidade máxima
    pytest_args = [
        "/home/vancim/whats_agent/tests/advanced_testing/",
        "-v",  # verbose
        "-s",  # não capturar output
        "--tb=long",  # traceback completo
        "--capture=no",  # mostrar prints em tempo real
        "--durations=10",  # mostrar 10 testes mais lentos
        "--maxfail=10",  # parar após 10 falhas
        f"--html=/home/vancim/whats_agent/tests/advanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        "--self-contained-html"
    ]
    
    # Executar testes
    exit_code = pytest.main(pytest_args)
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("🎉 TODOS OS TESTES AVANÇADOS PASSARAM!")
    else:
        print(f"❌ ALGUNS TESTES FALHARAM (exit code: {exit_code})")
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    # Verificar se estamos no diretório correto
    if not os.path.exists("/home/vancim/whats_agent/app"):
        print("❌ Execute este script do diretório do projeto WhatsApp Agent")
        sys.exit(1)
    
    # Instalar dependências necessárias se não estiverem instaladas
    try:
        import selenium
    except ImportError:
        print("📦 Instalando selenium para testes de dashboard...")
        os.system("pip install selenium webdriver-manager")
    
    try:
        import pytest_html
    except ImportError:
        print("📦 Instalando pytest-html para relatórios...")
        os.system("pip install pytest-html")
    
    # Executar testes
    exit_code = run_advanced_tests()
    sys.exit(exit_code)
