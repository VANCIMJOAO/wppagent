#!/usr/bin/env python3
"""
Dashboard sem Rate Limiting - Versão de Debug
==============================================

Esta é uma versão simplificada do dashboard sem rate limiting
para testar se o problema de loop é causado pelo sistema de autenticação
ou pelo rate limiting.
"""

import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import sys

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações básicas
from app.components.auth import create_login_page

print("🚀 DASHBOARD DEBUG - SEM RATE LIMITING")

# 🚀 DASHBOARD SIMPLES
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "WhatsApp Agent • Debug Dashboard"

# Layout simples
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='auth-store', storage_type='session'),
    dcc.Store(id='user-data', storage_type='session'),
    html.Div(id='main-content-wrapper'),
    html.Div(id='login-redirect', style={'display': 'none'})
])

# Callback principal
@callback(
    Output('main-content-wrapper', 'children'),
    [Input('url', 'pathname'),
     Input('auth-store', 'data')],
    prevent_initial_call=True
)
def display_page(pathname, auth_data):
    """Controlar exibição da página"""
    print(f"🔄 Callback principal: pathname={pathname}, auth={bool(auth_data)}")
    
    # Verificar autenticação
    if not auth_data or not auth_data.get('authenticated'):
        print("❌ Não autenticado, mostrando login")
        return create_login_page()
    
    # Dashboard simples
    print("✅ Autenticado, mostrando dashboard")
    return html.Div([
        dbc.Container([
            html.H1("🎉 Dashboard Funcionando!", className="text-center mb-4"),
            html.P(f"Bem-vindo, {auth_data.get('username', 'Usuário')}!", className="text-center"),
            dbc.Button("Logout", id="logout-btn", color="danger", className="mt-3")
        ])
    ])

# Callback de autenticação simples
@callback(
    [Output('auth-store', 'data'),
     Output('login-redirect', 'children')],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('auth-store', 'data')],
    prevent_initial_call=True
)
def handle_login_debug(n_clicks, username, password, current_auth):
    """Processar login - versão debug"""
    
    # Evitar reprocessamento se já autenticado
    if current_auth and current_auth.get('authenticated'):
        print(f"⚠️ Já autenticado como {current_auth.get('username')}, ignorando")
        return no_update, no_update
    
    # Verificar se é um clique válido
    if not n_clicks or n_clicks <= 0:
        return no_update, no_update
    
    print(f"🔐 DEBUG - Processando login: {username}")
    
    # Validar credenciais
    if username in ['admin', 'admin_env'] and password in ['admin123', 'lubNAN7MHC1vL77CFhrV27Zb']:
        print(f"✅ DEBUG - Login bem-sucedido: {username}")
        
        auth_data = {
            'authenticated': True,
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'session_id': f"debug_{int(datetime.now().timestamp())}"
        }
        
        return auth_data, no_update
    else:
        print(f"❌ DEBUG - Login falhou: {username}")
        return no_update, html.Div("Login falhou!", style={'color': 'red'})

# Callback de logout
@callback(
    Output('auth-store', 'data', allow_duplicate=True),
    [Input('logout-btn', 'n_clicks')],
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """Processar logout"""
    if n_clicks:
        print("🚪 Logout realizado")
        return {}
    return no_update

if __name__ == '__main__':
    print("🌐 Iniciando Dashboard Debug em http://localhost:8051/")
    app.run(debug=True, host='0.0.0.0', port=8051)
