#!/usr/bin/env python3
"""
🔧 PREPARAÇÃO PARA SUPER TESTE
===============================
Valida e prepara o ambiente para execução do Super Teste

🎯 VERIFICAÇÕES:
• Dependências instaladas
• Arquivos de teste presentes
• Conexão com banco de dados
• Variáveis de ambiente
• Permissões de execução
"""

import os
import sys
import json
from pathlib import Path

# Carregar variáveis do .env
def load_env_file():
    """Carrega variáveis do arquivo .env"""
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
        print(f"✅ Arquivo .env carregado: {env_path}")
        return True
    else:
        print(f"⚠️ Arquivo .env não encontrado: {env_path}")
        return False

# Carregar .env no início
load_env_file()

def check_python_version():
    """Verifica versão do Python"""
    print("🐍 Verificando versão do Python...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ necessário. Versão atual: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_dependencies():
    """Verifica dependências"""
    print("\n📦 Verificando dependências...")
    
    required_modules = [
        'asyncio',
        'asyncpg', 
        'aiohttp',
        'psutil',
        'json',
        'datetime'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n🚨 MÓDULOS AUSENTES: {', '.join(missing_modules)}")
        print("📋 Instale com: pip install -r requirements.txt")
        return False
    
    return True

def check_test_files():
    """Verifica arquivos de teste"""
    print("\n📁 Verificando arquivos de teste...")
    
    required_files = [
        'super_test_part1.py',
        'super_test_part2.py',
        'run_super_test.py'
    ]
    
    missing_files = []
    current_dir = Path.cwd()
    
    for filename in required_files:
        filepath = current_dir / filename
        if filepath.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename}")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n🚨 ARQUIVOS AUSENTES: {', '.join(missing_files)}")
        return False
    
    return True

def check_env_variables():
    """Verifica variáveis de ambiente"""
    print("\n🔐 Verificando variáveis de ambiente...")
    
    # Variáveis críticas para conexão com banco
    critical_vars = [
        'DATABASE_URL'
    ]
    
    # Variáveis opcionais mas recomendadas
    optional_vars = [
        'WEBHOOK_PORT',
        'LOG_LEVEL',
        'TEST_MODE'
    ]
    
    missing_critical = []
    
    for var in critical_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"❌ {var}")
            missing_critical.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"⚠️ {var} (opcional)")
    
    if missing_critical:
        print(f"\n🚨 VARIÁVEIS CRÍTICAS AUSENTES: {', '.join(missing_critical)}")
        print("📋 Configure no .env ou nas variáveis de sistema")
        return False
    
    return True

def test_database_connection():
    """Testa conexão básica com banco"""
    print("\n🗄️ Testando conexão com banco de dados...")
    
    try:
        import asyncpg
        import asyncio
        
        async def test_conn():
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return False
            
            try:
                conn = await asyncpg.connect(database_url)
                
                # Teste básico
                result = await conn.fetchval("SELECT 1")
                await conn.close()
                
                return result == 1
            except Exception as e:
                print(f"❌ Erro de conexão: {e}")
                return False
        
        success = asyncio.run(test_conn())
        
        if success:
            print("✅ Conexão com banco de dados OK")
            return True
        else:
            print("❌ Falha na conexão com banco de dados")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar banco: {e}")
        return False

def create_test_config():
    """Cria arquivo de configuração para testes"""
    print("\n⚙️ Criando configuração de teste...")
    
    config = {
        "test_mode": True,
        "cleanup_after_tests": True,
        "detailed_logging": True,
        "performance_monitoring": True,
        "timeout_seconds": 300,
        "max_concurrent_tests": 5,
        "webhook_port": int(os.getenv('WEBHOOK_PORT', 8080)),
        "database_url": os.getenv('DATABASE_URL', ''),
        "created_at": str(Path(__file__).stat().st_mtime)
    }
    
    config_file = Path.cwd() / 'super_test_config.json'
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuração salva: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return False

def make_executable():
    """Torna arquivos executáveis"""
    print("\n🔧 Configurando permissões de execução...")
    
    exec_files = [
        'super_test_part1.py',
        'super_test_part2.py', 
        'run_super_test.py'
    ]
    
    current_dir = Path.cwd()
    
    for filename in exec_files:
        filepath = current_dir / filename
        if filepath.exists():
            try:
                # Adicionar permissão de execução
                filepath.chmod(0o755)
                print(f"✅ {filename} - executável")
            except Exception as e:
                print(f"⚠️ {filename} - erro ao configurar: {e}")
        else:
            print(f"❌ {filename} - não encontrado")

def print_summary(checks_results):
    """Imprime resumo das verificações"""
    print("\n" + "="*60)
    print("📋 RESUMO DA PREPARAÇÃO")
    print("="*60)
    
    total_checks = len(checks_results)
    passed_checks = sum(1 for result in checks_results.values() if result)
    
    print(f"✅ Verificações aprovadas: {passed_checks}/{total_checks}")
    
    for check_name, result in checks_results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
    
    if passed_checks == total_checks:
        print("\n🎉 SISTEMA PRONTO PARA SUPER TESTE!")
        print("🚀 Execute: python run_super_test.py")
        return True
    else:
        print(f"\n⚠️ {total_checks - passed_checks} verificação(ões) falharam")
        print("🔧 Corrija os problemas antes de prosseguir")
        return False

def main():
    """Função principal"""
    print("🔧 PREPARAÇÃO PARA SUPER TESTE DEFINITIVO")
    print("🎯 WhatsApp Agent System - Validação Completa")
    print("="*60)
    
    # Executar todas as verificações
    checks = {
        "Versão do Python": check_python_version(),
        "Dependências": check_dependencies(),
        "Arquivos de teste": check_test_files(),
        "Variáveis de ambiente": check_env_variables(),
        "Conexão banco de dados": test_database_connection(),
        "Configuração de teste": create_test_config()
    }
    
    # Configurar permissões
    make_executable()
    
    # Mostrar resumo
    success = print_summary(checks)
    
    if success:
        print("\n🌟 PRÓXIMOS PASSOS:")
        print("1. 🚀 python run_super_test.py       (Teste completo)")
        print("2. 🚀 python super_test_part1.py     (Apenas Parte 1)")
        print("3. 🚀 python super_test_part2.py     (Apenas Parte 2)")
        print("4. 📊 Consultar relatórios JSON gerados")
        
        return True
    else:
        print("\n🚨 CORREÇÕES NECESSÁRIAS:")
        if not checks.get("Dependências", True):
            print("• pip install -r requirements.txt")
        if not checks.get("Variáveis de ambiente", True):
            print("• Configurar DATABASE_URL no .env")
        if not checks.get("Conexão banco de dados", True):
            print("• Verificar conectividade com PostgreSQL")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)