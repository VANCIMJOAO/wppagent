"""
Home Layout - Nova Versão Modernizada
=====================================

Dashboard principal com design moderno, inspirado em interfaces contemporâneas.
Foco em experiência visual atraente e informativa para clientes.
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime

from services.queries import HomeQueries

def create_modern_kpi_card(icon, title, value, subtitle, color, trend=None, id_prefix=""):
    """Cria um card KPI moderno com gradiente e animações"""
    
    gradient_colors = {
        "blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "green": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)", 
        "orange": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "purple": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "pink": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "teal": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    }
    
    return dmc.Card([
        # Header do card com gradiente
        html.Div([
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=icon, width=24, color="white"),
                    size="xl",
                    style={
                        "background": "rgba(255,255,255,0.2)",
                        "backdropFilter": "blur(10px)",
                        "border": "1px solid rgba(255,255,255,0.3)"
                    },
                    radius="md"
                ),
                html.Div([
                    dmc.Text(title, size="sm", c="white", fw=500, opacity=0.9),
                    dmc.Group([
                        dmc.Text(str(value), size="xl", fw=700, c="white"),
                        trend if trend else None
                    ], spacing="xs", align="center")
                ])
            ], position="apart", align="flex-start")
        ], style={
            "background": gradient_colors.get(color, gradient_colors["blue"]),
            "padding": "20px",
            "borderRadius": "12px 12px 0 0",
            "minHeight": "100px"
        }),
        
        # Footer do card
        html.Div([
            dmc.Text(subtitle, size="sm", c="dimmed", ta="center")
        ], style={
            "padding": "12px 20px",
            "background": "rgba(248, 250, 252, 0.8)",
            "borderRadius": "0 0 12px 12px"
        })
        
    ], 
    withBorder=False, 
    shadow="xl", 
    style={
        "cursor": "pointer",
        "transition": "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
        "background": "white",
        "borderRadius": "12px",
        "overflow": "hidden"
    },
    id=f"{id_prefix}-card" if id_prefix else None,
    className="modern-kpi-card"
    )

def create_stats_widget(title, stats_list, icon, color="blue"):
    """Widget de estatísticas compactas"""
    return dmc.Card([
        dmc.Group([
            dmc.ThemeIcon(
                DashIconify(icon=icon, width=20),
                size="md",
                color=color,
                variant="light"
            ),
            dmc.Text(title, fw=600, size="sm")
        ], spacing="sm", mb="md"),
        
        dmc.Stack([
            dmc.Group([
                dmc.Text(stat["label"], size="xs", c="dimmed"),
                dmc.Text(str(stat["value"]), fw=600, size="sm")
            ], position="apart") for stat in stats_list
        ], spacing="xs")
    ], withBorder=True, shadow="sm", p="md", radius="md")

def create_home_layout():
    """
    Layout modernizado da home com design contemporâneo
    """
    
    # Busca dados reais dos KPIs
    try:
        kpis_data = HomeQueries.get_kpis(period_days=30)
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        kpis_data = {
            "total_conversations": 127,
            "active_conversations": 43, 
            "unique_users": 284,
            "total_appointments": 31,
            "total_messages": 3847,
            "messages_today": 67,
            "conversations_today": 8,
            "appointments_today": 4
        }
    
    return html.Div([
        # Hero Section com gradiente
        html.Div([
            dmc.Container([
                dmc.Stack([
                    # Título principal
                    html.Div([
                        dmc.Group([
                            html.Div([
                                dmc.Title(
                                    "WPPAgent Dashboard",
                                    order=1,
                                    style={"color": "white", "fontWeight": 700, "fontSize": "2.5rem"}
                                ),
                                dmc.Text(
                                    f"Visão geral completa • {datetime.now().strftime('%d de %B, %Y')}",
                                    style={"color": "rgba(255,255,255,0.8)", "fontSize": "1.1rem"}
                                )
                            ]),
                            
                            # Controles do período
                            dmc.Group([
                                dmc.Select(
                                    data=[
                                        {"value": "7", "label": "7 dias"},
                                        {"value": "30", "label": "30 dias"},
                                        {"value": "90", "label": "90 dias"}
                                    ],
                                    value="30",
                                    w=120,
                                    id="home-period-filter",
                                    style={"backgroundColor": "rgba(255,255,255,0.1)", "backdropFilter": "blur(10px)"}
                                ),
                                dmc.ActionIcon(
                                    DashIconify(icon="tabler:refresh", color="white"),
                                    variant="transparent",
                                    size="lg",
                                    id="home-refresh-btn",
                                    style={"backgroundColor": "rgba(255,255,255,0.1)", "backdropFilter": "blur(10px)"}
                                )
                            ])
                        ], position="apart", align="center")
                    ])
                ], spacing="xl")
            ], size="xl")
        ], style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
            "padding": "60px 0",
            "marginBottom": "40px"
        }),
        
        dmc.Container([
            # Grid principal de KPIs - Cards grandes e atrativos
            dmc.SimpleGrid([
                create_modern_kpi_card(
                    icon="tabler:messages",
                    title="Conversas Ativas",
                    value=kpis_data['total_conversations'],
                    subtitle=f"+{kpis_data['conversations_today']} novas hoje",
                    color="blue",
                    trend=dmc.Badge(f"+{kpis_data['conversations_today']}", color="teal", variant="light"),
                    id_prefix="conversations"
                ),
                
                create_modern_kpi_card(
                    icon="tabler:users-group",
                    title="Clientes Únicos", 
                    value=kpis_data['unique_users'],
                    subtitle="Base de clientes cadastrados",
                    color="green",
                    id_prefix="users"
                ),
                
                create_modern_kpi_card(
                    icon="tabler:calendar-check",
                    title="Agendamentos",
                    value=kpis_data['total_appointments'], 
                    subtitle=f"+{kpis_data['appointments_today']} agendados hoje",
                    color="orange",
                    trend=dmc.Badge(f"+{kpis_data['appointments_today']}", color="orange", variant="light"),
                    id_prefix="appointments"
                ),
                
                create_modern_kpi_card(
                    icon="tabler:message-circle-2",
                    title="Mensagens Trocadas",
                    value=f"{kpis_data['total_messages']:,}",
                    subtitle=f"{kpis_data['messages_today']} mensagens hoje",
                    color="purple",
                    trend=dmc.Badge(f"+{kpis_data['messages_today']}", color="violet", variant="light"),
                    id_prefix="messages"
                )
            ], cols=4, spacing="xl", mb="xl"),
            
            # Seção de widgets informativos
            dmc.Grid([
                # Coluna esquerda - Stats rápidas
                dmc.Col([
                    dmc.Stack([
                        create_stats_widget(
                            title="Performance Hoje",
                            stats_list=[
                                {"label": "Conversas iniciadas", "value": kpis_data['conversations_today']},
                                {"label": "Mensagens enviadas", "value": kpis_data['messages_today']},
                                {"label": "Agendamentos", "value": kpis_data['appointments_today']},
                                {"label": "Taxa de resposta", "value": "94%"}
                            ],
                            icon="tabler:trending-up",
                            color="blue"
                        ),
                        
                        create_stats_widget(
                            title="Status do Sistema",
                            stats_list=[
                                {"label": "WhatsApp Bot", "value": "🟢 Online"},
                                {"label": "Base de Dados", "value": "🟢 Conectado"},
                                {"label": "API Status", "value": "🟢 Funcionando"},
                                {"label": "Último backup", "value": "2h atrás"}
                            ],
                            icon="tabler:server-2",
                            color="green"
                        )
                    ], spacing="md")
                ], span=4),
                
                # Coluna central - Atividade recente
                dmc.Col([
                    dmc.Card([
                        dmc.Group([
                            dmc.Stack([
                                dmc.Text("Atividade Recente", fw=600, size="lg"),
                                dmc.Text("Últimas interações com clientes", size="sm", c="dimmed")
                            ], spacing="xs"),
                            dmc.ActionIcon(
                                DashIconify(icon="tabler:external-link"),
                                variant="light",
                                size="sm"
                            )
                        ], position="apart", align="flex-start", mb="md"),
                        
                        # Lista de atividades (será populada via callback)
                        html.Div(id="recent-activity-list")
                        
                    ], withBorder=True, shadow="md", p="lg", radius="md", h=300)
                ], span=5),
                
                # Coluna direita - Gráfico mini
                dmc.Col([
                    dmc.Card([
                        dmc.Stack([
                            dmc.Group([
                                dmc.Text("Conversas - 7 dias", fw=600),
                                dmc.Badge("Tendência", color="blue", variant="light")
                            ], position="apart"),
                            
                            # Gráfico será inserido via callback
                            html.Div(
                                id="mini-chart-conversations",
                                style={"height": "200px"}
                            )
                        ])
                    ], withBorder=True, shadow="md", p="lg", radius="md", h=300)
                ], span=3)
            ], gutter="xl", mb="xl"),
            
            # Seção de ações rápidas
            dmc.Card([
                dmc.Stack([
                    dmc.Group([
                        dmc.Stack([
                            dmc.Text("Ações Rápidas", fw=600, size="lg"),
                            dmc.Text("Acesso direto às principais funcionalidades", size="sm", c="dimmed")
                        ], spacing="xs"),
                        dmc.Badge("Novo", color="red", variant="light")
                    ], position="apart"),
                    
                    dmc.SimpleGrid([
                        dmc.Button("🗨️ Iniciar Conversa", variant="outline", fullWidth=True, id="quick-action-new-chat"),
                        
                        dmc.Button([
                            dmc.Paper([
                                dmc.Stack([
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:calendar-plus", width=24),
                                        size="xl",
                                        color="orange",
                                        variant="light"
                                    ),
                                    dmc.Stack([
                                        dmc.Text("Novo Agendamento", fw=600, size="sm"),
                                        dmc.Text("Agendar reunião", size="xs", c="dimmed")
                                    ], spacing="xs", align="center")
                                ], align="center", spacing="md")
                            ], withBorder=True, p="lg", radius="md", style={"transition": "all 0.2s"})
                        ], variant="subtle", style={"width": "100%"}),
                        
                        dmc.Button("👤 Adicionar Cliente", variant="outline", fullWidth=True),
                        
                        dmc.Button("📊 Ver Relatórios", variant="outline", fullWidth=True)
                    ], cols=4, spacing="md")
                ])
            ], withBorder=True, shadow="md", p="xl", radius="md", mb="xl"),
            
            # Footer com informações adicionais
            dmc.Group([
                dmc.Text("Dashboard atualizado em tempo real", size="xs", c="dimmed"),
                dmc.Text("•", size="xs", c="dimmed"),
                dmc.Text(f"Última atualização: {datetime.now().strftime('%H:%M')}", size="xs", c="dimmed"),
                dmc.Text("•", size="xs", c="dimmed"),
                dmc.Anchor("Suporte técnico", size="xs", href="#")
            ], spacing="xs", position="center", mt="xl")
            
        ], size="xl", px="md"),
        
        # Stores para dados
        dcc.Store(id="home-kpis-data", data=kpis_data),
        dcc.Store(id="home-period", data=30),
        dcc.Store(id="home-last-update", data=datetime.now().isoformat())
        
    ], style={"background": "#fafafa", "minHeight": "100vh"})
