#!/usr/bin/env python3
"""
🚀 Script Principal para Executar Testes do WhatsApp Agent
Gerencia execução de testes, setup de ambiente e relatórios
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config.test_settings import *
from tests.config.backend_setup import BackendTestSetup


class TestRunner:
    """🏃 Gerenciador de execução de testes"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.tests_dir = TESTS_DIR
        self.setup = BackendTestSetup()
        
        # Comandos disponíveis
        self.test_suites = {
            'all': {
                'description': 'Todos os testes',
                'command': ['pytest', 'tests/', '-v']
            },
            'api': {
                'description': 'Testes de API real',
                'command': ['pytest', 'tests/real_backend/test_real_api_calls.py', '-v']
            },
            'flows': {
                'description': 'Fluxos completos de cliente',
                'command': ['pytest', 'tests/real_backend/test_real_whatsapp_flow.py', '-v']
            },
            'quick': {
                'description': 'Testes rápidos',
                'command': ['pytest', 'tests/', '-v', '--quick']
            },
            'performance': {
                'description': 'Testes de performance',
                'command': ['pytest', 'tests/', '-v', '--performance-only']
            },
            'single': {
                'description': 'Teste específico',
                'command': ['pytest', '-v']  # será completado dinamicamente
            }
        }
    
    def check_environment(self) -> bool:
        """🔍 Verifica se o ambiente está pronto"""
        print("🔍 Verificando ambiente...")
        
        # Verificar dependências
        try:
            import pytest
            import requests
            import sqlalchemy
            print("✅ Dependências Python OK")
        except ImportError as e:
            print(f"❌ Dependência faltando: {e}")
            return False
        
        # Verificar se pode conectar no banco
        try:
            from app.database import sync_engine
            from sqlalchemy import text
            with sync_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Banco de dados conectado")
        except Exception as e:
            print(f"❌ Erro no banco: {e}")
            return False
        
        return True
    
    def start_services(self, force: bool = False) -> bool:
        """🚀 Inicia serviços se necessário"""
        print("🚀 Verificando serviços...")
        
        status = self.setup.get_service_status()
        
        if status['backend']['health'] and not force:
            print("✅ Backend já está rodando")
            return True
        
        print("🔧 Iniciando backend...")
        if not self.setup.start_backend_services():
            print("❌ Falha ao iniciar backend")
            return False
        
        if not self.setup.wait_for_services():
            print("❌ Serviços não ficaram disponíveis")
            return False
        
        print("✅ Serviços iniciados com sucesso")
        return True
    
    def populate_test_data(self) -> bool:
        """📊 Popula dados de teste"""
        print("📊 Verificando dados de teste...")
        
        status = self.setup.get_service_status()
        
        if status['database']['test_data']:
            print("✅ Dados de teste já existem")
            return True
        
        print("📋 Populando dados de teste...")
        if not self.setup.populate_test_data():
            print("❌ Falha ao popular dados")
            return False
        
        print("✅ Dados de teste criados")
        return True
    
    def run_test_suite(self, suite_name: str, extra_args: List[str] = None) -> bool:
        """🧪 Executa uma suíte de testes"""
        if suite_name not in self.test_suites:
            print(f"❌ Suíte '{suite_name}' não encontrada")
            return False
        
        suite = self.test_suites[suite_name]
        command = suite['command'].copy()
        
        if extra_args:
            command.extend(extra_args)
        
        print(f"🧪 Executando: {suite['description']}")
        print(f"📋 Comando: {' '.join(command)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=False,  # Mostrar output em tempo real
                check=False
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ Testes completados com sucesso ({duration:.1f}s)")
                return True
            else:
                print(f"❌ Testes falharam ({duration:.1f}s)")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao executar testes: {e}")
            return False
    
    def run_single_test(self, test_path: str) -> bool:
        """🎯 Executa um teste específico"""
        command = ['pytest', test_path, '-v', '-s']
        
        print(f"🎯 Executando teste: {test_path}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                check=False
            )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Erro ao executar teste: {e}")
            return False
    
    def list_available_tests(self):
        """📋 Lista testes disponíveis"""
        print("📋 TESTES DISPONÍVEIS:")
        print("=" * 40)
        
        for suite_name, suite_info in self.test_suites.items():
            print(f"🧪 {suite_name:<12} - {suite_info['description']}")
        
        print("\n📁 ARQUIVOS DE TESTE:")
        test_files = list(TESTS_DIR.glob("**/*test*.py"))
        
        for test_file in test_files:
            rel_path = test_file.relative_to(PROJECT_ROOT)
            print(f"   📄 {rel_path}")
    
    def show_status(self):
        """📊 Mostra status atual do sistema"""
        print("📊 STATUS DO SISTEMA")
        print("=" * 30)
        
        status = self.setup.get_service_status()
        
        print(f"🖥️ Backend:")
        print(f"   URL: {status['backend']['url']}")
        print(f"   Rodando: {'✅' if status['backend']['running'] else '❌'}")
        print(f"   Saudável: {'✅' if status['backend']['health'] else '❌'}")
        
        if 'dashboard' in status:
            print(f"📊 Dashboard:")
            print(f"   URL: {status['dashboard']['url']}")
            print(f"   Rodando: {'✅' if status['dashboard']['running'] else '❌'}")
        
        print(f"🗄️ Database:")
        print(f"   Conectado: {'✅' if status['database']['connected'] else '❌'}")
        print(f"   Dados de teste: {'✅' if status['database']['test_data'] else '❌'}")
    
    def cleanup(self):
        """🧹 Limpa ambiente"""
        print("🧹 Limpando ambiente...")
        self.setup.cleanup_services()
        print("✅ Cleanup completo")


def main():
    """🚀 Função principal"""
    parser = argparse.ArgumentParser(
        description='🧪 Executor de Testes do WhatsApp Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --setup                    # Apenas configurar ambiente
  %(prog)s --run all                  # Executar todos os testes
  %(prog)s --run api                  # Apenas testes de API
  %(prog)s --run flows                # Apenas fluxos de cliente
  %(prog)s --test test_file.py        # Teste específico
  %(prog)s --status                   # Ver status dos serviços
  %(prog)s --list                     # Listar testes disponíveis
  %(prog)s --cleanup                  # Limpar ambiente
        """
    )
    
    parser.add_argument('--setup', action='store_true',
                       help='Configurar ambiente (iniciar serviços, popular dados)')
    
    parser.add_argument('--run', choices=['all', 'api', 'flows', 'quick', 'performance'],
                       help='Executar suíte de testes')
    
    parser.add_argument('--test', metavar='TEST_PATH',
                       help='Executar teste específico')
    
    parser.add_argument('--status', action='store_true',
                       help='Mostrar status dos serviços')
    
    parser.add_argument('--list', action='store_true',
                       help='Listar testes disponíveis')
    
    parser.add_argument('--cleanup', action='store_true',
                       help='Limpar ambiente (parar serviços)')
    
    parser.add_argument('--force-setup', action='store_true',
                       help='Forçar reinicialização dos serviços')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Output verboso')
    
    args = parser.parse_args()
    
    # Se nenhum argumento, mostrar ajuda
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    runner = TestRunner()
    
    print("🧪 WHATSAPP AGENT - EXECUTOR DE TESTES")
    print("=" * 50)
    
    try:
        # Verificar ambiente primeiro
        if not runner.check_environment():
            print("❌ Ambiente não está pronto")
            return 1
        
        # Comandos específicos
        if args.status:
            runner.show_status()
            return 0
        
        if args.list:
            runner.list_available_tests()
            return 0
        
        if args.cleanup:
            runner.cleanup()
            return 0
        
        # Setup de ambiente
        if args.setup or args.run or args.test:
            if not runner.start_services(force=args.force_setup):
                return 1
            
            if not runner.populate_test_data():
                return 1
        
        # Executar testes
        if args.run:
            success = runner.run_test_suite(args.run)
            return 0 if success else 1
        
        if args.test:
            success = runner.run_single_test(args.test)
            return 0 if success else 1
        
        if args.setup:
            print("✅ Ambiente configurado com sucesso!")
            runner.show_status()
            return 0
    
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        return 1
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
