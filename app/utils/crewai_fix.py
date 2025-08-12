#!/usr/bin/env python3
"""
🔧 FIX PARA PROBLEMA DE PERMISSÕES CREWAI
==========================================

Este script resolve o problema de permissões do CrewAI no container Docker
Deve ser executado ANTES de qualquer importação do CrewAI
"""

import os
import stat
import logging
from pathlib import Path

def fix_crewai_permissions():
    """
    Corrige permissões do CrewAI de forma robusta
    """
    try:
        # 1. Definir diretórios base
        home_dir = os.getenv('HOME', '/home/whatsapp')
        
        # 2. Diretórios que o CrewAI precisa
        crewai_dirs = [
            f"{home_dir}/.local",
            f"{home_dir}/.local/share", 
            f"{home_dir}/.local/share/app",
            f"{home_dir}/.cache",
            f"{home_dir}/.cache/crewai",
            f"{home_dir}/.config",
            f"{home_dir}/.config/crewai",
            # Diretórios adicionais que CrewAI pode usar
            "/tmp/crewai",
            "/tmp/crewai_cache",
            f"{home_dir}/.crewai"
        ]
        
        # 3. Criar e configurar diretórios
        for dir_path in crewai_dirs:
            try:
                # Criar diretório se não existir
                os.makedirs(dir_path, mode=0o777, exist_ok=True)
                
                # Forçar permissões 777 recursivamente
                path_obj = Path(dir_path)
                path_obj.chmod(0o777)
                
                # Para todos os arquivos dentro do diretório
                if path_obj.exists() and path_obj.is_dir():
                    for item in path_obj.rglob('*'):
                        try:
                            if item.is_file():
                                item.chmod(0o666)  # rw-rw-rw-
                            elif item.is_dir():
                                item.chmod(0o777)  # rwxrwxrwx
                        except (OSError, PermissionError):
                            pass  # Ignorar erros individuais
                
                print(f"✅ Diretório configurado: {dir_path}")
                
            except Exception as e:
                print(f"⚠️ Aviso ao configurar {dir_path}: {e}")
        
        # 4. Configurar variáveis de ambiente para forçar paths alternativos
        os.environ['XDG_DATA_HOME'] = f"{home_dir}/.local/share"
        os.environ['XDG_CACHE_HOME'] = f"{home_dir}/.cache"
        os.environ['XDG_CONFIG_HOME'] = f"{home_dir}/.config"
        os.environ['HOME'] = home_dir
        
        # 5. Variáveis específicas do CrewAI (se houver)
        os.environ['CREWAI_STORAGE_DIR'] = f"{home_dir}/.local/share/app"
        os.environ['CREWAI_CACHE_DIR'] = f"{home_dir}/.cache/crewai"
        os.environ['CREWAI_CONFIG_DIR'] = f"{home_dir}/.config/crewai"
        
        # 6. Fallback para /tmp se ainda não funcionar
        os.environ['TMPDIR'] = '/tmp'
        os.environ['TEMP'] = '/tmp'
        os.environ['TMP'] = '/tmp'
        
        print("✅ Permissões CrewAI configuradas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar permissões CrewAI: {e}")
        return False

def alternative_crewai_init():
    """
    Inicialização alternativa usando /tmp se o método principal falhar
    """
    try:
        # Usar /tmp como fallback completo
        tmp_base = "/tmp/crewai_app"
        
        os.makedirs(f"{tmp_base}/data", mode=0o777, exist_ok=True)
        os.makedirs(f"{tmp_base}/cache", mode=0o777, exist_ok=True)
        os.makedirs(f"{tmp_base}/config", mode=0o777, exist_ok=True)
        
        # Sobrescrever TODAS as variáveis para usar /tmp
        os.environ['XDG_DATA_HOME'] = f"{tmp_base}/data"
        os.environ['XDG_CACHE_HOME'] = f"{tmp_base}/cache"
        os.environ['XDG_CONFIG_HOME'] = f"{tmp_base}/config"
        os.environ['HOME'] = tmp_base
        
        print("✅ Configuração alternativa CrewAI usando /tmp")
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração alternativa: {e}")
        return False

# Executar fix automaticamente quando o módulo for importado
if __name__ == "__main__" or True:  # Sempre executar
    success = fix_crewai_permissions()
    if not success:
        print("🔄 Tentando configuração alternativa...")
        alternative_crewai_init()
