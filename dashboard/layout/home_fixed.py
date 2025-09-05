"""
Layout Home Corrigido - Sem erros de componentes None
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime

def create_modern_kpi_card_safe(icon, title, value, subtitle, color, trend=None, id_prefix=""):
    """Cria card KPI com verificação de segurança"""
    
    # Garantir que todos os valores são válidos
    icon = icon or "tabler:help-circle"
    title = str(title) if title is not None else "N/A"
    value = str(value) if value is not None else "0"
    subtitle = str(subtitle) if subtitle is not None else ""
    color = color or "blue"
    
    gradient_colors = {
        "blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "green": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)", 
        "orange": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "purple": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    }
    
    return dmc.Card([
        # Header do card
        html.Div([
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=icon, width=24),
                    size="xl",
                    color="white",
                    variant="filled"
                ),
                html.Div([
                    dmc.Text(title, size="sm", c="white", fw=500),
                    dmc.Text(value, size="xl", fw=700, c="white")
                ])
            ], position="apart", align="flex-start")
        ], style={
            "background": gradient_colors.get(color, gradient_colors["blue"]),
            "padding": "20px",
            "borderRadius": "12px 12px 0 0"
        }),
        
        # Footer do card  
        html.Div([
            dmc.Text(subtitle, size="sm", c="dimmed", ta="center")
        ], style={
            "padding": "12px 20px",
            "background": "#f8fafc",
            "borderRadius": "0 0 12px 12px"
        })
    ], 
    withBorder=False,
    shadow="md",
    className="kpi-card-safe",
    id=f"{id_prefix}-card" if id_prefix else None
    )

def create_home_layout_safe():
    """Layout home com proteção contra componentes None"""
    
    # Dados seguros para KPIs
    safe_kpis = {
        'total_conversations': 127,
        'unique_users': 284, 
        'total_appointments': 31,
        'total_messages': 3847,
        'messages_today': 67,
        'conversations_today': 8,
        'appointments_today': 4
    }
    
    return html.Div([
        # Hero Section
        html.Div([
            dmc.Container([
                dmc.Group([
                    html.Div([
                        dmc.Title("WPPAgent Dashboard", order=1, c="white"),
                        dmc.Text(
                            f"Visão geral • {datetime.now().strftime('%d/%m/%Y')}",
                            c="white", 
                            opacity=0.9
                        )
                    ]),
                    dmc.Select(
                        data=[
                            {"value": "7", "label": "7 dias"},
                            {"value": "30", "label": "30 dias"},
                            {"value": "90", "label": "90 dias"}
                        ],
                        value="30",
                        id="home-period-filter",
                        w=120
                    )
                ], position="apart", align="center")
            ], size="xl")
        ], style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "padding": "40px 0",
            "marginBottom": "30px"
        }),
        
        # KPIs Grid
        dmc.Container([
            dmc.SimpleGrid([
                create_modern_kpi_card_safe(
                    icon="tabler:message-circle-2",
                    title="Conversas Ativas",
                    value=safe_kpis['total_conversations'],
                    subtitle=f"+{safe_kpis['conversations_today']} hoje",
                    color="blue",
                    id_prefix="conversations"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:users-group",
                    title="Clientes Únicos",
                    value=safe_kpis['unique_users'],
                    subtitle="Base de clientes",
                    color="green",
                    id_prefix="users"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:calendar-check",
                    title="Agendamentos",
                    value=safe_kpis['total_appointments'],
                    subtitle=f"+{safe_kpis['appointments_today']} hoje",
                    color="orange",
                    id_prefix="appointments"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:message-dots",
                    title="Mensagens",
                    value=f"{safe_kpis['total_messages']:,}",
                    subtitle=f"{safe_kpis['messages_today']} hoje",
                    color="purple",
                    id_prefix="messages"
                )
            ], cols=4, spacing="lg", mb="xl"),
            
            # Seção de widgets
            dmc.Grid([
                # Performance
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Performance Hoje", fw=600, mb="md"),
                        dmc.Stack([
                            dmc.Group([
                                dmc.Text("Conversas iniciadas", size="sm"),
                                dmc.Text(str(safe_kpis['conversations_today']), fw=600)
                            ], position="apart"),
                            dmc.Group([
                                dmc.Text("Mensagens enviadas", size="sm"),
                                dmc.Text(str(safe_kpis['messages_today']), fw=600)
                            ], position="apart"),
                            dmc.Group([
                                dmc.Text("Taxa de resposta", size="sm"),
                                dmc.Text("94%", fw=600, c="green")
                            ], position="apart")
                        ])
                    ], withBorder=True, p="md")
                ], span=4),
                
                # Atividade Recente
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Atividade Recente", fw=600, mb="md"),
                        html.Div([
                            dmc.Text(
                                "Nenhuma atividade recente", 
                                size="sm", 
                                c="dimmed",
                                ta="center"
                            )
                        ], id="recent-activity-list")
                    ], withBorder=True, p="md")
                ], span=4),
                
                # Gráfico
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Conversas - 7 dias", fw=600, mb="md"),
                        html.Div(
                            dmc.Text("Carregando gráfico...", ta="center"),
                            id="mini-chart-conversations"
                        )
                    ], withBorder=True, p="md")
                ], span=4)
            ], gutter="md", mb="xl"),
            
            # Ações Rápidas
            dmc.Card([
                dmc.Text("Ações Rápidas", fw=600, mb="md"),
                dmc.SimpleGrid([
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:message-plus", width=24),
                                size="xl",
                                color="green",
                                variant="light"
                            ),
                            dmc.Text("Nova Conversa", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-nova-conversa"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:calendar-plus", width=24),
                                size="xl",
                                color="blue",
                                variant="light"
                            ),
                            dmc.Text("Novo Agendamento", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-novo-agendamento"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:user-plus", width=24),
                                size="xl",
                                color="violet",
                                variant="light"
                            ),
                            dmc.Text("Adicionar Cliente", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-adicionar-cliente"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:chart-line", width=24),
                                size="xl",
                                color="orange",
                                variant="light"
                            ),
                            dmc.Text("Ver Relatórios", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-ver-relatorios")
                ], cols=4, spacing="md")
            ], withBorder=True, p="lg", mb="xl")
            
        ], size="xl"),
        
        # Stores
        dcc.Store(id="home-kpis-data", data=safe_kpis),
        dcc.Store(id="home-period", data=30)
        
    ], style={"background": "#fafafa", "minHeight": "100vh"})
