#!/usr/bin/env python3
"""
🛠️ Configuração Completa para Testes com Backend Real
Gerencia todo o ciclo de vida dos serviços para testes end-to-end
"""

import os
import sys
import time
import json
import signal
import subprocess
import requests
import psutil
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import threading
import tempfile

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.models.database import User, Conversation, Message, Service, Appointment, Business


class BackendTestSetup:
    """🚀 Gerenciador completo do ambiente de teste"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.backend_url = "http://localhost:8000"
        self.dashboard_url = "http://localhost:8501"
        self.webhook_url = f"{self.backend_url}/webhook"
        
        # Processos em execução
        self.backend_process: Optional[subprocess.Popen] = None
        self.dashboard_process: Optional[subprocess.Popen] = None
        
        # IDs dos processos para cleanup
        self.process_pids: List[int] = []
        
        # Logs
        self.log_dir = self.project_root / "tests" / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        print(f"🏗️ Configurando ambiente de teste")
        print(f"📁 Diretório do projeto: {self.project_root}")
        print(f"🌐 Backend URL: {self.backend_url}")
        print(f"📊 Dashboard URL: {self.dashboard_url}")
    
    def check_dependencies(self) -> bool:
        """🔍 Verifica dependências necessárias"""
        print("🔍 Verificando dependências...")
        
        # Verificar se PostgreSQL está rodando
        try:
            import psycopg2
            from app.database import sync_engine
            from sqlalchemy import text
            
            with sync_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ PostgreSQL conectado")
        except Exception as e:
            print(f"❌ Erro ao conectar PostgreSQL: {e}")
            return False
        
        # Verificar se as migrações estão atualizadas
        try:
            result = subprocess.run(
                ["alembic", "current"], 
                cwd=self.project_root,
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print("✅ Migrações do Alembic OK")
            else:
                print("⚠️ Executando migrações...")
                subprocess.run(["alembic", "upgrade", "head"], cwd=self.project_root)
        except Exception as e:
            print(f"⚠️ Erro com migrações: {e}")
        
        # Verificar se as dependências Python estão instaladas
        required_packages = ['fastapi', 'streamlit', 'uvicorn', 'sqlalchemy', 'requests']
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} instalado")
            except ImportError:
                print(f"❌ {package} não encontrado")
                return False
        
        return True
    
    def start_backend_services(self) -> bool:
        """🚀 Inicia serviços do backend"""
        print("🚀 Iniciando serviços do backend...")
        
        if not self.check_dependencies():
            print("❌ Dependências não atendidas")
            return False
        
        # Verificar se as portas estão livres
        if self._is_port_in_use(8000):
            print("⚠️ Porta 8000 em uso, tentando parar processo existente...")
            self._kill_process_on_port(8000)
            time.sleep(2)
        
        if self._is_port_in_use(8501):
            print("⚠️ Porta 8501 em uso, tentando parar processo existente...")
            self._kill_process_on_port(8501)
            time.sleep(2)
        
        # Iniciar FastAPI
        print("🚀 Iniciando FastAPI na porta 8000...")
        fastapi_log = self.log_dir / "fastapi_test.log"
        
        try:
            self.backend_process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", 
                    "app.main:app", 
                    "--host", "0.0.0.0", 
                    "--port", "8000",
                    "--reload"
                ],
                cwd=self.project_root,
                stdout=open(fastapi_log, 'w'),
                stderr=subprocess.STDOUT,
                env=os.environ.copy()
            )
            
            self.process_pids.append(self.backend_process.pid)
            print(f"✅ FastAPI iniciado (PID: {self.backend_process.pid})")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar FastAPI: {e}")
            return False
        
        return True
    
    def start_dashboard(self) -> bool:
        """📊 Inicia dashboard Streamlit"""
        print("📊 Iniciando Dashboard Streamlit na porta 8501...")
        
        dashboard_log = self.log_dir / "streamlit_test.log"
        
        try:
            self.dashboard_process = subprocess.Popen(
                [
                    sys.executable, "-m", "streamlit", "run", 
                    "dashboard_whatsapp_complete.py",
                    "--server.port", "8501",
                    "--server.headless", "true"
                ],
                cwd=self.project_root,
                stdout=open(dashboard_log, 'w'),
                stderr=subprocess.STDOUT,
                env=os.environ.copy()
            )
            
            self.process_pids.append(self.dashboard_process.pid)
            print(f"✅ Streamlit iniciado (PID: {self.dashboard_process.pid})")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar Streamlit: {e}")
            return False
        
        return True
    
    def wait_for_services(self, timeout: int = 60, require_dashboard: bool = False) -> bool:
        """⏳ Aguarda serviços ficarem disponíveis"""
        print("⏳ Aguardando serviços ficarem disponíveis...")
        
        start_time = time.time()
        
        # Aguardar FastAPI (obrigatório)
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ FastAPI disponível")
                    break
            except:
                pass
            time.sleep(2)
        else:
            print("❌ Timeout aguardando FastAPI")
            return False
        
        # Aguardar Streamlit (opcional)
        if require_dashboard:
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(self.dashboard_url, timeout=5)
                    if response.status_code == 200:
                        print("✅ Streamlit disponível")
                        break
                except:
                    pass
                time.sleep(2)
            else:
                print("⚠️ Streamlit não disponível (continuando sem dashboard)")
        else:
            print("ℹ️ Dashboard não requerido para estes testes")
        
        print("🎯 Serviços essenciais estão prontos!")
        return True
    
    def populate_test_data(self) -> bool:
        """📊 Popula banco com dados de teste"""
        print("📊 Verificando dados de teste...")
        
        try:
            session = SessionLocal()
            
            # Verificar se já existem dados de teste
            existing_business = session.query(Business).filter(
                Business.name == "Barbearia do João - Teste"
            ).first()
            
            if existing_business:
                print("✅ Dados de teste já existem, pulando população")
                session.close()
                return True
            
            # Carregar dados de teste do JSON
            structure_file = self.project_root / "tests" / "fixtures" / "database_structure.json"
            if not structure_file.exists():
                print("⚠️ Arquivo de estrutura não encontrado, criando dados básicos...")
                # Criar dados básicos
                business = Business(
                    name="Barbearia do João - Teste",
                    email="teste@barbearia.com",
                    phone="+5511999887766",
                    address="Rua dos Testes, 123"
                )
                session.add(business)
                session.commit()
                print("✅ Business básico criado")
                session.close()
                return True
            
            with open(structure_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_data = data['test_data']
            
            # Criar business primeiro (dependência)
            business = Business(
                name="Barbearia do João - Teste",
                email="teste@barbearia.com",
                phone="+5511999887766",
                address="Rua dos Testes, 123"
            )
            session.add(business)
            session.commit()
            print(f"✅ Business criado: ID {business.id}")
            
            # Criar serviços
            services_created = []
            for service_data in test_data['services']:
                service = Service(
                    business_id=business.id,
                    name=service_data['name'],
                    description=service_data['description'],
                    price=service_data['price'],
                    duration_minutes=service_data.get('duration', 60),
                    is_active=service_data.get('active', True)
                )
                session.add(service)
                services_created.append(service)
            
            session.commit()
            print(f"✅ {len(services_created)} serviços criados")
            
            # Criar usuários
            users_created = []
            for user_data in test_data['users']:
                user = User(
                    wa_id=user_data['wa_id'],
                    nome=user_data['nome'],
                    telefone=user_data['telefone'],
                    email=user_data['email']
                )
                session.add(user)
                users_created.append(user)
            
            session.commit()
            print(f"✅ {len(users_created)} usuários criados")
            
            # Criar conversas
            conversations_created = []
            for i, conv_data in enumerate(test_data['conversations']):
                if i < len(users_created):
                    conversation = Conversation(
                        user_id=users_created[i].id,
                        status=conv_data['status']
                    )
                    session.add(conversation)
                    conversations_created.append(conversation)
            
            session.commit()
            print(f"✅ {len(conversations_created)} conversas criadas")
            
            # Criar mensagens
            messages_created = []
            for i, msg_data in enumerate(test_data['messages']):
                if i < len(users_created) and i < len(conversations_created):
                    message = Message(
                        user_id=users_created[i].id,
                        conversation_id=conversations_created[i].id,
                        message_id=msg_data['message_id'],
                        direction=msg_data['direction'],
                        content=msg_data['content'],
                        message_type=msg_data['message_type']
                    )
                    session.add(message)
                    messages_created.append(message)
            
            session.commit()
            print(f"✅ {len(messages_created)} mensagens criadas")
            
            # Criar agendamentos
            appointments_created = []
            for i, appt_data in enumerate(test_data['appointments']):
                if i < len(users_created) and i < len(services_created):
                    appointment = Appointment(
                        user_id=users_created[i].id,
                        service_id=services_created[i].id,
                        business_id=business.id,
                        date_time=datetime.fromisoformat(appt_data['date_time'].replace('Z', '+00:00')),
                        status=appt_data['status'],
                        notes=appt_data['notes']
                    )
                    session.add(appointment)
                    appointments_created.append(appointment)
            
            session.commit()
            print(f"✅ {len(appointments_created)} agendamentos criados")
            
            session.close()
            
            # Retornar dados criados para uso nos testes
            self.test_data = {
                'business': business,
                'services': services_created,
                'users': users_created,
                'conversations': conversations_created,
                'messages': messages_created,
                'appointments': appointments_created
            }
            
            print("🎯 Dados de teste populados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao popular dados de teste: {e}")
            return False
    
    def cleanup_test_data(self):
        """🧹 Limpa dados de teste do banco"""
        print("🧹 Limpando dados de teste...")
        
        try:
            session = SessionLocal()
            
            # Deletar em ordem reversa devido às foreign keys
            session.query(Appointment).filter(
                Appointment.notes.like('%teste%')
            ).delete(synchronize_session=False)
            
            session.query(Message).filter(
                Message.message_id.like('%test_%')
            ).delete(synchronize_session=False)
            
            session.query(Conversation).filter(
                Conversation.id.in_([conv.id for conv in getattr(self, 'test_data', {}).get('conversations', [])])
            ).delete(synchronize_session=False)
            
            session.query(User).filter(
                User.nome.like('%Teste%')
            ).delete(synchronize_session=False)
            
            session.query(Service).filter(
                Service.name.like('%Teste%')
            ).delete(synchronize_session=False)
            
            session.query(Business).filter(
                Business.name.like('%Teste%')
            ).delete(synchronize_session=False)
            
            session.commit()
            session.close()
            
            print("✅ Dados de teste limpos")
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar dados: {e}")
    
    def cleanup_services(self):
        """🧹 Para todos os serviços e limpa recursos"""
        print("🧹 Limpando serviços...")
        
        # Parar processos
        for process in [self.backend_process, self.dashboard_process]:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=10)
                    print(f"✅ Processo {process.pid} terminado")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"⚠️ Processo {process.pid} forçado a parar")
                except:
                    pass
        
        # Matar processos por PID se necessário
        for pid in self.process_pids:
            try:
                if psutil.pid_exists(pid):
                    p = psutil.Process(pid)
                    p.terminate()
                    p.wait(timeout=5)
                    print(f"✅ PID {pid} terminado")
            except:
                pass
        
        # Matar processos nas portas
        self._kill_process_on_port(8000)
        self._kill_process_on_port(8501)
        
        # Limpar dados de teste
        self.cleanup_test_data()
        
        print("🎯 Cleanup completo!")
    
    def _is_port_in_use(self, port: int) -> bool:
        """Verifica se uma porta está em uso"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def _kill_process_on_port(self, port: int):
        """Mata processo rodando em uma porta específica"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port:
                            proc.terminate()
                            proc.wait(timeout=5)
                            print(f"✅ Processo na porta {port} terminado")
                            return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass
    
    def get_service_status(self) -> Dict[str, Any]:
        """📊 Retorna status dos serviços"""
        status = {
            'backend': {
                'url': self.backend_url,
                'running': False,
                'health': None
            },
            'dashboard': {
                'url': self.dashboard_url,
                'running': False,
                'health': None
            },
            'database': {
                'connected': False,
                'test_data': False
            }
        }
        
        # Verificar backend
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            status['backend']['running'] = True
            status['backend']['health'] = response.status_code == 200
        except:
            pass
        
        # Verificar dashboard
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            status['dashboard']['running'] = True
            status['dashboard']['health'] = response.status_code == 200
        except:
            pass
        
        # Verificar banco
        try:
            session = SessionLocal()
            from sqlalchemy import text
            result = session.execute(text("SELECT COUNT(*) FROM users WHERE nome LIKE '%Teste%'")).scalar()
            status['database']['connected'] = True
            status['database']['test_data'] = result > 0
            session.close()
        except:
            pass
        
        return status
    
    def create_test_webhook_payload(self, user_data: Dict, message: str) -> Dict:
        """🎭 Cria payload realístico do WhatsApp"""
        return {
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
                            "profile": {"name": user_data['nome']},
                            "wa_id": user_data['wa_id']
                        }],
                        "messages": [{
                            "from": user_data['wa_id'],
                            "id": f"wamid.test_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "text": {"body": message},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }


class TestReporter:
    """📊 Relatórios e métricas dos testes"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def start_test_session(self):
        self.start_time = datetime.now()
        print(f"🚀 Sessão de testes iniciada: {self.start_time}")
    
    def end_test_session(self):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        print(f"✅ Sessão de testes finalizada: {self.end_time}")
        print(f"⏱️ Duração total: {duration}")
    
    def add_result(self, test_name: str, success: bool, duration: float, details: Dict):
        self.results.append({
            'test_name': test_name,
            'success': success,
            'duration': duration,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_report(self) -> Dict:
        total_tests = len(self.results)
        successful = len([r for r in self.results if r['success']])
        failed = total_tests - successful
        avg_duration = sum(r['duration'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_tests * 100) if total_tests > 0 else 0,
                'average_duration': avg_duration,
                'session_duration': (self.end_time - self.start_time).total_seconds() if self.end_time else None
            },
            'results': self.results
        }


def main():
    """🚀 Função principal para teste"""
    print("🛠️ CONFIGURADOR DE AMBIENTE DE TESTE")
    print("="*50)
    
    setup = BackendTestSetup()
    
    try:
        # Configurar signal handler para cleanup
        def signal_handler(sig, frame):
            print("\n🛑 Interrompido pelo usuário")
            setup.cleanup_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Iniciar serviços
        if not setup.start_backend_services():
            return False
        
        if not setup.start_dashboard():
            return False
        
        if not setup.wait_for_services():
            return False
        
        if not setup.populate_test_data():
            return False
        
        # Mostrar status
        status = setup.get_service_status()
        print("\n📊 STATUS DOS SERVIÇOS:")
        print(f"🖥️ Backend: {'✅' if status['backend']['health'] else '❌'} {setup.backend_url}")
        print(f"📊 Dashboard: {'✅' if status['dashboard']['health'] else '❌'} {setup.dashboard_url}")
        print(f"🗄️ Database: {'✅' if status['database']['connected'] else '❌'} Connected")
        print(f"📋 Test Data: {'✅' if status['database']['test_data'] else '❌'} Populated")
        
        print(f"\n🎯 Ambiente pronto para testes!")
        print(f"📱 Webhook URL: {setup.webhook_url}")
        print(f"📊 Use Ctrl+C para parar os serviços")
        
        # Manter rodando
        try:
            while True:
                time.sleep(60)
                # Verificar se os processos ainda estão rodando
                if setup.backend_process.poll() is not None:
                    print("❌ Backend parou inesperadamente")
                    break
                if setup.dashboard_process.poll() is not None:
                    print("❌ Dashboard parou inesperadamente")
                    break
        except KeyboardInterrupt:
            pass
    
    finally:
        setup.cleanup_services()


if __name__ == "__main__":
    main()
