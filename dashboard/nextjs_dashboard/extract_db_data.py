#!/usr/bin/env python3
"""
Script para extrair dados do PostgreSQL e salvar em JSON
para uso no dashboard Next.js
"""

import psycopg2
import json
from datetime import datetime, date

# Configuração do banco
DB_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

def serialize_datetime(obj):
    """Serializa objetos datetime para JSON"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def extract_database_data():
    """Extrai todos os dados relevantes do banco"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        data = {}
        
        # 1. Estrutura das tabelas
        print("📊 Extraindo estrutura das tabelas...")
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position;
        """)
        
        tables_structure = {}
        for row in cursor.fetchall():
            table_name, column_name, data_type, is_nullable = row
            if table_name not in tables_structure:
                tables_structure[table_name] = []
            tables_structure[table_name].append({
                'column': column_name,
                'type': data_type,
                'nullable': is_nullable == 'YES'
            })
        
        data['tables_structure'] = tables_structure
        
        # 2. Contagens gerais
        print("📈 Extraindo contagens gerais...")
        cursor.execute("SELECT 'conversations' as tabela, COUNT(*) as total FROM conversations")
        conversations_count = cursor.fetchone()[1]
        
        cursor.execute("SELECT 'users' as tabela, COUNT(*) as total FROM users")
        users_count = cursor.fetchone()[1]
        
        cursor.execute("SELECT 'messages' as tabela, COUNT(*) as total FROM messages")
        messages_count = cursor.fetchone()[1]
        
        cursor.execute("SELECT 'appointments' as tabela, COUNT(*) as total FROM appointments")
        appointments_count = cursor.fetchone()[1]
        
        data['totals'] = {
            'conversations': conversations_count,
            'users': users_count,
            'messages': messages_count,
            'appointments': appointments_count
        }
        
        # 3. Atividades recentes (últimas mensagens)
        print("⏰ Extraindo atividades recentes...")
        cursor.execute("""
            SELECT 
                m.id,
                'message' as type,
                'Nova mensagem recebida' as title,
                CONCAT('Conversa #', c.id, ' - ', COALESCE(u.nome, 'Usuário')) as description,
                m.created_at
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id  
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY m.created_at DESC
            LIMIT 10;
        """)
        
        recent_messages = []
        for row in cursor.fetchall():
            recent_messages.append({
                'id': row[0],
                'type': row[1],
                'title': row[2],
                'description': row[3],
                'created_at': row[4]
            })
        
        # 4. Últimos agendamentos
        cursor.execute("""
            SELECT 
                id,
                'appointment' as type,
                CONCAT('Agendamento ', status) as title,
                CONCAT('Status: ', status) as description,
                created_at
            FROM appointments
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        
        recent_appointments = []
        for row in cursor.fetchall():
            recent_appointments.append({
                'id': row[0],
                'type': row[1],
                'title': row[2],
                'description': row[3],
                'created_at': row[4]
            })
        
        data['recent_activities'] = recent_messages + recent_appointments
        data['recent_activities'].sort(key=lambda x: x['created_at'], reverse=True)
        data['recent_activities'] = data['recent_activities'][:8]
        
        # 5. Status dos agendamentos
        print("📅 Extraindo status dos agendamentos...")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM appointments
            GROUP BY status
            ORDER BY count DESC;
        """)
        
        appointment_status = []
        for row in cursor.fetchall():
            appointment_status.append({
                'status': row[0],
                'count': row[1]
            })
        
        data['appointment_status'] = appointment_status
        
        # 6. Métricas por período
        print("📊 Extraindo métricas por período...")
        
        # Hoje
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM messages WHERE DATE(created_at) = CURRENT_DATE) as messages_today,
                (SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE) as conversations_today,
                (SELECT COUNT(*) FROM appointments WHERE DATE(created_at) = CURRENT_DATE) as appointments_today;
        """)
        today_stats = cursor.fetchone()
        
        # Últimos 7 dias
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM messages WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as messages_7days,
                (SELECT COUNT(*) FROM conversations WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as conversations_7days,
                (SELECT COUNT(*) FROM appointments WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as appointments_7days;
        """)
        week_stats = cursor.fetchone()
        
        # Este mês
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM messages 
                 WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
                   AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)) as messages_month,
                (SELECT COUNT(*) FROM conversations 
                 WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
                   AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)) as conversations_month,
                (SELECT COUNT(*) FROM appointments 
                 WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
                   AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)) as appointments_month;
        """)
        month_stats = cursor.fetchone()
        
        data['period_stats'] = {
            'today': {
                'messages': today_stats[0],
                'conversations': today_stats[1],
                'appointments': today_stats[2]
            },
            'last_7_days': {
                'messages': week_stats[0],
                'conversations': week_stats[1],
                'appointments': week_stats[2]
            },
            'this_month': {
                'messages': month_stats[0],
                'conversations': month_stats[1],
                'appointments': month_stats[2]
            }
        }
        
        # 7. Conversas por data (últimos 30 dias)
        print("📈 Extraindo dados de conversas por período...")
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM conversations
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC;
        """)
        
        conversations_by_date = []
        for row in cursor.fetchall():
            conversations_by_date.append({
                'date': row[0],
                'count': row[1]
            })
        
        # 8. Mensagens por data (últimos 30 dias)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM messages
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC;
        """)
        
        messages_by_date = []
        for row in cursor.fetchall():
            messages_by_date.append({
                'date': row[0],
                'count': row[1]
            })
        
        data['charts_data'] = {
            'conversations_by_date': conversations_by_date,
            'messages_by_date': messages_by_date
        }
        
        # 9. Métricas calculadas
        print("🧮 Calculando métricas...")
        
        # Taxa de conversão
        cursor.execute("""
            SELECT 
                ROUND(
                    (COUNT(DISTINCT c.id) * 100.0) / NULLIF(
                        (SELECT COUNT(*) FROM users), 0
                    ), 2
                ) as conversion_rate
            FROM conversations c
            WHERE c.id IN (SELECT DISTINCT conversation_id FROM messages);
        """)
        conversion_rate = cursor.fetchone()[0]
        
        # Média de mensagens por conversa
        cursor.execute("""
            SELECT ROUND(AVG(msg_count)::numeric, 1) as avg_messages
            FROM (
                SELECT conversation_id, COUNT(*) as msg_count 
                FROM messages 
                GROUP BY conversation_id
            ) subconsulta;
        """)
        avg_messages = cursor.fetchone()[0]
        
        # Usuários ativos
        cursor.execute("""
            SELECT COUNT(DISTINCT u.id) as active_users
            FROM users u
            INNER JOIN conversations c ON u.id = c.user_id;
        """)
        active_users = cursor.fetchone()[0]
        
        data['calculated_metrics'] = {
            'conversion_rate': float(conversion_rate) if conversion_rate else 0,
            'avg_messages_per_conversation': float(avg_messages) if avg_messages else 0,
            'active_users': active_users
        }
        
        # 10. Informações gerais
        data['extraction_info'] = {
            'timestamp': datetime.now(),
            'database_url': DB_URL.split('@')[1],  # Remove credenciais
            'total_tables': len(tables_structure)
        }
        
        cursor.close()
        conn.close()
        
        return data
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados: {e}")
        return None

def save_to_json(data, filename='db_data.json'):
    """Salva os dados em arquivo JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=serialize_datetime)
        print(f"✅ Dados salvos em: {filename}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar JSON: {e}")
        return False

def main():
    print("🚀 Iniciando extração de dados do PostgreSQL...")
    print("=" * 50)
    
    # Extrair dados
    data = extract_database_data()
    if not data:
        print("❌ Falha na extração de dados")
        return
    
    # Salvar em JSON
    if save_to_json(data):
        print("=" * 50)
        print("📊 RESUMO DOS DADOS EXTRAÍDOS:")
        print(f"   • Tabelas: {len(data['tables_structure'])}")
        print(f"   • Conversas: {data['totals']['conversations']}")
        print(f"   • Usuários: {data['totals']['users']}")
        print(f"   • Mensagens: {data['totals']['messages']}")
        print(f"   • Agendamentos: {data['totals']['appointments']}")
        print(f"   • Taxa de conversão: {data['calculated_metrics']['conversion_rate']}%")
        print(f"   • Média mensagens/conversa: {data['calculated_metrics']['avg_messages_per_conversation']}")
        print("=" * 50)
        print("🎉 Extração concluída com sucesso!")
    
if __name__ == "__main__":
    main()
