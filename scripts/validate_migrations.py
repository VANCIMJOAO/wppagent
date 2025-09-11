#!/usr/bin/env python3
"""
🔍 VALIDADOR DE MIGRAÇÕES ALEMBIC
==================================

Script para verificar a integridade e ordem das migrações após reorganização.
"""

import os
import re
from typing import Dict, List, Tuple
from collections import defaultdict

def extract_migration_info(file_path: str) -> Dict:
    """Extrai informações da migração do arquivo"""
    info = {
        'file_name': os.path.basename(file_path),
        'revision': None,
        'down_revision': None,
        'create_date': None,
        'description': None
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extrair revision ID
        revision_match = re.search(r'revision[:\s]*=\s*[\'"]([^\'"]+)[\'"]', content)
        if revision_match:
            info['revision'] = revision_match.group(1)
            
        # Extrair down_revision
        down_revision_match = re.search(r'down_revision[:\s]*=\s*[\'"]([^\'"]+)[\'"]', content)
        if down_revision_match:
            info['down_revision'] = down_revision_match.group(1)
            
        # Extrair data de criação
        date_match = re.search(r'Create Date:\s*([^\n]+)', content)
        if date_match:
            info['create_date'] = date_match.group(1).strip()
            
        # Extrair descrição
        desc_match = re.search(r'"""([^"]+)(?:Revision ID:|$)', content, re.DOTALL)
        if desc_match:
            info['description'] = desc_match.group(1).strip()
    
    except Exception as e:
        info['error'] = str(e)
    
    return info

def validate_migrations(versions_dir: str) -> Dict:
    """Valida todas as migrações do diretório"""
    
    print('🔍 VALIDANDO CADEIA DE MIGRAÇÕES')
    print('=' * 40)
    
    # Listar todos os arquivos de migração
    migration_files = [
        f for f in os.listdir(versions_dir) 
        if f.endswith('.py') and f != '__pycache__'
    ]
    
    migrations = []
    revision_map = {}
    
    print(f'\n📊 TOTAL DE MIGRAÇÕES: {len(migration_files)}')
    print()
    
    # Processar cada migração
    for file_name in migration_files:
        file_path = os.path.join(versions_dir, file_name)
        info = extract_migration_info(file_path)
        migrations.append(info)
        
        if info['revision']:
            revision_map[info['revision']] = info
    
    # Categorizar por padrão de nomenclatura
    patterns = {
        'correct': [],    # YYYY_MM_DD_HHMM-hash-description.py
        'legacy': [],     # 001_initial.py, etc
        'broken': []      # Outros padrões
    }
    
    for migration in migrations:
        file_name = migration['file_name']
        
        # Padrão correto: YYYY_MM_DD_HHMM-hash_description.py
        if re.match(r'^\d{4}_\d{2}_\d{2}_\d{4}-.*\.py$', file_name):
            patterns['correct'].append(migration)
        elif re.match(r'^\d{3}_\w+\.py$', file_name):
            patterns['legacy'].append(migration)
        else:
            patterns['broken'].append(migration)
    
    # Relatório de padrões
    print('✅ PADRÕES DE NOMENCLATURA:')
    print(f'   • Corretos: {len(patterns["correct"])} ({len(patterns["correct"])/len(migrations)*100:.1f}%)')
    print(f'   • Legacy: {len(patterns["legacy"])} ({len(patterns["legacy"])/len(migrations)*100:.1f}%)')
    print(f'   • Problemas: {len(patterns["broken"])} ({len(patterns["broken"])/len(migrations)*100:.1f}%)')
    
    if patterns['broken']:
        print('\n❌ ARQUIVOS COM PADRÃO INCORRETO:')
        for migration in patterns['broken']:
            print(f'   ✗ {migration["file_name"]}')
    
    # Validar cadeia de dependências
    print('\n🔗 VALIDANDO CADEIA DE DEPENDÊNCIAS:')
    orphans = []
    circular_deps = []
    
    for migration in migrations:
        if migration['down_revision'] and migration['down_revision'] != 'None':
            if migration['down_revision'] not in revision_map:
                orphans.append(migration)
    
    if orphans:
        print('   ❌ MIGRAÇÕES ÓRFÃS (dependência não encontrada):')
        for orphan in orphans:
            print(f'      ✗ {orphan["file_name"]} → depende de: {orphan["down_revision"]}')
    else:
        print('   ✅ Todas as dependências são válidas')
    
    # Validar ordem cronológica
    print('\n📅 VALIDANDO ORDEM CRONOLÓGICA:')
    dated_migrations = [m for m in patterns['correct'] if m['create_date']]
    
    if dated_migrations:
        sorted_by_date = sorted(dated_migrations, key=lambda x: x['create_date'])
        sorted_by_filename = sorted(dated_migrations, key=lambda x: x['file_name'])
        
        if [m['file_name'] for m in sorted_by_date] == [m['file_name'] for m in sorted_by_filename]:
            print('   ✅ Ordem cronológica consistente com nomes de arquivo')
        else:
            print('   ⚠️  Possível inconsistência cronológica detectada')
    
    # Resultado final
    result = {
        'total_migrations': len(migrations),
        'correct_pattern': len(patterns['correct']),
        'legacy_pattern': len(patterns['legacy']),
        'broken_pattern': len(patterns['broken']),
        'orphaned_migrations': len(orphans),
        'success_rate': (len(patterns['correct']) + len(patterns['legacy'])) / len(migrations) * 100,
        'patterns': patterns,
        'orphans': orphans
    }
    
    print('\n🎯 RESULTADO FINAL:')
    print(f'   📊 Taxa de sucesso: {result["success_rate"]:.1f}%')
    
    if result['success_rate'] >= 90:
        print('   ✅ MIGRAÇÕES ORGANIZADAS!')
    elif result['success_rate'] >= 70:
        print('   🟡 MIGRAÇÕES PARCIALMENTE ORGANIZADAS')
    else:
        print('   ❌ MIGRAÇÕES DESORGANIZADAS')
    
    return result

if __name__ == "__main__":
    versions_dir = "/home/vancim/whats_agent/alembic/versions"
    result = validate_migrations(versions_dir)
