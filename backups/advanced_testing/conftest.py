"""
⚙️ CONFIGURAÇÃO DOS TESTES AVANÇADOS
Configurações e fixtures compartilhadas para todos os testes avançados
"""

import pytest
import requests
import time
import subprocess
import psutil
import os
from datetime import datetime

# Configurações globais
BACKEND_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"
PROJECT_DIR = "/home/vancim/whats_agent"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuração global para todos os testes avançados"""
    print("\n🔧 CONFIGURANDO AMBIENTE DE TESTES AVANÇADOS")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    assert os.path.exists(PROJECT_DIR), f"Diretório do projeto não encontrado: {PROJECT_DIR}"
    
    # Verificar recursos do sistema
    memory = psutil.virtual_memory()
    print(f"💾 Memória disponível: {memory.available / (1024**3):.1f}GB")
    print(f"💻 CPU cores: {psutil.cpu_count()}")
    
    # Garantir que temos recursos suficientes
    assert memory.available > 512 * 1024 * 1024, "Memória insuficiente para testes avançados"
    
    # Verificar/iniciar serviços necessários
    ensure_backend_running()
    
    print("✅ Ambiente configurado com sucesso")
    print("=" * 50)
    
    yield
    
    print("\n🧹 LIMPEZA PÓS-TESTES")
    print("=" * 50)
    
    # Cleanup final se necessário
    cleanup_test_environment()

def ensure_backend_running():
    """Garantir que o backend está funcionando"""
    print("🔍 Verificando backend...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend já está rodando")
            return
    except:
        pass
    
    print("🚀 Iniciando backend...")
    
    # Verificar se há processo uvicorn rodando
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'uvicorn' in cmdline and 'app.main:app' in cmdline:
                print(f"✅ Backend encontrado (PID: {proc.info['pid']})")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Iniciar backend
    subprocess.Popen([
        "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ], cwd=PROJECT_DIR)
    
    # Aguardar backend ficar disponível
    for attempt in range(30):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend iniciado com sucesso")
                return
        except:
            time.sleep(1)
    
    raise Exception("Falha ao iniciar backend")

def cleanup_test_environment():
    """Limpeza do ambiente após os testes"""
    print("🧹 Executando limpeza final...")
    
    # Verificar se backend ainda está funcionando
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend ainda funcionando")
        else:
            print("⚠️ Backend não respondeu no cleanup")
    except Exception as e:
        print(f"⚠️ Erro ao verificar backend: {e}")
    
    print("✅ Limpeza concluída")

@pytest.fixture
def test_metrics():
    """Fixture para capturar métricas de teste"""
    test_start_time = time.time()
    
    # Capturar estado inicial
    try:
        response = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        initial_metrics = response.json() if response.status_code == 200 else {}
    except:
        initial_metrics = {}
    
    yield {
        'start_time': test_start_time,
        'initial_metrics': initial_metrics
    }
    
    # Capturar estado final
    test_end_time = time.time()
    test_duration = test_end_time - test_start_time
    
    try:
        response = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        final_metrics = response.json() if response.status_code == 200 else {}
    except:
        final_metrics = {}
    
    print(f"\n📊 Métricas do teste:")
    print(f"⏱️ Duração: {test_duration:.2f}s")
    
    if initial_metrics and final_metrics:
        for key in ['total_users', 'total_messages', 'active_conversations']:
            initial = initial_metrics.get(key, 0)
            final = final_metrics.get(key, 0)
            if final != initial:
                print(f"📈 {key}: {initial} → {final} (+{final - initial})")

@pytest.fixture
def unique_phone_generator():
    """Gerar números de telefone únicos para testes"""
    counter = 0
    base_time = int(time.time()) % 10000  # últimos 4 dígitos do timestamp
    
    def generate():
        nonlocal counter
        counter += 1
        return f"5511999{base_time:04d}{counter:03d}"
    
    return generate

# Marcadores para categorizar testes
def pytest_configure(config):
    """Configurar marcadores personalizados"""
    config.addinivalue_line(
        "markers", "dashboard: testes relacionados ao dashboard Streamlit"
    )
    config.addinivalue_line(
        "markers", "stress: testes de stress e carga"
    )
    config.addinivalue_line(
        "markers", "failure: testes de cenários de falha"
    )
    config.addinivalue_line(
        "markers", "e2e: testes end-to-end completos"
    )
    config.addinivalue_line(
        "markers", "slow: testes que demoram mais de 30 segundos"
    )

# Hook para capturar resultados dos testes
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """Hook para capturar informações detalhadas dos testes"""
    test_start_time = datetime.now()
    
    # Executar o teste
    result = yield
    
    test_end_time = datetime.now()
    test_duration = (test_end_time - test_start_time).total_seconds()
    
    # Log detalhado do teste
    test_name = item.name
    test_file = item.fspath.basename
    
    print(f"\n📝 Teste: {test_file}::{test_name}")
    print(f"⏱️ Duração: {test_duration:.2f}s")
    print(f"📅 Início: {test_start_time.strftime('%H:%M:%S')}")
    print(f"📅 Fim: {test_end_time.strftime('%H:%M:%S')}")

# Configurações de timeout para requests
import requests.adapters
from urllib3.util.retry import Retry

def configure_requests_session():
    """Configurar sessão requests com retry e timeout"""
    session = requests.Session()
    
    # Configurar retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Session configurada globalmente
http_session = configure_requests_session()

@pytest.fixture
def http_client():
    """Cliente HTTP configurado para os testes"""
    return http_session
