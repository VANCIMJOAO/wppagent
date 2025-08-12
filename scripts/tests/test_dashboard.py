#!/usr/bin/env python3
"""Dashboard simples para teste de login"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import asyncio
import sys
import os

# Adicionar caminho do projeto
sys.path.append('/home/vancim/whats_agent')

# Configurar app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout simples
app.layout = dbc.Container([
    html.H1("🔐 Login Teste", className="text-center mb-4"),
    
    dbc.Card([
        dbc.CardBody([
            html.Div(id="alert-msg"),
            
            dbc.Input(
                id="username",
                placeholder="Username",
                value="admin_env",
                className="mb-3"
            ),
            
            dbc.Input(
                id="password",
                type="password",
                placeholder="Password", 
                value="lubNAN7MHC1vL77CFhrV27Zb",
                className="mb-3"
            ),
            
            dbc.Button(
                "LOGIN",
                id="login-btn",
                color="primary",
                className="w-100",
                n_clicks=0
            ),
            
            html.Hr(),
            html.Div(id="debug-info")
        ])
    ], style={"max-width": "400px", "margin": "auto"})
])

@app.callback(
    [Output('alert-msg', 'children'),
     Output('debug-info', 'children')],
    [Input('login-btn', 'n_clicks')],
    [State('username', 'value'),
     State('password', 'value')]
)
def handle_login(n_clicks, username, password):
    debug_msg = f"Cliques: {n_clicks}, User: {username}, Pass: {'*' * len(password) if password else 'None'}"
    
    if n_clicks == 0:
        return "", debug_msg
    
    print(f"🔍 TESTE - Login tentado: n_clicks={n_clicks}, username={username}")
    
    if username == "admin_env" and password == "lubNAN7MHC1vL77CFhrV27Zb":
        alert = dbc.Alert("✅ LOGIN SUCESSO!", color="success")
        return alert, debug_msg
    else:
        alert = dbc.Alert("❌ LOGIN FALHOU!", color="danger") 
        return alert, debug_msg

if __name__ == '__main__':
    print("🚀 Iniciando dashboard de teste na porta 8052...")
    app.run(debug=True, host='0.0.0.0', port=8052)
