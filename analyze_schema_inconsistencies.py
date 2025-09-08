#!/usr/bin/env python3
"""
🔍 ANÁLISE INCONSISTÊNCIAS SCHEMA APPOINTMENTS
================================================

Este script analisa as inconsistências entre:
- Backend (SQLAlchemy models)
- Frontend (TypeScript types)  
- API (Pydantic schemas)
- Banco de dados real

Identificará campos duplicados, tipos incompatíveis e nomes divergentes.
"""

import asyncio
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Any
from datetime import datetime


class SchemaAnalyzer:
    def __init__(self):
        self.backend_fields = {}
        self.frontend_fields = {}
        self.api_fields = {}
        self.inconsistencies = []
    
    def analyze_backend_model(self, file_path: str):
        """Analisa o modelo SQLAlchemy do backend"""
        print("🔍 Analisando modelo backend (SQLAlchemy)...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Procurar a classe Appointment
            appointment_match = re.search(
                r'class Appointment\(Base\):(.*?)(?=class\s+\w+\(Base\)|$)', 
                content, 
                re.DOTALL
            )
            
            if not appointment_match:
                print("  ❌ Classe Appointment não encontrada")
                return
            
            appointment_content = appointment_match.group(1)
            
            # Extrair campos Column
            column_pattern = r'(\w+)\s*=\s*Column\((.*?)\)'
            columns = re.findall(column_pattern, appointment_content)
            
            for field_name, column_def in columns:
                # Extrair tipo básico
                type_match = re.search(r'(Integer|String|DateTime|Numeric|Boolean|Text)', column_def)
                field_type = type_match.group(1) if type_match else 'Unknown'
                
                # Verificar se é nullable
                nullable = 'nullable=False' not in column_def
                
                # Verificar default
                default_match = re.search(r'default=([^,)]+)', column_def)
                default_value = default_match.group(1) if default_match else None
                
                self.backend_fields[field_name] = {
                    'type': field_type,
                    'nullable': nullable,
                    'default': default_value,
                    'source': 'SQLAlchemy Model'
                }
            
            print(f"  ✅ Encontrados {len(self.backend_fields)} campos no backend")
            
            # Identificar campos problemáticos específicos
            problematic_fields = []
            if 'price' in self.backend_fields and 'price_at_booking' in self.backend_fields:
                problematic_fields.append("price + price_at_booking (duplicação)")
            
            if 'duration' in self.backend_fields:
                problematic_fields.append("duration (deveria ser duration_minutes)")
            
            if problematic_fields:
                print(f"  ⚠️ Campos problemáticos: {', '.join(problematic_fields)}")
            
        except Exception as e:
            print(f"  ❌ Erro ao analisar backend: {e}")
    
    def analyze_frontend_types(self, file_path: str):
        """Analisa os tipos TypeScript do frontend"""
        print("\n🔍 Analisando tipos frontend (TypeScript)...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Procurar interface Appointment
            interface_match = re.search(
                r'export interface Appointment \{(.*?)\}', 
                content, 
                re.DOTALL
            )
            
            if not interface_match:
                print("  ❌ Interface Appointment não encontrada")
                return
            
            interface_content = interface_match.group(1)
            
            # Extrair campos da interface
            field_pattern = r'(\w+)(\??):\s*([^;]+);'
            fields = re.findall(field_pattern, interface_content)
            
            for field_name, optional, field_type in fields:
                is_optional = bool(optional)
                
                self.frontend_fields[field_name] = {
                    'type': field_type.strip(),
                    'optional': is_optional,
                    'source': 'TypeScript Interface'
                }
            
            print(f"  ✅ Encontrados {len(self.frontend_fields)} campos no frontend")
            
        except Exception as e:
            print(f"  ❌ Erro ao analisar frontend: {e}")
    
    def analyze_api_schema(self, file_path: str):
        """Analisa os esquemas Pydantic da API"""
        print("\n🔍 Analisando esquemas API (Pydantic)...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Procurar classe AppointmentResponse ou similar
            schema_matches = re.findall(
                r'class (\w*Appointment\w*)\([^)]*BaseModel[^)]*\):(.*?)(?=class\s+\w+|$)', 
                content, 
                re.DOTALL
            )
            
            if not schema_matches:
                print("  ⚠️ Nenhum schema Pydantic de Appointment encontrado")
                return
            
            for schema_name, schema_content in schema_matches:
                print(f"  📋 Analisando schema: {schema_name}")
                
                # Extrair campos do schema
                field_pattern = r'(\w+):\s*([^=\n]+)(?:\s*=\s*[^\n]*)?'
                fields = re.findall(field_pattern, schema_content)
                
                for field_name, field_type in fields:
                    if field_name not in ['class', 'Config']:
                        self.api_fields[field_name] = {
                            'type': field_type.strip(),
                            'schema': schema_name,
                            'source': 'Pydantic Schema'
                        }
            
            print(f"  ✅ Encontrados {len(self.api_fields)} campos na API")
            
        except Exception as e:
            print(f"  ❌ Erro ao analisar API: {e}")
    
    def find_inconsistencies(self):
        """Identifica inconsistências entre os schemas"""
        print("\n🚨 ANÁLISE DE INCONSISTÊNCIAS:")
        print("=" * 50)
        
        all_fields = set()
        all_fields.update(self.backend_fields.keys())
        all_fields.update(self.frontend_fields.keys())
        all_fields.update(self.api_fields.keys())
        
        for field in sorted(all_fields):
            backend = self.backend_fields.get(field)
            frontend = self.frontend_fields.get(field)
            api = self.api_fields.get(field)
            
            sources = []
            if backend: sources.append("Backend")
            if frontend: sources.append("Frontend") 
            if api: sources.append("API")
            
            # Campo existe em todos os lugares?
            if len(sources) < 3:
                missing = [s for s in ["Backend", "Frontend", "API"] if s not in sources]
                print(f"\n⚠️  CAMPO AUSENTE: {field}")
                print(f"   Presente em: {', '.join(sources)}")
                print(f"   Ausente em: {', '.join(missing)}")
                
                # Mostrar detalhes onde existe
                if backend:
                    print(f"   Backend: {backend['type']} (nullable={backend['nullable']})")
                if frontend:
                    print(f"   Frontend: {frontend['type']} (optional={frontend['optional']})")
                if api:
                    print(f"   API: {api['type']}")
        
        # Verificar campos conflitantes específicos
        print("\n🔍 CONFLITOS ESPECÍFICOS:")
        
        conflicts = [
            ("price", "price_at_booking", "Campos de preço duplicados"),
            ("duration", "duration_minutes", "Nomes inconsistentes para duração"),
            ("date_time", "data_agendamento", "Nomes diferentes para data"),
            ("user_id", "cliente_id", "Referência ao usuário inconsistente")
        ]
        
        for field1, field2, description in conflicts:
            has_field1 = any([field1 in schema for schema in [self.backend_fields, self.frontend_fields, self.api_fields]])
            has_field2 = any([field2 in schema for schema in [self.backend_fields, self.frontend_fields, self.api_fields]])
            
            if has_field1 and has_field2:
                print(f"   ❌ {description}")
                if field1 in self.backend_fields:
                    print(f"      {field1}: Backend ({self.backend_fields[field1]['type']})")
                if field2 in self.backend_fields:
                    print(f"      {field2}: Backend ({self.backend_fields[field2]['type']})")
                if field1 in self.frontend_fields:
                    print(f"      {field1}: Frontend ({self.frontend_fields[field1]['type']})")
                if field2 in self.frontend_fields:
                    print(f"      {field2}: Frontend ({self.frontend_fields[field2]['type']})")
    
    def generate_fix_recommendations(self):
        """Gera recomendações para corrigir as inconsistências"""
        print("\n🔧 RECOMENDAÇÕES DE CORREÇÃO:")
        print("=" * 50)
        
        # Padronização de campos
        recommendations = []
        
        if 'price_at_booking' in self.backend_fields and 'price' in self.backend_fields:
            recommendations.append({
                'priority': 'HIGH',
                'title': 'Unificar campos de preço',
                'description': 'Manter apenas "price" e remover "price_at_booking"',
                'actions': [
                    'Criar migration para consolidar price_at_booking -> price',
                    'Atualizar modelo SQLAlchemy para usar apenas "price"',
                    'Garantir que frontend usa "price" consistentemente'
                ]
            })
        
        if 'duration' in self.backend_fields:
            recommendations.append({
                'priority': 'MEDIUM',
                'title': 'Padronizar nome do campo duração',
                'description': 'Renomear "duration" para "duration_minutes"',
                'actions': [
                    'Criar migration: ALTER TABLE appointments RENAME COLUMN duration TO duration_minutes',
                    'Atualizar modelo SQLAlchemy',
                    'Verificar se frontend já usa "duration_minutes"'
                ]
            })
        
        if 'data_agendamento' in self.frontend_fields and 'date_time' in self.backend_fields:
            recommendations.append({
                'priority': 'LOW',
                'title': 'Padronizar nome do campo data',
                'description': 'Usar "date_time" em todos os lugares',
                'actions': [
                    'Atualizar interface TypeScript para usar "date_time"',
                    'Ajustar mapeamentos na API',
                    'Verificar componentes React que usam o campo'
                ]
            })
        
        # Mostrar recomendações ordenadas por prioridade
        for rec in sorted(recommendations, key=lambda x: {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[x['priority']], reverse=True):
            print(f"\n🔨 [{rec['priority']}] {rec['title']}")
            print(f"   {rec['description']}")
            for action in rec['actions']:
                print(f"   • {action}")
    
    def print_summary(self):
        """Imprime resumo da análise"""
        print("\n📊 RESUMO DA ANÁLISE:")
        print("=" * 50)
        print(f"Backend (SQLAlchemy): {len(self.backend_fields)} campos")
        print(f"Frontend (TypeScript): {len(self.frontend_fields)} campos")
        print(f"API (Pydantic): {len(self.api_fields)} campos")
        
        # Campos únicos por fonte
        backend_only = set(self.backend_fields.keys()) - set(self.frontend_fields.keys()) - set(self.api_fields.keys())
        frontend_only = set(self.frontend_fields.keys()) - set(self.backend_fields.keys()) - set(self.api_fields.keys())
        api_only = set(self.api_fields.keys()) - set(self.backend_fields.keys()) - set(self.frontend_fields.keys())
        
        if backend_only:
            print(f"\nApenas no Backend: {', '.join(sorted(backend_only))}")
        if frontend_only:
            print(f"Apenas no Frontend: {', '.join(sorted(frontend_only))}")
        if api_only:
            print(f"Apenas na API: {', '.join(sorted(api_only))}")


def main():
    print("🔍 ANÁLISE INCONSISTÊNCIAS SCHEMA APPOINTMENTS")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyzer = SchemaAnalyzer()
    
    # Analisar arquivos
    base_path = Path("/home/vancim/whats_agent")
    
    # Backend model
    backend_model = base_path / "app" / "models" / "database.py"
    if backend_model.exists():
        analyzer.analyze_backend_model(str(backend_model))
    else:
        print("❌ Arquivo do modelo backend não encontrado")
    
    # Frontend types  
    frontend_types = base_path / "nextjs_dashboard" / "types" / "api.ts"
    if frontend_types.exists():
        analyzer.analyze_frontend_types(str(frontend_types))
    else:
        print("❌ Arquivo de tipos frontend não encontrado")
    
    # API schemas
    api_schemas = base_path / "app" / "routes" / "appointments.py"
    if api_schemas.exists():
        analyzer.analyze_api_schema(str(api_schemas))
    else:
        print("❌ Arquivo de schemas API não encontrado")
    
    # Análise e recomendações
    analyzer.find_inconsistencies()
    analyzer.generate_fix_recommendations()
    analyzer.print_summary()
    
    print(f"\n⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Análise interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro crítico na análise: {e}")
        sys.exit(1)
