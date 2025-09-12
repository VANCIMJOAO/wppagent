#!/usr/bin/env python3
"""
C002: Análise de Inconsistências de Naming - Data/Hora
====================================================

Problema: Convenção inconsistente entre snake_case e camelCase
- Backend: date_time (snake_case)
- Frontend: dateTime (camelCase esperado por JS/TS)
- Atual: data_agendamento (português)
"""

import os
import json
import re

def analyze_date_naming():
    print("🔍 C002: Análise de Naming de Data/Hora")
    print("=" * 50)
    print()
    
    patterns = {
        "date_time": [],
        "dateTime": [],
        "data_agendamento": [],
        "datetime": []
    }
    
    files_to_check = [
        # Backend
        "app/models/database.py",
        "app/schemas/appointments.py",
        "app/schemas/unified.py",
        "app/routes/appointments.py",
        "app/routes/appointments_realtime.py",
        # Frontend
        "nextjs_dashboard/types/api.ts",
        "nextjs_dashboard/types/api-manual.ts",
        "nextjs_dashboard/lib/appointment-normalizer.ts",
        "nextjs_dashboard/app/(dashboard)/agendamentos/page.tsx"
    ]
    
    print("📊 MAPEAMENTO DE NAMING PATTERNS:")
    print("-" * 40)
    
    total_files_checked = 0
    total_inconsistencies = 0
    
    for file_path in files_to_check:
        full_path = f"/home/vancim/whats_agent/{file_path}"
        
        if not os.path.exists(full_path):
            continue
            
        total_files_checked += 1
        print(f"\n📁 {file_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_patterns = {}
            
            # Buscar padrões
            for pattern in patterns.keys():
                matches = re.findall(rf'\b{pattern}\b', content, re.IGNORECASE)
                if matches:
                    file_patterns[pattern] = len(matches)
                    patterns[pattern].append({
                        "file": file_path,
                        "count": len(matches)
                    })
            
            if file_patterns:
                for pattern, count in file_patterns.items():
                    print(f"   {pattern}: {count} ocorrências")
                total_inconsistencies += len(file_patterns)
            else:
                print("   ✅ Nenhum padrão de data encontrado")
                
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    
    print(f"\n📈 RESUMO GERAL:")
    print("-" * 25)
    
    for pattern, occurrences in patterns.items():
        total_count = sum(occ["count"] for occ in occurrences)
        files_count = len(occurrences)
        
        if total_count > 0:
            print(f"\n🔸 {pattern}")
            print(f"   Total: {total_count} ocorrências em {files_count} arquivos")
            
            for occ in occurrences:
                location = "Backend" if occ["file"].startswith("app/") else "Frontend"
                print(f"   └─ {location}: {occ['file']} ({occ['count']}x)")
    
    print(f"\n🎯 PROBLEMAS IDENTIFICADOS:")
    print("-" * 30)
    print("1. ❌ Backend usa 'date_time' (snake_case)")
    print("2. ❌ Frontend mistura 'date_time' e 'data_agendamento'")
    print("3. ❌ JavaScript/TypeScript espera 'dateTime' (camelCase)")
    print("4. ❌ API responses inconsistentes")
    
    print(f"\n🔧 SOLUÇÃO PROPOSTA:")
    print("-" * 20)
    print("✅ Usar Pydantic aliases para converter:")
    print("   - Backend mantém: date_time (compatibilidade DB)")
    print("   - API expõe: dateTime (convenção frontend)")
    print("   - Backward compatibility: aceita ambos")
    
    solution = {
        "backend_field": "date_time",
        "api_alias": "dateTime",
        "files_to_modify": [
            "app/schemas/appointments.py",
            "app/schemas/unified.py",
            "nextjs_dashboard/types/api.ts"
        ],
        "migration_needed": False,  # DB mantém snake_case
        "aliases_needed": True
    }
    
    print(f"\n📋 ARQUIVOS PARA MODIFICAR:")
    print("-" * 30)
    for file in solution["files_to_modify"]:
        print(f"   📄 {file}")
    
    # Salvar análise
    analysis_result = {
        "patterns_found": patterns,
        "total_files_checked": total_files_checked,
        "solution": solution,
        "impact": "baixo",  # Não quebra funcionalidade
        "priority": "media"  # Melhora consistência
    }
    
    with open('/home/vancim/whats_agent/c002_analysis.json', 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    print(f"\n💾 Análise salva em: c002_analysis.json")
    print(f"\n✅ C002: Análise completa. Pronto para implementar aliases!")
    
    return analysis_result

if __name__ == "__main__":
    analyze_date_naming()
