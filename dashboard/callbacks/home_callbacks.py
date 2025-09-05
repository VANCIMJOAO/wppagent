"""
Home Callbacks - Versão Elegante e Funcional (SEM REDIRECIONAMENTOS AUTOMÁTICOS)
================================================================================

Mantém a funcionalidade original mas remove os callbacks problemáticos
que causavam redirecionamentos automáticos.
"""

from dash import Input, Output, State, callback, no_update, html, dcc, callback_context
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from datetime import datetime, date, timedelta, timezone
from dash.exceptions import PreventUpdate

def register_all_home_callbacks(app):
    """
    Registra callbacks funcionais da Home SEM redirecionamentos automáticos.
    """
    
    # CALLBACK PARA ATUALIZAR KPIs (sem problemas)
    @app.callback(
        Output('home-kpis-data', 'data'),
        Input('home-period-filter', 'value'),
        prevent_initial_call=False
    )
    def update_kpis_data(period_days):
        """Atualiza dados dos KPIs baseado no período selecionado"""
        try:
            period_days = int(period_days) if period_days else 30
            
            # Dados simulados baseados no período
            base_stats = {
                'total_conversations': 127,
                'unique_users': 284, 
                'total_appointments': 31,
                'total_messages': 3847,
                'messages_today': 67,
                'conversations_today': 8,
                'appointments_today': 4
            }
            
            # Ajustar dados baseado no período (simulação)
            if period_days == 7:
                multiplier = 0.3
            elif period_days == 30:
                multiplier = 1.0
            else:  # 90 dias
                multiplier = 2.8
            
            adjusted_stats = {
                'total_conversations': int(base_stats['total_conversations'] * multiplier),
                'unique_users': int(base_stats['unique_users'] * multiplier),
                'total_appointments': int(base_stats['total_appointments'] * multiplier),
                'total_messages': int(base_stats['total_messages'] * multiplier),
                'messages_today': base_stats['messages_today'],  # Hoje sempre igual
                'conversations_today': base_stats['conversations_today'],
                'appointments_today': base_stats['appointments_today'],
                'period_days': period_days,
                'last_update': datetime.now().isoformat()
            }
            
            return adjusted_stats
            
        except Exception as e:
            print(f"Erro ao atualizar KPIs: {e}")
            return {
                'total_conversations': 127,
                'unique_users': 284,
                'total_appointments': 31,
                'total_messages': 3847,
                'messages_today': 67,
                'conversations_today': 8,
                'appointments_today': 4,
                'period_days': 30
            }

    # CALLBACK PARA ATUALIZAR VALORES DOS CARDS KPI
    @app.callback(
        [
            Output("kpi-conversations", "children"),
            Output("kpi-users", "children"),
            Output("kpi-appointments", "children"),
            Output("kpi-messages", "children")
        ],
        Input('home-kpis-data', 'data'),
        prevent_initial_call=False
    )
    def update_kpi_values(kpis_data):
        """Atualiza os valores exibidos nos cards KPI"""
        try:
            if not kpis_data:
                return ["--", "--", "--", "--"]
            
            conversations = str(kpis_data.get('total_conversations', 127))
            users = str(kpis_data.get('unique_users', 284))
            appointments = str(kpis_data.get('total_appointments', 31))
            messages = f"{kpis_data.get('total_messages', 3847):,}".replace(",", ".")
            
            return [conversations, users, appointments, messages]
            
        except Exception as e:
            print(f"Erro ao atualizar valores KPI: {e}")
            return ["Erro", "Erro", "Erro", "Erro"]

    # CALLBACK PARA ATIVIDADE RECENTE (funcional)
    @app.callback(
        Output("recent-activity-list", "children"),
        Input('home-kpis-data', 'data'),
        prevent_initial_call=False
    )
    def update_recent_activity(kpis_data):
        """Atualiza lista de atividades recentes"""
        try:
            # Atividades simuladas realistas
            activities = [
                {
                    "icon": "tabler:message",
                    "color": "blue",
                    "title": "Nova conversa iniciada",
                    "time": "2 min atrás"
                },
                {
                    "icon": "tabler:calendar",
                    "color": "green", 
                    "title": "Agendamento confirmado",
                    "time": "15 min atrás"
                },
                {
                    "icon": "tabler:user-plus",
                    "color": "orange",
                    "title": "Novo cliente cadastrado", 
                    "time": "1 hora atrás"
                }
            ]
            
            activity_items = []
            for activity in activities:
                item = dmc.Group(
                    children=[
                        dmc.ThemeIcon(
                            DashIconify(icon=activity["icon"]), 
                            size="sm",
                            color=activity["color"],
                            variant="light"
                        ),
                        html.Div(
                            children=[
                                dmc.Text(activity["title"], size="sm", fw=500),
                                dmc.Text(activity["time"], size="xs", c="dimmed")
                            ]
                        )
                    ],
                    spacing="sm"
                )
                activity_items.append(item)
            
            return dmc.Stack(children=activity_items, spacing="sm")
            
        except Exception as e:
            print(f"Erro ao carregar atividades: {e}")
            return dmc.Text("Nenhuma atividade recente", size="sm", c="dimmed")

    # CALLBACK PARA HOVER DOS BOTÕES (efeito visual)
    @app.callback(
        [
            Output('action-nova-conversa', 'style'),
            Output('action-novo-agendamento', 'style'),
            Output('action-adicionar-cliente', 'style'),
            Output('action-ver-relatorios', 'style')
        ],
        Input('home-kpis-data', 'data'),
        prevent_initial_call=False
    )
    def style_action_buttons(kpis_data):
        """Mantém estilo dos botões de ação sem causar redirecionamentos"""
        
        base_style = {
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "borderRadius": "8px"
        }
        
        return [base_style, base_style, base_style, base_style]

    # CALLBACK PARA STATUS DO SISTEMA (indicador)
    @app.callback(
        Output('home-refresh-trigger', 'data'),
        Input('url', 'pathname'),
        prevent_initial_call=False
    )
    def system_health_check(pathname):
        """Simula verificação de saúde do sistema"""
        if pathname in ['/home', '/']:
            return datetime.now().timestamp()
        return no_update

    print("✅ HOME callbacks ELEGANTES registrados (sem redirecionamentos automáticos)!")
    return True
