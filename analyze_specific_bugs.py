#!/usr/bin/env python3
"""
🔍 ANÁLISE ESPECÍFICA DOS BUGS SQL MENCIONADOS NO BUG REPORT
=============================================================

Análise focada nos problemas exatos mencionados no bug report:

1. conversations.py - Linha 65-85: func.count(Message.id) AMBÍGUO
2. appointments.py - Linha 45-60: JOIN com ID ambíguo  
3. dashboard.py - Linha 30-50: Queries complexas

"""

import ast
import re
from typing import List, Dict

def find_problematic_query_patterns():
    """Procura por padrões específicos de queries problemáticas"""
    
    print("🎯 ANÁLISE ESPECÍFICA DOS BUGS SQL MENCIONADOS")
    print("=" * 60)
    
    # 1. Análise detalhada do conversations.py
    print("\n1️⃣ CONVERSATIONS.PY - Análise das linhas 65-85")
    print("-" * 50)
    
    with open('/home/vancim/whats_agent/app/routes/conversations.py', 'r') as f:
        conv_lines = f.readlines()
    
    # Examinar linhas 65-85 (índices 64-84)
    for i in range(64, min(85, len(conv_lines))):
        line = conv_lines[i].strip()
        if any(pattern in line for pattern in ['func.count', 'Message.id', 'outerjoin']):
            print(f"   {i+1:3}: {line}")
    
    # 2. Análise detalhada do appointments.py
    print("\n2️⃣ APPOINTMENTS.PY - Análise das linhas 45-60") 
    print("-" * 50)
    
    with open('/home/vancim/whats_agent/app/routes/appointments.py', 'r') as f:
        appt_lines = f.readlines()
        
    # Examinar linhas 45-60 (índices 44-59)
    for i in range(44, min(60, len(appt_lines))):
        line = appt_lines[i].strip()
        if any(pattern in line for pattern in ['select', 'join', 'User.id', 'Business.id']):
            print(f"   {i+1:3}: {line}")
    
    # 3. Busca por queries complexas problemáticas
    print("\n3️⃣ DASHBOARD.PY - Busca por queries complexas")
    print("-" * 50)
    
    with open('/home/vancim/whats_agent/app/routes/dashboard.py', 'r') as f:
        dash_content = f.read()
    
    # Procurar por queries que fazem JOIN com COUNT
    join_count_pattern = re.compile(
        r'select\(.*func\.count.*\).*join.*join', 
        re.IGNORECASE | re.DOTALL
    )
    
    matches = join_count_pattern.finditer(dash_content)
    for match in matches:
        start_line = dash_content[:match.start()].count('\n') + 1
        print(f"   Linha ~{start_line}: Query complexa com JOIN + COUNT encontrada")
    
    # 4. Procurar por problemas específicos de ambiguidade
    print("\n4️⃣ PROBLEMAS DE AMBIGUIDADE ESPECÍFICOS")
    print("-" * 50)
    
    files_to_check = [
        ('/home/vancim/whats_agent/app/routes/conversations.py', 'conversations.py'),
        ('/home/vancim/whats_agent/app/routes/appointments.py', 'appointments.py'),
        ('/home/vancim/whats_agent/app/routes/dashboard.py', 'dashboard.py')
    ]
    
    for file_path, file_name in files_to_check:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Padrão: múltiplos func.count() na mesma query
        multiple_count = re.findall(
            r'select\((.*?)\).*?func\.count.*?func\.count', 
            content, 
            re.IGNORECASE | re.DOTALL
        )
        
        if multiple_count:
            print(f"   ⚠️  {file_name}: Múltiplos func.count() encontrados")
            
        # Padrão: JOIN sem alias em queries complexas
        complex_join = re.findall(
            r'\.join\(.*?\)\..*?join\(.*?\)\..*?outerjoin', 
            content, 
            re.IGNORECASE | re.DOTALL
        )
        
        if complex_join:
            print(f"   ⚠️  {file_name}: JOINs complexos sem aliases encontrados")
            
        # Padrão: func.count(X.id) com JOIN
        count_with_join = re.findall(
            r'func\.count\(.*?\.id\).*?join', 
            content, 
            re.IGNORECASE | re.DOTALL
        )
        
        if count_with_join:
            print(f"   ⚠️  {file_name}: func.count(X.id) com JOINs encontrados")

if __name__ == "__main__":
    find_problematic_query_patterns()
