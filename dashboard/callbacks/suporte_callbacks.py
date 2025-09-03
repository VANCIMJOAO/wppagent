"""
Suporte Callbacks - Funcionalidades da Página de Suporte
========================================================

Callbacks para:
- Formulário de contato/ticket
- Status do sistema em tempo real
- Interações com FAQs
- Funcionalidades da documentação
"""

from dash import Input, Output, State, callback, no_update, html, dcc, callback_context
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from datetime import datetime
from dash.exceptions import PreventUpdate
import json
import sys
import os

# Adiciona o caminho para importar serviços
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.database import DatabaseService
    database_available = True
except ImportError:
    database_available = False
    print("⚠️  Database service não disponível para página de suporte")

def register_suporte_callbacks(app):
    """
    Registra todos os callbacks da página de suporte.
    """
    
    @app.callback(
        [
            Output('support-form-submit', 'loading'),
            Output('support-form-name', 'value'),
            Output('support-form-email', 'value'),
            Output('support-form-category', 'value'),
            Output('support-form-priority', 'value'),
            Output('support-form-description', 'value'),
            Output('support-form-data', 'data')
        ],
        [
            Input('support-form-submit', 'n_clicks'),
            Input('support-form-clear', 'n_clicks')
        ],
        [
            State('support-form-name', 'value'),
            State('support-form-email', 'value'),
            State('support-form-category', 'value'),
            State('support-form-priority', 'value'),
            State('support-form-description', 'value')
        ],
        prevent_initial_call=True
    )
    def handle_support_form(submit_clicks, clear_clicks, name, email, category, priority, description):
        """
        Processa submissão e limpeza do formulário de suporte.
        """
        ctx = callback_context
        
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Limpeza do formulário
        if button_id == 'support-form-clear':
            return (
                False,  # loading
                "",     # name
                "",     # email  
                None,   # category
                "medium", # priority (volta ao default)
                "",     # description
                {}      # form data
            )
        
        # Submissão do formulário
        if button_id == 'support-form-submit' and submit_clicks:
            
            # Validação básica
            if not all([name, email, category, description]):
                return (
                    False,  # loading
                    name or "", 
                    email or "", 
                    category, 
                    priority or "medium", 
                    description or "",
                    {"error": "Preencha todos os campos obrigatórios"}
                )
            
            # Simula processamento (aqui seria enviado para sistema de tickets)
            ticket_data = {
                "id": f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": name,
                "email": email,
                "category": category,
                "priority": priority,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "status": "open"
            }
            
            try:
                # Aqui você pode integrar com sistema de tickets real
                # Por exemplo, enviar email, salvar no banco, integrar com Zendesk, etc.
                
                if database_available:
                    db = DatabaseService()
                    # Salva ticket na base de dados (opcional)
                    # insert_query = """
                    # INSERT INTO support_tickets (name, email, category, priority, description, created_at)
                    # VALUES (%s, %s, %s, %s, %s, %s)
                    # """
                    # db.execute_query(insert_query, (name, email, category, priority, description, datetime.now()))
                
                # Simula delay de processamento
                import time
                time.sleep(1)
                
                # Sucesso - limpa formulário
                return (
                    False,  # loading
                    "",     # name
                    "",     # email
                    None,   # category  
                    "medium", # priority
                    "",     # description
                    {"success": True, "ticket": ticket_data}
                )
                
            except Exception as e:
                print(f"Erro ao processar ticket: {e}")
                return (
                    False,  # loading
                    name, 
                    email, 
                    category, 
                    priority, 
                    description,
                    {"error": f"Erro interno: {str(e)[:50]}"}
                )
        
        raise PreventUpdate

    @app.callback(
        Output('support-system-status', 'data'),
        Input('url', 'pathname'),
        prevent_initial_call=False
    )
    def update_system_status(pathname):
        """
        Atualiza status dos sistemas em tempo real.
        """
        if pathname != '/suporte':
            raise PreventUpdate
        
        try:
            # Verificações reais de status
            status_checks = {}
            
            # Verificar database
            if database_available:
                try:
                    db = DatabaseService()
                    is_db_online = db.test_connection()
                    status_checks['database'] = {
                        'status': 'online' if is_db_online else 'offline',
                        'uptime': '99.9%' if is_db_online else '0%',
                        'last_check': datetime.now().isoformat()
                    }
                except Exception as e:
                    status_checks['database'] = {
                        'status': 'offline',
                        'uptime': '0%', 
                        'last_check': datetime.now().isoformat(),
                        'error': str(e)
                    }
            else:
                status_checks['database'] = {
                    'status': 'warning',
                    'uptime': 'N/A',
                    'last_check': datetime.now().isoformat(),
                    'message': 'Service not available'
                }
            
            # Verificar outros serviços (simulado)
            status_checks.update({
                'whatsapp_api': {
                    'status': 'online',
                    'uptime': '99.8%',
                    'last_check': datetime.now().isoformat()
                },
                'dashboard': {
                    'status': 'online',
                    'uptime': '100%',
                    'last_check': datetime.now().isoformat()
                },
                'backup_system': {
                    'status': 'online',
                    'uptime': '99.9%',
                    'last_check': datetime.now().isoformat()
                }
            })
            
            return status_checks
            
        except Exception as e:
            print(f"Erro ao verificar status do sistema: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    # Callback removido para evitar erro de componente inexistente

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        [Input(f'doc-item-{i}', 'n_clicks') for i in range(6)],
        prevent_initial_call=True
    )
    def handle_documentation_clicks(*clicks):
        """
        Navega para seções de documentação (placeholder).
        Em uma implementação real, isso redirecionaria para páginas específicas.
        """
        ctx = callback_context
        
        if not ctx.triggered or not any(clicks):
            raise PreventUpdate
        
        # Identifica qual item foi clicado
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Mapeamento de IDs para URLs (placeholder)
        doc_urls = {
            'doc-item-0': '/docs/getting-started',
            'doc-item-1': '/docs/whatsapp-setup', 
            'doc-item-2': '/docs/conversations',
            'doc-item-3': '/docs/appointments',
            'doc-item-4': '/docs/reports',
            'doc-item-5': '/docs/api'
        }
        
        target_url = doc_urls.get(triggered_id, '/suporte')
        
        # Por enquanto, mantém na página de suporte
        # Em implementação futura, criar páginas de documentação específicas
        return '/suporte'

def register_all_suporte_callbacks(app):
    """
    Função principal para registrar todos os callbacks de suporte.
    """
    try:
        register_suporte_callbacks(app)
        print("✅ SUPORTE callbacks registrados com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao registrar callbacks de suporte: {e}")
        return False
