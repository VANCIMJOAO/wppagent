#!/usr/bin/env python3
"""
Script para analisar a estrutura do banco de dados WhatsApp Agent
"""

import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text, inspect
import json

# Configurar variáveis de ambiente
os.environ['DATABASE_URL'] = 'postgresql://vancimj:os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")@localhost:5432/whats_agent'

def analyze_database():
    """Analisa a estrutura completa do banco de dados"""
    
    # Conectar ao banco
    engine = create_engine('postgresql://vancimj:os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")@localhost:5432/whats_agent')
    
    print("🔍 ANÁLISE DO BANCO DE DADOS - WhatsApp Agent")
    print("=" * 60)
    print(f"📅 Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obter informações sobre as tabelas
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"📊 TABELAS ENCONTRADAS: {len(tables)}")
    print("-" * 40)
    
    database_summary = {
        'total_tables': len(tables),
        'tables_info': {},
        'analysis_date': datetime.now().isoformat()
    }
    
    for table_name in sorted(tables):
        try:
            # Obter colunas da tabela
            columns = inspector.get_columns(table_name)
            
            # Contar registros
            with engine.connect() as conn:
                count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
                result = conn.execute(count_query)
                row_count = result.fetchone()[0]
                
                # Obter algumas amostras de dados se a tabela não estiver vazia
                sample_data = None
                if row_count > 0:
                    sample_query = text(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_result = conn.execute(sample_query)
                    sample_data = [dict(row._mapping) for row in sample_result.fetchall()]
            
            # Informações da tabela
            table_info = {
                'columns': len(columns),
                'rows': row_count,
                'column_details': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': str(col['default']) if col['default'] else None
                    }
                    for col in columns
                ],
                'sample_data': sample_data
            }
            
            database_summary['tables_info'][table_name] = table_info
            
            print(f"📋 {table_name}")
            print(f"   └── Colunas: {len(columns)}")
            print(f"   └── Registros: {row_count}")
            
            # Mostrar algumas colunas principais
            main_columns = [col['name'] for col in columns[:5]]
            print(f"   └── Principais colunas: {', '.join(main_columns)}")
            
            if row_count > 0 and sample_data:
                print(f"   └── Última atividade: dados disponíveis")
            print()
            
        except Exception as e:
            print(f"❌ Erro ao analisar {table_name}: {e}")
            database_summary['tables_info'][table_name] = {'error': str(e)}
    
    # Análise de relacionamentos e métricas importantes
    print("📈 MÉTRICAS PRINCIPAIS")
    print("-" * 40)
    
    try:
        with engine.connect() as conn:
            # Usuários únicos
            users_query = text("SELECT COUNT(*) FROM users")
            users_count = conn.execute(users_query).fetchone()[0]
            print(f"👥 Total de usuários: {users_count}")
            
            # Mensagens
            messages_query = text("SELECT COUNT(*) FROM messages")
            messages_count = conn.execute(messages_query).fetchone()[0]
            print(f"💬 Total de mensagens: {messages_count}")
            
            # Conversas
            conversations_query = text("SELECT COUNT(*) FROM conversation_contexts")
            conversations_count = conn.execute(conversations_query).fetchone()[0]
            print(f"🗣️ Total de conversas: {conversations_count}")
            
            # Agendamentos
            appointments_query = text("SELECT COUNT(*) FROM appointments")
            appointments_count = conn.execute(appointments_query).fetchone()[0]
            print(f"📅 Total de agendamentos: {appointments_count}")
            
            # Serviços
            services_query = text("SELECT COUNT(*) FROM services")
            services_count = conn.execute(services_query).fetchone()[0]
            print(f"🛠️ Total de serviços: {services_count}")
            
            database_summary['key_metrics'] = {
                'users': users_count,
                'messages': messages_count,
                'conversations': conversations_count,
                'appointments': appointments_count,
                'services': services_count
            }
            
    except Exception as e:
        print(f"❌ Erro ao obter métricas: {e}")
    
    print()
    print("🎯 ANÁLISE DE ATIVIDADE RECENTE")
    print("-" * 40)
    
    try:
        with engine.connect() as conn:
            # Mensagens recentes (últimas 24h)
            recent_messages_query = text("""
                SELECT COUNT(*) FROM messages 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """)
            recent_messages = conn.execute(recent_messages_query).fetchone()[0]
            print(f"📱 Mensagens últimas 24h: {recent_messages}")
            
            # Conversas ativas
            active_conversations_query = text("""
                SELECT COUNT(*) FROM conversation_contexts 
                WHERE is_active = true
            """)
            active_conversations = conn.execute(active_conversations_query).fetchone()[0]
            print(f"🔄 Conversas ativas: {active_conversations}")
            
            # Agendamentos futuros
            future_appointments_query = text("""
                SELECT COUNT(*) FROM appointments 
                WHERE scheduled_date >= CURRENT_DATE
            """)
            future_appointments = conn.execute(future_appointments_query).fetchone()[0]
            print(f"📋 Agendamentos futuros: {future_appointments}")
            
            database_summary['recent_activity'] = {
                'recent_messages_24h': recent_messages,
                'active_conversations': active_conversations,
                'future_appointments': future_appointments
            }
            
    except Exception as e:
        print(f"❌ Erro ao obter atividade recente: {e}")
    
    print()
    print("💾 SALVANDO ANÁLISE COMPLETA...")
    
    # Salvar análise em arquivo JSON
    with open('database_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(database_summary, f, indent=2, ensure_ascii=False, default=str)
    
    print("✅ Análise salva em 'database_analysis.json'")
    print()
    print("🚀 PRONTO PARA CRIAR DASHBOARD PERSONALIZADO!")
    
    return database_summary

if __name__ == "__main__":
    try:
        analyze_database()
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        sys.exit(1)
