from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Componentes de autenticação para o dashboard
"""
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, no_update
from datetime import datetime
import plotly.graph_objects as go
from app.config import settings


def create_login_page():
    """Criar página de login"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                # Card principal de login
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className="fas fa-whatsapp", style={
                                'fontSize': '48px',
                                'color': '#25D366',
                                'marginBottom': '16px'
                            }),
                            html.H2("WhatsApp Agent", className="mb-2"),
                            html.P("Dashboard Executivo", className="text-muted mb-0")
                        ], className="text-center")
                    ], className="bg-light"),
                    
                    dbc.CardBody([
                        html.Div(id="login-alerts"),
                        
                        dbc.Form([
                            # Username/Email
                            dbc.Row([
                                dbc.Label("Usuário ou Email", html_for="login-username", width=12),
                                dbc.Col([
                                    dbc.Input(
                                        type="text",
                                        id="login-username",
                                        placeholder="Digite seu usuário ou email",
                                        value="admin",  # Valor padrão para facilitar teste
                                        className="mb-3"
                                    )
                                ], width=12)
                            ], className="mb-3"),
                            
                            # Password
                            dbc.Row([
                                dbc.Label("Senha", html_for="login-password", width=12),
                                dbc.Col([
                                    dbc.Input(
                                        type="password",
                                        id="login-password",
                                        placeholder="Digite sua senha",
                                        className="mb-3"
                                    )
                                ], width=12)
                            ], className="mb-3"),
                            
                            # Lembrar login
                            dbc.Row([
                                dbc.Col([
                                    dbc.Checkbox(
                                        id="login-remember",
                                        label="Manter-me conectado",
                                        value=True
                                    )
                                ], width=12)
                            ], className="mb-4"),
                            
                            # Botão de login
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-sign-in-alt me-2"),
                                            "Entrar"
                                        ],
                                        id="login-button",
                                        color="success",
                                        size="lg",
                                        className="w-100",
                                        n_clicks=0
                                    )
                                ], width=12)
                            ])
                        ])
                    ], className="p-4"),
                    
                    dbc.CardFooter([
                        html.P([
                            "Versão 1.0 • ",
                            html.A("Documentação", href="#", className="text-decoration-none"),
                            " • ",
                            html.A("Suporte", href="#", className="text-decoration-none")
                        ], className="text-center text-muted mb-0 small")
                    ], className="bg-light")
                    
                ], className="shadow-lg border-0", style={'maxWidth': '400px'})
                
            ], width=12, className="d-flex justify-content-center align-items-center")
        ], style={'minHeight': '100vh'}, className="bg-light"),
        
        # Store para dados de autenticação
        dcc.Store(id='auth-store', storage_type='session'),
        dcc.Store(id='user-data', storage_type='session'),
        dcc.Location(id='login-redirect', refresh=True)
        
    ], fluid=True, className="p-0")


def create_logout_component():
    """Criar componente de logout"""
    return html.Div([
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem("Perfil", header=True),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem([
                    html.I(className="fas fa-user me-2"),
                    "Meu Perfil"
                ], id="profile-menu", n_clicks=0),
                dbc.DropdownMenuItem([
                    html.I(className="fas fa-cog me-2"),
                    "Configurações"
                ], id="settings-menu", n_clicks=0),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem([
                    html.I(className="fas fa-sign-out-alt me-2"),
                    "Sair"
                ], id="logout-menu", n_clicks=0, className="text-danger")
            ],
            label=html.Span([
                html.I(className="fas fa-user-circle me-2"),
                html.Span(id="user-display-name", children="Admin")
            ]),
            color="light",
            className="border-0",
            style={'backgroundColor': 'transparent'}
        )
    ])


def create_auth_callbacks(app):
    """Criar callbacks de autenticação"""
    
    @app.callback(
        [Output('login-alerts', 'children'),
         Output('auth-store', 'data'),
         Output('user-data', 'data'),
         Output('login-redirect', 'pathname')],
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value'),
         State('login-remember', 'value'),
         State('auth-store', 'data')],
        prevent_initial_call=True
    )
    def handle_login(n_clicks, username, password, remember, current_auth):
        """Processar login"""
        # Verificar se usuário já está autenticado
        if current_auth and current_auth.get('authenticated'):
            print(f"✅ Usuário já autenticado, ignorando callback: {current_auth.get('username')}")
            return no_update, no_update, no_update, no_update
        
        # Verificação mais rigorosa para evitar loops
        if not n_clicks or n_clicks is None or n_clicks <= 0:
            return no_update, no_update, no_update, no_update
            
        # Verificar se callback foi realmente triggered pelo botão
        from dash import ctx
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update
            
        triggered_prop = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
        if 'login-button.n_clicks' not in triggered_prop:
            return no_update, no_update, no_update, no_update
        
        print(f"🔍 Login callback VÁLIDO: n_clicks={n_clicks}, username={username}")
        
        print(f"🔐 Processando login: username='{username}', password={'*' * len(password) if password else 'None'}")
        
        if not username or not password:
            print(f"❌ Campos vazios: username='{username}', password='{password}'")
            alert = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Por favor, preencha todos os campos."
                ],
                color="warning",
                dismissable=True
            )
            return alert, no_update, no_update, no_update

        # SISTEMA DE AUTENTICAÇÃO USANDO VARIÁVEIS DE AMBIENTE
        admin_username = settings.admin_username or "admin"
        admin_password = settings.admin_password.get_secret_value() if settings.admin_password else None
        
        # Verificar credenciais
        login_successful = False
        if admin_password and username == admin_username and password == admin_password:
            login_successful = True
        elif not admin_password:
            # Log de erro se credenciais não estão configuradas
            logger.error("ADMIN_PASSWORD não configurada - configure as variáveis de ambiente ADMIN_USERNAME e ADMIN_PASSWORD")
            return (
                dbc.Alert("Credenciais de administrador não configuradas. Configure ADMIN_PASSWORD nas variáveis de ambiente.", 
                         color="danger", className="mt-3"), 
                no_update, no_update, no_update
            )
        
        if login_successful:
            print(f"✅ LOGIN PROCESSADO COM SUCESSO para: {username}")
            
            # Dados simples de autenticação com timestamp para evitar reprocessamento
            auth_data = {
                'authenticated': True,
                'session_token': f'test_token_{username}_{int(datetime.now().timestamp())}',
                'login_time': str(datetime.now()),
                'username': username,
                'login_processed': True  # Flag para evitar reprocessamento
            }
            
            user_data = {
                'username': username,
                'full_name': 'Admin User' if username == 'admin' else 'Environment Admin',
                'email': f'{username}@localhost.com',
                'login_timestamp': int(datetime.now().timestamp())
            }
            
            # Redirecionar para dashboard
            print(f"🚀 Redirecionando usuário {username} para dashboard")
            return no_update, auth_data, user_data, '/'
        else:
            print(f"❌ TESTE - Login falhou para: {username}")
            alert = dbc.Alert(
                [
                    html.I(className="fas fa-times-circle me-2"),
                    "Usuário ou senha incorretos."
                ],
                color="danger",
                dismissable=True
            )
            return alert, no_update, no_update, no_update
    
    @app.callback(
        [Output('logout-redirect', 'pathname', allow_duplicate=True),
         Output('auth-store', 'data', allow_duplicate=True),
         Output('user-data', 'data', allow_duplicate=True)],
        [Input('logout-menu', 'n_clicks')],
        [State('auth-store', 'data')],
        prevent_initial_call=True
    )
    def handle_logout(n_clicks, auth_data):
        """Processar logout"""
        if n_clicks == 0:
            return no_update, no_update, no_update
        
        try:
            if auth_data and auth_data.get('session_token'):
                from app.services.auth_manager import SyncAuthManager
                SyncAuthManager.logout_session_sync(auth_data['session_token'])
            
            # Limpar dados de autenticação
            return '/login', {}, {}
            
        except Exception as e:
            logger.info(f"Erro no logout: {e}")
            return '/login', {}, {}
    
    @app.callback(
        Output('user-display-name', 'children'),
        [Input('user-data', 'data')]
    )
    def update_user_display(user_data):
        """Atualizar nome do usuário na interface"""
        if user_data and user_data.get('full_name'):
            return user_data['full_name'].split()[0]  # Primeiro nome
        return "Admin"


def check_authentication(auth_data):
    """Verificar se o usuário está autenticado"""
    if not auth_data or not auth_data.get('authenticated'):
        return False
    
    session_token = auth_data.get('session_token')
    if not session_token:
        return False
    
    try:
        from app.services.auth_manager import SyncAuthManager
        user_data = SyncAuthManager.validate_session_sync(session_token)
        return user_data is not None
    except Exception as e:
        logger.info(f"Erro na validação de sessão: {e}")
        return False


def require_auth(auth_data):
    """Decorator para páginas que requerem autenticação"""
    if not check_authentication(auth_data):
        return create_login_page()
    return None  # Continuar com a página normal
