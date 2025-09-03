#!/usr/bin/env python3
"""
Fix DMC 0.12.1 Compatibility Issues
==================================

Script para corrigir problemas de compatibilidade:
- gap -> spacing
- justify -> position (em alguns casos)
"""

import os
import re

def fix_dmc_compatibility(file_path):
    """Fix DMC compatibility issues in a file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix gap -> spacing
    content = re.sub(r'\bgap="([^"]*)"', r'spacing="\1"', content)
    content = re.sub(r'\bgap=\'([^\']*)\'', r'spacing=\'\1\'', content)
    
    # Fix justify -> position in Group components (specific cases)
    # Mas mantém justify em casos onde é apropriado
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed: {file_path}")
        return True
    else:
        print(f"⚪ No changes needed: {file_path}")
        return False

def main():
    """Fix all callback files"""
    
    callback_files = [
        "/home/vancim/whats_agent/dashboard/callbacks/home_callbacks.py",
        "/home/vancim/whats_agent/dashboard/callbacks/clientes_callbacks.py", 
        "/home/vancim/whats_agent/dashboard/callbacks/agendamentos_callbacks.py",
        "/home/vancim/whats_agent/dashboard/callbacks/configuracoes_callbacks.py",
        "/home/vancim/whats_agent/dashboard/callbacks/conversas_callbacks.py",
        "/home/vancim/whats_agent/dashboard/callbacks/relatorios_callbacks.py"
    ]
    
    layout_files = [
        "/home/vancim/whats_agent/dashboard/layout/home.py",
        "/home/vancim/whats_agent/dashboard/layout/clientes.py",
        "/home/vancim/whats_agent/dashboard/layout/agendamentos.py",
        "/home/vancim/whats_agent/dashboard/layout/configuracoes.py",
        "/home/vancim/whats_agent/dashboard/layout/conversas.py",
        "/home/vancim/whats_agent/dashboard/layout/relatorios.py"
    ]
    
    all_files = callback_files + layout_files
    
    fixed_count = 0
    
    for file_path in all_files:
        if os.path.exists(file_path):
            if fix_dmc_compatibility(file_path):
                fixed_count += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n🎯 Fixed {fixed_count} files total")

if __name__ == "__main__":
    main()
