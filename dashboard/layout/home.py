"""
Home Layout - Versão Elegante e Segura
======================================

Mantém o design original bonito mas com correções de segurança
para evitar erros '_dashprivate_layout'.
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime

def safe_children(children_list):
    """Garante que lista de children não contém None"""
    if not children_list:
        return []
    if isinstance(children_list, list):
        return [child for child in children_list if child is not None]
    return [children_list] if children_list is not None else []

def create_modern_kpi_card_safe(icon, title, value, subtitle, color, id_prefix=""):
    """Cria card KPI moderno e seguro - versão corrigida"""
    
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
    
    return dmc.Card(
        children=[
            # Header do card
            html.Div(
                children=[
                    dmc.Group(
                        children=[
                            dmc.ThemeIcon(
                                DashIconify(icon=icon, width=24),
                                size="xl",
                                color="white",
                                style={
                                    "background": "rgba(255,255,255,0.2)",
                                    "backdropFilter": "blur(10px)",
                                    "border": "1px solid rgba(255,255,255,0.3)"
                                },
                                radius="md"
                            ),
                            html.Div(
                                children=[
                                    dmc.Text(title, size="sm", c="white", fw=500, opacity=0.9),
                                    dmc.Text(value, size="xl", fw=700, c="white", id=f"kpi-{id_prefix}" if id_prefix else None)
                                ]
                            )
                        ],
                        position="apart",
                        align="flex-start"
                    )
                ],
                style={
                    "background": gradient_colors.get(color, gradient_colors["blue"]),
                    "padding": "20px",
                    "borderRadius": "12px 12px 0 0",
                    "minHeight": "100px"
                }
            ),
            
            # Footer do card  
            html.Div(
                children=[
                    dmc.Text(subtitle, size="sm", c="dimmed", ta="center")
                ],
                style={
                    "padding": "12px 20px",
                    "background": "#f8fafc",
                    "borderRadius": "0 0 12px 12px"
                }
            )
        ],
        withBorder=False,
        shadow="md",
        className=f"kpi-card-{id_prefix}" if id_prefix else "kpi-card-safe",
        id=f"{id_prefix}-card" if id_prefix else None
    )

def create_safe_stats_grid(stats_data):
    """Grid de estatísticas seguro mantendo design original"""
    
    # Dados padrão
    if not stats_data or not isinstance(stats_data, dict):
        stats_data = {
            'total_conversations': 127,
            'unique_users': 284, 
            'total_appointments': 31,
            'total_messages': 3847,
            'messages_today': 67,
            'conversations_today': 8,
            'appointments_today': 4
        }
    
    # Criar cards individuais
    cards = [
        create_modern_kpi_card_safe(
            icon="tabler:message-circle-2",
            title="Conversas Ativas",
            value=stats_data.get('total_conversations', 127),
            subtitle=f"+{stats_data.get('conversations_today', 8)} hoje",
            color="blue",
            id_prefix="conversations"
        ),
        create_modern_kpi_card_safe(
            icon="tabler:users-group", 
            title="Clientes Únicos",
            value=stats_data.get('unique_users', 284),
            subtitle="Base de clientes",
            color="green",
            id_prefix="users"
        ),
        create_modern_kpi_card_safe(
            icon="tabler:calendar-check",
            title="Agendamentos", 
            value=stats_data.get('total_appointments', 31),
            subtitle=f"+{stats_data.get('appointments_today', 4)} hoje",
            color="orange",
            id_prefix="appointments"
        ),
        create_modern_kpi_card_safe(
            icon="tabler:message-dots",
            title="Mensagens",
            value=f"{stats_data.get('total_messages', 3847):,}".replace(",", "."),
            subtitle=f"{stats_data.get('messages_today', 67)} hoje",
            color="purple",
            id_prefix="messages"
        )
    ]
    
    # Filtrar None e retornar apenas cards válidos
    return [card for card in cards if card is not None]

def create_action_button_safe(icon, label, color, action_id):
    """Botão de ação seguro mantendo design original"""
    
    try:
        return dmc.Paper(
            children=[
                dmc.Stack(
                    children=[
                        dmc.ThemeIcon(
                            DashIconify(icon=icon or "tabler:help-circle", width=24),
                            size="xl",
                            color=color or "blue",
                            variant="light"
                        ),
                        dmc.Text(
                            str(label) if label else "Ação", 
                            fw=600, 
                            size="sm", 
                            ta="center"
                        )
                    ],
                    align="center",
                    spacing="sm"
                )
            ],
            withBorder=True,
            p="md",
            className="action-card hover-effect",
            id=action_id or "default-action",
            style={
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "borderRadius": "8px"
            }
        )
    except Exception:
        # Fallback simples
        return html.Div(
            children=[
                html.Button(
                    str(label) if label else "Ação",
                    id=action_id or "default-action",
                    style={
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "8px",
                        "background": "#007bff",
                        "color": "white",
                        "cursor": "pointer"
                    }
                )
            ]
        )

def create_elegant_home_layout():
    """Layout home elegante e seguro"""
    
    default_stats = {
        'total_conversations': 127,
        'unique_users': 284, 
        'total_appointments': 31,
        'total_messages': 3847,
        'messages_today': 67,
        'conversations_today': 8,
        'appointments_today': 4
    }
    
    return html.Div(
        children=[
            # Hero Section com gradiente elegante
            html.Div(
                children=[
                    dmc.Container(
                        children=[
                            dmc.Group(
                                children=[
                                    html.Div(
                                        children=[
                                            dmc.Title("WPPAgent Dashboard", order=1, c="white"),
                                            dmc.Text(
                                                f"Visão geral • {datetime.now().strftime('%d/%m/%Y')}", 
                                                c="white", 
                                                opacity=0.9
                                            )
                                        ]
                                    ),
                                    dmc.Select(
                                        data=[
                                            {"value": "7", "label": "7 dias"},
                                            {"value": "30", "label": "30 dias"},
                                            {"value": "90", "label": "90 dias"}
                                        ],
                                        value="30",
                                        id="home-period-filter",
                                        w=120,
                                        style={"background": "white"}
                                    )
                                ],
                                position="apart",
                                align="center"
                            )
                        ],
                        size="xl"
                    )
                ],
                style={
                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "padding": "40px 0",
                    "marginBottom": "30px"
                }
            ),
            
            # Container Principal
            dmc.Container(
                children=[
                    # KPIs Grid - SEGURO com children explícito
                    dmc.SimpleGrid(
                        children=create_safe_stats_grid(default_stats),
                        cols=4,
                        spacing="lg",
                        mb="xl"
                    ),
                    
                    # Seção de Widgets
                    dmc.Grid(
                        children=[
                            # Performance Card
                            dmc.Col(
                                children=[
                                    dmc.Card(
                                        children=[
                                            dmc.Text("Performance Hoje", fw=600, mb="md"),
                                            dmc.Stack(
                                                children=[
                                                    dmc.Group(
                                                        children=[
                                                            dmc.Text("Conversas iniciadas", size="sm"),
                                                            dmc.Text("8", fw=600)
                                                        ],
                                                        position="apart"
                                                    ),
                                                    dmc.Group(
                                                        children=[
                                                            dmc.Text("Mensagens enviadas", size="sm"),
                                                            dmc.Text("67", fw=600)
                                                        ],
                                                        position="apart"
                                                    ),
                                                    dmc.Group(
                                                        children=[
                                                            dmc.Text("Taxa de resposta", size="sm"),
                                                            dmc.Text("94%", fw=600, c="green")
                                                        ],
                                                        position="apart"
                                                    )
                                                ]
                                            )
                                        ],
                                        withBorder=True,
                                        p="md"
                                    )
                                ],
                                span=4
                            ),
                            
                            # Atividade Recente
                            dmc.Col(
                                children=[
                                    dmc.Card(
                                        children=[
                                            dmc.Text("Atividade Recente", fw=600, mb="md"),
                                            html.Div(
                                                children=[
                                                    dmc.Stack(
                                                        children=[
                                                            dmc.Group(
                                                                children=[
                                                                    dmc.ThemeIcon(
                                                                        DashIconify(icon="tabler:message"), 
                                                                        size="sm", 
                                                                        color="blue", 
                                                                        variant="light"
                                                                    ),
                                                                    html.Div(
                                                                        children=[
                                                                            dmc.Text("Nova conversa iniciada", size="sm", fw=500),
                                                                            dmc.Text("2 min atrás", size="xs", c="dimmed")
                                                                        ]
                                                                    )
                                                                ],
                                                                spacing="sm"
                                                            ),
                                                            dmc.Group(
                                                                children=[
                                                                    dmc.ThemeIcon(
                                                                        DashIconify(icon="tabler:calendar"), 
                                                                        size="sm", 
                                                                        color="green", 
                                                                        variant="light"
                                                                    ),
                                                                    html.Div(
                                                                        children=[
                                                                            dmc.Text("Agendamento confirmado", size="sm", fw=500),
                                                                            dmc.Text("15 min atrás", size="xs", c="dimmed")
                                                                        ]
                                                                    )
                                                                ],
                                                                spacing="sm"
                                                            ),
                                                            dmc.Group(
                                                                children=[
                                                                    dmc.ThemeIcon(
                                                                        DashIconify(icon="tabler:user-plus"), 
                                                                        size="sm", 
                                                                        color="orange", 
                                                                        variant="light"
                                                                    ),
                                                                    html.Div(
                                                                        children=[
                                                                            dmc.Text("Novo cliente cadastrado", size="sm", fw=500),
                                                                            dmc.Text("1 hora atrás", size="xs", c="dimmed")
                                                                        ]
                                                                    )
                                                                ],
                                                                spacing="sm"
                                                            )
                                                        ],
                                                        spacing="sm"
                                                    )
                                                ],
                                                id="recent-activity-list"
                                            )
                                        ],
                                        withBorder=True,
                                        p="md"
                                    )
                                ],
                                span=4
                            ),
                            
                            # Chart Widget
                            dmc.Col(
                                children=[
                                    dmc.Card(
                                        children=[
                                            dmc.Group(
                                                children=[
                                                    dmc.Text("Conversas - 7 dias", fw=600, size="md"),
                                                    dmc.ActionIcon(
                                                        DashIconify(icon="tabler:refresh"),
                                                        variant="subtle",
                                                        id="chart-refresh"
                                                    )
                                                ],
                                                position="apart"
                                            ),
                                            html.Div(
                                                children=[
                                                    # Mini gráfico de barras CSS
                                                    html.Div(
                                                        children=[
                                                            html.Div(style={"width": "12px", "height": "30px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "45px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "60px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "40px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "55px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "35px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"}),
                                                            html.Div(style={"width": "12px", "height": "50px", "backgroundColor": "#667eea", "margin": "4px", "borderRadius": "4px", "display": "inline-block"})
                                                        ],
                                                        style={
                                                            "display": "flex",
                                                            "alignItems": "flex-end", 
                                                            "justifyContent": "center",
                                                            "height": "150px",
                                                            "paddingTop": "70px"
                                                        }
                                                    )
                                                ],
                                                id="mini-chart-conversations",
                                                style={"marginTop": "10px"}
                                            )
                                        ],
                                        withBorder=True,
                                        p="lg",
                                        mb="lg"
                                    )
                                ],
                                span=4
                            )
                        ],
                        gutter="md",
                        mb="xl"
                    ),
                    
                    # Ações Rápidas
                    dmc.Card(
                        children=[
                            dmc.Text("Ações Rápidas", fw=600, mb="md"),
                            dmc.SimpleGrid(
                                children=[
                                    create_action_button_safe("tabler:message-plus", "Nova Conversa", "green", "action-nova-conversa"),
                                    create_action_button_safe("tabler:calendar-plus", "Novo Agendamento", "blue", "action-novo-agendamento"),
                                    create_action_button_safe("tabler:user-plus", "Adicionar Cliente", "violet", "action-adicionar-cliente"),
                                    create_action_button_safe("tabler:chart-line", "Ver Relatórios", "orange", "action-ver-relatorios")
                                ],
                                cols=4,
                                spacing="md"
                            )
                        ],
                        withBorder=True,
                        p="lg",
                        mb="xl"
                    )
                ],
                size="xl"
            ),
            
            # Stores
            dcc.Store(id="home-kpis-data", data=default_stats),
            dcc.Store(id="home-period", data=30),
            dcc.Store(id="home-refresh-trigger", data=0)
        ],
        style={"background": "#fafafa", "minHeight": "100vh"}
    )

def create_home_layout():
    """Função principal para criar o layout"""
    try:
        return create_elegant_home_layout()
    except Exception as e:
        print(f"Erro no layout home: {e}")
        # Fallback muito simples se tudo falhar
        return html.Div(
            children=[
                html.H1("WPPAgent Dashboard"),
                html.P("Carregando..."),
                dcc.Store(id="home-kpis-data", data={}),
                dcc.Store(id="home-period", data=30)
            ],
            style={"padding": "50px", "textAlign": "center"}
        )

# Para compatibilidade
layout = create_home_layout()
