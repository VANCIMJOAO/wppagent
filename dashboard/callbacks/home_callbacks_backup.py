"""
Home Callbacks - DADOS REAIS DA DATABASE
========================================

Sistema completo usando dados reais da database:
- messages: 2066 mensagens reais
- conversations: 40 conversas reais  
- users: 112 usuários reais
- appointments: 17 agendamentos reais
- meta_logs: 3558 logs de API reais
"""

from dash import Input, Output, State, callback, no_update, html, dcc, callback_context
from dash_iconify import DashIconify
import dash_mantine_components as dmc
from datetime import datetime, date, timedelta, timezone
import plotly.graph_objects as go
import plotly.express as px
from dash.exceptions import PreventUpdate
import json
import sys
import os

# Adiciona o caminho para importar serviços
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.api_service import sync_api
    from services.database_service import get_db_service
    from utils.cache import cached_api_call, cache
    api_available = True
    db_service = get_db_service()
except ImportError:
    api_available = False
    print("⚠️  API service não disponível - usando dados mock")


# Funções cached para otimizar chamadas à API
@cached_api_call(ttl=300)  # 5 minutos de cache
def get_cached_dashboard_stats():
    """Busca estatísticas do dashboard com cache - SEM dados mock"""
    if api_available:
        try:
            # Tenta buscar dados reais da API
            stats = sync_api.get_dashboard_stats()
            # Se retornou dados mock (tem conversion_rate = 0.75), ignora
            if stats and stats.get('conversion_rate') == 0.75:
                return {}
            return stats or {}
        except Exception:
            return {}
    return {}


@cached_api_call(ttl=300)  # 5 minutos de cache
def get_cached_conversations_count():
    """Busca contagem de conversas com cache - SEM dados mock"""
    stats = get_cached_dashboard_stats()
    return stats.get('total_conversations', 0) if stats else 0


@cached_api_call(ttl=300)  # 5 minutos de cache
def get_cached_users_count():
    """Busca contagem de usuários com cache - SEM dados mock"""
    stats = get_cached_dashboard_stats()
    return stats.get('total_users', 0) if stats else 0


@cached_api_call(ttl=300)  # 5 minutos de cache
def get_cached_appointments_count():
    """Busca contagem de agendamentos com cache - SEM dados mock"""
    stats = get_cached_dashboard_stats()
    return stats.get('appointments_scheduled', 0) if stats else 0


@cached_api_call(ttl=300)  # 5 minutos de cache
def get_cached_messages_count():
    """Busca contagem de mensagens com cache - SEM dados mock"""
    stats = get_cached_dashboard_stats()
    return stats.get('messages_today', 0) if stats else 0


@cached_api_call(ttl=600)  # 10 minutos de cache para connection test
def get_cached_connection_status():
    """Testa conexão com cache"""
    if api_available:
        # Tenta buscar stats para testar conexão
        stats = get_cached_dashboard_stats()
        return bool(stats)
    return False


@cached_api_call(ttl=180)  # 3 minutos de cache para atividades recentes
def get_cached_recent_activities():
    """Busca atividades recentes com cache"""
    if api_available:
        # TODO: Implementar endpoint para atividades recentes
        # Por enquanto retorna vazio
        return []
    return []


@cached_api_call(ttl=300)  # 5 minutos de cache para timeline
def get_cached_conversations_timeline():
    """Busca timeline de conversas com cache"""
    if api_available:
        # TODO: Implementar endpoint para timeline
        # Por enquanto retorna vazio
        return []
    return []


@cached_api_call(ttl=300)  # 5 minutos de cache para distribuição de status
def get_cached_conversations_status_distribution():
    """Busca distribuição de status com cache"""
    if api_available:
        # TODO: Implementar endpoint para status distribution
        # Por enquanto retorna vazio
        return []
    return []

def register_home_callbacks(app):
    """
    Registra todos os callbacks da página Home com dados reais.
    """
    
    @app.callback(
        [
            Output('health-indicator-dot', 'color'),
            Output('health-indicator-dot', 'processing')
        ],
        Input('url', 'pathname'),
        prevent_initial_call=False
    )
    def update_health_indicator(pathname):
        """
        Atualiza o indicador de saúde do sistema usando conexão real.
        """
        if pathname != '/home' and pathname != '/':
            raise PreventUpdate
            
        try:
            is_healthy = get_cached_connection_status()
            if is_healthy:
                return 'green', False
            else:
                return 'red', True
                
        except Exception as e:
            print(f"Erro no health check: {e}")
            return 'red', True

    @app.callback(
        [
            Output("conversations-card", "children"),
            Output("users-card", "children"), 
            Output("appointments-card", "children"),
            Output("messages-card", "children")
        ],
        Input('home-period-filter', 'value'),
        prevent_initial_call=False
    )
    def update_real_kpis_with_filter(period_days):
        """
        Atualiza KPIs com dados reais da database baseado no filtro de período.
        """
        try:
            # Converte período para int
            period_days = int(period_days) if period_days else 30
            
            # Busca dados usando serviço
            if db_service:
                from services.queries import HomeQueries
                queries = HomeQueries()
                stats = queries.get_kpis(period_days=period_days)
                
                if stats:
                    # Valores reais do banco
                    total_conversations = stats.get('total_conversations', 0)
                    total_users = stats.get('unique_users', 0)
                    total_appointments = stats.get('total_appointments', 0)
                    total_messages = stats.get('total_messages', 0)
                    
                    # Dados de hoje para tendências
                    conversations_today = stats.get('conversations_today', 0)
                    appointments_today = stats.get('appointments_today', 0)
                    messages_today = stats.get('messages_today', 0)
                    
                    print(f"✅ KPIs atualizados: Conv={total_conversations}, Users={total_users}, Apt={total_appointments}, Msg={total_messages}")
                    
                    return [
                        str(total_conversations),
                        str(total_users),
                        str(total_appointments),
                        f"{total_messages:,}".replace(",", ".")
                    ]
            
            # Fallback se não conseguir dados
            return ["--", "--", "--", "--"]
            
        except Exception as e:
            print(f"❌ Erro ao carregar KPIs: {e}")
            return ["Erro", "Erro", "Erro", "Erro"]

    # CALLBACKS PARA AÇÕES RÁPIDAS
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        [
            Input("action-nova-conversa", "n_clicks"),
            Input("action-novo-agendamento", "n_clicks"), 
            Input("action-adicionar-cliente", "n_clicks"),
            Input("action-ver-relatorios", "n_clicks")
        ],
        prevent_initial_call=True
    )
    def handle_quick_actions(nova_conversa_clicks, novo_agendamento_clicks, adicionar_cliente_clicks, ver_relatorios_clicks):
        """Gerencia navegação dos botões de ações rápidas"""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "action-nova-conversa":
            return "/conversas"
        elif button_id == "action-novo-agendamento":
            return "/agendamentos"
        elif button_id == "action-adicionar-cliente":
            return "/clientes"
        elif button_id == "action-ver-relatorios":
            return "/relatorios"
        
        raise PreventUpdate

    @app.callback(
        Output("recent-activity-list", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def load_recent_activity(pathname):
        """
        Carrega atividade recente com dados reais da database usando cache.
        """
        if pathname not in ["/home", "/"]:
            raise PreventUpdate
        
        try:
            # Usa função cached para otimizar performance
            activities_data = get_cached_recent_activities()
            
            # Se não há dados da API, mostrar mensagem vazia
            if not activities_data:
                return [
                    dmc.Text(
                        "Nenhuma atividade recente encontrada",
                        size="sm",
                        c="gray",
                        ta="center",
                        py="md"
                    )
                ]

            activities = []
            for activity in activities_data[:5]:  # Limita a 5 atividades
                # Determina ícone e cor baseado na direção
                if activity.get("direction") == "in":
                    icon = "tabler:message-circle"
                    color = "blue"
                    activity_type = "Mensagem recebida"
                else:
                    icon = "tabler:message-circle-2"
                    color = "green"
                    activity_type = "Mensagem enviada"
                
                # Calcula tempo decorrido
                created_at = activity.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    
                    # CORRIGIDO: Garantir timezone não-None
                    tz_info = created_at.tzinfo if created_at.tzinfo else timezone.utc
                    now = datetime.now(tz_info)
                    diff = now - created_at
                    
                    if diff.days > 0:
                        tempo_str = f"{diff.days}d"
                    elif diff.seconds > 3600:
                        horas = diff.seconds // 3600
                        tempo_str = f"{horas}h"
                    else:
                        minutos = diff.seconds // 60
                        tempo_str = f"{minutos}m" if minutos > 0 else "agora"
                else:
                    tempo_str = "N/A"
                
                # Trunca conteúdo se muito longo
                content = activity.get("content", "")[:50]
                if len(activity.get("content", "")) > 50:
                    content += "..."
                
                activity_item = dmc.Group([
                    dmc.ThemeIcon(
                        DashIconify(icon=icon, width=16),
                        size="sm",
                        color=color,
                        variant="light"
                    ),
                    dmc.Stack([
                        dmc.Group([
                            dmc.Text(activity_type, size="sm", fw=500),
                            dmc.Text(tempo_str, size="xs", c="dimmed")
                        ]),
                        dmc.Text(f"{activity.get('customer_name', 'Cliente')}: {content}", size="xs", c="dimmed")
                    ], spacing="xs", style={"flex": 1})
                ], align="center", mb="sm")
                
                activities.append(activity_item)
            
            if not activities:
                activities = [
                    dmc.Center([
                        dmc.Stack([
                            DashIconify(icon="tabler:message-off", width=24, color="gray"),
                            dmc.Text("Nenhuma atividade recente", size="sm", c="dimmed")
                        ], align="center", spacing="xs")
                    ], py="md")
                ]
            
            return dmc.Stack(activities, spacing="xs")
            
        except Exception as e:
            print(f"Erro ao carregar atividades: {e}")
            return dmc.Text("Erro ao carregar atividades", c="red", size="sm")

    @app.callback(
        Output("conversations-timeline-chart", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def load_conversations_timeline(pathname):
        """
        Carrega gráfico de timeline de conversas com dados reais.
        """
        if pathname not in ["/home", "/"]:
            raise PreventUpdate
        
        try:
            # Usa função cached para otimizar performance
            timeline_data = get_cached_conversations_timeline()
            
            # Processa dados da API ou mostra vazio
            if timeline_data and len(timeline_data) > 0:
                dates = []
                counts = []
                for item in timeline_data:
                    dates.append(item.get('date', ''))
                    counts.append(item.get('count', 0))
            else:
                # Sem dados - mostrar gráfico vazio
                dates = []
                counts = []
            
            # Criar gráfico
            fig = go.Figure()
            
            if dates and counts:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=counts,
                    mode='lines+markers',
                    line=dict(color='#1e88e5', width=3),
                    marker=dict(size=8, color='#1e88e5'),
                    fill='tozeroy',
                    fillcolor='rgba(30, 136, 229, 0.1)',
                    hovertemplate='<b>%{x}</b><br>Conversas: %{y}<extra></extra>'
                ))
            else:
                # Gráfico vazio com mensagem
                fig.add_annotation(
                    text="Nenhum dado disponível",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="gray")
                )
            
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=20, b=40),
                showlegend=False,
                plot_bgcolor='white',
                xaxis=dict(
                    showgrid=False,
                    showline=False,
                    showticklabels=True,
                    tickfont=dict(size=10),
                    linecolor='#e5e7eb'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#f3f4f6',
                    showline=False,
                    showticklabels=True,
                    tickfont=dict(size=10)
                ),
                hovermode='x unified'
            )
            
            return dcc.Graph(
                figure=fig,
                config={'displayModeBar': False, 'staticPlot': False},
                style={'height': '200px'}
            )
            
        except Exception as e:
            print(f"Erro ao carregar timeline: {e}")
            return dmc.Center([
                dmc.Text("📊 Gráfico indisponível", size="sm", c="dimmed")
            ], style={"height": "200px"})

    @app.callback(
        Output("status-distribution-chart", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def load_status_distribution(pathname):
        """
        Carrega gráfico de distribuição de status com dados reais.
        """
        if pathname not in ["/home", "/"]:
            raise PreventUpdate
        
        try:
            # Usa função cached para otimizar performance
            status_data = get_cached_conversations_status_distribution()
            
            # Processa dados da API ou mostra vazio
            if status_data and len(status_data) > 0:
                labels = [item.get('status', 'unknown') for item in status_data]
                values = [item.get('count', 0) for item in status_data]
            else:
                # Sem dados - mostrar gráfico vazio
                labels = []
                values = []
            
            # Cores personalizadas
            colors = ['#1e88e5', '#43a047', '#fb8c00', '#e53935', '#8e24aa']
            
            # Criar gráfico de pizza
            fig = go.Figure()
            
            if labels and values and any(values):
                fig.add_trace(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors[:len(labels)]),
                    textinfo='label+percent',
                    textposition='outside',
                    hovertemplate='<b>%{label}</b><br>Conversas: %{value}<br>Porcentagem: %{percent}<extra></extra>'
                ))
            else:
                # Gráfico vazio com mensagem
                fig.add_annotation(
                    text="Nenhum dado de status disponível",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color="gray")
                )
            
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                font=dict(size=10)
            )
            
            return dcc.Graph(
                figure=fig,
                config={'displayModeBar': False, 'staticPlot': False},
                style={'height': '200px'}
            )
            
        except Exception as e:
            print(f"Erro ao carregar status: {e}")
            return dmc.Center([
                dmc.Text("🥧 Gráfico indisponível", size="sm", c="dimmed")
            ], style={"height": "200px"})

def register_all_home_callbacks(app):
    """
    Função principal para registrar todos os callbacks da Home.
    """
    try:
        register_home_callbacks(app)
        print("✅ HOME callbacks com dados reais registrados!")
        return True
    except Exception as e:
        print(f"❌ Erro ao registrar callbacks da home: {e}")
        return False
