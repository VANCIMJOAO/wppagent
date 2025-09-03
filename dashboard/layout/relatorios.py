"""
Relatórios Layout
================

Página de relatórios com filtros, tabelas e análises completas.
Focada em dados detalhados de conversas e agendamentos com exportação CSV.
Baseada na estrutura real do banco de dados WppAgent.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc, dash_table, callback
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date

from components.cards import create_chart_card, create_stat_card
from components.tables import create_data_table
from components.nav import create_page_header
from services.queries import ReportsQueries

def create_relatorios_layout():
    """
    Layout da página de relatórios com filtros e tabelas detalhadas.
    
    Seções:
    - Filtros de período e status
    - Abas para Conversas e Agendamentos
    - Tabelas com paginação e exportação
    - Gráficos analíticos
    """
    
    # Data stores para paginação
    pagination_stores = html.Div([
        dcc.Store(id='conversations-pagination-current', data=1),
        dcc.Store(id='appointments-pagination-current', data=1),
        dcc.Download(id="download-conversations-csv"),
        dcc.Download(id="download-appointments-csv"),
        dcc.Loading(id="loading-table", children=[])
    ])
    
    # Filtros principais
    filters_section = create_filters_section()
    
    # Seção principal com abas
    main_content = create_tabbed_content()
    
    # Gráficos analíticos
    analytics_section = create_analytics_section()
    
    # Layout principal
    layout = dmc.Stack([
        # Stores invisíveis
        pagination_stores,
        
        # Cabeçalho da página
        create_page_header(
            title="Relatórios e Análises",
            subtitle="Visualize dados detalhados de conversas e agendamentos",
            actions=[
                dmc.Button(
                    "Limpar Filtros",
                    leftIcon=DashIconify(icon="tabler:x", width=16, height=16),
                    variant="outline",
                    color="gray",
                    id="clear-filters-btn"
                ),
                dmc.Button(
                    "Atualizar",
                    leftIcon=DashIconify(icon="tabler:refresh", width=16, height=16),
                    variant="light",
                    id="refresh-reports-btn"
                )
            ]
        ),
        
        # Seção de filtros
        filters_section,
        
        # Conteúdo principal com abas
        main_content,
        
        # Seção de análises
        analytics_section
        
    ], spacing="xl", className="relatorios-layout")
    
    return layout

def create_filters_section():
    """
    Seção de filtros para relatórios.
    """
    
    # Data padrão - últimos 30 dias
    today = date.today()
    default_start = today - timedelta(days=30)
    
    filters = dmc.Card([
        dmc.Stack([
            dmc.Text("Filtros", size="lg", fw=600, className="heading"),
            
            dmc.Group([
                # Filtro de período
                dmc.DatePicker(
                    label="Data Inicial",
                    value=default_start,
                    placeholder="Selecione a data inicial",
                    id="date-start-filter",
                    style={"minWidth": "180px"}
                ),
                
                dmc.DatePicker(
                    label="Data Final", 
                    value=today,
                    placeholder="Selecione a data final",
                    id="date-end-filter",
                    style={"minWidth": "180px"}
                ),
                
                # Filtro de status
                dmc.Select(
                    label="Status",
                    placeholder="Todos os status",
                    data=[
                        {"value": "all", "label": "Todos"},
                        {"value": "active", "label": "Ativo"},
                        {"value": "completed", "label": "Concluído"},
                        {"value": "pending", "label": "Pendente"},
                        {"value": "confirmed", "label": "Confirmado"},
                        {"value": "cancelled", "label": "Cancelado"}
                    ],
                    value="all",
                    clearable=True,
                    id="status-filter",
                    style={"minWidth": "160px"}
                ),
                
                # Filtro de período rápido
                dmc.Select(
                    label="Período Rápido",
                    placeholder="Selecione o período",
                    data=[
                        {"value": "today", "label": "Hoje"},
                        {"value": "yesterday", "label": "Ontem"},
                        {"value": "week", "label": "Última Semana"},
                        {"value": "month", "label": "Último Mês"},
                        {"value": "quarter", "label": "Último Trimestre"},
                        {"value": "year", "label": "Último Ano"}
                    ],
                    clearable=True,
                    id="quick-period-filter",
                    style={"minWidth": "160px"}
                ),
                
                # Botão aplicar filtros
                dmc.Button(
                    "Aplicar Filtros",
                    leftIcon=DashIconify(icon="tabler:search", width=16, height=16),
                    id="apply-filters-btn",
                    style={"marginTop": "24px"}
                )
                
            ], spacing="md", align="end", noWrap=False)
        ], spacing="md")
    ], shadow="sm", p="md", radius="md", className="filters-section")
    
    return filters

def create_tabbed_content():
    """
    Conteúdo principal com abas para conversas e agendamentos.
    """
    
    return dmc.Card([
        dmc.Tabs(
            [
                dmc.TabsList([
                    dmc.Tab("Conversas", value="conversations", 
                               icon=DashIconify(icon="tabler:message-circle", width=16)),
                    dmc.Tab("Agendamentos", value="appointments", 
                               icon=DashIconify(icon="tabler:calendar", width=16))
                ]),
                
                dmc.TabsPanel([
                    create_conversations_tab()
                ], value="conversations"),
                
                dmc.TabsPanel([
                    create_appointments_tab()
                ], value="appointments")
            ],
            value="conversations",
            orientation="horizontal",
            id="report-type-tabs"
        )
    ], shadow="sm", p="md", radius="md")

def create_conversations_tab():
    """
    Aba de relatório de conversas.
    """
    
    return dmc.Stack([
        # Cabeçalho da aba com exportação
        dmc.Group([
            dmc.Text("Relatório de Conversas", size="lg", fw=600),
            dmc.Button(
                "Exportar CSV",
                leftIcon=DashIconify(icon="tabler:download", width=16),
                variant="outline",
                size="sm",
                id="export-conversations-csv-btn"
            )
        ], position="apart"),
        
        # Info da tabela
        html.Div(id="conversations-table-info", children="Carregando..."),
        
        # Tabela de conversas
        html.Div([
            dash_table.DataTable(
                id="conversations-table",
                columns=[
                    {"name": "ID", "id": "id", "type": "numeric"},
                    {"name": "Cliente", "id": "cliente"},
                    {"name": "Telefone", "id": "telefone"},
                    {"name": "Email", "id": "email"},
                    {"name": "Status", "id": "status"},
                    {"name": "Mensagens", "id": "total_mensagens", "type": "numeric"},
                    {"name": "Entrada", "id": "mensagens_entrada", "type": "numeric"},
                    {"name": "Saída", "id": "mensagens_saida", "type": "numeric"},
                    {"name": "Duração (min)", "id": "duracao_min", "type": "numeric"},
                    {"name": "Criado em", "id": "criado_em"},
                    {"name": "Última Msg", "id": "ultima_mensagem"}
                ],
                data=[],
                page_size=20,
                sort_action="native",
                filter_action="native",
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'font-family': 'var(--font-body)',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': 'var(--background-secondary)',
                    'fontWeight': '600',
                    'border': '1px solid var(--border)'
                },
                style_data={
                    'backgroundColor': 'var(--background)',
                    'border': '1px solid var(--border)'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'var(--background-secondary)'
                    }
                ]
            )
        ]),
        
        # Controles de paginação para conversas
        create_pagination_controls("conversations")
        
    ], spacing="md")

def create_appointments_tab():
    """
    Aba de relatório de agendamentos.
    """
    
    return dmc.Stack([
        # Cabeçalho da aba com exportação
        dmc.Group([
            dmc.Text("Relatório de Agendamentos", size="lg", fw=600),
            dmc.Button(
                "Exportar CSV",
                leftIcon=DashIconify(icon="tabler:download", width=16),
                variant="outline",
                size="sm",
                id="export-appointments-csv-btn"
            )
        ], position="apart"),
        
        # Info da tabela
        html.Div(id="appointments-table-info", children="Carregando..."),
        
        # Tabela de agendamentos
        html.Div([
            dash_table.DataTable(
                id="appointments-table",
                columns=[
                    {"name": "ID", "id": "id", "type": "numeric"},
                    {"name": "Cliente", "id": "cliente"},
                    {"name": "Telefone", "id": "telefone"},
                    {"name": "Status", "id": "status"},
                    {"name": "Data/Hora", "id": "data_hora"},
                    {"name": "Fim", "id": "fim"},
                    {"name": "Duração (min)", "id": "duracao_min", "type": "numeric"},
                    {"name": "Preço", "id": "preco"},
                    {"name": "Serviço", "id": "servico"},
                    {"name": "Negócio", "id": "negocio"},
                    {"name": "Observações", "id": "observacoes"}
                ],
                data=[],
                page_size=20,
                sort_action="native",
                filter_action="native",
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'font-family': 'var(--font-body)',
                    'fontSize': '14px'
                },
                style_header={
                    'backgroundColor': 'var(--background-secondary)',
                    'fontWeight': '600',
                    'border': '1px solid var(--border)'
                },
                style_data={
                    'backgroundColor': 'var(--background)',
                    'border': '1px solid var(--border)'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'var(--background-secondary)'
                    }
                ]
            )
        ]),
        
        # Controles de paginação para agendamentos
        create_pagination_controls("appointments")
        
    ], spacing="md")

def create_pagination_controls(table_type):
    """
    Cria controles de paginação para as tabelas.
    """
    
    return dmc.Group([
        dmc.ActionIcon(
            DashIconify(icon="tabler:chevron-left", width=16, height=16),
            variant="outline",
            id=f"{table_type}-prev-page"
        ),
        html.Div(id=f"{table_type}-pagination-info", children="Página 1"),
        dmc.ActionIcon(
            DashIconify(icon="tabler:chevron-right", width=16, height=16),
            variant="outline",
            id=f"{table_type}-next-page"
        ),
        dmc.NumberInput(
            placeholder="Ir para página",
            w=120,
            min=1,
            id=f"{table_type}-page-input"
        )
    ], spacing="sm", position="center")

def create_analytics_section():
    """
    Seção com gráficos analíticos.
    """
    
    # Layout dos gráficos em grid
    charts_layout = dmc.SimpleGrid([
        create_conversations_timeline_chart(),
        create_messages_direction_chart(),
        create_appointments_status_chart()
    ], cols={"base": 1, "md": 2, "lg": 3}, spacing="md")
    
    return dmc.Stack([
        dmc.Text("Análises Gráficas", size="xl", fw=700, className="heading"),
        charts_layout
    ], spacing="lg")

def create_conversations_timeline_chart():
    """
    Card com gráfico de timeline de conversas.
    """
    
    return create_chart_card(
        title="Timeline de Conversas",
        chart_component=dcc.Graph(
            id="conversations-timeline-chart",
            config={'displayModeBar': False},
            style={"height": "400px"}
        ),
        subtitle="Evolução das conversas ao longo do tempo"
    )

def create_messages_direction_chart():
    """
    Card com gráfico de distribuição de mensagens.
    """
    
    return create_chart_card(
        title="Distribuição de Mensagens",
        chart_component=dcc.Graph(
            id="messages-direction-chart",
            config={'displayModeBar': False},
            style={"height": "400px"}
        ),
        subtitle="Proporção de mensagens por direção"
    )

def create_appointments_status_chart():
    """
    Card com gráfico de status de agendamentos.
    """
    
    return create_chart_card(
        title="Status dos Agendamentos",
        chart_component=dcc.Graph(
            id="appointments-status-chart",
            config={'displayModeBar': False},
            style={"height": "400px"}
        ),
        subtitle="Distribuição por status de agendamento"
    )

def create_summary_cards():
    """
    Cards de resumo dos dados filtrados (opcional - pode ser usado no futuro).
    """
    
    # Dados simulados baseados na estrutura real
    period_data = {
        "total_conversations": 40,
        "completed_conversations": 28,
        "active_conversations": 12,
        "response_rate": 70.0,
        "total_messages": 2066,
        "unique_users": 112,
        "total_appointments": 17,
        "confirmed_appointments": 12
    }
    
    cards = [
        create_stat_card(
            "Resumo de Conversas",
            [
                {"label": "Total de Conversas", "value": f"{period_data['total_conversations']:,}"},
                {"label": "Concluídas", "value": f"{period_data['completed_conversations']:,}"},
                {"label": "Taxa de Conclusão", "value": f"{period_data['response_rate']:.1f}%", "color": "green"}
            ]
        ),
        
        create_stat_card(
            "Métricas Gerais",
            [
                {"label": "Total Mensagens", "value": f"{period_data['total_messages']:,}"},
                {"label": "Usuários Únicos", "value": f"{period_data['unique_users']:,}"},
                {"label": "Agendamentos", "value": f"{period_data['total_appointments']:,}", "color": "blue"}
            ]
        )
    ]
    
    return dmc.SimpleGrid(
        cards,
        cols={"base": 1, "md": 2},
        spacing="md",
        className="summary-cards"
    )

def create_empty_state(message="Sem dados disponíveis"):
    """
    Estado vazio para quando não há dados.
    """
    
    return dmc.Center([
        dmc.Stack([
            DashIconify(icon="tabler:database-off", width=48, height=48, color="gray"),
            dmc.Text(message, size="lg", c="dimmed"),
            dmc.Text("Ajuste os filtros ou verifique a conectividade", size="sm", c="dimmed")
        ], align="center", spacing="sm")
    ], style={"height": "300px"})
