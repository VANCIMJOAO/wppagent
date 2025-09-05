"""
Home Callbacks - Versão Segura (SEM REDIRECIONAMENTOS AUTOMÁTICOS)
===================================================================

Versão temporária sem callbacks que causam redirecionamentos automáticos.
"""

from dash import Input, Output, State, callback, no_update, html, dcc, callback_context
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from datetime import datetime, date, timedelta, timezone
import plotly.graph_objects as go
import plotly.express as px
from dash.exceptions import PreventUpdate

def register_all_home_callbacks(app):
    """
    Função principal para registrar apenas callbacks essenciais da Home.
    SEM callbacks de redirecionamento que causam problemas.
    """
    
    # CALLBACK BÁSICO PARA TESTE (sem redirecionamentos)
    @app.callback(
        Output('home-data', 'data'),
        Input('url', 'pathname'),
        prevent_initial_call=False
    )
    def update_home_data(pathname):
        """Callback básico para testar funcionamento"""
        if pathname in ['/home', '/']:
            return {
                'conversations': 127,
                'users': 284,
                'appointments': 31,
                'messages': 3847,
                'last_update': datetime.now().isoformat()
            }
        return no_update

    # CALLBACK PARA EXIBIR DADOS NOS BOTÕES (sem navegação)
    @app.callback(
        [
            Output('action-nova-conversa', 'style'),
            Output('action-novo-agendamento', 'style'),
            Output('action-novo-cliente', 'style'),
            Output('action-relatorios', 'style')
        ],
        Input('home-data', 'data'),
        prevent_initial_call=False
    )
    def style_action_buttons(data):
        """Estiliza botões de ação sem causar redirecionamentos"""
        base_style = {
            "margin": "5px", 
            "padding": "10px", 
            "border": "none", 
            "borderRadius": "4px", 
            "cursor": "pointer",
            "transition": "all 0.2s ease"
        }
        
        return [
            {**base_style, "background": "#28a745", "color": "white"},
            {**base_style, "background": "#007bff", "color": "white"},
            {**base_style, "background": "#6f42c1", "color": "white"},
            {**base_style, "background": "#fd7e14", "color": "white"}
        ]

    print("✅ HOME callbacks SEGUROS registrados (sem redirecionamentos automáticos)!")
    return True
