#!/usr/bin/env python3
"""
Script para limpar arquivos desnecessários da raiz do projeto
Mantém apenas arquivos essenciais: dashboard e comprehensive_bot_test
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """Remove arquivos temporários e de teste da raiz do projeto"""
    
    # Arquivos ESSENCIAIS que devem ser mantidos
    keep_files = {
        # Core do projeto
        'README.md',
        'requirements.txt', 
        'requirements-test.txt',
        'pyproject.toml',
        'pytest.ini',
        'alembic.ini',
        
        # Docker e Deploy
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        '.gitignore',
        
        # Configuração
        '.env.example',
        
        # Scripts importantes 
        'dashboard_whatsapp_complete.py',  # ESSENCIAL - Dashboard
        'comprehensive_bot_test.py',       # ESSENCIAL - Teste principal
        
        # SQL importante
        'create_business_tables.sql',
        
        # Terraform para produção
        'terraform.tfvars',
        'railway-monitoring.tf'
    }
    
    # Diretórios ESSENCIAIS que devem ser mantidos
    keep_dirs = {
        'app',      # Core da aplicação
        'alembic',  # Migrations
        'testing',  # Testes estruturados
        'tests',    # Testes unitários
        '.git',     # Git
        '.github',  # GitHub Actions
        'venv',     # Virtual env (se existir)
        '__pycache__'  # Python cache (será ignorado pelo git)
    }
    
    root_path = Path('/home/vancim/whats_agent')
    removed_files = []
    
    print("🧹 LIMPEZA DO PROJETO - Removendo arquivos desnecessários")
    print("=" * 60)
    
    # Listar todos os itens na raiz
    for item in root_path.iterdir():
        item_name = item.name
        
        # Pular diretórios essenciais
        if item.is_dir() and item_name in keep_dirs:
            print(f"📁 MANTENDO diretório: {item_name}")
            continue
            
        # Pular arquivos essenciais
        if item.is_file() and item_name in keep_files:
            print(f"📄 MANTENDO arquivo: {item_name}")
            continue
            
        # Pular arquivos .env (sensíveis)
        if item_name.startswith('.env') and item_name != '.env.example':
            print(f"🔒 MANTENDO arquivo sensível: {item_name}")
            continue
            
        # Remover item
        try:
            if item.is_file():
                item.unlink()
                print(f"🗑️  REMOVIDO arquivo: {item_name}")
                removed_files.append(f"arquivo: {item_name}")
            elif item.is_dir():
                # Verificar se é diretório de teste/temp
                if any(x in item_name.lower() for x in ['test', 'temp', 'log', 'backup']):
                    shutil.rmtree(item)
                    print(f"🗑️  REMOVIDO diretório: {item_name}/")
                    removed_files.append(f"diretório: {item_name}/")
                else:
                    print(f"⚠️  PULANDO diretório desconhecido: {item_name}/")
        except Exception as e:
            print(f"❌ ERRO ao remover {item_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ LIMPEZA CONCLUÍDA - {len(removed_files)} itens removidos")
    
    if removed_files:
        print("\n📋 ITENS REMOVIDOS:")
        for item in removed_files:
            print(f"   • {item}")
    
    print("\n📁 ESTRUTURA FINAL:")
    essential_items = sorted([item.name for item in root_path.iterdir()])
    for item in essential_items:
        print(f"   • {item}")

if __name__ == "__main__":
    cleanup_project()
