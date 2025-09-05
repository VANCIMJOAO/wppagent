#!/usr/bin/env python3
"""
Script de Limpeza do Projeto WhatsApp Agent
Organiza e arquiva arquivos desnecessários para manter o projeto limpo.
"""

import os
import shutil
import datetime
from pathlib import Path

def create_archive_folder():
    """Cria pasta de arquivo com timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = f"_archived_{timestamp}"
    os.makedirs(archive_folder, exist_ok=True)
    print(f"📁 Pasta de arquivo criada: {archive_folder}")
    return archive_folder

def cleanup_root_files():
    """Remove arquivos de desenvolvimento da raiz"""
    print("\n🧹 LIMPEZA DA RAIZ DO PROJETO")
    print("=" * 40)
    
    # Arquivos para remover (desenvolvimento/teste/debug)
    files_to_remove = [
        'alternative_recovery.sh',
        'debug_admin_login.py', 
        'deep_search.sh',
        'diagnose_pyc.sh',
        'emergency_recovery.sh',
        'extract_strings.sh',
        'forensic_search.sh',
        'full_recovery.sh',
        'recover_complete_dashboard.sh',
        'recover_dashboard.py',
        'recover_dashboard.sh', 
        'recover_dashboard_v2.py',
        'search_backups.sh',
        'simple_test.py',
        'test_jwt_corrected_final.py',
        'test_jwt_post_correction.py',
        'test_recovery.py',
        'test_webhook_websocket.py',
        'test_websocket_railway.py',
        'try_python312.sh',
        'verify_recovery.sh',
        'jwt_test_results.json',
        'DEPLOY_WEBSOCKET_CHECKLIST.md',
        'WEBSOCKET_TESTS_FINAL_REPORT.md'
    ]
    
    removed_count = 0
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✅ Removido: {file}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Erro removendo {file}: {e}")
    
    print(f"\n📊 Total removido da raiz: {removed_count} arquivos")
    return removed_count

def cleanup_dashboard_files():
    """Remove arquivos de teste/desenvolvimento do dashboard"""
    print("\n🧹 LIMPEZA DO DASHBOARD")
    print("=" * 40)
    
    dashboard_path = Path("dashboard")
    if not dashboard_path.exists():
        print("❌ Pasta dashboard não encontrada")
        return 0
    
    # Arquivos de teste/desenvolvimento
    test_files = [
        'auth_setup.py',
        'callback_alternativo.py',
        'callback_final_teste.py', 
        'demo_auth.py',
        'fix_aplicado.py',
        'fix_dmc_compatibility.py',
        'fix_loop_aplicado.py',
        'fix_unstyled_button.py',
        'test_api_integration.py',
        'test_auth.py',
        'test_dados_reais.py',
        'test_dashboard_websocket.py',
        'test_dmc_compatibility.py',
        'teste_callbacks.py',
        'teste_click.py',
        'teste_conversas_corrigidas.py',
        'teste_final.py',
        'teste_link_perfil.py',
        'teste_perfil.py',
        'teste_rapido.py',
        'teste_switch_correcao.py',
        'test_quick_websocket.py',
        'test_relatorios.py',
        'test_suporte.py',
        'test_websocket_final.py',
        'verificacao_final.py',
        'websocket_server_example.py',
        'all_strings.txt',
        'app_strings.py',
        'dashboard_test.log',
        'dashboard.log'
    ]
    
    # Arquivos .md de desenvolvimento (mantém README.md)
    md_files_to_remove = []
    for md_file in dashboard_path.glob("*.md"):
        if md_file.name != "README.md":
            md_files_to_remove.append(md_file.name)
    
    all_files_to_remove = test_files + md_files_to_remove
    removed_count = 0
    
    for file in all_files_to_remove:
        file_path = dashboard_path / file
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"  ✅ Removido: dashboard/{file}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Erro removendo dashboard/{file}: {e}")
    
    print(f"\n📊 Total removido do dashboard: {removed_count} arquivos")
    return removed_count

def cleanup_backup_folders():
    """Remove pastas de backup antigas"""
    print("\n🧹 LIMPEZA DE BACKUPS ANTIGOS")
    print("=" * 40)
    
    folders_to_remove = [
        'backups',
        'cleanup_backup',
        'logs'
    ]
    
    removed_count = 0
    for folder in folders_to_remove:
        if os.path.exists(folder):
            try:
                # Só remove se não estiver vazio ou contiver apenas arquivos antigos
                folder_path = Path(folder)
                files_in_folder = list(folder_path.glob("**/*"))
                
                if len(files_in_folder) == 0:
                    shutil.rmtree(folder)
                    print(f"  ✅ Pasta vazia removida: {folder}")
                    removed_count += 1
                else:
                    print(f"  ⚠️  Mantida (contém arquivos): {folder}")
            except Exception as e:
                print(f"  ❌ Erro removendo pasta {folder}: {e}")
    
    print(f"\n📊 Total de pastas removidas: {removed_count}")
    return removed_count

def organize_important_files():
    """Organiza arquivos importantes em estrutura limpa"""
    print("\n📂 ORGANIZANDO ARQUIVOS IMPORTANTES")
    print("=" * 40)
    
    # Arquivos importantes que devem ficar na raiz
    important_root_files = [
        'README.md',
        'requirements.txt', 
        'requirements-test.txt',
        'pyproject.toml',
        'pytest.ini',
        'alembic.ini',
        'docker-compose.yml',
        'Dockerfile',
        'dashboard.db',
        'dashboard.py',
        'create_admin.py'
    ]
    
    print("📋 Arquivos importantes mantidos na raiz:")
    for file in important_root_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (não encontrado)")
    
    print("\n📋 Pastas importantes mantidas:")
    important_folders = ['app', 'dashboard', 'config', 'tests', 'alembic', 'prometheus', 'secrets']
    for folder in important_folders:
        if os.path.exists(folder):
            print(f"  ✅ {folder}/")
        else:
            print(f"  ⚠️  {folder}/ (não encontrada)")

def show_final_structure():
    """Mostra estrutura final do projeto"""
    print("\n🏗️  ESTRUTURA FINAL DO PROJETO")
    print("=" * 40)
    
    os.system("tree -L 2 -a --dirsfirst || ls -la")

def main():
    """Executa limpeza completa do projeto"""
    print("🧹 LIMPEZA COMPLETA DO PROJETO WHATSAPP AGENT")
    print("=" * 50)
    print("⚠️  Executando remoção de arquivos de desenvolvimento/teste")
    
    total_removed = 0
    
    try:
        # Executa limpezas
        total_removed += cleanup_root_files()
        total_removed += cleanup_dashboard_files() 
        total_removed += cleanup_backup_folders()
        
        # Organiza arquivos importantes
        organize_important_files()
        
        # Mostra estrutura final
        show_final_structure()
        
        print(f"\n🎉 LIMPEZA CONCLUÍDA!")
        print(f"📊 Total de arquivos removidos: {total_removed}")
        print("✨ Projeto organizado e limpo!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a limpeza: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Muda para diretório do projeto
    os.chdir("/home/vancim/whats_agent")
    main()
