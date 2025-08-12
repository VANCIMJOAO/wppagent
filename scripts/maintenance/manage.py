#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
import requests
from pathlib import Path

# Configurações
PIDS_DIR = Path(".pids")
LOGS_DIR = Path("logs")

def ensure_dirs():
    """Cria diretórios necessários"""
    PIDS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

def get_pid_file(service):
    """Retorna o caminho do arquivo PID para um serviço"""
    return PIDS_DIR / f"{service}.pid"

def is_process_running(pid):
    """Verifica se um processo está rodando"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def get_service_pid(service):
    """Obtém o PID de um serviço"""
    pid_file = get_pid_file(service)
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                return pid
        except (ValueError, FileNotFoundError):
            pass
    return None

def start_service(service, command, port=None):
    """Inicia um serviço"""
    pid = get_service_pid(service)
    if pid:
        print(f"  ✅ {service} já está rodando (PID: {pid})")
        return True
    
    print(f"  🚀 Iniciando {service}...")
    
    # Arquivo de log
    log_file = LOGS_DIR / f"{service}.log"
    
    try:
        # Inicia o processo em background
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
        
        # Salva o PID
        with open(get_pid_file(service), 'w') as f:
            f.write(str(process.pid))
        
        # Aguarda um pouco
        time.sleep(3)
        
        print(f"  ✅ {service} iniciado (PID: {process.pid})")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao iniciar {service}: {e}")
        return False

def stop_service(service):
    """Para um serviço"""
    pid = get_service_pid(service)
    if not pid:
        print(f"  ℹ️  {service} não está rodando")
        return True
    
    print(f"  🛑 Parando {service} (PID: {pid})...")
    
    try:
        # Envia SIGTERM
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        time.sleep(2)
        
        # Remove o arquivo PID
        pid_file = get_pid_file(service)
        if pid_file.exists():
            pid_file.unlink()
        
        print(f"  ✅ {service} parado")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao parar {service}: {e}")
        return False

def start_all():
    """Inicia todos os serviços"""
    print("🚀 Iniciando WhatsApp Agent...")
    ensure_dirs()
    
    # Define Python path completo
    python_path = "/home/vancim/whats_agent/venv/bin/python"
    if not os.path.exists(python_path):
        python_path = "python3"
    
    services = [
        ("fastapi", f"{python_path} -m uvicorn app.main:app --host 0.0.0.0 --port 8000", 8000),
        ("dashboard", f"{python_path} -m streamlit run dashboard_whatsapp_complete.py --server.port 8501 --server.headless true", 8501),
        ("costs", f"{python_path} -m streamlit run cost_dashboard.py --server.port 8502 --server.headless true", 8502),
    ]
    
    for service, command, port in services:
        start_service(service, command, port)
    
    print("\n🎉 WhatsApp Agent iniciado!")
    print("\n📊 Acesse os dashboards:")
    print("  • API: http://localhost:8000/docs")
    print("  • Dashboard: http://localhost:8501")
    print("  • Custos: http://localhost:8502")
    print("\n💡 Use './manage.py status' para verificar")

def stop_all():
    """Para todos os serviços"""
    print("🛑 Parando WhatsApp Agent...")
    
    services = ["fastapi", "dashboard", "costs"]
    
    for service in services:
        stop_service(service)
    
    print("\n✅ WhatsApp Agent parado!")

def status_all():
    """Mostra status de todos os serviços"""
    print("📊 Status dos Serviços:")
    print("=" * 40)
    
    services = [
        ("FastAPI", "fastapi", 8000),
        ("Dashboard", "dashboard", 8501),
        ("Custos", "costs", 8502),
    ]
    
    for name, service, port in services:
        pid = get_service_pid(service)
        if pid:
            print(f"  {name:12} 🟢 Rodando (PID: {pid})")
            print(f"  {'':12} http://localhost:{port}")
        else:
            print(f"  {name:12} 🔴 Parado")

def main():
    if len(sys.argv) < 2:
        print("Uso: ./manage.py [start|stop|status|restart]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        start_all()
    elif command == "stop":
        stop_all()
    elif command == "status":
        status_all()
    elif command == "restart":
        stop_all()
        time.sleep(2)
        start_all()
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
