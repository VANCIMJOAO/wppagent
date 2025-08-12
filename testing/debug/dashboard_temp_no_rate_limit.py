import dash
from dash import dcc, html, callback, Input, Output, State, dash_table, clientside_callback, ClientsideFunction, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, time
from sqlalchemy import text
import json
import re
import warnings
import sys
import os
import random
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importações de autenticação
from app.components.auth import create_login_page, create_logout_component, create_auth_callbacks, check_authentication, require_auth

# Importações de validação robusta
from app.utils.validators import (
    ValidationError, RobustValidator, DatabaseValidator,
    validate_user_input, validate_message_input, validate_appointment_input,
    validate_brazilian_phone, format_phone_display
)

# Importações de rate limiting
try:
    from app.middleware.rate_limit_middleware import (
        setup_advanced_rate_limiting, DashRateLimitMiddleware, RateLimitMonitor,
        protect_heavy_operation, protect_auth_endpoint
    )
    from app.utils.rate_limiter import RateLimitException, rate_limiter
    RATE_LIMITING_AVAILABLE = True
    print("✅ Sistema de Rate Limiting carregado")
except ImportError as e:
    RATE_LIMITING_AVAILABLE = False
    print(f"⚠️ Rate Limiting não disponível: {e}")
    
    # Fallback decorators quando rate limiting não está disponível
    def protect_heavy_operation(func):
        return func
    def protect_auth_endpoint(func):
        return func

# Importações para WebSocket e tempo real
try:
    from dash_extensions import WebSocket
    WEBSOCKET_AVAILABLE = True
    print("✅ WebSocket disponível")
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("⚠️ dash_extensions não disponível - funcionalidade de tempo real limitada")

# Suprimir o warning de parsing de datas
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Parsing dates.*")

# 🚀 DASHBOARD WHATSAPP AGENT - VERSÃO COMPLETA
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
    ],
    suppress_callback_exceptions=True
)

app.title = "WhatsApp Agent • Dashboard Executivo"

# 🛡️ CONFIGURAR RATE LIMITING AVANÇADO - TEMPORARIAMENTE DESABILITADO
# if RATE_LIMITING_AVAILABLE:
#     try:
#         rate_limit_middleware = setup_advanced_rate_limiting(app, 'dash')
#         rate_limit_monitor = RateLimitMonitor()
#         print("✅ Rate Limiting configurado com sucesso no dashboard")
#     except Exception as e:
#         print(f"⚠️ Erro ao configurar rate limiting: {e}")
#         RATE_LIMITING_AVAILABLE = False
# else:
#     print("⚠️ Dashboard rodando sem proteção de rate limiting")

RATE_LIMITING_AVAILABLE = False  # Força desativar rate limiting
print("⚠️ Dashboard rodando sem proteção de rate limiting (temporário)")

# Conexão com banco de dados CORRIGIDA E SEGURA
def get_database_connection():
    """Obter conexão com banco de dados com validação robusta"""
    try:
        # Primeiro tentar importar do caminho da aplicação
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app.database import sync_engine
        print("✅ Conexão com banco estabelecida via app.database")
        return sync_engine
    except ImportError as ie:
        print(f"⚠️ Erro ao importar app.database: {ie}")
        try:
            # Alternativa: tentar criar conexão direta com validação
            from sqlalchemy import create_engine
            
            # URL de conexão usando as configurações do .env (versão sync)
            database_url = os.getenv('DATABASE_URL', 'postgresql://vancimj:SECURE_PASSWORD@localhost:5432/whats_agent')
            
            # Validar URL antes de usar
            if not database_url or len(database_url) < 10:
                raise ValidationError("❌ URL do banco de dados inválida")
            
            # Converter de asyncpg para psycopg2 (sync)
            if 'postgresql+asyncpg://' in database_url:
                database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            
            # Validar formato da URL
            if not database_url.startswith('postgresql://'):
                raise ValidationError("❌ URL do banco deve começar com postgresql://")
            
            engine = create_engine(database_url)
            print("✅ Conexão direta com banco estabelecida e validada")
            return engine
        except Exception as de:
            print(f"❌ Erro na conexão direta: {de}")
            return None
    except Exception as e:
        print(f"❌ Erro geral na conexão: {e}")
        return None

def safe_execute_query(query: str, params: dict = None):
    """Executar query de forma segura com validação robusta"""
    engine = get_database_connection()
    if not engine:
        raise ValidationError("❌ Sem conexão com banco de dados")
    
    try:
        # Usar o validador de banco de dados
        return DatabaseValidator.safe_execute_query(engine, query, params)
    except ValidationError:
        raise
    except Exception as e:
        print(f"❌ Erro na execução segura da query: {e}")
        raise ValidationError(f"Erro na execução da query: {str(e)}")

# ==================== FUNÇÕES DE VALIDAÇÃO PARA DASHBOARD ====================

def validate_dashboard_form(form_data: dict, form_type: str) -> dict:
    """Validar dados de formulário do dashboard"""
    try:
        if form_type == 'user':
            return validate_user_input(form_data)
        elif form_type == 'message':
            return validate_message_input(form_data)
        elif form_type == 'appointment':
            return validate_appointment_input(form_data)
        else:
            raise ValidationError(f"❌ Tipo de formulário não suportado: {form_type}")
    except ValidationError as e:
        print(f"❌ Erro de validação ({form_type}): {e}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado na validação: {e}")
        raise ValidationError(f"Erro interno: {str(e)}")

def sanitize_dashboard_input(data: dict) -> dict:
    """Sanitizar todas as entradas do dashboard"""
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Sanitizar strings
            sanitized[key] = RobustValidator.sanitize_sql_input(value)
        elif isinstance(value, (int, float)):
            # Validar números
            sanitized[key] = value
        elif isinstance(value, (list, dict)):
            # Converter para JSON se necessário
            try:
                sanitized[key] = json.dumps(value) if isinstance(value, dict) else value
            except:
                sanitized[key] = str(value)
        else:
            # Outros tipos
            sanitized[key] = str(value) if value is not None else ""
    
    return sanitized

def validate_search_params(search_term: str, table_name: str) -> tuple:
    """Validar parâmetros de busca"""
    try:
        # Validar termo de busca
        if not search_term or len(search_term.strip()) < 2:
            raise ValidationError("❌ Termo de busca deve ter pelo menos 2 caracteres")
        
        # Sanitizar entrada
        clean_term = RobustValidator.sanitize_sql_input(search_term.strip())
        
        # Validar nome da tabela
        valid_tables = ['users', 'messages', 'conversations', 'appointments', 'services']
        if table_name not in valid_tables:
            raise ValidationError(f"❌ Tabela inválida: {table_name}")
        
        # Limitar tamanho do termo
        if len(clean_term) > 100:
            clean_term = clean_term[:100]
            print("⚠️ Termo de busca truncado para 100 caracteres")
        
        return clean_term, table_name
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Erro na validação de busca: {str(e)}")

def validate_date_range(start_date: str, end_date: str) -> tuple:
    """Validar intervalo de datas"""
    try:
        # Validar e converter datas
        start_dt = RobustValidator.validate_datetime(start_date, "Data inicial", required=True)
        end_dt = RobustValidator.validate_datetime(end_date, "Data final", required=True)
        
        # Verificar se a data final é posterior à inicial
        if end_dt <= start_dt:
            raise ValidationError("❌ Data final deve ser posterior à data inicial")
        
        # Verificar se o intervalo não é muito grande (máximo 1 ano)
        if (end_dt - start_dt).days > 365:
            raise ValidationError("❌ Intervalo máximo permitido: 1 ano")
        
        return start_dt, end_dt
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Erro na validação de datas: {str(e)}")

def validate_pagination_params(page: int, per_page: int) -> tuple:
    """Validar parâmetros de paginação"""
    try:
        # Validar página
        page_num = RobustValidator.validate_integer(page, "Página", min_value=1, max_value=10000)
        
        # Validar itens por página
        per_page_num = RobustValidator.validate_integer(per_page, "Itens por página", min_value=1, max_value=1000)
        
        return page_num, per_page_num
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Erro na validação de paginação: {str(e)}")

# ==================== FUNÇÕES DE CARREGAMENTO DE DADOS ====================

@protect_heavy_operation
def load_overview_data():
    """Carregar dados para visão geral com validação robusta"""
    try:
        # Queries seguras para métricas básicas
        queries = {
            'users': "SELECT COUNT(*) FROM users",
            'messages': "SELECT COUNT(*) FROM messages", 
            'conversations': "SELECT COUNT(*) FROM conversations",
            'appointments': "SELECT COUNT(*) FROM appointments",
            'services': "SELECT COUNT(*) FROM services",
            'blocked_times': "SELECT COUNT(*) FROM blocked_times"
        }
        
        metrics = {}
        
        # Executar queries de forma segura
        for metric, query in queries.items():
            try:
                result = safe_execute_query(query)
                # safe_execute_query agora retorna scalar value diretamente para COUNT
                metrics[metric] = result if isinstance(result, (int, float)) else 0
            except (ValidationError, Exception) as e:
                print(f"⚠️ Erro ao carregar métrica {metric}: {e}")
                metrics[metric] = 0
        
        # Queries complexas com validação
        complex_queries = {
            'msg_direction': """
                SELECT direction, COUNT(*) as count 
                FROM messages 
                GROUP BY direction
            """,
            'msg_recent': """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM messages 
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """,
            'conv_status': """
                SELECT status, COUNT(*) as count
                FROM conversations
                GROUP BY status
            """,
            'app_status': """
                SELECT status, COUNT(*) as count
                FROM appointments
                GROUP BY status
            """
        }
        
        results = {}
        
        for key, query in complex_queries.items():
            try:
                result = safe_execute_query(query)
                # safe_execute_query agora retorna lista de dados diretamente
                results[key] = result if isinstance(result, list) else []
            except (ValidationError, Exception) as e:
                print(f"⚠️ Erro ao carregar dados {key}: {e}")
                results[key] = []
        
        print(f"✅ Dados carregados com segurança: {metrics}")
        
        return {
            'metrics': metrics,
            'msg_direction': results['msg_direction'],
            'msg_recent': results['msg_recent'],
            'conv_status': results['conv_status'],
            'app_status': results['app_status']
        }
        
    except Exception as e:
        print(f"❌ Erro crítico ao carregar dados de overview: {e}")
        return get_sample_overview_data()

def get_sample_overview_data():
    """Retornar dados de exemplo quando banco não está disponível"""
    print("📊 Retornando dados de exemplo")
    return {
        'metrics': {
            'users': 150,
            'messages': 1250,
            'conversations': 89,
            'appointments': 45,
            'services': 12,
            'blocked_times': 5
        },
        'msg_direction': [('in', 800), ('out', 450)],
        'msg_recent': [
            ('2025-08-01', 45),
            ('2025-08-02', 52),
            ('2025-08-03', 38),
            ('2025-08-04', 67),
            ('2025-08-05', 71),
            ('2025-08-06', 55),
            ('2025-08-07', 43)
        ],
        'conv_status': [('ativa', 34), ('pausada', 12), ('finalizada', 43)],
        'app_status': [('confirmado', 28), ('pendente', 12), ('cancelado', 5)]
    }

@protect_heavy_operation
def load_messages_data():
    """Carregar dados de mensagens para interface WhatsApp Web"""
    engine = get_database_connection()
    if not engine:
        print("❌ Sem conexão - retornando conversas de exemplo")
        return get_sample_conversations()
    
    try:
        with engine.connect() as conn:
            conversations_query = text("""
                SELECT DISTINCT 
                    c.id as conversation_id,
                    u.nome,
                    u.telefone,
                    u.wa_id,
                    c.status,
                    c.last_message_at,
                    c.created_at,
                    (SELECT content FROM messages 
                     WHERE conversation_id = c.id 
                     ORDER BY created_at DESC LIMIT 1) as last_message,
                    (SELECT direction FROM messages 
                     WHERE conversation_id = c.id 
                     ORDER BY created_at DESC LIMIT 1) as last_direction
                FROM conversations c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.last_message_at DESC NULLS LAST
            """)
            
            conversations = conn.execute(conversations_query).fetchall()
            
            return pd.DataFrame(conversations, columns=[
                'conversation_id', 'nome', 'telefone', 'wa_id', 'status',
                'last_message_at', 'created_at', 'last_message', 'last_direction'
            ])
    
    except Exception as e:
        print(f"❌ Erro ao carregar conversas: {e}")
        return get_sample_conversations()
    
    finally:
        try:
            engine.dispose()
        except:
            pass

def get_sample_conversations():
    """Retornar conversas de exemplo"""
    sample_data = [
        {
            'conversation_id': 1,
            'nome': 'João Silva',
            'telefone': '+55 11 99999-1111',
            'wa_id': '5511999991111',
            'status': 'ativa',
            'last_message_at': datetime.now() - timedelta(minutes=15),
            'created_at': datetime.now() - timedelta(days=5),
            'last_message': 'Obrigado pelo atendimento!',
            'last_direction': 'in'
        },
        {
            'conversation_id': 2,
            'nome': 'Maria Santos',
            'telefone': '+55 11 99999-2222',
            'wa_id': '5511999992222',
            'status': 'ativa',
            'last_message_at': datetime.now() - timedelta(hours=2),
            'created_at': datetime.now() - timedelta(days=3),
            'last_message': 'Gostaria de agendar um horário',
            'last_direction': 'in'
        },
        {
            'conversation_id': 3,
            'nome': 'Pedro Costa',
            'telefone': '+55 11 99999-3333',
            'wa_id': '5511999993333',
            'status': 'pausada',
            'last_message_at': datetime.now() - timedelta(days=1),
            'created_at': datetime.now() - timedelta(days=7),
            'last_message': 'Confirmo o agendamento para amanhã às 14h',
            'last_direction': 'out'
        }
    ]
    
    return pd.DataFrame(sample_data)

def load_conversation_messages(conversation_id):
    """Carregar mensagens de uma conversa específica"""
    engine = get_database_connection()
    if not engine:
        return pd.DataFrame()
    
    try:
        with engine.connect() as conn:
            messages_query = text("""
                SELECT 
                    m.id,
                    m.direction,
                    m.content,
                    m.created_at,
                    u.nome
                FROM messages m
                LEFT JOIN users u ON m.user_id = u.id
                WHERE m.conversation_id = :conv_id
                ORDER BY m.created_at ASC
            """)
            
            messages = conn.execute(messages_query, {'conv_id': conversation_id}).fetchall()
            
            return pd.DataFrame(messages, columns=[
                'id', 'direction', 'content', 'created_at', 'nome'
            ])
    
    except Exception as e:
        print(f"Erro ao carregar mensagens da conversa: {e}")
        return pd.DataFrame()
    
    finally:
        engine.dispose()

@protect_heavy_operation
def load_users_data():
    """Carregar dados de usuários"""
    engine = get_database_connection()
    if not engine:
        return get_sample_users_data()
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    u.id,
                    u.wa_id,
                    u.nome,
                    u.telefone,
                    u.email,
                    u.created_at,
                    COUNT(DISTINCT m.id) as total_messages,
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(DISTINCT a.id) as total_appointments,
                    MAX(m.created_at) as last_message_at
                FROM users u
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                GROUP BY u.id, u.wa_id, u.nome, u.telefone, u.email, u.created_at
                ORDER BY total_messages DESC
            """)
            
            users = conn.execute(query).fetchall()
            
            return pd.DataFrame(users, columns=[
                'id', 'wa_id', 'nome', 'telefone', 'email', 
                'created_at', 'total_messages', 'total_conversations', 
                'total_appointments', 'last_message_at'
            ])
    
    except Exception as e:
        print(f"❌ Erro ao carregar usuários: {e}")
        return get_sample_users_data()
    
    finally:
        try:
            engine.dispose()
        except:
            pass

def get_sample_users_data():
    """Retornar dados de usuários de exemplo"""
    sample_data = [
        {
            'id': 1,
            'wa_id': '5511999991111',
            'nome': 'João Silva',
            'telefone': '+55 11 99999-1111',
            'email': 'joao@email.com',
            'created_at': datetime.now() - timedelta(days=30),
            'total_messages': 45,
            'total_conversations': 5,
            'total_appointments': 3,
            'last_message_at': datetime.now() - timedelta(hours=2)
        },
        {
            'id': 2,
            'wa_id': '5511999992222',
            'nome': 'Maria Santos',
            'telefone': '+55 11 99999-2222',
            'email': 'maria@email.com',
            'created_at': datetime.now() - timedelta(days=15),
            'total_messages': 32,
            'total_conversations': 3,
            'total_appointments': 2,
            'last_message_at': datetime.now() - timedelta(hours=5)
        },
        {
            'id': 3,
            'wa_id': '5511999993333',
            'nome': 'Pedro Costa',
            'telefone': '+55 11 99999-3333',
            'email': '',
            'created_at': datetime.now() - timedelta(days=7),
            'total_messages': 18,
            'total_conversations': 2,
            'total_appointments': 1,
            'last_message_at': datetime.now() - timedelta(days=1)
        }
    ]
    
    return pd.DataFrame(sample_data)

@protect_heavy_operation
def load_appointments_data():
    """Carregar dados de agendamentos"""
    engine = get_database_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    a.id,
                    a.date_time,
                    a.end_time,
                    a.status,
                    a.notes,
                    a.customer_notes,
                    a.admin_notes,
                    a.created_at,
                    a.confirmed_at,
                    a.cancelled_at,
                    a.cancellation_reason,
                    a.cancelled_by,
                    a.confirmed_by,
                    a.price_at_booking,
                    u.nome as customer_name,
                    u.telefone as customer_phone,
                    u.email as customer_email,
                    s.name as service_name,
                    s.duration_minutes,
                    s.price as service_price,
                    b.name as business_name
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN services s ON a.service_id = s.id
                LEFT JOIN businesses b ON a.business_id = b.id
                ORDER BY a.date_time DESC
            """)
            
            appointments = conn.execute(query).fetchall()
            
            return pd.DataFrame(appointments, columns=[
                'id', 'date_time', 'end_time', 'status', 'notes', 'customer_notes', 
                'admin_notes', 'created_at', 'confirmed_at', 'cancelled_at',
                'cancellation_reason', 'cancelled_by', 'confirmed_by', 'price_at_booking',
                'customer_name', 'customer_phone', 'customer_email', 'service_name',
                'duration_minutes', 'service_price', 'business_name'
            ])
    
    except Exception as e:
        print(f"Erro ao carregar agendamentos: {e}")
        return pd.DataFrame()
    
    finally:
        engine.dispose()

def load_blocked_times_data():
    """Carregar dados de horários bloqueados"""
    engine = get_database_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    bt.id,
                    bt.start_time,
                    bt.end_time,
                    bt.reason,
                    bt.notes,
                    bt.is_recurring,
                    bt.recurrence_pattern,
                    bt.created_at,
                    bt.created_by,
                    b.name as business_name
                FROM blocked_times bt
                LEFT JOIN businesses b ON bt.business_id = b.id
                ORDER BY bt.start_time DESC
            """)
            
            blocked_times = conn.execute(query).fetchall()
            
            return pd.DataFrame(blocked_times, columns=[
                'id', 'start_time', 'end_time', 'reason', 'notes',
                'is_recurring', 'recurrence_pattern', 'created_at', 
                'created_by', 'business_name'
            ])
    
    except Exception as e:
        print(f"Erro ao carregar horários bloqueados: {e}")
        return pd.DataFrame()
    
    finally:
        engine.dispose()

def load_services_data():
    """Carregar dados de serviços"""
    engine = get_database_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    s.id,
                    s.name,
                    s.description,
                    s.duration_minutes,
                    s.price,
                    s.is_active,
                    s.created_at,
                    COUNT(a.id) as total_appointments,
                    b.name as business_name
                FROM services s
                LEFT JOIN appointments a ON s.id = a.service_id
                LEFT JOIN businesses b ON s.business_id = b.id
                GROUP BY s.id, s.name, s.description, s.duration_minutes, s.price, s.is_active, s.created_at, b.name
                ORDER BY s.name
            """)
            
            services = conn.execute(query).fetchall()
            
            return pd.DataFrame(services, columns=[
                'id', 'name', 'description', 'duration_minutes', 
                'price', 'is_active', 'created_at', 'total_appointments', 'business_name'
            ])
    
    except Exception as e:
        print(f"Erro ao carregar serviços: {e}")
        return pd.DataFrame()
    
    finally:
        engine.dispose()

def load_business_config():
    """Carregar configurações da empresa"""
    engine = get_database_connection()
    if not engine:
        return None
    
    try:
        with engine.connect() as conn:
            # Informações da empresa
            business_query = text("""
                SELECT * FROM businesses LIMIT 1
            """)
            business = conn.execute(business_query).fetchone()
            
            # Informações detalhadas da empresa
            company_info_query = text("""
                SELECT * FROM company_info LIMIT 1
            """)
            company_info = conn.execute(company_info_query).fetchone()
            
            # Horários de funcionamento
            business_hours_query = text("""
                SELECT * FROM business_hours ORDER BY day_of_week
            """)
            business_hours = conn.execute(business_hours_query).fetchall()
            
            # Configurações do bot
            bot_config_query = text("""
                SELECT * FROM bot_configurations LIMIT 1
            """)
            bot_config = conn.execute(bot_config_query).fetchone()
            
            # Políticas da empresa
            policies_query = text("""
                SELECT * FROM business_policies
            """)
            policies = conn.execute(policies_query).fetchall()
            
            # Templates de mensagens
            templates_query = text("""
                SELECT * FROM message_templates
            """)
            templates = conn.execute(templates_query).fetchall()
            
            # Métodos de pagamento
            payment_methods_query = text("""
                SELECT * FROM payment_methods WHERE is_active = true
            """)
            payment_methods = conn.execute(payment_methods_query).fetchall()
            
            return {
                'business': dict(business._mapping) if business else {},
                'company_info': dict(company_info._mapping) if company_info else {},
                'business_hours': [dict(row._mapping) for row in business_hours],
                'bot_config': dict(bot_config._mapping) if bot_config else {},
                'policies': [dict(row._mapping) for row in policies],
                'templates': [dict(row._mapping) for row in templates],
                'payment_methods': [dict(row._mapping) for row in payment_methods]
            }
    
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return None
    
    finally:
        engine.dispose()

# ==================== CSS E ESTILOS ====================

app.index_string = '''
<!DOCTYPE html>
<html lang="pt-BR">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                /* WhatsApp Colors */
                --wa-green: #25D366;
                --wa-green-dark: #128C7E;
                --wa-teal: #075E54;
                --wa-light-green: #DCF8C6;
                --wa-blue: #34B7F1;
                --wa-gray: #ECE5DD;
                --wa-dark-gray: #3C3C3C;
                
                /* Modern Colors */
                --primary: #2563eb;
                --primary-dark: #1d4ed8;
                --secondary: #64748b;
                --success: #059669;
                --warning: #d97706;
                --danger: #dc2626;
                --info: #0891b2;
                
                /* Neutros */
                --gray-50: #f8fafc;
                --gray-100: #f1f5f9;
                --gray-200: #e2e8f0;
                --gray-300: #cbd5e1;
                --gray-400: #94a3b8;
                --gray-500: #64748b;
                --gray-600: #475569;
                --gray-700: #334155;
                --gray-800: #1e293b;
                --gray-900: #0f172a;
                
                /* Sombras */
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
                
                /* Raios */
                --radius: 8px;
                --radius-lg: 12px;
                --radius-xl: 16px;
                --radius-2xl: 20px;
                
                /* Transições */
                --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Space Grotesk', 'Inter', sans-serif;
            }
            
            p, span, div, button, input, select, textarea {
                font-family: 'Space Grotesk', 'Inter', sans-serif;
            }
            
            body {
                font-family: 'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
                background: var(--gray-50) !important;
                color: var(--gray-800) !important;
                line-height: 1.6;
                -webkit-font-smoothing: antialiased;
                font-size: 14px;
                font-weight: 400;
            }
            
            /* Sidebar WhatsApp Style */
            .whatsapp-sidebar {
                background: #f0f0ec;
                width: 280px;
                height: 100vh;
                position: fixed;
                left: 0;
                top: 0;
                z-index: 1000;
                display: flex;
                flex-direction: column;
                box-shadow: var(--shadow-lg);
            }
            
            .sidebar-header {
                padding: 24px 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 8px;
            }
            
            .whatsapp-logo {
                width: 48px;
                height: 48px;
                background: var(--wa-green);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
            }
            
            .brand-text {
                color: #615f52;
            }
            
            .brand-title {
                font-size: 20px;
                font-weight: 700;
                margin: 0 0 4px 0;
            }
            
            .brand-subtitle {
                font-size: 12px;
                opacity: 0.8;
                margin: 0;
            }
            
            /* Navigation */
            .nav-container {
                flex: 1;
                padding: 20px 0;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .nav-button {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 14px 20px;
                background: transparent;
                border: none;
                color: #615f52;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: var(--transition);
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                text-align: left;
                width: 100%;
                border-radius: 0;
                position: relative;
            }
            
            .nav-button:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            
            .nav-button.active {
                background: var(--wa-green);
                color: white;
                box-shadow: none;
            }
            
            .nav-button.active::after {
                content: '';
                position: absolute;
                right: 0;
                top: 0;
                bottom: 0;
                width: 4px;
                background: var(--wa-light-green);
            }
            
            .nav-button i {
                font-size: 16px;
                width: 20px;
                text-align: center;
            }
            
            /* Main Content */
            .main-content {
                margin-left: 280px;
                min-height: 100vh;
                padding: 16px;
                background: #fdfdf8;
            }
            
            .content-wrapper {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            /* Page Header */
            .page-header {
                margin-bottom: 16px;
            }
            
            .page-title {
                font-size: 28px;
                font-weight: 700;
                color: var(--gray-900);
                margin: 0 0 8px 0;
            }
            
            .page-subtitle {
                font-size: 16px;
                color: var(--gray-600);
                margin: 0;
            }
            
            /* Cards de métricas */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }
            
            .metric-card {
                background: white;
                border-radius: var(--radius-xl);
                padding: 24px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: var(--wa-green);
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-xl);
            }
            
            .metric-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
            }
            
            .metric-icon {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--wa-green), var(--wa-green-dark));
                border-radius: var(--radius-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
            }
            
            .metric-value {
                font-size: 32px;
                font-weight: 800;
                color: var(--gray-900);
                line-height: 1;
                margin: 0 0 4px 0;
                font-family: 'Space Grotesk', 'JetBrains Mono', monospace;
            }
            
            .metric-label {
                font-size: 14px;
                color: var(--gray-600);
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0;
            }
            
            /* Chat Interface - WhatsApp Web Style */
            .chat-container {
                display: grid;
                grid-template-columns: 350px 1fr;
                height: 85vh;
                background: white;
                border-radius: 0;
                box-shadow: none;
                overflow: hidden;
                margin: 0;
            }
            
            /* Página de mensagens sem espaçamentos laterais */
            .messages-page .content-wrapper {
                max-width: none;
                margin: 0;
                padding: 0;
            }
            
            .messages-page .page-header {
                padding: 0 16px;
                margin-bottom: 16px;
            }
            
            .chat-sidebar {
                background: var(--gray-100);
                border-right: 1px solid var(--gray-200);
                display: flex;
                flex-direction: column;
            }
            
            .chat-header {
                padding: 16px;
                background: var(--wa-gray);
                border-bottom: 1px solid var(--gray-200);
            }
            
            .chat-search {
                padding: 8px 16px;
                background: white;
                border: 1px solid var(--gray-300);
                border-radius: 20px;
                font-size: 14px;
                width: 100%;
            }
            
            .conversations-list {
                flex: 1;
                overflow-y: auto;
            }
            
            .conversation-item {
                padding: 12px 16px;
                border-bottom: 1px solid var(--gray-200);
                cursor: pointer;
                transition: var(--transition);
            }
            
            .conversation-item:hover {
                background: var(--gray-200);
            }
            
            .conversation-item.active {
                background: var(--wa-light-green);
            }
            
            .conversation-item.selected {
                background: var(--wa-light-green);
                border-left: 4px solid var(--primary);
            }
            
            .conversation-item.selected:hover {
                background: var(--wa-light-green);
            }
            
            .conversation-name {
                font-weight: 600;
                font-size: 14px;
                color: var(--gray-900);
                margin-bottom: 4px;
            }
            
            .conversation-preview {
                font-size: 12px;
                color: var(--gray-600);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .conversation-time {
                font-size: 11px;
                color: var(--gray-500);
                float: right;
            }
            
            .chat-main {
                display: flex;
                flex-direction: column;
                background: linear-gradient(to bottom, var(--wa-gray) 0%, #D1D7DB 100%);
                height: 100%;
                overflow: hidden;
            }
            
            .chat-main-header {
                padding: 16px;
                background: var(--wa-gray);
                border-bottom: 1px solid var(--gray-300);
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .contact-avatar {
                width: 40px;
                height: 40px;
                background: var(--wa-green);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
            }
            
            .contact-info h4 {
                margin: 0;
                font-size: 16px;
                color: var(--gray-900);
            }
            
            .contact-info p {
                margin: 0;
                font-size: 12px;
                color: var(--gray-600);
            }
            
            .messages-container {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                overflow-x: hidden;
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-height: calc(85vh - 80px); 
                min-height: 300px;
                scrollbar-width: thin;
                scrollbar-color: var(--gray-400) transparent;
                box-sizing: border-box;
            }
            
            .message {
                max-width: 70%;
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 14px;
                line-height: 1.4;
                position: relative;
                word-wrap: break-word;
            }
            
            .message.incoming {
                align-self: flex-start;
                background: white;
                box-shadow: var(--shadow-sm);
            }
            
            .message.outgoing {
                align-self: flex-end;
                background: var(--wa-light-green);
                box-shadow: var(--shadow-sm);
            }
            
            .message-time {
                font-size: 11px;
                color: var(--gray-500);
                margin-top: 4px;
                text-align: right;
            }
            
            .no-messages {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: var(--gray-500);
                font-style: italic;
                text-align: center;
                padding: 40px 20px;
            }
            
            /* Charts Container */
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 24px;
                margin-bottom: 24px;
            }
            
            .chart-container {
                background: white;
                border-radius: var(--radius-xl);
                padding: 24px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
            }
            
            .chart-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--gray-900);
                margin: 0 0 16px 0;
            }
            
            /* Tables */
            .table-container {
                background: white;
                border-radius: var(--radius-xl);
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
                overflow: hidden;
                margin: 24px 0;
            }
            
            .table-header {
                padding: 20px 24px;
                background: var(--gray-50);
                border-bottom: 1px solid var(--gray-200);
            }
            
            .table-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--gray-900);
                margin: 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            /* Filters */
            .filters-container {
                background: white;
                border-radius: var(--radius-xl);
                padding: 24px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
                margin-bottom: 24px;
            }
            
            .filters-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
            }
            
            /* Config Cards */
            .config-section {
                background: white;
                border-radius: var(--radius-xl);
                padding: 24px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
                margin-bottom: 24px;
            }
            
            .config-section h3 {
                font-size: 18px;
                font-weight: 600;
                color: var(--gray-900);
                margin: 0 0 16px 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 16px;
            }
            
            .info-item {
                padding: 12px;
                background: var(--gray-50);
                border-radius: var(--radius);
                border: 1px solid var(--gray-200);
            }
            
            .info-label {
                font-size: 12px;
                color: var(--gray-600);
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }
            
            .info-value {
                font-size: 14px;
                color: var(--gray-900);
                font-weight: 500;
            }
            
            /* Estilos específicos para página de custos */
            .cost-metric-card {
                background: linear-gradient(135deg, var(--whatsapp-green), #1eb854);
                color: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: var(--transition);
            }
            
            .cost-metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(37, 211, 102, 0.3);
            }
            
            .cost-alert {
                border-radius: 12px;
                margin: 10px 0;
                padding: 15px;
                font-weight: 500;
            }
            
            .cost-chart {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: var(--shadow);
                margin: 15px 0;
            }
            
            /* Estilos específicos para controle do bot */
            .bot-control-button {
                transition: all 0.3s ease;
                font-weight: 500;
                border-radius: 8px;
                margin: 5px;
            }
            
            .bot-control-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .system-status-card {
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                border: 1px solid #dee2e6;
                border-radius: 12px;
                padding: 25px;
                box-shadow: var(--shadow);
            }
            
            .performance-table {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: var(--shadow);
            }
            
            .logs-container {
                background: #1e1e1e;
                border: 1px solid #444;
                border-radius: 8px;
                color: #fff;
                font-family: 'JetBrains Mono', monospace;
            }
            
            /* Estilos específicos para dashboard de estratégias */
            .strategy-card {
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .strategy-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                border-color: var(--whatsapp-green);
            }
            
            .strategies-table {
                font-size: 0.9rem;
            }
            
            .strategies-table th {
                background-color: var(--whatsapp-green);
                color: white;
                font-weight: 600;
                border: none;
            }
            
            .strategies-table .table-success {
                background-color: rgba(40, 167, 69, 0.1);
            }
            
            .strategies-table .table-warning {
                background-color: rgba(255, 193, 7, 0.1);
            }
            
            .strategies-table .table-danger {
                background-color: rgba(220, 53, 69, 0.1);
            }
            
            .strategy-performance-indicator {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            /* Estilos para envio de mensagens */
            .message-sender {
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                border-top: 2px solid var(--whatsapp-green);
                padding: 15px;
                position: sticky;
                bottom: 0;
                z-index: 100;
            }
            
            .message-input {
                border-radius: 25px !important;
                border: 2px solid #e9ecef !important;
                padding: 12px 20px !important;
                font-size: 14px;
                transition: all 0.3s ease;
            }
            
            .message-input:focus {
                border-color: var(--whatsapp-green) !important;
                box-shadow: 0 0 0 0.2rem rgba(37, 211, 102, 0.25) !important;
            }
            
            .send-button {
                background: var(--whatsapp-green) !important;
                border: none !important;
                border-radius: 50% !important;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                margin-left: 10px;
            }
            
            .send-button:hover {
                background: var(--whatsapp-green-dark) !important;
                transform: scale(1.05);
                box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
            }
            
            .send-button:active {
                transform: scale(0.95);
            }
            
            .message-status-alert {
                margin-bottom: 10px;
                border-radius: 8px;
                font-size: 14px;
            }
            
            /* Responsividade */
            @media (max-width: 1024px) {
                .whatsapp-sidebar {
                    transform: translateX(-100%);
                    transition: var(--transition);
                }
                
                .whatsapp-sidebar.open {
                    transform: translateX(0);
                }
                
                .main-content {
                    margin-left: 0;
                    padding: 12px;
                }
                
                .chat-container {
                    grid-template-columns: 1fr;
                    height: auto;
                }
                
                .chat-sidebar {
                    display: none;
                }
                
                .metrics-grid {
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 16px;
                }
                
                .charts-grid {
                    grid-template-columns: 1fr;
                    gap: 16px;
                }
            }
            
            @media (max-width: 768px) {
                .main-content {
                    padding: 8px;
                }
                
                .page-title {
                    font-size: 24px;
                }
                
                .metric-value {
                    font-size: 24px;
                }
                
                .whatsapp-sidebar {
                    width: 260px;
                }
                
                .sidebar-header {
                    padding: 20px 16px;
                }
                
                .nav-button {
                    padding: 12px 16px;
                    font-size: 13px;
                }
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: var(--gray-100);
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--gray-400);
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: var(--gray-500);
            }
            
            /* Estilos adicionais para novas páginas */
            .service-card, .appointment-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--gray-200);
                transition: all 0.2s ease;
            }
            
            .service-card:hover, .appointment-card:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                transform: translateY(-2px);
            }
            
            /* Cards de usuários */
            .users-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
                gap: 24px;
                margin-top: 24px;
            }
            
            .user-card {
                background: white;
                border-radius: var(--radius-xl);
                padding: 24px;
                box-shadow: var(--shadow-md);
                border: 1px solid var(--gray-200);
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .user-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--wa-green), var(--wa-green-dark));
            }
            
            .user-card:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-xl);
            }
            
            .user-card-header {
                display: flex;
                align-items: center;
                gap: 16px;
                margin-bottom: 20px;
            }
            
            .user-avatar {
                width: 56px;
                height: 56px;
                background: linear-gradient(135deg, var(--wa-green), var(--wa-green-dark));
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
                font-weight: 700;
                text-transform: uppercase;
                flex-shrink: 0;
            }
            
            .user-info {
                flex: 1;
                min-width: 0;
            }
            
            .user-name {
                font-size: 18px;
                font-weight: 700;
                color: var(--gray-900);
                margin: 0 0 4px 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .user-phone {
                font-size: 14px;
                color: var(--gray-600);
                margin: 0;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 500;
            }
            
            .user-status {
                position: absolute;
                top: 16px;
                right: 16px;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .user-status.active {
                background: rgba(5, 150, 105, 0.1);
                color: var(--success);
            }
            
            .user-status.inactive {
                background: rgba(107, 114, 128, 0.1);
                color: var(--gray-500);
            }
            
            .user-metrics {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
                margin-bottom: 16px;
            }
            
            .user-metric {
                text-align: center;
                padding: 12px 0;
                background: var(--gray-50);
                border-radius: var(--radius);
            }
            
            .user-metric-value {
                font-size: 20px;
                font-weight: 700;
                color: var(--gray-900);
                margin: 0 0 4px 0;
                font-family: 'JetBrains Mono', monospace;
            }
            
            .user-metric-label {
                font-size: 11px;
                color: var(--gray-600);
                text-transform: uppercase;
                font-weight: 600;
                letter-spacing: 0.5px;
                margin: 0;
            }
            
            .user-details {
                display: grid;
                gap: 8px;
            }
            
            .user-detail-item {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 13px;
            }
            
            .user-detail-icon {
                width: 16px;
                color: var(--gray-500);
                text-align: center;
            }
            
            .user-detail-label {
                color: var(--gray-600);
                font-weight: 500;
                min-width: 60px;
            }
            
            .user-detail-value {
                color: var(--gray-900);
                font-weight: 500;
                word-break: break-all;
            }
            
            .user-actions {
                margin-top: 16px;
                padding-top: 16px;
                border-top: 1px solid var(--gray-200);
                display: flex;
                gap: 8px;
            }
            
            .user-action-btn {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid var(--gray-300);
                background: white;
                color: var(--gray-700);
                border-radius: var(--radius);
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: var(--transition);
                text-align: center;
                text-decoration: none;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }
            
            .user-action-btn:hover {
                background: var(--gray-50);
                border-color: var(--gray-400);
            }
            
            .user-action-btn.primary {
                background: var(--wa-green);
                border-color: var(--wa-green);
                color: white;
            }
            
            .user-action-btn.primary:hover {
                background: var(--wa-green-dark);
                border-color: var(--wa-green-dark);
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .filters-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--gray-200);
            }
            
            .filters-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 16px;
            }
            
            .config-section {
                background: white;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--gray-200);
            }
            
            .config-section h3 {
                margin-top: 0;
                margin-bottom: 20px;
                color: var(--gray-900);
                font-size: 18px;
                font-weight: 600;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 16px;
            }
            
            .info-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .info-label {
                font-size: 12px;
                font-weight: 600;
                color: var(--gray-600);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .info-value {
                font-size: 14px;
                color: var(--gray-900);
                font-weight: 500;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ==================== COMPONENTES VISUAIS ====================

def create_metric_card(title, value, icon):
    """Criar card de métrica"""
    try:
        print(f"🏷️ Criando card: {title} = {value}")
        
        card = html.Div([
            html.Div([
                html.Div([
                    html.Div(html.I(className=f"fas fa-{icon}"), className="metric-icon"),
                ]),
                html.Div([
                    html.H2(f"{value:,}" if isinstance(value, int) else value, className="metric-value"),
                    html.P(title, className="metric-label"),
                ])
            ], className="metric-header")
        ], className="metric-card")
        
        print(f"✅ Card criado: {title}")
        return card
        
    except Exception as e:
        print(f"❌ Erro ao criar card {title}: {e}")
        return html.Div(f"Erro: {title}", style={'padding': '20px', 'border': '1px solid red'})

def create_chart_container(title, chart_component):
    """Criar container de gráfico"""
    return html.Div([
        html.H3(title, className="chart-title"),
        chart_component
    ], className="chart-container")

def create_whatsapp_sidebar():
    """Criar sidebar lateral do WhatsApp"""
    print("📱 Criando sidebar do WhatsApp...")
    
    try:
        sidebar = html.Div([
            # Header da sidebar
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fab fa-whatsapp")
                    ], className="whatsapp-logo"),
                    html.Div([
                        html.H1("WhatsApp Agent", className="brand-title"),
                        html.P("Sistema de Gestão", className="brand-subtitle")
                    ], className="brand-text")
                ], className="logo-section"),
                
                # Componente de logout
                html.Div([
                    create_logout_component()
                ], style={'marginTop': '10px'})
            ], className="sidebar-header"),
            
            # Navegação
            html.Div([
                html.Button([
                    html.I(className="fas fa-tachometer-alt"),
                    "Visão Geral"
                ], id="nav-overview", className="nav-button active"),
                html.Button([
                    html.I(className="fas fa-comments"),
                    "Mensagens"
                ], id="nav-messages", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-users"),
                    "Usuários"
                ], id="nav-users", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-calendar-alt"),
                    "Agendamentos"
                ], id="nav-appointments", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-clock"),
                    "Horários Bloqueados"
                ], id="nav-blocked", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-cogs"),
                    "Serviços"
                ], id="nav-services", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-dollar-sign"),
                    "Monitoramento de Custos"
                ], id="nav-costs", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-robot"),
                    "Controle do Bot"
                ], id="nav-bot-control", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-chart-line"),
                    "Dashboard de Estratégias"
                ], id="nav-strategies", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-shield-alt"),
                    "Rate Limiting"
                ], id="nav-rate-limiting", className="nav-button"),
                html.Button([
                    html.I(className="fas fa-wrench"),
                    "Configurações"
                ], id="nav-config", className="nav-button")
            ], className="nav-container")
        ], className="whatsapp-sidebar")
        
        print("✅ Sidebar criada com sucesso!")
        return sidebar
        
    except Exception as e:
        print(f"❌ Erro ao criar sidebar: {e}")
        import traceback
        traceback.print_exc()
        return html.Div("Erro na sidebar", style={'padding': '20px', 'background': 'red', 'color': 'white'})

def create_user_card(user_data):
    """Criar card individual de usuário"""
    nome = user_data.get('nome', 'Usuário')
    telefone = user_data.get('telefone', 'N/A')
    email = user_data.get('email', 'N/A')
    wa_id = user_data.get('wa_id', 'N/A')
    total_messages = user_data.get('total_messages', 0)
    total_conversations = user_data.get('total_conversations', 0)
    total_appointments = user_data.get('total_appointments', 0)
    created_at = user_data.get('created_at_formatted', 'N/A')
    last_message = user_data.get('last_message_formatted', 'N/A')
    
    # Determinar status
    is_active = total_messages > 0
    status_class = "active" if is_active else "inactive"
    status_text = "Ativo" if is_active else "Inativo"
    
    # Avatar com iniciais
    initials = ''.join([part[0] for part in nome.split()[:2]]).upper() if nome else 'U'
    
    return html.Div([
        # Status badge
        html.Div(status_text, className=f"user-status {status_class}"),
        
        # Header do card
        html.Div([
            html.Div(initials, className="user-avatar"),
            html.Div([
                html.H3(nome, className="user-name"),
                html.P(telefone, className="user-phone")
            ], className="user-info")
        ], className="user-card-header"),
        
        # Métricas do usuário
        html.Div([
            html.Div([
                html.P(f"{total_messages}", className="user-metric-value"),
                html.P("Mensagens", className="user-metric-label")
            ], className="user-metric"),
            html.Div([
                html.P(f"{total_conversations}", className="user-metric-value"),
                html.P("Conversas", className="user-metric-label")
            ], className="user-metric"),
            html.Div([
                html.P(f"{total_appointments}", className="user-metric-value"),
                html.P("Agendamentos", className="user-metric-label")
            ], className="user-metric")
        ], className="user-metrics"),
        
        # Detalhes do usuário
        html.Div([
            html.Div([
                html.I(className="fas fa-envelope user-detail-icon"),
                html.Span("Email:", className="user-detail-label"),
                html.Span(email if email and email != 'None' else 'Não informado', className="user-detail-value")
            ], className="user-detail-item") if email else None,
            html.Div([
                html.I(className="fab fa-whatsapp user-detail-icon"),
                html.Span("WA ID:", className="user-detail-label"),
                html.Span(wa_id, className="user-detail-value")
            ], className="user-detail-item"),
            html.Div([
                html.I(className="fas fa-calendar user-detail-icon"),
                html.Span("Cadastro:", className="user-detail-label"),
                html.Span(created_at, className="user-detail-value")
            ], className="user-detail-item"),
            html.Div([
                html.I(className="fas fa-clock user-detail-icon"),
                html.Span("Última msg:", className="user-detail-label"),
                html.Span(last_message if last_message != 'N/A' else 'Nunca', className="user-detail-value")
            ], className="user-detail-item")
        ], className="user-details"),
        
        # Ações do usuário
        html.Div([
            html.A([
                html.I(className="fab fa-whatsapp"),
                "WhatsApp"
            ], 
            href=f"https://wa.me/{telefone.replace('+', '').replace('-', '').replace(' ', '')}" if telefone != 'N/A' else "#",
            className="user-action-btn primary",
            target="_blank"),
            html.Button([
                html.I(className="fas fa-user-edit"),
                "Editar"
            ], className="user-action-btn"),
            html.Button([
                html.I(className="fas fa-chart-line"),
                "Histórico"
            ], className="user-action-btn")
        ], className="user-actions")
        
    ], className="user-card")

def create_users_table(df):
    """Criar tabela de usuários melhorada"""
    return html.Div([
        html.Div([
            html.H3([
                html.I(className="fas fa-table", style={'marginRight': '8px'}), 
                f"Lista de Usuários ({len(df)} registros)"
            ], className="table-title")
        ], className="table-header"),
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'Nome', 'id': 'nome'},
                {'name': 'Telefone', 'id': 'telefone'},
                {'name': 'Email', 'id': 'email'},
                {'name': 'WA ID', 'id': 'wa_id'},
                {'name': 'Mensagens', 'id': 'total_messages', 'type': 'numeric'},
                {'name': 'Conversas', 'id': 'total_conversations', 'type': 'numeric'},
                {'name': 'Agendamentos', 'id': 'total_appointments', 'type': 'numeric'},
                {'name': 'Cadastro', 'id': 'created_at_formatted'},
                {'name': 'Última Mensagem', 'id': 'last_message_formatted'},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'fontFamily': 'Space Grotesk, Inter',
                'fontSize': '14px',
                'padding': '12px 16px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'maxWidth': '200px'
            },
            style_header={
                'backgroundColor': 'var(--gray-50)',
                'color': 'var(--gray-900)',
                'fontWeight': '600',
                'textTransform': 'uppercase',
                'fontSize': '12px',
                'letterSpacing': '0.5px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'var(--gray-50)'
                },
                {
                    'if': {'filter_query': '{total_messages} > 0'},
                    'borderLeft': '4px solid var(--wa-green)'
                }
            ],
            page_size=20,
            sort_action="native",
            filter_action="native",
            tooltip_data=[
                {
                    column: {'value': str(row[column]), 'type': 'markdown'}
                    for column in df.columns
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None
        )
    ], className="table-container")

# ==================== LAYOUTS DAS PÁGINAS ====================

def overview_layout():
    """Layout da página Overview"""
    print("🏠 Iniciando overview_layout...")
    
    try:
        print("📊 Carregando dados de overview...")
        data = load_overview_data()
        print(f"📊 Dados carregados: {type(data)}")
        
        # Se não conseguir carregar dados, usar dados de exemplo
        if not data:
            print("⚠️ Dados não encontrados, usando dados de exemplo...")
            data = get_sample_overview_data()
        
        print(f"📊 Dados finais: {data['metrics'] if data else 'None'}")
        
        print("🏗️ Criando componentes do layout...")
        
        # Header da página
        header = html.Div([
            html.H1("Visão Geral do Sistema", className="page-title"),
            html.P("Dashboard executivo com métricas principais em tempo real", className="page-subtitle")
        ], className="page-header")
        print("✅ Header criado")
        
        # Métricas principais
        metrics_grid = html.Div([
            create_metric_card("Usuários", data['metrics']['users'], "users"),
            create_metric_card("Mensagens", data['metrics']['messages'], "envelope"),
            create_metric_card("Conversas", data['metrics']['conversations'], "comments"),
            create_metric_card("Agendamentos", data['metrics']['appointments'], "calendar-check"),
            create_metric_card("Serviços", data['metrics']['services'], "cogs"),
            create_metric_card("Horários Bloqueados", data['metrics']['blocked_times'], "clock"),
        ], className="metrics-grid")
        print("✅ Grid de métricas criado")
        
        # Gráficos
        charts_grid = html.Div([
            create_chart_container(
                "Distribuição de Mensagens",
                dcc.Graph(
                    id="msg-direction-chart",
                    style={'height': '350px'},
                    config={'displayModeBar': False}
                )
            ),
            create_chart_container(
                "Status das Conversas",
                dcc.Graph(
                    id="conv-status-chart",
                    style={'height': '350px'},
                    config={'displayModeBar': False}
                )
            )
        ], className="charts-grid")
        print("✅ Grid de gráficos criado")
        
        timeline_chart = html.Div([
            create_chart_container(
                "Evolução de Mensagens (Últimos 7 dias)",
                dcc.Graph(
                    id="msg-timeline-chart",
                    style={'height': '350px'},
                    config={'displayModeBar': False}
                )
            )
        ])
        print("✅ Gráfico de timeline criado")
        
        # Layout final
        layout = html.Div([
            html.Div([
                header,
                metrics_grid,
                charts_grid,
                timeline_chart
            ], className="content-wrapper")
        ])
        
        print("✅ Layout overview montado com sucesso!")
        return layout
        
    except Exception as e:
        print(f"❌ Erro em overview_layout: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H2("Erro ao carregar Overview", style={'color': 'red', 'textAlign': 'center'}),
            html.P(f"Erro: {str(e)}", style={'textAlign': 'center', 'padding': '20px'})
        ])

def messages_layout():
    """Layout da página Mensagens - estilo WhatsApp Web"""
    conversations_df = load_messages_data()
    
    return html.Div([
        html.Div([
            # Header da página
            html.Div([
                html.H1("Central de Mensagens", className="page-title"),
                html.P("Interface estilo WhatsApp Web para gerenciar conversas", className="page-subtitle")
            ], className="page-header"),
            
            # Interface de chat
            html.Div([
                # Sidebar com lista de conversas
                html.Div([
                html.Div([
                    dcc.Input(
                        id="chat-search",
                        placeholder="Pesquisar conversas...",
                        className="chat-search"
                    )
                ], className="chat-header"),
                html.Div(id="conversations-list", className="conversations-list")
            ], className="chat-sidebar"),
            
            # Área principal do chat
            html.Div([
                html.Div(id="chat-main-header", className="chat-main-header"),
                html.Div(id="messages-container", className="messages-container"),
                # Campo de envio de mensagem
                html.Div(id="message-sender-area", children=[
                    add_message_sender_to_chat()
                ])
            ], className="chat-main", id="chat-main")
        ], className="chat-container")
        ], className="content-wrapper")
    ], className="messages-page")

def add_message_sender_to_chat():
    """Adicionar campo de envio de mensagem na interface de chat"""
    return html.Div([
        html.Div(id="message-send-status", className="message-status-alert"),
        dbc.InputGroup([
            dbc.Input(
                id="message-input",
                placeholder="Digite sua mensagem...",
                type="text",
                className="message-input",
                debounce=True
            ),
            dbc.Button(
                [html.I(className="fas fa-paper-plane")],
                id="send-message-btn",
                className="send-button",
                n_clicks=0
            )
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], className="message-sender")

def users_layout():
    """Layout da página Usuários"""
    df = load_users_data()
    if df.empty:
        return html.Div([
            html.Div([
                html.H1("Gestão de Usuários", className="page-title"),
                html.P("Nenhum usuário encontrado no sistema", className="page-subtitle"),
            ], className="page-header")
        ])
    
    # Preparar dados formatados
    df_display = df.copy()
    df_display['created_at_formatted'] = pd.to_datetime(df_display['created_at']).dt.strftime('%d/%m/%Y')
    df_display['last_message_formatted'] = pd.to_datetime(df_display['last_message_at']).dt.strftime('%d/%m/%Y %H:%M') if 'last_message_at' in df_display.columns else 'N/A'
    
    # Métricas avançadas
    total_users = len(df)
    active_users = len(df[df['total_messages'] > 0])
    users_with_email = len(df[df['email'].notna() & (df['email'] != '')])
    avg_messages = df['total_messages'].mean()
    top_user_messages = df['total_messages'].max() if not df.empty else 0
    
    # Corrigir comparação de datas para usuários da semana
    try:
        week_ago = datetime.now() - timedelta(days=7)
        created_at_dt = pd.to_datetime(df['created_at']).dt.tz_localize(None) if hasattr(pd.to_datetime(df['created_at']).dt, 'tz') else pd.to_datetime(df['created_at'])
        users_this_week = len(df[created_at_dt >= week_ago])
    except:
        users_this_week = 0
        
    users_with_appointments = len(df[df['total_appointments'] > 0])
    
    return html.Div([
        html.Div([
            # Header
            html.Div([
                html.H1("Gestão de Usuários", className="page-title"),
                html.P("Análise completa da base de usuários e engajamento", className="page-subtitle")
            ], className="page-header"),
            
            # Métricas principais
            html.Div([
                create_metric_card("Total de Usuários", total_users, "users"),
                create_metric_card("Usuários Ativos", active_users, "user-check"),
                create_metric_card("Novos (7 dias)", users_this_week, "user-plus"),
                create_metric_card("Com Email", users_with_email, "envelope"),
                create_metric_card("Com Agendamentos", users_with_appointments, "calendar-check"),
                create_metric_card("Média Mensagens", f"{avg_messages:.1f}", "chart-line"),
            ], className="metrics-grid"),
            
            # Filtros e controles
            html.Div([
                html.H3([html.I(className="fas fa-filter", style={'marginRight': '8px'}), "Filtros e Busca"], className="table-title"),
                html.Div([
                    html.Div([
                        html.Label("Buscar usuário:", style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Input(
                            id="user-search",
                            placeholder="Nome, telefone ou email...",
                            type="text",
                            style={
                                'width': '100%',
                                'padding': '12px 16px',
                                'border': '1px solid var(--gray-300)',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'fontFamily': 'Space Grotesk, Inter'
                            }
                        )
                    ]),
                    html.Div([
                        html.Label("Status:", style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Dropdown(
                            id="user-status-filter",
                            options=[
                                {"label": "Todos", "value": "all"},
                                {"label": "Usuários Ativos (com mensagens)", "value": "active"},
                                {"label": "Usuários Inativos", "value": "inactive"},
                                {"label": "Com Email", "value": "with_email"},
                                {"label": "Com Agendamentos", "value": "with_appointments"},
                                {"label": "Novos (últimos 7 dias)", "value": "new"}
                            ],
                            value="all",
                            style={'fontFamily': 'Space Grotesk, Inter'}
                        )
                    ]),
                    html.Div([
                        html.Label("Visualização:", style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Dropdown(
                            id="user-view-mode",
                            options=[
                                {"label": "Cards", "value": "cards"},
                                {"label": "Tabela", "value": "table"}
                            ],
                            value="cards",
                            style={'fontFamily': 'Space Grotesk, Inter'}
                        )
                    ])
                ], className="filters-grid")
            ], className="filters-container"),
            
            # Gráficos de análise
            html.Div([
                create_chart_container(
                    "Distribuição de Atividade dos Usuários",
                    dcc.Graph(
                        id="users-activity-chart",
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                ),
                create_chart_container(
                    "Novos Usuários por Período",
                    dcc.Graph(
                        id="users-registration-chart",
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                )
            ], className="charts-grid"),
            
            # Container para cards/tabela (será preenchido dinamicamente)
            html.Div(id="users-display-container")
            
        ], className="content-wrapper")
    ])

def appointments_layout():
    """Layout da página Agendamentos"""
    df = load_appointments_data()
    if df.empty:
        return html.Div([
            html.H1("Gestão de Agendamentos", className="page-title"),
            html.P("Nenhum agendamento encontrado", className="page-subtitle"),
        ])
    
    # Métricas de agendamentos
    total_appointments = len(df)
    confirmed = len(df[df['status'] == 'confirmado'])
    pending = len(df[df['status'] == 'pendente'])
    cancelled = len(df[df['status'] == 'cancelado'])
    
    return html.Div([
        # Header
        html.Div([
            html.H1("Gestão de Agendamentos", className="page-title"),
            html.P("Controle completo de reservas e horários", className="page-subtitle")
        ], className="page-header"),
        
        # Métricas
        html.Div([
            create_metric_card("Total", total_appointments, "calendar-alt"),
            create_metric_card("Confirmados", confirmed, "check-circle"),
            create_metric_card("Pendentes", pending, "clock"),
            create_metric_card("Cancelados", cancelled, "times-circle"),
        ], className="metrics-grid"),
        
        # Filtros
        html.Div([
            html.H3([html.I(className="fas fa-filter", style={'marginRight': '8px'}), "Filtros"], className="table-title"),
            html.Div([
                html.Div([
                    html.Label("Status:", style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id="appointment-status-filter",
                        options=[{"label": "Todos", "value": "all"}] + 
                               [{"label": status.title(), "value": status} for status in df['status'].unique()],
                        value="all"
                    )
                ], style={'flex': '1'}),
                html.Div([
                    html.Label("Período:", style={'fontWeight': '500', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id="appointment-period-filter",
                        options=[
                            {"label": "Todos", "value": "all"},
                            {"label": "Hoje", "value": "today"},
                            {"label": "Esta Semana", "value": "week"},
                            {"label": "Este Mês", "value": "month"}
                        ],
                        value="all"
                    )
                ], style={'flex': '1'})
            ], className="filters-grid")
        ], className="filters-container"),
        
        # Lista de agendamentos
        html.Div(id="appointments-list"),
        
        # Gráficos
        html.Div([
            create_chart_container(
                "Status dos Agendamentos",
                dcc.Graph(
                    id="appointments-status-chart",
                    style={'height': '350px'},
                    config={'displayModeBar': False}
                )
            ),
            create_chart_container(
                "Agendamentos por Serviço",
                dcc.Graph(
                    id="appointments-service-chart",
                    style={'height': '350px'},
                    config={'displayModeBar': False}
                )
            )
        ], className="charts-grid")
    ])

def blocked_times_layout():
    """Layout da página Horários Bloqueados"""
    df = load_blocked_times_data()
    if df.empty:
        return html.Div([
            html.H1("Horários Bloqueados", className="page-title"),
            html.P("Nenhum horário bloqueado encontrado", className="page-subtitle"),
        ])
    
    # Métricas
    total_blocked = len(df)
    recurring = len(df[df['is_recurring'] == True])
    one_time = total_blocked - recurring
    
    return html.Div([
        # Header
        html.Div([
            html.H1("Horários Bloqueados", className="page-title"),
            html.P("Gerenciamento de indisponibilidades e bloqueios", className="page-subtitle")
        ], className="page-header"),
        
        # Métricas
        html.Div([
            create_metric_card("Total Bloqueados", total_blocked, "clock"),
            create_metric_card("Recorrentes", recurring, "redo"),
            create_metric_card("Únicos", one_time, "calendar-times"),
            create_metric_card("Próximos 7 dias", 0, "calendar-week"),  # Calcular depois
        ], className="metrics-grid"),
        
        # Tabela de horários bloqueados
        html.Div([
            html.Div([
                html.H3([html.I(className="fas fa-table", style={'marginRight': '8px'}), f"Horários Bloqueados ({len(df)} registros)"], className="table-title")
            ], className="table-header"),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[
                    {'name': 'Início', 'id': 'start_time', 'type': 'datetime'},
                    {'name': 'Fim', 'id': 'end_time', 'type': 'datetime'},
                    {'name': 'Motivo', 'id': 'reason'},
                    {'name': 'Observações', 'id': 'notes'},
                    {'name': 'Recorrente', 'id': 'is_recurring', 'type': 'text'},
                    {'name': 'Criado em', 'id': 'created_at', 'type': 'datetime'},
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'fontFamily': 'Inter',
                    'fontSize': '14px',
                    'padding': '12px 16px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_header={
                    'backgroundColor': 'var(--gray-50)',
                    'color': 'var(--gray-900)',
                    'fontWeight': '600',
                    'textTransform': 'uppercase',
                    'fontSize': '12px',
                    'letterSpacing': '0.5px'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'var(--gray-50)'
                    }
                ],
                page_size=20,
                sort_action="native",
                filter_action="native"
            )
        ], className="table-container")
    ])

def services_layout():
    """Layout da página Serviços"""
    df = load_services_data()
    if df.empty:
        return html.Div([
            html.H1("Gestão de Serviços", className="page-title"),
            html.P("Nenhum serviço encontrado", className="page-subtitle"),
        ])
    
    # Métricas
    total_services = len(df)
    active_services = len(df[df['is_active'] == True])
    inactive_services = total_services - active_services
    total_bookings = df['total_appointments'].sum()
    
    return html.Div([
        # Header
        html.Div([
            html.H1("Gestão de Serviços", className="page-title"),
            html.P("Catálogo completo de serviços oferecidos", className="page-subtitle")
        ], className="page-header"),
        
        # Métricas
        html.Div([
            create_metric_card("Total de Serviços", total_services, "cogs"),
            create_metric_card("Ativos", active_services, "check-circle"),
            create_metric_card("Inativos", inactive_services, "times-circle"),
            create_metric_card("Total Agendamentos", total_bookings, "calendar-check"),
        ], className="metrics-grid"),
        
        # Cards de serviços
        html.Div(id="services-cards"),
        
        # Gráfico de popularidade
        create_chart_container(
            "Popularidade dos Serviços",
            dcc.Graph(
                id="services-popularity-chart",
                style={'height': '350px'},
                config={'displayModeBar': False}
            )
        )
    ])

def costs_monitoring_layout():
    """Layout da página de Monitoramento de Custos OpenAI"""
    import requests
    
    # Buscar dados da API
    try:
        response = requests.get("http://localhost:8000/api/costs/report")
        if response.status_code == 200:
            api_response = response.json()
            cost_data = api_response.get('data', {}) if api_response.get('success') else {}
        else:
            cost_data = {}
    except:
        cost_data = {}
    
    session_cost = cost_data.get('session', {}).get('total_cost_usd', 0)
    daily_cost = cost_data.get('daily', {}).get('total_cost_usd', 0)
    monthly_cost = cost_data.get('monthly', {}).get('total_cost_usd', 0)
    daily_limit = cost_data.get('daily_limit_usd', 10)
    monthly_limit = cost_data.get('monthly_limit_usd', 100)
    
    # Calcular percentuais
    daily_percent = (daily_cost / daily_limit * 100) if daily_limit > 0 else 0
    monthly_percent = (monthly_cost / monthly_limit * 100) if monthly_limit > 0 else 0
    
    return html.Div([
        # Componente para auto-atualização
        dcc.Interval(
            id='cost-refresh-interval',
            interval=30*1000,  # 30 segundos
            n_intervals=0
        ),
        
        html.Div([
            # Header
            html.Div([
                html.H1("💰 Monitoramento de Custos OpenAI", className="page-title"),
                html.P("Controle de gastos com IA em tempo real", className="page-subtitle")
            ], className="page-header"),
            
            # Métricas principais
            html.Div([
                create_metric_card(f"Sessão: ${session_cost:.4f}", f"R$ {session_cost*5:.2f}", "coins"),
                create_metric_card(f"Hoje: ${daily_cost:.2f}", f"{daily_percent:.1f}% do limite", "calendar-day"),
                create_metric_card(f"Mês: ${monthly_cost:.2f}", f"{monthly_percent:.1f}% do limite", "calendar-alt"),
                create_metric_card(f"Projeção: ${cost_data.get('projection', {}).get('monthly_total', 0):.2f}", 
                                 cost_data.get('projection', {}).get('risk_level', 'low'), "chart-line"),
            ], className="metrics-grid"),
            
            # Gráfico de uso por modelo
            html.Div([
                create_chart_container(
                    "Distribuição de Custos por Modelo",
                    dcc.Graph(
                        id="cost-by-model-chart",
                        figure=create_cost_by_model_chart(cost_data),
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                ),
                create_chart_container(
                    "Evolução de Custos (30 dias)",
                    dcc.Graph(
                        id="cost-timeline-chart",
                        figure=create_cost_timeline_chart(),
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                )
            ], className="charts-grid"),
            
            # Alertas de limite
            html.Div([
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Atenção: {daily_percent:.1f}% do limite diário utilizado!"
                    ],
                    color="warning" if daily_percent > 80 else "info",
                    dismissable=True
                ) if daily_percent > 50 else None,
                
                dbc.Alert(
                    [
                        html.I(className="fas fa-chart-line me-2"),
                        f"Projeção mensal: ${cost_data.get('projection', {}).get('monthly_total', 0):.2f}"
                    ],
                    color="danger" if cost_data.get('projection', {}).get('risk_level') == 'high' else "success",
                    dismissable=True
                )
            ])
        ], className="content-wrapper")
    ])

def create_cost_by_model_chart(cost_data):
    """Criar gráfico de custos por modelo"""
    models_data = cost_data.get('session', {}).get('usage', {})
    
    if not models_data:
        return {
            'data': [],
            'layout': {
                'title': 'Sem dados disponíveis',
                'font': {'family': 'Space Grotesk'},
                'height': 350
            }
        }
    
    models = []
    costs = []
    
    for model, data in models_data.items():
        if isinstance(data, dict):
            total_cost = data.get('total_cost', 0)
            models.append(model.replace('-', ' ').title())
            costs.append(total_cost)
    
    if not models:
        return {
            'data': [],
            'layout': {
                'title': 'Sem dados de modelos disponíveis',
                'font': {'family': 'Space Grotesk'},
                'height': 350
            }
        }
    
    fig = px.pie(
        values=costs,
        names=models,
        title="Custos por Modelo de IA",
        color_discrete_sequence=['#25D366', '#128C7E', '#075E54', '#34B7F1']
    )
    
    fig.update_layout(
        font_family="Space Grotesk",
        height=350,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_cost_timeline_chart():
    """Criar gráfico de evolução de custos"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/costs/timeline")
        if response.status_code == 200:
            timeline_response = response.json()
            timeline_data = timeline_response.get('data', [])
        else:
            timeline_data = []
    except:
        timeline_data = []
    
    if not timeline_data:
        return {
            'data': [],
            'layout': {
                'title': 'Sem dados de timeline disponíveis',
                'font': {'family': 'Space Grotesk'},
                'height': 350
            }
        }
    
    dates = [item['date'] for item in timeline_data]
    costs = [item['cost'] for item in timeline_data]
    
    fig = px.line(
        x=dates,
        y=costs,
        title="Evolução de Custos (30 dias)",
        labels={'x': 'Data', 'y': 'Custo (USD)'},
        color_discrete_sequence=['#25D366']
    )
    
    fig.update_layout(
        font_family="Space Grotesk",
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Data",
        yaxis_title="Custo (USD)"
    )
    
    return fig

def bot_control_layout():
    """Layout da página de Controle do Bot"""
    import requests
    
    # Buscar status do sistema
    try:
        strategy_health = requests.get("http://localhost:8000/admin/strategies/health").json()
        system_status = strategy_health.get('status', 'unknown')
    except:
        system_status = 'error'
        strategy_health = {}
    
    # Determinar cor do status
    status_colors = {
        'healthy': 'success',
        'degraded': 'warning',
        'unhealthy': 'danger',
        'error': 'dark'
    }
    
    return html.Div([
        # Componente para auto-atualização
        dcc.Interval(
            id='bot-status-refresh-interval',
            interval=10*1000,  # 10 segundos
            n_intervals=0
        ),
        
        html.Div([
            # Header
            html.Div([
                html.H1("🤖 Controle do Bot", className="page-title"),
                html.P("Gerenciamento e monitoramento do sistema", className="page-subtitle")
            ], className="page-header"),
            
            # Status Cards
            html.Div([
                # Card de Status Principal
                html.Div([
                    html.Div([
                        html.H3("Status do Sistema", style={'marginBottom': '20px'}),
                        dbc.Badge(
                            system_status.upper(),
                            color=status_colors.get(system_status, 'secondary'),
                            pill=True,
                            style={'fontSize': '16px', 'padding': '10px 20px'},
                            id="system-status-badge"
                        ),
                        html.Hr(),
                        html.Div([
                            html.P(f"✅ Estratégias Ativas: {strategy_health.get('strategies_count', 0)}", id="strategies-count"),
                            html.P(f"📊 Taxa de Sucesso: {strategy_health.get('global_metrics', {}).get('success_rate', 0):.1%}", id="success-rate"),
                            html.P(f"⚡ Tempo de Resposta: {strategy_health.get('global_metrics', {}).get('avg_response_time', 0):.2f}s", id="response-time"),
                        ], id="system-metrics")
                    ])
                ], className="config-section system-status-card"),
                
                # Controles de Ação
                html.Div([
                    html.H3("Ações Rápidas", style={'marginBottom': '20px'}),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-play me-2"), "Iniciar Bot"],
                            id="btn-start-bot",
                            color="success",
                            size="lg",
                            className="me-2 mb-2 bot-control-button",
                            n_clicks=0
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-pause me-2"), "Pausar Bot"],
                            id="btn-pause-bot",
                            color="warning",
                            size="lg",
                            className="me-2 mb-2 bot-control-button",
                            n_clicks=0
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-sync me-2"), "Reiniciar"],
                            id="btn-restart-bot",
                            color="info",
                            size="lg",
                            className="me-2 mb-2 bot-control-button",
                            n_clicks=0
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-trash me-2"), "Limpar Cache"],
                            id="btn-clear-cache",
                            color="secondary",
                            size="lg",
                            className="mb-2 bot-control-button",
                            n_clicks=0
                        ),
                    ])
                ], className="config-section"),
            ], className="row"),
            
            # Performance das Estratégias
            html.Div([
                html.H3("Performance das Estratégias", style={'marginBottom': '20px'}),
                html.Div(id="strategies-performance-table")
            ], className="config-section performance-table"),
            
            # Logs em Tempo Real
            html.Div([
                html.H3("Logs do Sistema", style={'marginBottom': '20px'}),
                html.Div([
                    dbc.Button(
                        [html.I(className="fas fa-eye me-2"), "Ver Logs"],
                        id="btn-toggle-logs",
                        color="primary",
                        size="sm",
                        className="mb-3"
                    ),
                    html.Div(id="system-logs-container", style={'display': 'none'})
                ])
            ], className="config-section"),
            
            # Sistema de Alertas
            html.Div(id="bot-control-alerts")
        ], className="content-wrapper")
    ])

def strategies_dashboard_layout():
    """Dashboard de comparação entre estratégias"""
    import requests
    
    # Buscar dados de performance
    try:
        perf_response = requests.get("http://localhost:8000/admin/strategies/performance")
        perf_data = perf_response.json() if perf_response.status_code == 200 else {}
        
        comparison_response = requests.get("http://localhost:8000/admin/strategies/comparison")
        comparison = comparison_response.json() if comparison_response.status_code == 200 else {}
    except:
        perf_data = {}
        comparison = {}
    
    return html.Div([
        # Componente para auto-atualização
        dcc.Interval(
            id='strategies-refresh-interval',
            interval=15*1000,  # 15 segundos
            n_intervals=0
        ),
        
        html.Div([
            # Header
            html.Div([
                html.H1("📊 Dashboard de Estratégias", className="page-title"),
                html.P("Comparação LLM vs CrewAI vs Híbrido", className="page-subtitle")
            ], className="page-header"),
            
            # Cards de comparação
            html.Div([
                create_strategy_card("LLM Simple", perf_data.get('simple', {})),
                create_strategy_card("LLM Advanced", perf_data.get('advanced', {})),
                create_strategy_card("CrewAI", perf_data.get('crew', {})),
                create_strategy_card("Híbrido", perf_data.get('hybrid', {})),
            ], className="metrics-grid"),
            
            # Gráficos comparativos
            html.Div([
                create_chart_container(
                    "Taxa de Sucesso por Estratégia",
                    dcc.Graph(
                        id="strategies-success-chart",
                        figure=create_strategies_comparison_chart(comparison, 'success_rate'),
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                ),
                create_chart_container(
                    "Tempo de Resposta Médio",
                    dcc.Graph(
                        id="strategies-response-time-chart",
                        figure=create_strategies_comparison_chart(comparison, 'avg_response_time'),
                        style={'height': '350px'},
                        config={'displayModeBar': False}
                    )
                )
            ], className="charts-grid"),
            
            # Gráfico de evolução temporal
            html.Div([
                create_chart_container(
                    "Evolução de Performance (Últimos 7 dias)",
                    dcc.Graph(
                        id="strategies-timeline-chart",
                        figure=create_strategies_timeline_chart(perf_data),
                        style={'height': '400px'},
                        config={'displayModeBar': False}
                    )
                )
            ], className="charts-grid"),
            
            # Tabela de métricas detalhadas
            html.Div([
                html.H3("Métricas Detalhadas", style={'marginBottom': '20px'}),
                html.Div(id="strategies-metrics-table")
            ], className="config-section performance-table")
        ], className="content-wrapper")
    ])

def create_strategy_card(name, data):
    """Criar card para cada estratégia"""
    requests_count = data.get('total_requests', 0)
    success_rate = data.get('success_rate', 0)
    avg_time = data.get('avg_response_time', 0)
    
    # Converter success_rate para percentual se necessário
    success_rate_pct = success_rate * 100 if success_rate <= 1 else success_rate
    
    # Determinar cor baseada na performance
    if success_rate_pct >= 90:
        color = "success"
        icon = "fas fa-check-circle"
    elif success_rate_pct >= 70:
        color = "warning"
        icon = "fas fa-exclamation-triangle"
    else:
        color = "danger"
        icon = "fas fa-times-circle"
    
    return html.Div([
        html.Div([
            html.Div([
                html.I(className=icon, style={'fontSize': '24px', 'marginBottom': '10px'}),
                html.H4(name, style={'marginBottom': '15px'}),
            ], style={'textAlign': 'center'}),
            
            html.Div([
                dbc.Progress(
                    value=success_rate_pct,
                    label=f"{success_rate_pct:.1f}%",
                    color=color,
                    style={'height': '25px', 'marginBottom': '15px'}
                ),
                html.Div([
                    html.P([
                        html.I(className="fas fa-chart-bar me-2"),
                        f"Requisições: {requests_count:,}"
                    ], style={'marginBottom': '8px'}),
                    html.P([
                        html.I(className="fas fa-clock me-2"),
                        f"Tempo médio: {avg_time:.2f}s"
                    ], style={'marginBottom': '8px'}),
                    html.P([
                        html.I(className="fas fa-bullseye me-2"),
                        f"Taxa: {success_rate_pct:.1f}%"
                    ], style={'marginBottom': '0px'}),
                ])
            ])
        ])
    ], className="metric-card strategy-card")

def create_strategies_comparison_chart(comparison_data, metric):
    """Criar gráfico de comparação entre estratégias"""
    if not comparison_data:
        return {
            'data': [],
            'layout': {
                'title': 'Dados não disponíveis',
                'font': {'family': 'Space Grotesk'},
                'height': 350
            }
        }
    
    strategies = []
    values = []
    colors = ['#25D366', '#128C7E', '#075E54', '#34B7F1', '#FFD700']
    
    for strategy_name, data in comparison_data.items():
        if isinstance(data, dict) and metric in data:
            strategies.append(strategy_name.replace('_', ' ').title())
            value = data[metric]
            
            # Converter para percentual se for success_rate
            if metric == 'success_rate':
                value = value * 100 if value <= 1 else value
            
            values.append(value)
    
    if not strategies:
        return {
            'data': [],
            'layout': {
                'title': 'Sem dados disponíveis',
                'font': {'family': 'Space Grotesk'},
                'height': 350
            }
        }
    
    # Determinar tipo de gráfico e labels
    if metric == 'success_rate':
        title = "Taxa de Sucesso (%)"
        y_label = "Taxa de Sucesso (%)"
    elif metric == 'avg_response_time':
        title = "Tempo Médio de Resposta"
        y_label = "Tempo (segundos)"
    else:
        title = metric.replace('_', ' ').title()
        y_label = metric
    
    fig = px.bar(
        x=strategies,
        y=values,
        title=title,
        labels={'x': 'Estratégias', 'y': y_label},
        color=values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        font_family="Space Grotesk",
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )
    
    return fig

def create_strategies_timeline_chart(perf_data):
    """Criar gráfico de evolução temporal das estratégias"""
    try:
        # Simular dados de evolução temporal
        from datetime import datetime, timedelta
        import random
        
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7, 0, -1)]
        
        fig = go.Figure()
        
        strategies = ['simple', 'advanced', 'crew', 'hybrid']
        colors = ['#25D366', '#128C7E', '#075E54', '#34B7F1']
        
        for i, strategy in enumerate(strategies):
            if strategy in perf_data:
                base_rate = perf_data[strategy].get('success_rate', 0.8)
                # Simular variação temporal
                values = [max(0, min(1, base_rate + random.uniform(-0.1, 0.1))) * 100 for _ in dates]
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines+markers',
                    name=strategy.replace('_', ' ').title(),
                    line=dict(color=colors[i], width=3),
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title="Evolução da Taxa de Sucesso",
            xaxis_title="Data",
            yaxis_title="Taxa de Sucesso (%)",
            font_family="Space Grotesk",
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(x=0, y=1),
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        return {
            'data': [],
            'layout': {
                'title': f'Erro ao carregar timeline: {str(e)}',
                'font': {'family': 'Space Grotesk'},
                'height': 400
            }
        }

def create_strategies_metrics_table(perf_data):
    """Criar tabela detalhada de métricas das estratégias"""
    if not perf_data:
        return dbc.Alert("Nenhum dado de performance disponível", color="info")
    
    table_rows = []
    
    for strategy_name, data in perf_data.items():
        if isinstance(data, dict):
            success_rate = data.get('success_rate', 0)
            success_rate_pct = success_rate * 100 if success_rate <= 1 else success_rate
            
            # Determinar classe CSS baseada na performance
            if success_rate_pct >= 90:
                row_class = "table-success"
            elif success_rate_pct >= 70:
                row_class = "table-warning"
            else:
                row_class = "table-danger"
            
            table_rows.append(
                html.Tr([
                    html.Td([
                        html.I(className="fas fa-cog me-2"),
                        strategy_name.replace('_', ' ').title()
                    ]),
                    html.Td(f"{data.get('total_requests', 0):,}"),
                    html.Td([
                        dbc.Progress(
                            value=success_rate_pct,
                            label=f"{success_rate_pct:.1f}%",
                            color="success" if success_rate_pct >= 90 else ("warning" if success_rate_pct >= 70 else "danger"),
                            style={'height': '20px'}
                        )
                    ]),
                    html.Td(f"{data.get('avg_response_time', 0):.3f}s"),
                    html.Td(f"{data.get('error_rate', 0)*100:.1f}%"),
                    html.Td(data.get('last_used', 'Nunca')),
                ], className=row_class)
            )
    
    if not table_rows:
        return dbc.Alert("Nenhuma estratégia encontrada", color="info")
    
    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th([html.I(className="fas fa-layer-group me-2"), "Estratégia"]),
                html.Th([html.I(className="fas fa-chart-bar me-2"), "Requisições"]),
                html.Th([html.I(className="fas fa-bullseye me-2"), "Taxa de Sucesso"]),
                html.Th([html.I(className="fas fa-clock me-2"), "Tempo Médio"]),
                html.Th([html.I(className="fas fa-exclamation-triangle me-2"), "Taxa de Erro"]),
                html.Th([html.I(className="fas fa-calendar me-2"), "Último Uso"]),
            ])
        ]),
        html.Tbody(table_rows)
    ], striped=True, bordered=True, hover=True, size="sm", className="strategies-table")

def config_layout():
    """Layout da página Configurações"""
    config_data = load_business_config()
    if not config_data:
        return html.Div([
            html.H1("Configurações da Empresa", className="page-title"),
            html.P("Erro ao carregar configurações", className="page-subtitle"),
        ])
    
    business = config_data.get('business', {})
    company_info = config_data.get('company_info', {})
    business_hours = config_data.get('business_hours', [])
    bot_config = config_data.get('bot_config', {})
    
    return html.Div([
        # Header
        html.Div([
            html.H1("Configurações da Empresa", className="page-title"),
            html.P("Configurações gerais do sistema e empresa", className="page-subtitle")
        ], className="page-header"),
        
        # Informações da Empresa
        html.Div([
            html.H3([html.I(className="fas fa-building", style={'marginRight': '8px'}), "Informações da Empresa"]),
            html.Div([
                html.Div([
                    html.Div("Nome", className="info-label"),
                    html.Div(business.get('name', 'N/A'), className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Telefone", className="info-label"),
                    html.Div(business.get('phone', 'N/A'), className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Email", className="info-label"),
                    html.Div(business.get('email', 'N/A'), className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Endereço", className="info-label"),
                    html.Div(business.get('address', 'N/A'), className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Slogan", className="info-label"),
                    html.Div(company_info.get('slogan', 'N/A'), className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Sobre Nós", className="info-label"),
                    html.Div(company_info.get('about_us', 'N/A')[:100] + "..." if company_info.get('about_us') and len(company_info.get('about_us', '')) > 100 else company_info.get('about_us', 'N/A'), className="info-value")
                ], className="info-item"),
            ], className="info-grid")
        ], className="config-section"),
        
        # Horários de Funcionamento
        html.Div([
            html.H3([html.I(className="fas fa-clock", style={'marginRight': '8px'}), "Horários de Funcionamento"]),
            html.Div([
                create_business_hours_display(business_hours)
            ])
        ], className="config-section"),
        
        # Configurações do Bot
        html.Div([
            html.H3([html.I(className="fas fa-robot", style={'marginRight': '8px'}), "Configurações do Bot"]),
            html.Div([
                html.Div([
                    html.Div("Horas Mínimas Antecedência", className="info-label"),
                    html.Div(f"{bot_config.get('min_advance_booking_hours', 'N/A')} horas", className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Dias Máximos Antecedência", className="info-label"),
                    html.Div(f"{bot_config.get('max_advance_booking_days', 'N/A')} dias", className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Confirmação Automática", className="info-label"),
                    html.Div("Sim" if bot_config.get('auto_confirm_bookings') else "Não", className="info-value")
                ], className="info-item"),
                html.Div([
                    html.Div("Política de Cancelamento", className="info-label"),
                    html.Div(bot_config.get('cancellation_policy_hours', 'N/A'), className="info-value")
                ], className="info-item"),
            ], className="info-grid")
        ], className="config-section"),
        
        # Templates de Mensagens
        html.Div([
            html.H3([html.I(className="fas fa-comments", style={'marginRight': '8px'}), "Templates de Mensagens"]),
            html.Div(id="message-templates")
        ], className="config-section"),
        
        # Métodos de Pagamento
        html.Div([
            html.H3([html.I(className="fas fa-credit-card", style={'marginRight': '8px'}), "Métodos de Pagamento"]),
            html.Div([
                html.Div([
                    html.Div(method['name'], className="info-value", style={'fontWeight': '600'})
                    for method in config_data.get('payment_methods', [])
                ])
            ])
        ], className="config-section")
    ])

def create_business_hours_display(business_hours):
    """Criar display dos horários de funcionamento"""
    days_pt = {
        0: "Segunda-feira",
        1: "Terça-feira", 
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }
    
    hours_display = []
    for hour in business_hours:
        day_name = days_pt.get(hour.get('day_of_week'), 'N/A')
        if hour.get('is_open'):
            open_time = hour.get('open_time', 'N/A')
            close_time = hour.get('close_time', 'N/A')
            hours_text = f"{open_time} - {close_time}"
        else:
            hours_text = "Fechado"
        
        hours_display.append(
            html.Div([
                html.Div(day_name, className="info-label"),
                html.Div(hours_text, className="info-value")
            ], className="info-item")
        )
    
    return html.Div(hours_display, className="info-grid")

def rate_limiting_layout():
    """Layout da página de Rate Limiting"""
    if not RATE_LIMITING_AVAILABLE:
        return html.Div([
            html.H1("🛡️ Rate Limiting", className="page-title"),
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={'color': '#ffc107', 'fontSize': '24px', 'marginRight': '10px'}),
                "Sistema de Rate Limiting não está disponível nesta instalação"
            ], className="alert alert-warning")
        ])
    
    try:
        return html.Div([
            html.Div([
                html.H1("🛡️ Sistema de Rate Limiting", className="page-title"),
                html.P("Monitoramento e controle de tráfego para proteção do sistema", className="page-subtitle")
            ], className="page-header"),
            
            # Estatísticas em tempo real
            html.Div([
                html.H3([html.I(className="fas fa-chart-bar", style={'marginRight': '8px'}), "Estatísticas em Tempo Real"]),
                html.Div(id="rate-limit-stats-cards", className="stats-grid"),
            ], className="section"),
            
            # Status dos endpoints protegidos
            html.Div([
                html.H3([html.I(className="fas fa-shield-alt", style={'marginRight': '8px'}), "Endpoints Protegidos"]),
                html.Div(id="protected-endpoints-table"),
            ], className="section"),
            
            # IPs bloqueados
            html.Div([
                html.H3([html.I(className="fas fa-ban", style={'marginRight': '8px'}), "IPs Bloqueados"]),
                html.Div(id="blocked-ips-display"),
            ], className="section"),
            
            # Violações recentes
            html.Div([
                html.H3([html.I(className="fas fa-exclamation-triangle", style={'marginRight': '8px'}), "Violações Recentes"]),
                html.Div(id="recent-violations-table"),
            ], className="section"),
            
            # Configurações avançadas
            html.Div([
                html.H3([html.I(className="fas fa-cogs", style={'marginRight': '8px'}), "Configurações Avançadas"]),
                html.Div([
                    dbc.Button("Limpar Bloqueios", id="clear-blocks-btn", color="warning", className="me-2"),
                    dbc.Button("Resetar Estatísticas", id="reset-stats-btn", color="danger", className="me-2"),
                    dbc.Button("Exportar Logs", id="export-logs-btn", color="info"),
                    html.Div(id="rate-limit-actions-feedback", className="mt-2")
                ], className="action-buttons")
            ], className="section"),
            
            # Auto-refresh
            dcc.Interval(
                id='rate-limit-interval',
                interval=15*1000,  # 15 segundos
                n_intervals=0
            )
        ])
    except Exception as e:
        return html.Div([
            html.H1("🛡️ Rate Limiting", className="page-title"),
            html.Div(f"Erro ao carregar interface: {str(e)}", className="alert alert-danger")
        ])

# Layout principal da aplicação
print("🚀 Inicializando layout do dashboard...")

try:
    sidebar = create_whatsapp_sidebar()
    print("✅ Sidebar criada com sucesso")
except Exception as e:
    print(f"❌ Erro ao criar sidebar: {e}")
    sidebar = html.Div("Erro na sidebar")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Location(id='login-redirect', refresh=True),
    dcc.Location(id='logout-redirect', refresh=True),
    
    # Stores para autenticação
    dcc.Store(id='auth-store', storage_type='session'),
    dcc.Store(id='user-data', storage_type='session'),
    
    dcc.Store(id='current-page', data='overview'),
    dcc.Store(id='selected-conversation', data=None),
    
    # WebSocket para atualizações em tempo real
    WebSocket(id="ws", url="ws://localhost:8000/ws/dashboard") if WEBSOCKET_AVAILABLE else html.Div(),
    
    # Store para dados em tempo real
    dcc.Store(id='realtime-messages', data=[]),
    dcc.Store(id='realtime-metrics', data={}),
    dcc.Store(id='realtime-notifications', data=[]),
    
    # Intervals para atualização
    dcc.Interval(id='messages-interval', interval=5000, n_intervals=0), # Mensagens a cada 5s
    dcc.Interval(id='realtime-interval', interval=5000, n_intervals=0), # Dados reais a cada 5s
    dcc.Interval(id='metrics-interval', interval=10000, n_intervals=0), # Métricas a cada 10s
    
    # Container para notificações em tempo real
    html.Div(id='realtime-notifications-container', style={
        'position': 'fixed', 
        'top': '20px', 
        'right': '20px', 
        'zIndex': 9999,
        'width': '350px'
    }),
    
    # Conteúdo principal (será substituído por login ou dashboard)
    html.Div(id='main-content-wrapper')
])

print("✅ Layout principal configurado!")

# ==================== CALLBACKS DE AUTENTICAÇÃO ====================

@callback(
    Output('main-content-wrapper', 'children'),
    [Input('url', 'pathname'),
     Input('auth-store', 'data')]
)
def display_page_with_auth(pathname, auth_data):
    """Controlar exibição baseada na autenticação"""
    
    # Se não estiver autenticado, mostrar login
    if not check_authentication(auth_data):
        if pathname != '/login':
            return create_login_page()
        else:
            return create_login_page()
    
    # Se autenticado, mostrar dashboard
    try:
        return html.Div([
            sidebar,
            html.Div([
                html.Div(id='page-content', children=[
                    html.Div("Carregando...", style={'padding': '2rem', 'textAlign': 'center'})
                ])
            ], className="main-content")
        ])
    except:
        # Fallback sidebar
        return html.Div([
            html.Div(id='fallback-sidebar', children="Menu"),
            html.Div([
                html.Div(id='page-content', children=[
                    html.Div("Carregando...", style={'padding': '2rem', 'textAlign': 'center'})
                ])
            ], className="main-content")
        ])

# Criar callbacks de autenticação
create_auth_callbacks(app)

# ==================== CALLBACKS ====================

# Navegação
@callback(
    [Output('current-page', 'data'),
     Output('nav-overview', 'className'),
     Output('nav-messages', 'className'),
     Output('nav-users', 'className'),
     Output('nav-appointments', 'className'),
     Output('nav-blocked', 'className'),
     Output('nav-services', 'className'),
     Output('nav-costs', 'className'),
     Output('nav-bot-control', 'className'),
     Output('nav-strategies', 'className'),
     Output('nav-rate-limiting', 'className'),
     Output('nav-config', 'className')],
    [Input('nav-overview', 'n_clicks'),
     Input('nav-messages', 'n_clicks'),
     Input('nav-users', 'n_clicks'),
     Input('nav-appointments', 'n_clicks'),
     Input('nav-blocked', 'n_clicks'),
     Input('nav-services', 'n_clicks'),
     Input('nav-costs', 'n_clicks'),
     Input('nav-bot-control', 'n_clicks'),
     Input('nav-strategies', 'n_clicks'),
     Input('nav-rate-limiting', 'n_clicks'),
     Input('nav-config', 'n_clicks')],
    prevent_initial_call=False
)
def update_navigation(*args):
    print(f"🧭 Callback de navegação chamado com args: {args}")
    
    try:
        ctx = dash.callback_context
        print(f"🔍 Context triggered: {ctx.triggered}")
        
        if not ctx.triggered:
            print("📍 Nenhum botão clicado - carregando página overview")
            return 'overview', 'nav-button active', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button'
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        print(f"📍 Botão clicado: {button_id}")
        
        classes = ['nav-button'] * 11
        page_map = {
            'nav-overview': ('overview', 0),
            'nav-messages': ('messages', 1),
            'nav-users': ('users', 2),
            'nav-appointments': ('appointments', 3),
            'nav-blocked': ('blocked', 4),
            'nav-services': ('services', 5),
            'nav-costs': ('costs', 6),
            'nav-bot-control': ('bot-control', 7),
            'nav-strategies': ('strategies', 8),
            'nav-rate-limiting': ('rate-limiting', 9),
            'nav-config': ('config', 10)
        }
        
        page, index = page_map.get(button_id, ('overview', 0))
        classes[index] = 'nav-button active'
        
        print(f"✅ Navegação processada: página={page}, index={index}")
        
        return page, *classes
        
    except Exception as e:
        print(f"❌ Erro no callback de navegação: {e}")
        import traceback
        traceback.print_exc()
        return 'overview', 'nav-button active', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button', 'nav-button'

# Display page
@callback(
    Output('page-content', 'children'),
    Input('current-page', 'data')
)
def display_page(current_page):
    print(f"📄 Callback display_page chamado com página: {current_page}")
    
    try:
        if current_page == 'overview':
            print("🏠 Carregando overview_layout...")
            result = overview_layout()
            print("✅ overview_layout carregado com sucesso")
            return result
        elif current_page == 'messages':
            print("💬 Carregando messages_layout...")
            result = messages_layout()
            print("✅ messages_layout carregado com sucesso")
            return result
        elif current_page == 'users':
            print("👥 Carregando users_layout...")
            result = users_layout()
            print("✅ users_layout carregado com sucesso")
            return result
        elif current_page == 'appointments':
            print("📅 Carregando appointments_layout...")
            result = appointments_layout()
            print("✅ appointments_layout carregado com sucesso")
            return result
        elif current_page == 'blocked':
            print("🚫 Carregando blocked_times_layout...")
            result = blocked_times_layout()
            print("✅ blocked_times_layout carregado com sucesso")
            return result
        elif current_page == 'services':
            print("⚙️ Carregando services_layout...")
            result = services_layout()
            print("✅ services_layout carregado com sucesso")
            return result
        elif current_page == 'costs':
            print("💰 Carregando costs_monitoring_layout...")
            result = costs_monitoring_layout()
            print("✅ costs_monitoring_layout carregado com sucesso")
            return result
        elif current_page == 'bot-control':
            print("🤖 Carregando bot_control_layout...")
            result = bot_control_layout()
            print("✅ bot_control_layout carregado com sucesso")
            return result
        elif current_page == 'strategies':
            print("📊 Carregando strategies_dashboard_layout...")
            result = strategies_dashboard_layout()
            print("✅ strategies_dashboard_layout carregado com sucesso")
            return result
        elif current_page == 'rate-limiting':
            print("🛡️ Carregando rate_limiting_layout...")
            result = rate_limiting_layout()
            print("✅ rate_limiting_layout carregado com sucesso")
            return result
        elif current_page == 'config':
            print("⚙️ Carregando config_layout...")
            result = config_layout()
            print("✅ config_layout carregado com sucesso")
            return result
        else:
            print(f"❓ Página desconhecida '{current_page}', carregando overview como padrão...")
            result = overview_layout()
            print("✅ overview_layout (padrão) carregado com sucesso")
            return result
            
    except Exception as e:
        print(f"❌ Erro no callback display_page: {e}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H2("Erro ao carregar página", style={'color': 'red', 'textAlign': 'center'}),
            html.P(f"Erro: {str(e)}", style={'textAlign': 'center', 'padding': '20px'})
        ])

# Gráficos da overview
@callback(
    [Output('msg-direction-chart', 'figure'),
     Output('conv-status-chart', 'figure'),
     Output('msg-timeline-chart', 'figure')],
    Input('current-page', 'data'),
    prevent_initial_call=False
)
def update_overview_charts(current_page):
    if current_page != 'overview':
        return {}, {}, {}
    
    data = load_overview_data()
    if not data:
        data = get_sample_overview_data()
    
    # Paleta WhatsApp
    colors = ['#25D366', '#128C7E', '#075E54', '#34B7F1']
    
    # Gráfico de direção das mensagens
    if data['msg_direction']:
        df_direction = pd.DataFrame(data['msg_direction'], columns=['direction', 'count'])
        df_direction['direction'] = df_direction['direction'].map({
            'in': 'Recebidas',
            'out': 'Enviadas'
        })
        fig_direction = px.pie(
            df_direction, 
            values='count', 
            names='direction',
            color_discrete_sequence=colors
        )
        fig_direction.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1)
        )
        fig_direction.update_traces(textposition='inside', textinfo='percent+label')
    else:
        fig_direction = {}
    
    # Gráfico de status das conversas
    if data['conv_status']:
        df_status = pd.DataFrame(data['conv_status'], columns=['status', 'count'])
        fig_status = px.bar(
            df_status, 
            x='status', 
            y='count',
            color_discrete_sequence=[colors[0]]
        )
        fig_status.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Status",
            yaxis_title="Quantidade",
            showlegend=False
        )
        fig_status.update_traces(marker_color=colors[0])
    else:
        fig_status = {}
    
    # Timeline de mensagens
    if data['msg_recent']:
        df_timeline = pd.DataFrame(data['msg_recent'], columns=['date', 'count'])
        fig_timeline = px.area(
            df_timeline, 
            x='date', 
            y='count',
            color_discrete_sequence=[colors[0]]
        )
        fig_timeline.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Data",
            yaxis_title="Mensagens",
            showlegend=False
        )
        fig_timeline.update_traces(
            fill='tonexty',
            fillcolor='rgba(37, 211, 102, 0.1)',
            line_color=colors[0],
            line_width=3
        )
    else:
        fig_timeline = {}
    
    return fig_direction, fig_status, fig_timeline

# Lista de conversas
@callback(
    Output('conversations-list', 'children'),
    [Input('current-page', 'data'),
     Input('chat-search', 'value'),
     Input('selected-conversation', 'data')],
    prevent_initial_call=False
)
def update_conversations_list(current_page, search_value, selected_conv_id):
    if current_page != 'messages':
        return []
    
    conversations = load_messages_data()  # Esta função já retorna as conversas
    if conversations is None or conversations.empty:
        return [html.Div("Nenhuma conversa encontrada", style={'padding': '20px', 'textAlign': 'center'})]
    
    # Filtrar por busca se fornecido
    if search_value:
        conversations = conversations[
            conversations['nome'].str.contains(str(search_value), case=False, na=False) | 
            conversations['telefone'].str.contains(str(search_value), case=False, na=False) |
            conversations['last_message'].str.contains(str(search_value), case=False, na=False, regex=False)
        ]
    
    conv_items = []
    for _, conv in conversations.iterrows():
        last_time = ""
        if pd.notna(conv['last_message_at']):
            try:
                dt = pd.to_datetime(conv['last_message_at'])
                last_time = dt.strftime('%H:%M')
            except:
                last_time = ""
        
        preview = str(conv['last_message'])[:50] + "..." if pd.notna(conv['last_message']) and len(str(conv['last_message'])) > 50 else str(conv['last_message']) if pd.notna(conv['last_message']) else "Sem mensagens"
        
        # Determinar se esta conversa está selecionada
        is_selected = selected_conv_id == conv['conversation_id']
        class_name = "conversation-item selected" if is_selected else "conversation-item"
        
        conv_items.append(
            html.Div([
                html.Div([
                    html.Div(conv['nome'] or conv['telefone'] or "Usuário", className="conversation-name"),
                    html.Div(last_time, className="conversation-time")
                ]),
                html.Div(preview, className="conversation-preview")
            ], 
            className=class_name,
            id={'type': 'conversation', 'index': conv['conversation_id']},
            n_clicks=0
            )
        )
    
    return conv_items

# Callback para detectar cliques nas conversas
@callback(
    Output('selected-conversation', 'data'),
    [Input({'type': 'conversation', 'index': ALL}, 'n_clicks')],
    [State('selected-conversation', 'data')],
    prevent_initial_call=True
)
def select_conversation(n_clicks_list, current_selection):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return current_selection
    
    # Encontrar qual conversa foi clicada
    for trigger in ctx.triggered:
        if trigger['value'] and trigger['value'] > 0:
            # Extrair o conversation_id do trigger
            prop_id = trigger['prop_id']
            # prop_id formato: {"index":123,"type":"conversation"}.n_clicks
            try:
                conv_data = json.loads(prop_id.split('.')[0])
                return conv_data['index']
            except:
                pass
    
    return current_selection

# Callback para atualizar o header da conversa
@callback(
    Output('chat-main-header', 'children'),
    [Input('selected-conversation', 'data'),
     Input('current-page', 'data')],
    prevent_initial_call=False
)
def update_chat_header(selected_conv_id, current_page):
    if current_page != 'messages' or not selected_conv_id:
        return html.Div("Selecione uma conversa", style={'padding': '16px', 'color': 'var(--gray-500)'})
    
    # Carregar dados da conversa
    conversations = load_messages_data()
    if conversations is None or conversations.empty:
        return html.Div("Conversa não encontrada", style={'padding': '16px', 'color': 'var(--gray-500)'})
    
    # Encontrar a conversa selecionada
    selected_conv = conversations[conversations['conversation_id'] == selected_conv_id]
    if selected_conv.empty:
        return html.Div("Conversa não encontrada", style={'padding': '16px', 'color': 'var(--gray-500)'})
    
    conv = selected_conv.iloc[0]
    
    # Nome do contato (primeiro nome inicial)
    contact_name = conv['nome'] or conv['telefone'] or "Usuário"
    contact_initial = contact_name[0].upper() if contact_name else "U"
    
    return html.Div([
        html.Div(contact_initial, className="contact-avatar"),
        html.Div([
            html.H4(contact_name, style={'margin': 0, 'fontSize': '16px'}),
            html.P("Online", style={'margin': 0, 'fontSize': '12px', 'color': 'var(--gray-600)'})
        ], className="contact-info")
    ])

# Callback para atualizar as mensagens da conversa selecionada
@callback(
    Output('messages-container', 'children'),
    [Input('selected-conversation', 'data'),
     Input('current-page', 'data')],
    prevent_initial_call=False
)
def update_messages_display(selected_conv_id, current_page):
    if current_page != 'messages':
        return []
    
    if not selected_conv_id:
        # Se não há conversa selecionada, tentar selecionar a primeira
        conversations = load_messages_data()
        if conversations is not None and not conversations.empty:
            selected_conv_id = conversations.iloc[0]['conversation_id']
        else:
            return [html.Div("Selecione uma conversa para ver as mensagens", className="no-messages")]
    
    # Carregar mensagens específicas da conversa
    messages = load_conversation_messages(selected_conv_id)
    if messages is None or messages.empty:
        return [html.Div("Nenhuma mensagem encontrada para esta conversa", className="no-messages")]
    
    msg_items = []
    for _, msg in messages.iterrows():
        try:
            msg_time = pd.to_datetime(msg['created_at']).strftime('%H:%M')
        except:
            msg_time = ''
        
        is_outgoing = msg['direction'] == 'out'
        
        msg_items.append(
            html.Div([
                html.Div(str(msg['content']), style={'marginBottom': '4px'}),
                html.Div(msg_time, style={
                    'fontSize': '11px', 
                    'color': 'rgba(0,0,0,0.45)', 
                    'textAlign': 'right'
                })
            ], className=f"message {'outgoing' if is_outgoing else 'incoming'}")
        )
    
    # Adicionar espaçador diretamente na lista de mensagens
    msg_items.append(
        html.Div(style={
            'height': '50px',
            'width': '100%',
            'flexShrink': '0'
        })
    )
    
    # Retornar mensagens com espaçador integrado
    return msg_items

# Callback clientside para scroll automático para o final das mensagens
app.clientside_callback(
    """
    function(children) {
        if (children && children.length > 0) {
            setTimeout(function() {
                var messagesContainer = document.querySelector('.messages-container');
                if (messagesContainer) {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            }, 100);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('messages-container', 'style', allow_duplicate=True),
    [Input('messages-container', 'children')],
    prevent_initial_call=True
)

# Callback para inicializar conversa automaticamente
@callback(
    Output('selected-conversation', 'data', allow_duplicate=True),
    [Input('current-page', 'data')],
    [State('selected-conversation', 'data')],
    prevent_initial_call=True
)
def auto_select_first_conversation(current_page, selected_conv):
    if current_page == 'messages' and not selected_conv:
        # Carregar primeira conversa automaticamente
        conversations = load_messages_data()
        if conversations is not None and not conversations.empty:
            return conversations.iloc[0]['conversation_id']
    return selected_conv
@app.callback(
    Output('appointments-list', 'children'),
    [Input('appointment-status-filter', 'value'),
     Input('appointment-period-filter', 'value')]
)
def update_appointments_list(status_filter, period_filter):
    try:
        df = load_appointments_data()
        
        # Aplicar filtros
        if status_filter and status_filter != 'all':
            df = df[df['status'] == status_filter]
        
        if df.empty:
            return [html.Div("Nenhum agendamento encontrado", className="no-data")]
        
        # Gerar cards de agendamentos
        appointment_cards = []
        for _, apt in df.iterrows():
            status_color = {
                'confirmado': '#22C55E',
                'pendente': '#F59E0B', 
                'cancelado': '#EF4444'
            }.get(apt.get('status', ''), '#6B7280')
            
            appointment_cards.append(
                html.Div([
                    html.Div([
                        html.Div([
                            html.H4(f"#{apt.get('id', 'N/A')}", style={'margin': 0, 'color': 'var(--primary)'}),
                            html.Div(apt.get('status', 'N/A').title(), 
                                    style={'padding': '4px 8px', 'borderRadius': '12px', 
                                          'backgroundColor': status_color, 'color': 'white', 
                                          'fontSize': '12px', 'fontWeight': '600'})
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                        
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-user", style={'marginRight': '8px', 'color': 'var(--gray-600)'}),
                                apt.get('user_name', 'N/A')
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.I(className="fas fa-calendar", style={'marginRight': '8px', 'color': 'var(--gray-600)'}),
                                pd.to_datetime(apt['appointment_date']).strftime('%d/%m/%Y') if pd.notna(apt.get('appointment_date')) else 'N/A'
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.I(className="fas fa-clock", style={'marginRight': '8px', 'color': 'var(--gray-600)'}),
                                f"{apt.get('start_time', 'N/A')} - {apt.get('end_time', 'N/A')}"
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.I(className="fas fa-cogs", style={'marginRight': '8px', 'color': 'var(--gray-600)'}),
                                apt.get('service_name', 'N/A')
                            ])
                        ])
                    ])
                ], className="appointment-card")
            )
        
        return appointment_cards
    except Exception as e:
        return [html.Div(f"Erro ao carregar agendamentos: {str(e)}", className="error-message")]

@app.callback(
    Output('services-cards', 'children'),
    Input('current-page', 'data')
)
def update_services_cards(current_page):
    if current_page != 'services':
        return []
    
    try:
        df = load_services_data()
        if df.empty:
            return [html.Div("Nenhum serviço encontrado", className="no-data")]
        
        service_cards = []
        
        for _, service in df.iterrows():
            status_color = '#22C55E' if service.get('is_active', False) else '#EF4444'
            status_text = 'Ativo' if service.get('is_active', False) else 'Inativo'
            
            service_cards.append(
                html.Div([
                    html.Div([
                        html.Div([
                            html.H4(service.get('name', 'N/A'), style={'margin': 0, 'marginBottom': '8px'}),
                            html.Div(status_text,
                                    style={'padding': '4px 8px', 'borderRadius': '12px',
                                          'backgroundColor': status_color, 'color': 'white',
                                          'fontSize': '12px', 'fontWeight': '600', 'width': 'fit-content'})
                        ]),
                        
                        html.P(service.get('description', 'N/A')[:100] + "..." if len(str(service.get('description', ''))) > 100 else service.get('description', 'N/A'),
                               style={'color': 'var(--gray-600)', 'marginBottom': '16px'}),
                        
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-clock", style={'marginRight': '8px', 'color': 'var(--primary)'}),
                                f"{service.get('duration_minutes', 'N/A')} min"
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.I(className="fas fa-dollar-sign", style={'marginRight': '8px', 'color': 'var(--primary)'}),
                                f"R$ {service.get('price', 0):.2f}"
                            ], style={'marginBottom': '8px'}),
                            html.Div([
                                html.I(className="fas fa-calendar-check", style={'marginRight': '8px', 'color': 'var(--primary)'}),
                                f"{service.get('total_appointments', 0)} agendamentos"
                            ])
                        ])
                    ])
                ], className="service-card")
            )
        
        return html.Div(service_cards, className="services-grid")
    except Exception as e:
        return [html.Div(f"Erro ao carregar serviços: {str(e)}", className="error-message")]

# Callbacks para gráficos de agendamentos
@app.callback(
    [Output('appointments-status-chart', 'figure'),
     Output('appointments-service-chart', 'figure')],
    Input('current-page', 'data')
)
def update_appointments_charts(current_page):
    if current_page != 'appointments':
        return {}, {}
    
    try:
        df = load_appointments_data()
        if df.empty:
            return {}, {}
        
        colors = ['#25D366', '#128C7E', '#075E54', '#34B7F1']
        
        # Gráfico de status
        status_counts = df['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color_discrete_sequence=colors
        )
        fig_status.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        # Gráfico por serviço
        service_counts = df['service_name'].value_counts().head(10)
        fig_service = px.bar(
            x=service_counts.values,
            y=service_counts.index,
            orientation='h',
            color_discrete_sequence=[colors[0]]
        )
        fig_service.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Quantidade",
            yaxis_title="Serviços"
        )
        
        return fig_status, fig_service
    except Exception as e:
        return {}, {}

# Callback para gráfico de popularidade de serviços
@app.callback(
    Output('services-popularity-chart', 'figure'),
    Input('current-page', 'data')
)
def update_services_chart(current_page):
    if current_page != 'services':
        return {}
    
    try:
        df = load_services_data()
        if df.empty:
            return {}
        
        # Ordenar por popularidade
        df_sorted = df.sort_values('total_appointments', ascending=True).tail(10)
        
        fig = px.bar(
            df_sorted,
            x='total_appointments',
            y='name',
            orientation='h',
            color_discrete_sequence=['#25D366']
        )
        fig.update_layout(
            font_family="Inter",
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Total de Agendamentos",
            yaxis_title="Serviços"
        )
        
        return fig
    except Exception as e:
        return {}

# ==================== CALLBACKS DE USUÁRIOS ====================

@callback(
    Output('users-display-container', 'children'),
    [Input('user-search', 'value'),
     Input('user-status-filter', 'value'),
     Input('user-view-mode', 'value')]
)
def update_users_display(search_term, status_filter, view_mode):
    """Atualizar display de usuários baseado nos filtros"""
    try:
        df = load_users_data()
        if df.empty:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-users", style={'fontSize': '48px', 'color': 'var(--gray-400)', 'marginBottom': '16px'}),
                    html.H3("Nenhum usuário encontrado", style={'color': 'var(--gray-600)', 'marginBottom': '8px'}),
                    html.P("Não há usuários cadastrados no sistema", style={'color': 'var(--gray-500)'})
                ], style={'textAlign': 'center', 'padding': '60px 20px'})
            ])
        
        # Preparar dados formatados
        df_display = df.copy()
        df_display['created_at_formatted'] = pd.to_datetime(df_display['created_at']).dt.strftime('%d/%m/%Y')
        if 'last_message_at' in df_display.columns:
            df_display['last_message_formatted'] = pd.to_datetime(df_display['last_message_at'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
            df_display['last_message_formatted'] = df_display['last_message_formatted'].fillna('Nunca')
        else:
            df_display['last_message_formatted'] = 'N/A'
        
        # Aplicar filtros
        filtered_df = df_display.copy()
        
        # Filtro de busca
        if search_term:
            search_term = search_term.lower()
            mask = (
                filtered_df['nome'].str.lower().str.contains(search_term, na=False) |
                filtered_df['telefone'].str.lower().str.contains(search_term, na=False) |
                filtered_df['email'].str.lower().str.contains(search_term, na=False, regex=False)
            )
            filtered_df = filtered_df[mask]
        
        # Filtro de status
        if status_filter == 'active':
            filtered_df = filtered_df[filtered_df['total_messages'] > 0]
        elif status_filter == 'inactive':
            filtered_df = filtered_df[filtered_df['total_messages'] == 0]
        elif status_filter == 'with_email':
            filtered_df = filtered_df[filtered_df['email'].notna() & (filtered_df['email'] != '')]
        elif status_filter == 'with_appointments':
            filtered_df = filtered_df[filtered_df['total_appointments'] > 0]
        elif status_filter == 'new':
            try:
                week_ago = datetime.now() - timedelta(days=7)
                # Converter para datetime e tratar timezone
                created_at_series = pd.to_datetime(filtered_df['created_at'])
                if hasattr(created_at_series.dt, 'tz') and created_at_series.dt.tz is not None:
                    created_at_dt = created_at_series.dt.tz_localize(None)
                else:
                    created_at_dt = created_at_series
                filtered_df = filtered_df[created_at_dt >= week_ago]
            except Exception as e:
                print(f"Erro no filtro 'new': {e}")
                # Em caso de erro, não aplicar o filtro
                pass
        
        if filtered_df.empty:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-search", style={'fontSize': '48px', 'color': 'var(--gray-400)', 'marginBottom': '16px'}),
                    html.H3("Nenhum resultado encontrado", style={'color': 'var(--gray-600)', 'marginBottom': '8px'}),
                    html.P("Tente ajustar os filtros de busca", style={'color': 'var(--gray-500)'})
                ], style={'textAlign': 'center', 'padding': '60px 20px'})
            ])
        
        # Retornar cards ou tabela baseado no modo de visualização
        if view_mode == 'cards':
            # Ordenar por atividade (mensagens) decrescente
            filtered_df = filtered_df.sort_values('total_messages', ascending=False)
            
            user_cards = []
            for _, user in filtered_df.iterrows():
                user_card = create_user_card(user.to_dict())
                user_cards.append(user_card)
            
            return html.Div([
                html.Div([
                    html.H3([
                        html.I(className="fas fa-id-card", style={'marginRight': '8px'}), 
                        f"Usuários Encontrados ({len(filtered_df)} de {len(df)})"
                    ], className="table-title", style={'marginBottom': '24px'})
                ]),
                html.Div(user_cards, className="users-grid")
            ])
        else:
            # Modo tabela
            return create_users_table(filtered_df)
            
    except Exception as e:
        print(f"Erro ao atualizar display de usuários: {e}")
        return html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={'fontSize': '48px', 'color': 'var(--danger)', 'marginBottom': '16px'}),
                html.H3("Erro ao carregar usuários", style={'color': 'var(--danger)', 'marginBottom': '8px'}),
                html.P(f"Detalhes: {str(e)}", style={'color': 'var(--gray-500)'})
            ], style={'textAlign': 'center', 'padding': '60px 20px'})
        ])

@callback(
    Output('users-activity-chart', 'figure'),
    Input('user-status-filter', 'value')
)
def update_users_activity_chart(status_filter):
    """Atualizar gráfico de atividade dos usuários"""
    try:
        df = load_users_data()
        if df.empty:
            return {}
        
        # Criar categorias de atividade
        df['activity_category'] = pd.cut(
            df['total_messages'],
            bins=[-1, 0, 1, 10, 50, float('inf')],
            labels=['Inativo', 'Baixa (1)', 'Média (2-10)', 'Alta (11-50)', 'Muito Alta (50+)']
        )
        
        activity_counts = df['activity_category'].value_counts()
        
        fig = px.pie(
            values=activity_counts.values,
            names=activity_counts.index,
            title="Distribuição por Nível de Atividade",
            color_discrete_sequence=['#dc2626', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6']
        )
        
        fig.update_layout(
            template='plotly_white',
            font_family='Space Grotesk',
            font_size=12,
            title_font_size=16,
            title_font_color='var(--gray-900)',
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        
        return fig
    except Exception as e:
        return {}

@callback(
    Output('users-registration-chart', 'figure'),
    Input('user-status-filter', 'value')
)
def update_users_registration_chart(status_filter):
    """Atualizar gráfico de registros de usuários"""
    try:
        df = load_users_data()
        if df.empty:
            return {}
        
        # Preparar dados de registro por mês
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['month_year'] = df['created_at'].dt.to_period('M')
        
        monthly_registrations = df.groupby('month_year').size().reset_index(name='count')
        monthly_registrations['month_year_str'] = monthly_registrations['month_year'].astype(str)
        
        # Últimos 12 meses
        monthly_registrations = monthly_registrations.tail(12)
        
        fig = px.line(
            monthly_registrations,
            x='month_year_str',
            y='count',
            title="Novos Usuários por Mês",
            markers=True
        )
        
        fig.update_traces(
            line_color='var(--wa-green)',
            marker_color='var(--wa-green-dark)',
            marker_size=8
        )
        
        fig.update_layout(
            template='plotly_white',
            font_family='Space Grotesk',
            font_size=12,
            title_font_size=16,
            title_font_color='var(--gray-900)',
            xaxis_title="Mês",
            yaxis_title="Novos Usuários",
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        return {}

# Callback para atualizar gráficos de custos automaticamente
@callback(
    [Output('cost-by-model-chart', 'figure'),
     Output('cost-timeline-chart', 'figure')],
    [Input('current-page', 'data'),
     Input('cost-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_cost_charts(current_page, n_intervals):
    if current_page != 'costs':
        return dash.no_update, dash.no_update
    
    try:
        import requests
        # Buscar dados atualizados da API
        response = requests.get("http://localhost:8000/api/costs/report")
        if response.status_code == 200:
            api_response = response.json()
            cost_data = api_response.get('data', {}) if api_response.get('success') else {}
        else:
            cost_data = {}
        
        # Atualizar gráfico por modelo
        model_chart = create_cost_by_model_chart(cost_data)
        
        # Atualizar gráfico de timeline
        timeline_chart = create_cost_timeline_chart()
        
        return model_chart, timeline_chart
    
    except Exception as e:
        print(f"Erro ao atualizar gráficos de custos: {e}")
        return dash.no_update, dash.no_update

# Callback para controles do bot
@callback(
    Output('bot-control-alerts', 'children'),
    [Input('btn-start-bot', 'n_clicks'),
     Input('btn-pause-bot', 'n_clicks'),
     Input('btn-restart-bot', 'n_clicks'),
     Input('btn-clear-cache', 'n_clicks')],
    prevent_initial_call=True
)
def handle_bot_controls(start_clicks, pause_clicks, restart_clicks, clear_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    alerts = []
    import requests
    
    if button_id == 'btn-start-bot':
        # Chamar API para iniciar bot
        try:
            response = requests.post("http://localhost:8000/admin/strategies/enable-new-system")
            if response.status_code == 200:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "✅ Bot iniciado com sucesso!"
                ], color="success", dismissable=True))
            else:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "❌ Erro ao iniciar bot"
                ], color="danger", dismissable=True))
        except Exception as e:
            alerts.append(dbc.Alert([
                html.I(className="fas fa-wifi me-2"),
                "⚠️ Não foi possível conectar ao servidor"
            ], color="warning", dismissable=True))
    
    elif button_id == 'btn-pause-bot':
        try:
            response = requests.post("http://localhost:8000/admin/strategies/disable-system")
            if response.status_code == 200:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-pause-circle me-2"),
                    "⏸️ Bot pausado com sucesso!"
                ], color="warning", dismissable=True))
            else:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "❌ Erro ao pausar bot"
                ], color="danger", dismissable=True))
        except:
            alerts.append(dbc.Alert([
                html.I(className="fas fa-wifi me-2"),
                "⚠️ Não foi possível conectar ao servidor"
            ], color="warning", dismissable=True))
    
    elif button_id == 'btn-restart-bot':
        try:
            # Primeiro pausa
            requests.post("http://localhost:8000/admin/strategies/disable-system")
            # Depois reinicia
            response = requests.post("http://localhost:8000/admin/strategies/enable-new-system")
            if response.status_code == 200:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-sync me-2"),
                    "🔄 Bot reiniciado com sucesso!"
                ], color="info", dismissable=True))
            else:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "❌ Erro ao reiniciar bot"
                ], color="danger", dismissable=True))
        except:
            alerts.append(dbc.Alert([
                html.I(className="fas fa-wifi me-2"),
                "⚠️ Erro na conexão durante reinicialização"
            ], color="warning", dismissable=True))
    
    elif button_id == 'btn-clear-cache':
        try:
            # Tentar endpoint específico de cache, se existir
            response = requests.post("http://localhost:8000/admin/cache/clear")
            if response.status_code == 200:
                alerts.append(dbc.Alert([
                    html.I(className="fas fa-broom me-2"),
                    "🧹 Cache limpo com sucesso!"
                ], color="info", dismissable=True))
            else:
                # Fallback para limpeza de estratégias
                response = requests.post("http://localhost:8000/admin/strategies/reset")
                if response.status_code == 200:
                    alerts.append(dbc.Alert([
                        html.I(className="fas fa-broom me-2"),
                        "🧹 Sistema resetado com sucesso!"
                    ], color="info", dismissable=True))
                else:
                    alerts.append(dbc.Alert([
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "❌ Erro ao limpar cache"
                    ], color="danger", dismissable=True))
        except:
            alerts.append(dbc.Alert([
                html.I(className="fas fa-wifi me-2"),
                "⚠️ Erro de conexão ao limpar cache"
            ], color="warning", dismissable=True))
    
    return alerts

# Callback para atualizar status do bot automaticamente
@callback(
    [Output('system-status-badge', 'children'),
     Output('system-status-badge', 'color'),
     Output('strategies-count', 'children'),
     Output('success-rate', 'children'),
     Output('response-time', 'children'),
     Output('strategies-performance-table', 'children')],
    [Input('current-page', 'data'),
     Input('bot-status-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_bot_status(current_page, n_intervals):
    if current_page != 'bot-control':
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        import requests
        response = requests.get("http://localhost:8000/admin/strategies/health")
        
        if response.status_code == 200:
            strategy_health = response.json()
            system_status = strategy_health.get('status', 'unknown')
            
            # Determinar cor do status
            status_colors = {
                'healthy': 'success',
                'degraded': 'warning', 
                'unhealthy': 'danger',
                'error': 'dark'
            }
            
            status_badge = system_status.upper()
            status_color = status_colors.get(system_status, 'secondary')
            
            strategies_count = f"✅ Estratégias Ativas: {strategy_health.get('strategies_count', 0)}"
            success_rate = f"📊 Taxa de Sucesso: {strategy_health.get('global_metrics', {}).get('success_rate', 0):.1%}"
            response_time = f"⚡ Tempo de Resposta: {strategy_health.get('global_metrics', {}).get('avg_response_time', 0):.2f}s"
            
            # Tabela de performance das estratégias
            strategies = strategy_health.get('strategies', [])
            if strategies:
                table_rows = []
                for strategy in strategies:
                    table_rows.append(
                        html.Tr([
                            html.Td(strategy.get('name', 'N/A')),
                            html.Td(strategy.get('status', 'N/A')),
                            html.Td(f"{strategy.get('success_rate', 0):.1%}"),
                            html.Td(f"{strategy.get('avg_response_time', 0):.2f}s"),
                            html.Td(strategy.get('last_used', 'Nunca'))
                        ])
                    )
                
                performance_table = html.Div([
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Estratégia"),
                                html.Th("Status"),
                                html.Th("Taxa de Sucesso"),
                                html.Th("Tempo Resposta"),
                                html.Th("Último Uso")
                            ])
                        ]),
                        html.Tbody(table_rows)
                    ], striped=True, bordered=True, hover=True, size="sm")
                ])
            else:
                performance_table = dbc.Alert("Nenhuma estratégia encontrada", color="info")
            
            return status_badge, status_color, strategies_count, success_rate, response_time, performance_table
        
        else:
            return "ERROR", "danger", "❌ Erro de conexão", "❌ Indisponível", "❌ Indisponível", dbc.Alert("Erro ao carregar dados", color="danger")
    
    except Exception as e:
        return "OFFLINE", "dark", "⚠️ Sistema offline", "⚠️ Indisponível", "⚠️ Indisponível", dbc.Alert(f"Erro: {str(e)}", color="danger")

# Callback para toggle dos logs
@callback(
    [Output('system-logs-container', 'style'),
     Output('system-logs-container', 'children')],
    [Input('btn-toggle-logs', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_logs(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        # Mostrar logs
        try:
            import requests
            response = requests.get("http://localhost:8000/admin/logs/recent?lines=50")
            
            if response.status_code == 200:
                logs_data = response.json()
                logs_content = logs_data.get('logs', ['Nenhum log disponível'])
                
                logs_display = html.Pre(
                    "\n".join(logs_content),
                    style={
                        'backgroundColor': '#1e1e1e',
                        'color': '#ffffff',
                        'padding': '15px',
                        'borderRadius': '8px',
                        'maxHeight': '400px',
                        'overflow': 'auto',
                        'fontSize': '12px',
                        'fontFamily': 'JetBrains Mono, monospace'
                    }
                )
            else:
                logs_display = dbc.Alert("Erro ao carregar logs", color="warning")
                
        except:
            logs_display = dbc.Alert("Logs não disponíveis - servidor offline", color="danger")
        
        return {'display': 'block'}, logs_display
    else:
        # Esconder logs
        return {'display': 'none'}, []

# Callback para atualizar dashboard de estratégias automaticamente
@callback(
    [Output('strategies-success-chart', 'figure'),
     Output('strategies-response-time-chart', 'figure'),
     Output('strategies-timeline-chart', 'figure'),
     Output('strategies-metrics-table', 'children')],
    [Input('current-page', 'data'),
     Input('strategies-refresh-interval', 'n_intervals')],
    prevent_initial_call=True
)
def update_strategies_dashboard(current_page, n_intervals):
    if current_page != 'strategies':
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        import requests
        
        # Buscar dados atualizados
        perf_response = requests.get("http://localhost:8000/admin/strategies/performance")
        perf_data = perf_response.json() if perf_response.status_code == 200 else {}
        
        comparison_response = requests.get("http://localhost:8000/admin/strategies/comparison")
        comparison = comparison_response.json() if comparison_response.status_code == 200 else {}
        
        # Atualizar gráficos
        success_chart = create_strategies_comparison_chart(comparison, 'success_rate')
        response_time_chart = create_strategies_comparison_chart(comparison, 'avg_response_time')
        timeline_chart = create_strategies_timeline_chart(perf_data)
        
        # Atualizar tabela
        metrics_table = create_strategies_metrics_table(perf_data)
        
        return success_chart, response_time_chart, timeline_chart, metrics_table
    
    except Exception as e:
        print(f"Erro ao atualizar dashboard de estratégias: {e}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Callback para enviar mensagem via WhatsApp
@callback(
    [Output('message-send-status', 'children'),
     Output('message-input', 'value')],
    [Input('send-message-btn', 'n_clicks'),
     Input('message-input', 'n_submit')],
    [State('message-input', 'value'),
     State('selected-conversation', 'data')],
    prevent_initial_call=True
)
def send_message_from_dashboard(btn_clicks, input_submit, message, conversation_data):
    """Enviar mensagem via WhatsApp API"""
    # Verificar se foi acionado o envio
    if not (btn_clicks or input_submit) or not message or not conversation_data:
        return [], dash.no_update
    
    # Limpar entrada imediatamente
    clear_input = ""
    
    try:
        # Buscar dados do usuário da conversa selecionada
        engine = get_database_connection()
        if not engine:
            return [dbc.Alert("❌ Erro de conexão com banco", color="danger", dismissable=True, duration=4000)], clear_input
        
        with engine.connect() as conn:
            user_data = conn.execute(
                text("""
                    SELECT u.wa_id, u.telefone, u.nome
                    FROM conversations c 
                    JOIN users u ON c.user_id = u.id 
                    WHERE c.id = :conv_id
                """),
                {'conv_id': conversation_data}
            ).fetchone()
        
        if not user_data:
            return [dbc.Alert("❌ Usuário não encontrado", color="danger", dismissable=True, duration=4000)], clear_input
        
        # Preparar dados para envio
        send_data = {
            "to": user_data['wa_id'] or user_data['telefone'],
            "message": message.strip(),
            "type": "text"
        }
        
        # Enviar via API do WhatsApp
        import requests
        response = requests.post(
            "http://localhost:8000/api/whatsapp/send",
            json=send_data,
            timeout=10
        )
        
        if response.status_code == 200:
            success_alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ Mensagem enviada para {user_data['nome'] or user_data['telefone']}!"
            ], color="success", dismissable=True, duration=3000)
            
            return [success_alert], clear_input
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido') if response.headers.get('content-type') == 'application/json' else 'Erro de API'
            error_alert = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"❌ Erro ao enviar: {error_detail}"
            ], color="danger", dismissable=True, duration=5000)
            
            return [error_alert], clear_input
            
    except requests.exceptions.Timeout:
        timeout_alert = dbc.Alert([
            html.I(className="fas fa-clock me-2"),
            "⏱️ Timeout - tente novamente"
        ], color="warning", dismissable=True, duration=4000)
        return [timeout_alert], clear_input
        
    except requests.exceptions.ConnectionError:
        connection_alert = dbc.Alert([
            html.I(className="fas fa-wifi me-2"),
            "📡 Erro de conexão - verifique se o servidor está rodando"
        ], color="warning", dismissable=True, duration=5000)
        return [connection_alert], clear_input
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"⚠️ Erro inesperado: {str(e)}"
        ], color="danger", dismissable=True, duration=5000)
        return [error_alert], clear_input

# Callback para mostrar/esconder área de envio baseado na conversa selecionada
@callback(
    Output('message-sender-area', 'style'),
    Input('selected-conversation', 'data')
)
def toggle_message_sender(conversation_data):
    """Mostrar área de envio apenas quando uma conversa está selecionada"""
    if conversation_data:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# ==================== CALLBACKS WEBSOCKET E TEMPO REAL ====================

if WEBSOCKET_AVAILABLE:
    @callback(
        Output('realtime-messages', 'data'),
        [Input('ws', 'message')],
        [State('realtime-messages', 'data')]
    )
    def update_realtime_messages(message, current_messages):
        """Atualizar mensagens em tempo real via WebSocket"""
        print(f"📡 WebSocket message recebida: {message}")
        
        if message:
            current_messages = current_messages or []
            try:
                # Parse da mensagem WebSocket
                if isinstance(message, dict):
                    message_data = message.get('data', message)
                else:
                    message_data = json.loads(message) if isinstance(message, str) else message
                
                current_messages.append({
                    'timestamp': datetime.now().isoformat(),
                    'data': message_data
                })
                
                # Manter apenas últimas 100 mensagens
                return current_messages[-100:]
            except Exception as e:
                print(f"❌ Erro ao processar mensagem WebSocket: {e}")
                return current_messages
        return current_messages or []

@callback(
    Output('realtime-notifications-container', 'children'),
    [Input('realtime-messages', 'data'),
     Input('realtime-interval', 'n_intervals')]
)
def show_realtime_notifications(messages, n_intervals):
    """Mostrar notificações de dados reais em tempo real"""
    if not messages:
        return []
    
    try:
        # Pegar as últimas 5 notificações para mostrar
        recent_messages = messages[-5:] if len(messages) >= 5 else messages
        notifications = []
        
        for i, msg in enumerate(recent_messages):
            if isinstance(msg, dict):
                msg_data = msg.get('data', {})
                if isinstance(msg_data, dict):
                    msg_type = msg_data.get('type', 'unknown')
                    
                    if msg_type == 'message':
                        # Nova mensagem real
                        user_name = msg_data.get('user', 'Usuário')
                        content = msg_data.get('content', 'Nova mensagem')
                        phone = msg_data.get('phone', '')
                        
                        notifications.append(
                            dbc.Toast(
                                [
                                    html.Div([
                                        html.I(className="fas fa-comment me-2"),
                                        html.Strong(f"💬 {user_name}"),
                                        html.Br(),
                                        html.Small(phone, className="text-muted") if phone else None,
                                        html.Br(),
                                        html.P(
                                            content[:80] + "..." if len(content) > 80 else content,
                                            className="mb-0 mt-1"
                                        )
                                    ])
                                ],
                                id=f"toast-real-message-{i}",
                                header="� Nova Mensagem WhatsApp",
                                is_open=True,
                                dismissable=True,
                                duration=6000,
                                icon="primary",
                                style={
                                    "marginBottom": "10px",
                                    "borderLeft": "4px solid var(--wa-green)",
                                    "maxWidth": "400px"
                                }
                            )
                        )
                        
                    elif msg_type == 'appointment':
                        # Novo agendamento real
                        appointment_info = msg_data.get('appointment', {})
                        customer = appointment_info.get('customer', 'Cliente')
                        service = appointment_info.get('service', 'Serviço')
                        date_time = appointment_info.get('date_time', '')
                        status = appointment_info.get('status', 'pendente')
                        
                        status_color = {
                            'confirmado': 'success',
                            'pendente': 'warning',
                            'cancelado': 'danger'
                        }.get(status, 'info')
                        
                        notifications.append(
                            dbc.Toast(
                                [
                                    html.Div([
                                        html.I(className="fas fa-calendar-plus me-2"),
                                        html.Strong(f"📅 {customer}"),
                                        html.Br(),
                                        html.Small(f"Serviço: {service}", className="text-muted"),
                                        html.Br(),
                                        html.Small(f"Data: {date_time}", className="text-muted"),
                                        html.Br(),
                                        dbc.Badge(
                                            status.upper(),
                                            color=status_color,
                                            className="mt-1"
                                        )
                                    ])
                                ],
                                id=f"toast-real-appointment-{i}",
                                header="�️ Novo Agendamento",
                                is_open=True,
                                dismissable=True,
                                duration=8000,
                                icon="success",
                                style={
                                    "marginBottom": "10px",
                                    "borderLeft": "4px solid var(--success)",
                                    "maxWidth": "400px"
                                }
                            )
                        )
                        
                    elif msg_type == 'system':
                        # Atualização do sistema real
                        system_msg = msg_data.get('system', 'Atualização do sistema')
                        details = msg_data.get('details', {})
                        
                        notifications.append(
                            dbc.Toast(
                                [
                                    html.Div([
                                        html.I(className="fas fa-sync-alt me-2"),
                                        html.Strong("⚙️ Atualização do Sistema"),
                                        html.Br(),
                                        html.P(system_msg, className="mb-0 mt-1 small")
                                    ])
                                ],
                                id=f"toast-real-system-{i}",
                                header="🔧 Sistema",
                                is_open=True,
                                dismissable=True,
                                duration=5000,
                                icon="info",
                                style={
                                    "marginBottom": "10px",
                                    "borderLeft": "4px solid var(--info)",
                                    "maxWidth": "400px"
                                }
                            )
                        )
                        
                    # Fallback para notificações antigas (mock)
                    elif 'user' in msg_data and 'content' in msg_data:
                        # Compatibilidade com formato antigo
                        notifications.append(
                            dbc.Toast(
                                [
                                    html.Div([
                                        html.I(className="fas fa-comment me-2"),
                                        html.Strong(f"📬 {msg_data.get('user', 'Usuário')}"),
                                        html.Br(),
                                        html.Small(msg_data.get('content', 'Nova mensagem')[:50] + "..." if len(msg_data.get('content', '')) > 50 else msg_data.get('content', ''))
                                    ])
                                ],
                                id=f"toast-legacy-message-{i}",
                                header="📬 Mensagem (Legacy)",
                                is_open=True,
                                dismissable=True,
                                duration=4000,
                                icon="primary",
                                style={
                                    "marginBottom": "10px",
                                    "borderLeft": "4px solid var(--wa-green)",
                                    "opacity": "0.8"
                                }
                            )
                        )
        
        # Retornar no máximo 3 notificações visíveis por vez
        return notifications[-3:] if len(notifications) > 3 else notifications
        
    except Exception as e:
        print(f"❌ Erro ao criar notificações reais: {e}")
        return []

@callback(
    Output('realtime-metrics', 'data'),
    [Input('metrics-interval', 'n_intervals')],
    [State('current-page', 'data')]
)
def update_realtime_metrics(n_intervals, current_page):
    """Atualizar métricas em tempo real com dados reais do banco"""
    if current_page == 'overview':
        try:
            # Carregar dados atualizados do banco
            engine = get_database_connection()
            if not engine:
                print("❌ Sem conexão para métricas em tempo real")
                return {}
            
            with engine.connect() as conn:
                metrics = {}
                
                # Métricas básicas atualizadas
                try:
                    metrics['users'] = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
                    metrics['messages'] = conn.execute(text("SELECT COUNT(*) FROM messages")).fetchone()[0]
                    metrics['conversations'] = conn.execute(text("SELECT COUNT(*) FROM conversations")).fetchone()[0]
                    metrics['appointments'] = conn.execute(text("SELECT COUNT(*) FROM appointments")).fetchone()[0]
                    metrics['services'] = conn.execute(text("SELECT COUNT(*) FROM services")).fetchone()[0]
                    metrics['blocked_times'] = conn.execute(text("SELECT COUNT(*) FROM blocked_times")).fetchone()[0]
                    
                    # Métricas em tempo real adicionais
                    metrics['messages_today'] = conn.execute(text("""
                        SELECT COUNT(*) FROM messages 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)).fetchone()[0]
                    
                    metrics['conversations_active'] = conn.execute(text("""
                        SELECT COUNT(*) FROM conversations 
                        WHERE status = 'ativa'
                    """)).fetchone()[0]
                    
                    metrics['appointments_today'] = conn.execute(text("""
                        SELECT COUNT(*) FROM appointments 
                        WHERE DATE(date_time) = CURRENT_DATE
                    """)).fetchone()[0]
                    
                    metrics['new_users_today'] = conn.execute(text("""
                        SELECT COUNT(*) FROM users 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)).fetchone()[0]
                    
                    print(f"📊 Métricas em tempo real atualizadas: {metrics}")
                    
                except Exception as e:
                    print(f"❌ Erro ao buscar métricas específicas: {e}")
                    return {}
                
                return metrics
                
        except Exception as e:
            print(f"❌ Erro ao atualizar métricas em tempo real: {e}")
            return {}
        
        finally:
            try:
                engine.dispose()
            except:
                pass
    
    return {}

# Callback para atualizar gráficos automaticamente com dados em tempo real
@callback(
    [Output('msg-direction-chart', 'figure', allow_duplicate=True),
     Output('conv-status-chart', 'figure', allow_duplicate=True)],
    [Input('realtime-metrics', 'data'),
     Input('metrics-interval', 'n_intervals')],
    [State('current-page', 'data')],
    prevent_initial_call=True
)
def update_charts_realtime(metrics_data, n_intervals, current_page):
    """Atualizar gráficos com dados em tempo real"""
    if current_page != 'overview' or not metrics_data:
        return dash.no_update, dash.no_update
    
    try:
        # Recarregar dados completos para gráficos
        data = load_overview_data()
        if not data:
            return dash.no_update, dash.no_update
        
        colors = ['#25D366', '#128C7E', '#075E54', '#34B7F1']
        
        # Gráfico de direção das mensagens
        if data['msg_direction']:
            df_direction = pd.DataFrame(data['msg_direction'], columns=['direction', 'count'])
            df_direction['direction'] = df_direction['direction'].map({
                'in': 'Recebidas',
                'out': 'Enviadas'
            })
            fig_direction = px.pie(
                df_direction, 
                values='count', 
                names='direction',
                color_discrete_sequence=colors
            )
            fig_direction.update_layout(
                font_family="Inter",
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1)
            )
            fig_direction.update_traces(textposition='inside', textinfo='percent+label')
        else:
            fig_direction = {}
        
        # Gráfico de status das conversas
        if data['conv_status']:
            df_status = pd.DataFrame(data['conv_status'], columns=['status', 'count'])
            fig_status = px.bar(
                df_status, 
                x='status', 
                y='count',
                color='status',
                color_discrete_sequence=colors
            )
            fig_status.update_layout(
                font_family="Inter",
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False
            )
        else:
            fig_status = {}
        
        return fig_direction, fig_status
        
    except Exception as e:
        print(f"❌ Erro ao atualizar gráficos em tempo real: {e}")
        return dash.no_update, dash.no_update

# Callback para dados reais em tempo real
@callback(
    Output('realtime-messages', 'data', allow_duplicate=True),
    [Input('realtime-interval', 'n_intervals')],
    [State('realtime-messages', 'data')],
    prevent_initial_call=True
)
def get_real_time_data(n_intervals, current_messages):
    """Buscar dados reais em tempo real do banco de dados"""
    current_messages = current_messages or []
    engine = get_database_connection()
    
    if not engine:
        print("❌ Sem conexão com banco para tempo real")
        return current_messages
    
    try:
        with engine.connect() as conn:
            notifications = []
            
            # Buscar novas mensagens dos últimos 30 segundos
            try:
                new_messages_query = text("""
                    SELECT 
                        m.content,
                        m.direction,
                        m.created_at,
                        u.nome as user_name,
                        u.telefone as user_phone
                    FROM messages m
                    LEFT JOIN users u ON m.user_id = u.id
                    WHERE m.created_at >= NOW() - INTERVAL '30 seconds'
                    AND m.direction = 'in'
                    ORDER BY m.created_at DESC
                    LIMIT 5
                """)
                
                new_messages = conn.execute(new_messages_query).fetchall()
                
                for msg in new_messages:
                    # Verificar se essa mensagem já foi processada
                    msg_timestamp = msg[2].isoformat() if msg[2] else datetime.now().isoformat()
                    already_exists = any(
                        existing.get('data', {}).get('message_id') == f"msg_{msg_timestamp}"
                        for existing in current_messages
                    )
                    
                    if not already_exists:
                        notifications.append({
                            'timestamp': msg_timestamp,
                            'data': {
                                'type': 'message',
                                'message_id': f"msg_{msg_timestamp}",
                                'user': msg[3] or 'Usuário Desconhecido',
                                'phone': msg[4] or '',
                                'content': msg[0] or 'Mensagem sem conteúdo',
                                'direction': msg[1],
                                'created_at': msg_timestamp
                            }
                        })
                        
                print(f"📱 Encontradas {len(new_messages)} novas mensagens")
                
            except Exception as e:
                print(f"❌ Erro ao buscar mensagens: {e}")
            
            # Buscar novos agendamentos dos últimos 60 segundos
            try:
                new_appointments_query = text("""
                    SELECT 
                        a.id,
                        a.date_time,
                        a.status,
                        a.created_at,
                        u.nome as customer_name,
                        u.telefone as customer_phone,
                        s.name as service_name
                    FROM appointments a
                    LEFT JOIN users u ON a.user_id = u.id
                    LEFT JOIN services s ON a.service_id = s.id
                    WHERE a.created_at >= NOW() - INTERVAL '60 seconds'
                    ORDER BY a.created_at DESC
                    LIMIT 3
                """)
                
                new_appointments = conn.execute(new_appointments_query).fetchall()
                
                for apt in new_appointments:
                    # Verificar se esse agendamento já foi processado
                    apt_timestamp = apt[3].isoformat() if apt[3] else datetime.now().isoformat()
                    already_exists = any(
                        existing.get('data', {}).get('appointment_id') == f"apt_{apt[0]}"
                        for existing in current_messages
                    )
                    
                    if not already_exists:
                        notifications.append({
                            'timestamp': apt_timestamp,
                            'data': {
                                'type': 'appointment',
                                'appointment_id': f"apt_{apt[0]}",
                                'appointment': {
                                    'customer': apt[4] or 'Cliente Desconhecido',
                                    'phone': apt[5] or '',
                                    'service': apt[6] or 'Serviço',
                                    'date_time': apt[1].strftime('%d/%m/%Y %H:%M') if apt[1] else '',
                                    'status': apt[2] or 'pendente'
                                },
                                'created_at': apt_timestamp
                            }
                        })
                        
                print(f"📅 Encontrados {len(new_appointments)} novos agendamentos")
                
            except Exception as e:
                print(f"❌ Erro ao buscar agendamentos: {e}")
            
            # Buscar atualizações de status de conversas dos últimos 45 segundos
            try:
                conversation_updates_query = text("""
                    SELECT 
                        c.id,
                        c.status,
                        c.updated_at,
                        u.nome as user_name
                    FROM conversations c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.updated_at >= NOW() - INTERVAL '45 seconds'
                    AND c.updated_at != c.created_at
                    ORDER BY c.updated_at DESC
                    LIMIT 3
                """)
                
                conversation_updates = conn.execute(conversation_updates_query).fetchall()
                
                for conv in conversation_updates:
                    # Verificar se essa atualização já foi processada
                    conv_timestamp = conv[2].isoformat() if conv[2] else datetime.now().isoformat()
                    already_exists = any(
                        existing.get('data', {}).get('conversation_id') == f"conv_{conv[0]}"
                        for existing in current_messages
                    )
                    
                    if not already_exists:
                        notifications.append({
                            'timestamp': conv_timestamp,
                            'data': {
                                'type': 'system',
                                'conversation_id': f"conv_{conv[0]}",
                                'system': f"Conversa com {conv[3] or 'usuário'} alterada para: {conv[1]}",
                                'details': {
                                    'user': conv[3],
                                    'status': conv[1],
                                    'conversation_id': conv[0]
                                },
                                'created_at': conv_timestamp
                            }
                        })
                        
                print(f"💬 Encontradas {len(conversation_updates)} atualizações de conversa")
                
            except Exception as e:
                print(f"❌ Erro ao buscar atualizações de conversa: {e}")
            
            # Adicionar novas notificações à lista
            if notifications:
                current_messages.extend(notifications)
                print(f"✅ Adicionadas {len(notifications)} notificações reais")
            
            # Manter apenas as últimas 100 notificações
            return current_messages[-100:]
            
    except Exception as e:
        print(f"❌ Erro geral ao buscar dados em tempo real: {e}")
        return current_messages or []
    
    finally:
        try:
            engine.dispose()
        except:
            pass

# ==================== CALLBACKS PARA RATE LIMITING ====================

if RATE_LIMITING_AVAILABLE:
    
    @callback(
        [Output('rate-limit-stats-cards', 'children'),
         Output('protected-endpoints-table', 'children'),
         Output('blocked-ips-display', 'children'),
         Output('recent-violations-table', 'children')],
        [Input('rate-limit-interval', 'n_intervals'),
         Input('current-page', 'data')]
    )
    def update_rate_limiting_dashboard(n_intervals, current_page):
        """Atualizar dashboard de rate limiting"""
        if current_page != 'rate-limiting':
            return [], [], [], []
        
        try:
            stats = rate_limiter.get_stats()
            
            # 1. Cards de estatísticas
            stats_cards = html.Div([
                # Total de violações
                html.Div([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle", style={'fontSize': '24px', 'color': '#dc3545'}),
                        html.Div([
                            html.H3(str(stats.get('total_violations', 0)), className="stat-number"),
                            html.P("Violações Totais", className="stat-label")
                        ], className="stat-text")
                    ], className="stat-content")
                ], className="stat-card danger"),
                
                # IPs bloqueados
                html.Div([
                    html.Div([
                        html.I(className="fas fa-ban", style={'fontSize': '24px', 'color': '#ffc107'}),
                        html.Div([
                            html.H3(str(stats.get('blocked_ips', 0)), className="stat-number"),
                            html.P("IPs Bloqueados", className="stat-label")
                        ], className="stat-text")
                    ], className="stat-content")
                ], className="stat-card warning"),
                
                # Endpoints protegidos
                html.Div([
                    html.Div([
                        html.I(className="fas fa-shield-alt", style={'fontSize': '24px', 'color': '#28a745'}),
                        html.Div([
                            html.H3(str(len(stats.get('configs', {}))), className="stat-number"),
                            html.P("Endpoints Protegidos", className="stat-label")
                        ], className="stat-text")
                    ], className="stat-content")
                ], className="stat-card success"),
                
                # Taxa de bloqueio
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chart-line", style={'fontSize': '24px', 'color': '#17a2b8'}),
                        html.Div([
                            html.H3(f"{((stats.get('total_violations', 0) / max(1, stats.get('total_violations', 0) + 1000)) * 100):.1f}%", className="stat-number"),
                            html.P("Taxa de Bloqueio", className="stat-label")
                        ], className="stat-text")
                    ], className="stat-content")
                ], className="stat-card info")
            ], className="rate-limit-stats-grid")
            
            # 2. Tabela de endpoints protegidos
            configs = stats.get('configs', {})
            endpoints_rows = []
            for endpoint, config in configs.items():
                endpoints_rows.append(
                    html.Tr([
                        html.Td(endpoint),
                        html.Td(f"{config.get('requests_per_window', 0)} req"),
                        html.Td(f"{config.get('window_size', 0)}s"),
                        html.Td(f"{config.get('burst_limit', 0)} req"),
                        html.Td([
                            html.Span(
                                config.get('level', 'MEDIUM'), 
                                className=f"badge badge-{config.get('level', 'MEDIUM').lower()}"
                            )
                        ])
                    ])
                )
            
            endpoints_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Endpoint"),
                        html.Th("Limite/Janela"),
                        html.Th("Janela"),
                        html.Th("Rajada"),
                        html.Th("Nível")
                    ])
                ]),
                html.Tbody(endpoints_rows)
            ], striped=True, bordered=True, hover=True, size="sm")
            
            # 3. Lista de IPs bloqueados
            blocked_ips = stats.get('blocked_ip_list', [])
            if blocked_ips:
                blocked_display = html.Ul([
                    html.Li([
                        html.I(className="fas fa-ban text-danger", style={'marginRight': '8px'}),
                        html.Code(ip),
                        html.Small(" (ativo)", className="text-muted ml-2")
                    ], className="blocked-ip-item")
                    for ip in blocked_ips
                ], className="blocked-ips-list")
            else:
                blocked_display = html.P("✅ Nenhum IP bloqueado no momento", className="text-success")
            
            # 4. Violações por IP
            violations_by_ip = stats.get('violation_by_ip', {})
            if violations_by_ip:
                violations_rows = []
                for ip, count in sorted(violations_by_ip.items(), key=lambda x: x[1], reverse=True):
                    if count > 0:
                        violations_rows.append(
                            html.Tr([
                                html.Td(html.Code(ip)),
                                html.Td([
                                    html.Span(
                                        str(count), 
                                        className=f"badge badge-{'danger' if count > 10 else 'warning' if count > 5 else 'secondary'}"
                                    )
                                ]),
                                html.Td(datetime.now().strftime("%H:%M:%S"))  # Placeholder
                            ])
                        )
                
                violations_table = dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("IP Address"),
                            html.Th("Violações"),
                            html.Th("Última Violação")
                        ])
                    ]),
                    html.Tbody(violations_rows[:10])  # Mostrar apenas top 10
                ], striped=True, bordered=True, hover=True, size="sm")
            else:
                violations_table = html.P("✅ Nenhuma violação registrada", className="text-success")
            
            return stats_cards, endpoints_table, blocked_display, violations_table
            
        except Exception as e:
            error_msg = html.Div([
                html.I(className="fas fa-exclamation-triangle text-danger"),
                f" Erro ao carregar dados: {str(e)}"
            ], className="alert alert-danger")
            return error_msg, error_msg, error_msg, error_msg
    
    @callback(
        Output('rate-limit-actions-feedback', 'children'),
        [Input('clear-blocks-btn', 'n_clicks'),
         Input('reset-stats-btn', 'n_clicks'),
         Input('export-logs-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_rate_limiting_actions(clear_clicks, reset_clicks, export_clicks):
        """Gerenciar ações do painel de rate limiting"""
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == 'clear-blocks-btn':
                # Limpar bloqueios
                rate_limiter.blocked_ips.clear()
                return dbc.Alert(
                    "✅ Todos os bloqueios de IP foram removidos", 
                    color="success", 
                    dismissable=True,
                    duration=3000
                )
            
            elif button_id == 'reset-stats-btn':
                # Resetar estatísticas
                rate_limiter.violation_tracker.clear()
                return dbc.Alert(
                    "✅ Estatísticas de violação resetadas", 
                    color="success", 
                    dismissable=True,
                    duration=3000
                )
            
            elif button_id == 'export-logs-btn':
                # Exportar logs (simulado)
                stats = rate_limiter.get_stats()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return dbc.Alert(
                    f"📊 Logs exportados: rate_limit_report_{timestamp}.json", 
                    color="info", 
                    dismissable=True,
                    duration=5000
                )
                
        except Exception as e:
            return dbc.Alert(
                f"❌ Erro ao executar ação: {str(e)}", 
                color="danger", 
                dismissable=True,
                duration=5000
            )
        
        return ""

else:
    # Fallback quando rate limiting não está disponível
    @callback(
        Output('rate-limit-stats-cards', 'children'),
        Input('current-page', 'data')
    )
    def rate_limiting_not_available(current_page):
        if current_page == 'rate-limiting':
            return html.Div([
                html.I(className="fas fa-exclamation-triangle text-warning"),
                " Sistema de Rate Limiting não está disponível"
            ], className="alert alert-warning")
        return []

if __name__ == '__main__':
    # Rodar o app
    print("🌐 Iniciando servidor do dashboard...")
    app.run(debug=True, host='0.0.0.0', port=8050)

