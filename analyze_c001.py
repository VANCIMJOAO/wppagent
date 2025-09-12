#!/usr/bin/env python3
"""
C001: Análise de Inconsistência Status Enum
==========================================

Problema: Status enum inconsistente entre backend e frontend
"""

import os
import json

def analyze_status_enum():
    print("🔍 C001: Análise de Status Enum Inconsistente")
    print("=" * 60)
    print()
    
    # Definir onde encontramos cada enum
    locations = {
        "app/models/database.py": {
            "line": 199,
            "status_values": ["pendente", "confirmado", "cancelado", "concluido", "bloqueado"],
            "context": "Modelo SQLAlchemy - comentário na definição"
        },
        "app/schemas/unified.py": {
            "line": 25,
            "status_values": ["agendado", "confirmado", "realizado", "cancelado", "pendente"],
            "context": "Schema Pydantic - enum oficial"
        },
        "app/schemas/appointments.py": {
            "line": 30,
            "status_values": ["pendente", "confirmado", "cancelado", "concluido", "bloqueado"],
            "context": "Schema específico appointments - validador"
        },
        "nextjs_dashboard/types/api.ts": {
            "line": 14,
            "status_values": ["agendado", "confirmado", "realizado", "cancelado", "pendente"],
            "context": "TypeScript interface - frontend"
        },
        "nextjs_dashboard/app/(dashboard)/agendamentos/page.tsx": {
            "line": 55,
            "status_values": ["confirmado", "agendado", "cancelado", "realizado", "pendente"],
            "context": "React component - mapeamento de cores/labels"
        }
    }
    
    print("📊 INCONSISTÊNCIAS ENCONTRADAS:")
    print("-" * 40)
    
    # Agrupar por valores únicos
    unique_enums = {}
    for location, data in locations.items():
        key = str(sorted(data["status_values"]))
        if key not in unique_enums:
            unique_enums[key] = []
        unique_enums[key].append({
            "location": location,
            "line": data["line"],
            "context": data["context"]
        })
    
    for i, (enum_key, locations_list) in enumerate(unique_enums.items(), 1):
        values = eval(enum_key)  # Converte string de volta para lista
        print(f"\n🔸 VARIAÇÃO {i}: {values}")
        for loc in locations_list:
            print(f"   📁 {loc['location']}:{loc['line']}")
            print(f"      └─ {loc['context']}")
    
    print(f"\n❌ TOTAL: {len(unique_enums)} versões diferentes encontradas!")
    
    print("\n🎯 ANÁLISE DO IMPACTO:")
    print("-" * 25)
    print("✅ Frontend usa: agendado, confirmado, realizado, cancelado, pendente")
    print("❌ Backend DB: pendente, confirmado, cancelado, concluido, bloqueado")
    print("⚠️  Schema appointments: pendente, confirmado, cancelado, concluido, bloqueado")
    print("✅ Schema unified: agendado, confirmado, realizado, cancelado, pendente")
    
    print("\n🔧 PROBLEMAS IDENTIFICADOS:")
    print("-" * 30)
    print("1. 'agendado' vs 'pendente' - Status inicial")
    print("2. 'realizado' vs 'concluido' - Status finalizado") 
    print("3. 'bloqueado' só existe no backend")
    print("4. Frontend não conhece 'bloqueado'")
    print("5. Backend não conhece 'agendado' e 'realizado'")
    
    print("\n🎯 SOLUÇÃO PROPOSTA:")
    print("-" * 20)
    print("Usar enum unificado do schemas/unified.py como padrão:")
    print("- AGENDADO (em vez de pendente)")
    print("- CONFIRMADO")  
    print("- REALIZADO (em vez de concluido)")
    print("- CANCELADO")
    print("- PENDENTE (status especial para aguardando confirmação)")
    
    return {
        "total_inconsistencies": len(unique_enums),
        "recommended_enum": ["agendado", "confirmado", "realizado", "cancelado", "pendente"],
        "files_to_fix": [
            "app/models/database.py",
            "app/schemas/appointments.py"
        ]
    }

if __name__ == "__main__":
    result = analyze_status_enum()
    
    # Salvar análise
    with open('/home/vancim/whats_agent/c001_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Análise salva em: c001_analysis.json")
    print("\n✅ C001: Análise completa. Pronto para correção!")
