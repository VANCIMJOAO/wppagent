#!/usr/bin/env python3
"""
🔍 SCRIPT DE ANÁLISE DETALHADA - BUGS SQL DE AMBIGUIDADE
==========================================================

Este script analisa queries SQL específicas para identificar problemas 
de ambiguidade de colunas mencionados no bug report.

Problemas identificados:
1. conversations.py - Stats query com múltiplos func.count()
2. appointments.py - Query com múltiplos JOINs 
3. dashboard.py - Queries complexas com agregações

"""

import re
import os
from typing import List, Dict, Tuple

def analyze_sql_queries(file_path: str) -> List[Dict]:
    """Analisa queries SQL em um arquivo para identificar problemas de ambiguidade"""
    
    problems = []
    
    if not os.path.exists(file_path):
        return problems
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Padrões problemáticos específicos
    patterns = [
        {
            'name': 'Multiple COUNT with JOINs',
            'pattern': r'func\.count.*\.id.*func\.count.*\.id',
            'description': 'Múltiplos func.count() com colunas id em queries com JOINs'
        },
        {
            'name': 'Ambiguous ID in JOIN',
            'pattern': r'\.id\s*==.*\.id',
            'description': 'Referências a .id que podem ser ambíguas em JOINs complexos'
        },
        {
            'name': 'COUNT without table specification',
            'pattern': r'func\.count\(\s*id\s*\)',
            'description': 'func.count(id) sem especificar tabela'
        },
        {
            'name': 'Complex JOIN with GROUP BY',
            'pattern': r'join.*outerjoin.*group_by.*\.id.*\.id',
            'description': 'GROUP BY com múltiplos .id em queries com múltiplos JOINs'
        }
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern_info in patterns:
            if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                problems.append({
                    'file': file_path,
                    'line': i,
                    'content': line.strip(),
                    'pattern': pattern_info['name'],
                    'description': pattern_info['description']
                })
    
    return problems

def analyze_specific_query_context(file_path: str, line_num: int, context_lines: int = 10) -> str:
    """Analisa contexto ao redor de uma linha específica"""
    
    if not os.path.exists(file_path):
        return "Arquivo não encontrado"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    start = max(0, line_num - context_lines - 1)
    end = min(len(lines), line_num + context_lines)
    
    context = []
    for i in range(start, end):
        marker = ">>> " if i == line_num - 1 else "    "
        context.append(f"{marker}{i+1:3}: {lines[i].rstrip()}")
    
    return "\n".join(context)

def main():
    print("🔍 ANÁLISE DETALHADA DE BUGS SQL - AMBIGUIDADE DE COLUNAS")
    print("=" * 60)
    
    # Arquivos para análise (mencionados no bug report)
    files_to_analyze = [
        '/home/vancim/whats_agent/app/routes/conversations.py',
        '/home/vancim/whats_agent/app/routes/appointments.py',
        '/home/vancim/whats_agent/app/routes/dashboard.py'
    ]
    
    total_problems = 0
    
    for file_path in files_to_analyze:
        print(f"\n📁 ANALISANDO: {os.path.basename(file_path)}")
        print("-" * 50)
        
        problems = analyze_sql_queries(file_path)
        
        if not problems:
            print("✅ Nenhum problema de ambiguidade detectado")
            continue
        
        total_problems += len(problems)
        
        for problem in problems:
            print(f"\n🚨 PROBLEMA ENCONTRADO:")
            print(f"   📍 Linha: {problem['line']}")
            print(f"   🔍 Padrão: {problem['pattern']}")
            print(f"   📝 Descrição: {problem['description']}")
            print(f"   💻 Código: {problem['content']}")
            
            # Mostrar contexto
            print(f"\n📋 CONTEXTO (±10 linhas):")
            context = analyze_specific_query_context(file_path, problem['line'])
            print(context)
            print("-" * 40)
    
    print(f"\n📊 RESUMO DA ANÁLISE:")
    print(f"   📁 Arquivos analisados: {len(files_to_analyze)}")
    print(f"   🚨 Problemas encontrados: {total_problems}")
    
    if total_problems > 0:
        print(f"\n⚠️  RECOMENDAÇÕES:")
        print(f"   1. Especificar tabelas em todas as referências a .id")
        print(f"   2. Usar func.distinct() em COUNT quando necessário")
        print(f"   3. Quebrar queries complexas em múltiplas queries")
        print(f"   4. Usar aliases de tabela em queries com múltiplos JOINs")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
