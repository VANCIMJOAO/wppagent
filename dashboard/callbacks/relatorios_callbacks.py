"""
Relatórios Callbacks
===================

Callbacks completos para a página de relatórios com lógica de filtros, paginação e exportação.
Gerencia a interatividade da tabela, gráficos analíticos e relatórios de appointments.
Baseado na estrutura real do banco de dados WppAgent.
"""

from dash import Input, Output, State, callback, no_update, html, ctx
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import pandas as pd
import io
import base64
from datetime import datetime, date, timedelta
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px

from services.queries_reports import ReportsQueries
from services.api_service import sync_api
from utils.cache import cached_api_call, cache
from utils.error_handler import safe_execute

# Marca API como disponível (usando try/except no import se necessário)
api_available = True

# Funções cached para otimizar chamadas de relatórios
@cached_api_call(ttl=600)  # 10 minutos para relatórios
def get_cached_report_stats(period="30d"):
    """Busca estatísticas de relatórios via API REST com cache"""
    if api_available:
        return sync_api.get_dashboard_stats(period=period) or {}
    return {}


@cached_api_call(ttl=900)  # 15 minutos para dados históricos  
def get_cached_monthly_data():
    """Busca dados mensais via API REST com cache"""
    if api_available:
        # TODO: Implementar endpoint específico no backend para dados históricos
        return sync_api.get_dashboard_stats(period="12m") or {}
    return {}


@cached_api_call(ttl=300)  # 5 minutos para dados gerais
def get_cached_appointments_data(limit=100, offset=0, filters=None):
    """Busca dados de agendamentos via API REST com cache"""
    if api_available:
        return sync_api.get_appointments(limit=limit, offset=offset, filters=filters) or []
    return []

def register_relatorios_callbacks(app):
    """
    Registra todos os callbacks da página de Relatórios.
    
    Args:
        app: Instância do app Dash
    """
    
    # Callback principal para filtros e atualização da tabela de conversas
    @app.callback(
        [
            Output('conversations-table', 'data'),
            Output('conversations-table-info', 'children'),
            Output('loading-table', 'children')
        ],
        [
            Input('apply-filters-btn', 'n_clicks'),
            Input('refresh-reports-btn', 'n_clicks'),
            Input('report-type-tabs', 'value')
        ],
        [
            State('date-start-filter', 'value'),
            State('date-end-filter', 'value'),
            State('status-filter', 'value'),
            State('conversations-pagination-current', 'data')
        ],
        prevent_initial_call=False
    )
    def update_conversations_table(apply_clicks, refresh_clicks, tab_value, start_date, end_date, status_filter, current_page):
        """
        Atualiza a tabela de conversas baseado nos filtros aplicados.
        """
        if tab_value != 'conversations':
            return no_update, no_update, no_update
        
        # Processa datas
        if start_date:
            if isinstance(start_date, str):
                start_date = start_date
            else:
                start_date = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if end_date:
            if isinstance(end_date, str):
                end_date = end_date
            else:
                end_date = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Página atual
        page = current_page if current_page else 1
        
        try:
            # Busca dados do relatório
            report_data = ReportsQueries.get_conversations_report(
                start_date=start_date,
                end_date=end_date,
                status_filter=status_filter if status_filter != 'all' else None,
                limit=20,
                offset=(page - 1) * 20
            )
            
            # Formata dados para a tabela
            table_data = []
            for item in report_data["data"]:
                created_at = item["created_at"]
                if isinstance(created_at, datetime):
                    created_at = created_at.strftime("%d/%m/%Y %H:%M")
                elif isinstance(created_at, str):
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        created_at = str(created_at)[:16]
                
                last_message_at = item.get("last_message_at")
                if isinstance(last_message_at, datetime):
                    last_message_at = last_message_at.strftime("%d/%m/%Y %H:%M")
                elif isinstance(last_message_at, str):
                    try:
                        dt = datetime.fromisoformat(last_message_at.replace('Z', '+00:00'))
                        last_message_at = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        last_message_at = str(last_message_at)[:16] if last_message_at else "-"
                else:
                    last_message_at = "-"
                
                table_data.append({
                    "id": item["id"],
                    "cliente": item["customer_name"],
                    "telefone": item["phone_number"],
                    "email": item["email"],
                    "status": item["status"].title(),
                    "total_mensagens": item["total_messages"],
                    "mensagens_entrada": item["incoming_messages"],
                    "mensagens_saida": item["outgoing_messages"],
                    "duracao_min": f"{item['duration_minutes']:.1f}" if item["duration_minutes"] else "0.0",
                    "criado_em": created_at,
                    "ultima_mensagem": last_message_at
                })
            
            # Info da tabela
            info_text = f"Exibindo {len(table_data)} de {report_data['total']} conversas (Página {page} de {report_data['total_pages']})"
            
            return table_data, info_text, ""
            
        except Exception as e:
            print(f"Erro ao buscar dados do relatório de conversas: {e}")
            return [], "Erro ao carregar dados", "Erro na consulta"
    
    # Callback para tabela de agendamentos
    @app.callback(
        [
            Output('appointments-table', 'data'),
            Output('appointments-table-info', 'children')
        ],
        [
            Input('apply-filters-btn', 'n_clicks'),
            Input('refresh-reports-btn', 'n_clicks'),
            Input('report-type-tabs', 'value')
        ],
        [
            State('date-start-filter', 'value'),
            State('date-end-filter', 'value'),
            State('status-filter', 'value'),
            State('appointments-pagination-current', 'data')
        ],
        prevent_initial_call=False
    )
    def update_appointments_table(apply_clicks, refresh_clicks, tab_value, start_date, end_date, status_filter, current_page):
        """
        Atualiza a tabela de agendamentos baseado nos filtros aplicados.
        """
        if tab_value != 'appointments':
            return no_update, no_update
        
        # Processa datas
        if start_date:
            start_date = start_date if isinstance(start_date, str) else start_date.strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if end_date:
            end_date = end_date if isinstance(end_date, str) else end_date.strftime('%Y-%m-%d')
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        page = current_page if current_page else 1
        
        try:
            # Busca dados dos agendamentos
            report_data = ReportsQueries.get_appointments_report(
                start_date=start_date,
                end_date=end_date,
                status_filter=status_filter if status_filter != 'all' else None,
                limit=20,
                offset=(page - 1) * 20
            )
            
            # Formata dados para a tabela
            table_data = []
            for item in report_data["data"]:
                date_time = item["date_time"]
                if isinstance(date_time, datetime):
                    date_time = date_time.strftime("%d/%m/%Y %H:%M")
                elif isinstance(date_time, str):
                    try:
                        dt = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                        date_time = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        date_time = str(date_time)[:16]
                
                end_time = item.get("end_time")
                if isinstance(end_time, datetime):
                    end_time = end_time.strftime("%H:%M")
                elif isinstance(end_time, str) and end_time:
                    try:
                        dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        end_time = dt.strftime("%H:%M")
                    except:
                        end_time = str(end_time)[-8:-3] if len(str(end_time)) >= 8 else str(end_time)
                else:
                    end_time = "-"
                
                table_data.append({
                    "id": item["id"],
                    "cliente": item["customer_name"],
                    "telefone": item["phone_number"],
                    "status": item["status"].title(),
                    "data_hora": date_time,
                    "fim": end_time,
                    "duracao_min": item["duration"] or 0,
                    "preco": f"R$ {item['price']:.2f}" if item["price"] else "R$ 0,00",
                    "servico": item["service_name"],
                    "negocio": item["business_name"],
                    "observacoes": (item["notes"] or "")[:30] + "..." if item["notes"] and len(item["notes"]) > 30 else (item["notes"] or "-")
                })
            
            # Info da tabela
            info_text = f"Exibindo {len(table_data)} de {report_data['total']} agendamentos (Página {page} de {report_data['total_pages']})"
            
            return table_data, info_text
            
        except Exception as e:
            print(f"Erro ao buscar dados do relatório de agendamentos: {e}")
            return [], "Erro ao carregar dados"
    
    # Callback para período rápido
    @app.callback(
        [
            Output('date-start-filter', 'value'),
            Output('date-end-filter', 'value')
        ],
        Input('quick-period-filter', 'value'),
        prevent_initial_call=True
    )
    def update_date_filters_from_quick_period(period):
        """
        Atualiza filtros de data baseado na seleção de período rápido.
        """
        if not period:
            return no_update, no_update
        
        today = date.today()
        
        period_map = {
            'today': (today, today),
            'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
            'week': (today - timedelta(days=7), today),
            'month': (today - timedelta(days=30), today),
            'quarter': (today - timedelta(days=90), today),
            'year': (today - timedelta(days=365), today)
        }
        
        if period in period_map:
            start_date, end_date = period_map[period]
            return start_date, end_date
        
        return no_update, no_update
    
    # Callback para exportação CSV - Conversas
    @app.callback(
        Output('download-conversations-csv', 'data'),
        Input('export-conversations-csv-btn', 'n_clicks'),
        [
            State('date-start-filter', 'value'),
            State('date-end-filter', 'value'),
            State('status-filter', 'value')
        ],
        prevent_initial_call=True
    )
    def export_conversations_to_csv(n_clicks, start_date, end_date, status_filter):
        """
        Exporta dados de conversas filtradas para CSV.
        """
        if not n_clicks:
            raise PreventUpdate
        
        # Processa datas
        if start_date:
            start_date = start_date if isinstance(start_date, str) else start_date.strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if end_date:
            end_date = end_date if isinstance(end_date, str) else end_date.strftime('%Y-%m-%d')
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Busca todos os dados (sem paginação)
            report_data = ReportsQueries.get_conversations_report(
                start_date=start_date,
                end_date=end_date,
                status_filter=status_filter if status_filter != 'all' else None,
                limit=10000,  # Limite alto para exportar tudo
                offset=0
            )
            
            # Converte para DataFrame
            df_data = []
            for item in report_data["data"]:
                created_at = item["created_at"]
                if isinstance(created_at, datetime):
                    created_at = created_at.strftime("%d/%m/%Y %H:%M")
                elif isinstance(created_at, str):
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        created_at = str(created_at)
                
                last_message_at = item.get("last_message_at")
                if isinstance(last_message_at, datetime):
                    last_message_at = last_message_at.strftime("%d/%m/%Y %H:%M")
                elif isinstance(last_message_at, str) and last_message_at:
                    try:
                        dt = datetime.fromisoformat(last_message_at.replace('Z', '+00:00'))
                        last_message_at = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        last_message_at = str(last_message_at)
                else:
                    last_message_at = ""
                
                df_data.append({
                    "ID": item["id"],
                    "Cliente": item["customer_name"],
                    "Telefone": item["phone_number"],
                    "Email": item["email"],
                    "Status": item["status"],
                    "Total Mensagens": item["total_messages"],
                    "Mensagens Entrada": item["incoming_messages"],
                    "Mensagens Saida": item["outgoing_messages"],
                    "Duracao (minutos)": round(item["duration_minutes"], 1) if item["duration_minutes"] else 0,
                    "Criado em": created_at,
                    "Ultima Mensagem": last_message_at,
                    "Status Ultimo Agendamento": item.get("last_appointment_status", "")
                })
            
            df = pd.DataFrame(df_data)
            
            # Nome do arquivo com data
            filename = f"relatorio_conversas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return {
                "content": df.to_csv(index=False, encoding='utf-8-sig'),  # utf-8-sig para Excel
                "filename": filename,
                "type": "text/csv",
                "base64": False
            }
            
        except Exception as e:
            print(f"Erro ao exportar CSV de conversas: {e}")
            raise PreventUpdate
    
    # Callback para exportação CSV - Agendamentos
    @app.callback(
        Output('download-appointments-csv', 'data'),
        Input('export-appointments-csv-btn', 'n_clicks'),
        [
            State('date-start-filter', 'value'),
            State('date-end-filter', 'value'),
            State('status-filter', 'value')
        ],
        prevent_initial_call=True
    )
    def export_appointments_to_csv(n_clicks, start_date, end_date, status_filter):
        """
        Exporta dados de agendamentos filtrados para CSV.
        """
        if not n_clicks:
            raise PreventUpdate
        
        # Processa datas
        if start_date:
            start_date = start_date if isinstance(start_date, str) else start_date.strftime('%Y-%m-%d')
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        if end_date:
            end_date = end_date if isinstance(end_date, str) else end_date.strftime('%Y-%m-%d')
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Busca todos os dados
            report_data = ReportsQueries.get_appointments_report(
                start_date=start_date,
                end_date=end_date,
                status_filter=status_filter if status_filter != 'all' else None,
                limit=10000,
                offset=0
            )
            
            # Converte para DataFrame
            df_data = []
            for item in report_data["data"]:
                date_time = item["date_time"]
                if isinstance(date_time, datetime):
                    date_time = date_time.strftime("%d/%m/%Y %H:%M")
                elif isinstance(date_time, str):
                    try:
                        dt = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                        date_time = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        date_time = str(date_time)
                
                end_time = item.get("end_time")
                if isinstance(end_time, datetime):
                    end_time = end_time.strftime("%d/%m/%Y %H:%M")
                elif isinstance(end_time, str) and end_time:
                    try:
                        dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        end_time = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        end_time = str(end_time)
                else:
                    end_time = ""
                
                df_data.append({
                    "ID": item["id"],
                    "Cliente": item["customer_name"],
                    "Telefone": item["phone_number"],
                    "Status": item["status"],
                    "Data e Hora": date_time,
                    "Fim": end_time,
                    "Duracao (minutos)": item["duration"] or 0,
                    "Preco": item["price"] if item["price"] else 0,
                    "Servico": item["service_name"],
                    "Negocio": item["business_name"],
                    "Observacoes": item["notes"] or ""
                })
            
            df = pd.DataFrame(df_data)
            
            # Nome do arquivo com data
            filename = f"relatorio_agendamentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return {
                "content": df.to_csv(index=False, encoding='utf-8-sig'),
                "filename": filename,
                "type": "text/csv",
                "base64": False
            }
            
        except Exception as e:
            print(f"Erro ao exportar CSV de agendamentos: {e}")
            raise PreventUpdate
    
    # Callback para atualização dos gráficos analíticos
    @app.callback(
        [
            Output('conversations-timeline-chart', 'figure'),
            Output('messages-direction-chart', 'figure'),
            Output('appointments-status-chart', 'figure')
        ],
        [
            Input('apply-filters-btn', 'n_clicks'),
            Input('refresh-reports-btn', 'n_clicks')
        ],
        [
            State('date-start-filter', 'value'),
            State('date-end-filter', 'value'),
            State('status-filter', 'value')
        ],
        prevent_initial_call=False
    )
    def update_analytics_charts(apply_clicks, refresh_clicks, start_date, end_date, status_filter):
        """
        Atualiza os gráficos analíticos baseado nos filtros.
        """
        
        # Processa datas para calcular período
        if start_date:
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = start_date
        else:
            start_dt = datetime.now() - timedelta(days=30)
        
        if end_date:
            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = end_date
        else:
            end_dt = datetime.now()
        
        period_days = (end_dt - start_dt).days + 1
        
        try:
            # Importa as queries do home para buscar dados dos gráficos
            from services.queries import HomeQueries
            
            # Dados da timeline de conversas
            timeline_data = HomeQueries.get_conversations_timeline(period_days=period_days)
            conversations_fig = create_conversations_timeline_figure(timeline_data)
            
            # Dados de distribuição de mensagens
            messages_data = HomeQueries.get_messages_by_direction(period_days=period_days)
            messages_fig = create_messages_direction_figure(messages_data)
            
            # Dados de status de agendamentos (mock baseado no período)
            appointments_fig = create_appointments_status_figure(period_days)
            
            return conversations_fig, messages_fig, appointments_fig
            
        except Exception as e:
            print(f"Erro ao atualizar gráficos analíticos: {e}")
            # Retorna figuras vazias em caso de erro
            empty_fig = create_empty_figure("Erro ao carregar dados")
            return empty_fig, empty_fig, empty_fig
    
    # Callback para limpeza de filtros
    @app.callback(
        [
            Output('date-start-filter', 'value', allow_duplicate=True),
            Output('date-end-filter', 'value', allow_duplicate=True),
            Output('status-filter', 'value', allow_duplicate=True),
            Output('quick-period-filter', 'value')
        ],
        Input('clear-filters-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def clear_all_filters(n_clicks):
        """
        Limpa todos os filtros aplicados.
        """
        if not n_clicks:
            raise PreventUpdate
        
        today = date.today()
        default_start = today - timedelta(days=30)
        
        return default_start, today, 'all', None
    
    # Mensagem de sucesso do registro de callbacks
    print("✅ RELATÓRIOS callbacks com dados reais registrados!")

# Funções auxiliares para criação de gráficos

def create_conversations_timeline_figure(timeline_data):
    """
    Cria gráfico de timeline de conversas.
    """
    if not timeline_data:
        return create_empty_figure("Sem dados de conversas")
    
    dates = [item["date"] for item in timeline_data]
    conversations = [item["conversations"] for item in timeline_data]
    active_conversations = [item["active_conversations"] for item in timeline_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=conversations,
        mode='lines+markers',
        name='Total',
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Total: %{y}<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=active_conversations,
        mode='lines+markers',
        name='Ativas',
        line=dict(color='#10b981', width=2),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Ativas: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Timeline de Conversas",
        xaxis_title="Data",
        yaxis_title="Quantidade",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#374151"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    return fig

def create_messages_direction_figure(messages_data):
    """
    Cria gráfico de distribuição de mensagens por direção.
    """
    if not messages_data:
        return create_empty_figure("Sem dados de mensagens")
    
    # Agrupa por direção
    direction_totals = {}
    for item in messages_data:
        direction = item["direction"]
        count = item["count"]
        if direction in direction_totals:
            direction_totals[direction] += count
        else:
            direction_totals[direction] = count
    
    labels = list(direction_totals.keys())
    values = list(direction_totals.values())
    
    # Mapeia cores
    colors = {'incoming': '#10b981', 'outgoing': '#3b82f6'}
    colors_list = [colors.get(label, '#6b7280') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=[label.title() for label in labels],
        values=values,
        marker_colors=colors_list,
        hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>",
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Distribuição de Mensagens",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#374151"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )
    
    return fig

def create_appointments_status_figure(period_days):
    """
    Cria gráfico de status de agendamentos (dados simulados baseados no período).
    """
    # Dados simulados baseados no período
    # Em produção, viria de uma query real
    total_appointments = max(1, period_days // 2)  # Simula baseado no período
    
    status_data = {
        'Confirmado': int(total_appointments * 0.7),
        'Pendente': int(total_appointments * 0.2),
        'Cancelado': int(total_appointments * 0.1)
    }
    
    labels = list(status_data.keys())
    values = list(status_data.values())
    colors = ['#10b981', '#f59e0b', '#ef4444']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>",
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Status dos Agendamentos",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#374151"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )
    
    return fig

def create_empty_figure(message="Sem dados disponíveis"):
    """
    Cria uma figura vazia com mensagem.
    """
    fig = go.Figure()
    fig.update_layout(
        title=message,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#6b7280"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#6b7280")
    )
    return fig
