"""
Callbacks de Autenticação
=========================

Callbacks para login, logout e gestão de sessões.
"""

from dash import Input, Output, State, callback_context, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from .auth_service import AuthService
from .models import UserRole

def register_auth_callbacks(app):
    """Registra todos os callbacks de autenticação"""
    auth_service = AuthService()
    
    @app.callback(
        [Output('login-alert', 'children'),
         Output('login-alert', 'title'),
         Output('login-alert', 'style'),
         Output('session-store', 'data'),
         Output('url', 'pathname')],
        Input('login-button', 'n_clicks'),
        [State('login-email', 'value'),
         State('login-password', 'value'),
         State('login-remember', 'checked')],
        prevent_initial_call=True
    )
    def handle_login(n_clicks, email, password, remember_me):
        """Processa tentativa de login"""
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update
        
        if not email or not password:
            return (
                "Por favor, preencha todos os campos.",
                "Campos obrigatórios",
                {"display": "block"},
                no_update,
                no_update
            )
        
        try:
            # Tenta autenticar
            user, session_id = auth_service.authenticate(email, password, "127.0.0.1")
            
            # Guarda dados da sessão
            session_data = {
                'session_id': session_id,
                'user': user.to_dict(),
                'remember_me': remember_me or False
            }
            
            return (
                no_update,
                no_update,
                {"display": "none"},
                session_data,
                '/home'  # Redireciona para home
            )
        
        except Exception as e:
            return (
                str(e),
                "Erro no login",
                {"display": "block"},
                no_update,
                no_update
            )
    
    @app.callback(
        [Output('session-store', 'data', allow_duplicate=True),
         Output('url', 'pathname', allow_duplicate=True)],
        Input('logout-button', 'n_clicks'),
        State('session-store', 'data'),
        prevent_initial_call=True
    )
    def handle_logout(n_clicks, session_data):
        """Processa logout do usuário"""
        if not n_clicks or not session_data:
            return no_update, no_update
        
        try:
            session_id = session_data.get('session_id')
            if session_id:
                auth_service.logout(session_id)
            
            return None, '/login'
        
        except Exception as e:
            print(f"Erro no logout: {e}")
            return None, '/login'
    
    @app.callback(
        [Output('page-content', 'children', allow_duplicate=True),
         Output('url', 'pathname', allow_duplicate=True)],
        Input('session-expired-login', 'n_clicks'),
        prevent_initial_call=True
    )
    def redirect_to_login_from_expired(n_clicks):
        """Redireciona para login quando sessão expira"""
        if n_clicks:
            return no_update, '/login'
        return no_update, no_update
    
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True)],
        Input('access-denied-home', 'n_clicks'),
        prevent_initial_call=True
    )
    def redirect_to_home_from_denied(n_clicks):
        """Redireciona para home quando acesso negado"""
        if n_clicks:
            return '/home'
        return no_update
    
    # Callbacks opcionais para componentes de usuário (se existirem na interface)
    try:
        @app.callback(
            [Output('current-user-info', 'children')],
            Input('session-store', 'data'),
            prevent_initial_call=True
        )
        def update_user_info_display(session_data):
            """Atualiza informações do usuário logado na interface"""
            if not session_data or not session_data.get('user'):
                return ["Usuário não autenticado"]
            
            user_data = session_data['user']
            
            return [
                dmc.Group([
                    dmc.Avatar(
                        src=user_data.get('avatar_url'),
                        size="sm",
                        radius="xl"
                    ),
                    dmc.Stack([
                        dmc.Text(user_data.get('name', 'Usuário'), size="sm", fw=500),
                        dmc.Text(user_data.get('role', '').replace('_', ' ').title(), size="xs", c="dimmed")
                    ], spacing=0, align="flex-start")
                ])
            ]
    except:
        # Callback opcional - não falha se componente não existir
        pass
    
    try:
        @app.callback(
            Output('user-role-badge', 'children'),
            Input('session-store', 'data'),
            prevent_initial_call=True
        )
        def update_user_role_badge(session_data):
            """Atualiza badge de role do usuário"""
            if not session_data or not session_data.get('user'):
                return ""
            
            role = session_data['user'].get('role', '')
            
            role_colors = {
                'super_admin': 'red',
                'admin': 'blue',
                'manager': 'green',
                'operator': 'orange',
                'viewer': 'gray'
            }
            
            return dmc.Badge(
                role.replace('_', ' ').title(),
                color=role_colors.get(role, 'gray'),
                size="xs"
            )
    except:
        # Callback opcional - não falha se componente não existir
        pass
    
    # Callback para verificar sessão periodicamente
    @app.callback(
        [Output('session-store', 'data', allow_duplicate=True),
         Output('url', 'pathname', allow_duplicate=True)],
        Input('session-check-interval', 'n_intervals'),
        State('session-store', 'data'),
        prevent_initial_call=True
    )
    def check_session_validity(n_intervals, session_data):
        """Verifica se a sessão ainda é válida"""
        if not session_data or not session_data.get('session_id'):
            return no_update, no_update
        
        try:
            user = auth_service.get_user_by_session(session_data['session_id'])
            if not user:
                # Sessão inválida ou expirada
                return None, '/session-expired'
            
            return no_update, no_update
        
        except Exception as e:
            print(f"Erro ao verificar sessão: {e}")
            return None, '/login'
