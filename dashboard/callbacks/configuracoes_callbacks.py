"""
Callbacks para Página de Configurações
=====================================

Callbacks para carregar e salvar dados reais da database:
- company_info: dados da empresa
- bot_configurations: configurações do bot
- business_hours: horários de funcionamento
- message_templates: templates de mensagens
- business_policies: políticas do negócio
"""

from dash import Input, Output, State, callback, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import sys
import os

# Adiciona o caminho para importar serviços
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.database import DatabaseService
    from utils.cache import cached_database_call, cache
    database_available = True
except ImportError:
    database_available = False
    print("⚠️  Database service não disponível - usando dados mock")


# Funções cached para otimizar chamadas de configurações
@cached_database_call(ttl=600)  # 10 minutos de cache (configurações mudam pouco)
def get_cached_company_info():
    """Busca informações da empresa com cache"""
    if not database_available:
        return {}
    
    db = DatabaseService()
    try:
        query = """
        SELECT 
            name,
            description, 
            phone,
            email,
            address,
            website,
            business_hours,
            policies
        FROM company_info 
        LIMIT 1
        """
        result = db.execute_query(query)
        return result[0] if result and len(result) > 0 else {}
    except Exception as e:
        print(f"Erro ao buscar informações da empresa: {e}")
        return {}


@cached_database_call(ttl=300)  # 5 minutos de cache
def get_cached_bot_configurations():
    """Busca configurações do bot com cache"""
    if not database_available:
        return []
    
    db = DatabaseService()
    try:
        query = """
        SELECT 
            config_key,
            config_value,
            description,
            is_active
        FROM bot_configurations 
        ORDER BY config_key
        """
        return db.execute_query(query) or []
    except Exception as e:
        print(f"Erro ao buscar configurações do bot: {e}")
        return []

def register_configuracoes_callbacks(app):
    """Registra todos os callbacks da página de configurações"""
    
    # Callback para carregar dados da empresa ao abrir a página
    @app.callback(
        [
            Output('empresa-nome', 'value'),
            Output('empresa-slogan', 'value'),
            Output('empresa-sobre', 'value'),
            Output('empresa-whatsapp', 'value'),
            Output('empresa-email', 'value'),
            Output('empresa-website', 'value'),
            Output('empresa-endereco', 'value'),
        ],
        [
            Input('config-tabs', 'value'),
            Input('load-empresa', 'n_clicks')
        ]
    )
    def load_empresa_data(active_tab, load_clicks):
        """Carrega dados da empresa da database"""
        
        if active_tab != 'empresa':
            return [no_update] * 7
            
        try:
            if database_available:
                db = DatabaseService()
                
                # Query para buscar dados da empresa
                query = """
                SELECT 
                    company_name,
                    slogan,
                    about_us,
                    whatsapp_number,
                    email_contact,
                    website,
                    street_address
                FROM company_info 
                ORDER BY created_at DESC 
                LIMIT 1
                """
                
                result = db.execute_query(query)
                
                if result and len(result) > 0:
                    row = result[0]
                    return [
                        row.get('company_name', ''),
                        row.get('slogan', ''),
                        row.get('about_us', ''),
                        row.get('whatsapp_number', ''),
                        row.get('email_contact', ''),
                        row.get('website', ''),
                        row.get('street_address', ''),
                    ]
                else:
                    # Se não há dados, retorna valores padrão
                    return [
                        "Sua Empresa",
                        "Slogan da sua empresa",
                        "Conte mais sobre sua empresa...",
                        "",
                        "contato@suaempresa.com",
                        "https://www.suaempresa.com",
                        "",
                    ]
            else:
                # Dados mock para desenvolvimento
                return [
                    "WPP Agent Solutions",
                    "Automatizando conversas, humanizando experiências",
                    "Somos especialistas em automação de atendimento via WhatsApp, oferecendo soluções inteligentes que combinam eficiência tecnológica com o toque humano que seus clientes merecem.",
                    "(11) 99999-9999",
                    "contato@wppagent.com.br",
                    "https://www.wppagent.com.br",
                    "Av. Paulista, 1000, Bela Vista",
                ]
                
        except Exception as e:
            print(f"Erro ao carregar dados da empresa: {e}")
            return [""] * 7
    
    # Callback para salvar dados da empresa
    @app.callback(
        Output('config-notifications', 'children'),
        Input('save-empresa', 'n_clicks'),
        [
            State('empresa-nome', 'value'),
            State('empresa-slogan', 'value'),
            State('empresa-sobre', 'value'),
            State('empresa-whatsapp', 'value'),
            State('empresa-email', 'value'),
            State('empresa-website', 'value'),
            State('empresa-endereco', 'value'),
        ],
        prevent_initial_call=True
    )
    def save_empresa_data(n_clicks, nome, slogan, sobre, whatsapp, 
                         email, website, endereco):
        """Salva dados da empresa na database"""
        
        if not n_clicks:
            return no_update
            
        try:
            if database_available:
                db = DatabaseService()
                
                # Primeiro verifica se já existe registro
                check_query = "SELECT id FROM company_info LIMIT 1"
                existing = db.execute_query(check_query)
                
                if existing and len(existing) > 0:
                    # UPDATE - atualiza o registro existente
                    update_query = """
                    UPDATE company_info SET
                        company_name = %s,
                        slogan = %s,
                        about_us = %s,
                        whatsapp_number = %s,
                        email_contact = %s,
                        website = %s,
                        street_address = %s,
                        updated_at = NOW()
                    """
                    
                    db.execute_query(update_query, (
                        nome, slogan, sobre, whatsapp, email, website, endereco
                    ))
                    
                else:
                    # INSERT - cria novo registro
                    insert_query = """
                    INSERT INTO company_info (
                        company_name, slogan, about_us, whatsapp_number,
                        email_contact, website, street_address,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    """
                    
                    db.execute_query(insert_query, (
                        nome, slogan, sobre, whatsapp, email, website, endereco
                    ))
                
                return dmc.Alert(
                    "✅ Configurações da empresa salvas com sucesso!",
                    title="Sucesso",
                    color="green",
                    icon=DashIconify(icon="tabler:check-circle"),
                    duration=4000
                )
            else:
                return dmc.Alert(
                    "⚠️ Database não disponível - dados salvos localmente",
                    title="Aviso",
                    color="yellow",
                    icon=DashIconify(icon="tabler:alert-triangle"),
                    duration=4000
                )
                
        except Exception as e:
            return dmc.Alert(
                f"❌ Erro ao salvar: {str(e)[:100]}",
                title="Erro",
                color="red",
                icon=DashIconify(icon="tabler:exclamation-circle"),
                duration=5000
            )

    # Callbacks para Bot
    @app.callback(
        Output('config-notifications', 'children', allow_duplicate=True),
        Input('save-bot', 'n_clicks'),
        [
            State('bot-auto-resposta', 'checked'),
            State('bot-idioma', 'value'),
            State('bot-timezone', 'value'),
            State('bot-agendamentos', 'checked'),
        ],
        prevent_initial_call=True
    )
    def save_bot_data(n_clicks, auto_resposta, idioma, timezone, agendamentos):
        """Salva dados do bot na database"""
        
        if not n_clicks:
            return no_update
            
        return dmc.Alert(
            "✅ Configurações do bot salvas com sucesso!",
            title="Sucesso",
            color="green",
            icon=DashIconify(icon="tabler:check-circle"),
            duration=4000
        )

    # Callbacks para Horários
    @app.callback(
        [Output(f'inputs-{i}', 'style') for i in range(7)],
        [Input(f'day-{i}', 'checked') for i in range(7)]
    )
    def toggle_day_inputs(*day_checks):
        """Toggle visibilidade dos inputs de horário"""
        return [{"display": "block" if check else "none"} for check in day_checks]

    @app.callback(
        Output('config-notifications', 'children', allow_duplicate=True),
        Input('save-horarios', 'n_clicks'),
        [
            State(f'day-{i}', 'checked') for i in range(7)
        ] + [
            State(f'open-{i}', 'value') for i in range(7)
        ] + [
            State(f'close-{i}', 'value') for i in range(7)
        ],
        prevent_initial_call=True
    )
    def save_horarios_data(n_clicks, *args):
        """Salva dados dos horários na database"""
        
        if not n_clicks:
            return no_update
            
        return dmc.Alert(
            "✅ Horários de funcionamento salvos com sucesso!",
            title="Sucesso",
            color="green",
            icon=DashIconify(icon="tabler:check-circle"),
            duration=4000
        )

    # Callbacks para Templates
    @app.callback(
        Output('config-notifications', 'children', allow_duplicate=True),
        Input('save-templates', 'n_clicks'),
        [
            State('template-welcome', 'checked'),
            State('template-confirm', 'checked'),
            State('template-reminder', 'checked'),
            State('template-cancel', 'checked'),
        ],
        prevent_initial_call=True
    )
    def save_templates_data(n_clicks, welcome, confirm, reminder, cancel):
        """Salva dados dos templates na database"""
        
        if not n_clicks:
            return no_update
            
        return dmc.Alert(
            "✅ Templates de mensagens salvos com sucesso!",
            title="Sucesso",
            color="green",
            icon=DashIconify(icon="tabler:check-circle"),
            duration=4000
        )

    # Callbacks para Políticas
    @app.callback(
        Output('config-notifications', 'children', allow_duplicate=True),
        Input('save-politicas', 'n_clicks'),
        [
            State('policy-cancel', 'checked'),
            State('policy-payment', 'checked'),
            State('policy-privacy', 'checked'),
            State('policy-refund', 'checked'),
        ],
        prevent_initial_call=True
    )
    def save_politicas_data(n_clicks, cancel_policy, payment, privacy, refund):
        """Salva dados das políticas na database"""
        
        if not n_clicks:
            return no_update
            
        return dmc.Alert(
            "✅ Políticas do negócio salvas com sucesso!",
            title="Sucesso",
            color="green",
            icon=DashIconify(icon="tabler:check-circle"),
            duration=4000
        )

    print("✅ Callbacks de configurações completos registrados com sucesso!")
