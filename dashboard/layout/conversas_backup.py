import dash
from dash import html, dcc, Input, Output, State, callback, ctx, ALL
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils.database import get_conversations, get_conversation_messages, create_conversation
import sqlite3

def render_conversation_card(conv_id, summary, last_message, timestamp, total_messages, customer_name=None):
    """Renderiza um card de conversa otimizado para melhor uso do espaço"""
    # Garantir que timestamp é um objeto datetime
    if isinstance(timestamp, str):
        try:
            from datetime import datetime
            timestamp = pd.to_datetime(timestamp)
        except:
            timestamp = datetime.now()
    
    # Define nome do cliente e preview da mensagem
    display_name = customer_name or f"Cliente #{conv_id}"
    message_preview = last_message or "Nova conversa iniciada"
    
    return html.Div([
        # Avatar da conversa
        html.Div([
            html.Div("AI", className="avatar-text")
        ], className="conversation-avatar", style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        }),
        
        # Informações da conversa - estrutura otimizada
        html.Div([
            html.Div([
                html.H4(display_name, className="conversation-name"),  # Nome do cliente
                html.Span(timestamp.strftime("%H:%M"), className="conversation-time")
            ], className="conversation-header"),
            
            html.P(message_preview, className="conversation-preview"),  # Preview da última mensagem
            
            html.Div([
                html.Span([
                    html.I(className="fas fa-comment"),
                    f" {total_messages}"
                ], className="message-count"),
                html.Span([
                    html.I(className="fas fa-clock"),
                    f" {timestamp.strftime('%d/%m/%Y')}"
                ], className="last-seen")
            ], className="conversation-meta")
        ], className="conversation-info")
    ], className="conversation-item", id={"type": "open-chat", "index": conv_id})

def render_message_bubble(message, is_user=True):
    """Renderiza uma bolha de mensagem"""
    # Garantir que timestamp é um objeto datetime
    timestamp = message['timestamp']
    if isinstance(timestamp, str):
        try:
            from datetime import datetime
            timestamp = pd.to_datetime(timestamp)
        except:
            timestamp = datetime.now()
    
    message_class = "user-message" if is_user else "ai-message"
    container_class = "user-container" if is_user else "ai-container"
    
    return html.Div([
        html.Div([
            html.Div(message['content'], className="message-text"),
            html.Div(
                timestamp.strftime("%H:%M"),
                className="message-timestamp"
            )
        ], className=f"message-bubble {message_class}")
    ], className=f"message-container {container_class}")

def render_conversations_grid(conversations, search_term=None, filter_option="all"):
    """Renderiza apenas os itens de conversa"""
    if not conversations:
        return html.Div([
            html.Div([
                html.I(className="fas fa-comments empty-icon"),
                html.H3("Nenhuma conversa ainda", className="empty-title"),
                html.P("Comece uma nova conversa com a IA!", className="empty-subtitle"),
                html.Button([
                    html.I(className="fas fa-plus"),
                    " Criar primeira conversa"
                ], className="btn-primary", id="first-conversation-btn")
            ], className="empty-chat-state")
        ])
    
    # Filtrar conversas
    filtered_conversations = conversations.copy()
    
    if search_term:
        filtered_conversations = [
            conv for conv in filtered_conversations
            if search_term.lower() in (conv.get('summary', '') or '').lower()
        ]
    
    if filter_option != "all":
        now = datetime.now()
        if filter_option == "today":
            filtered_conversations = [
                conv for conv in filtered_conversations
                if pd.to_datetime(conv['timestamp']).date() == now.date()
            ]
        elif filter_option == "week":
            week_ago = now - timedelta(days=7)
            filtered_conversations = [
                conv for conv in filtered_conversations
                if pd.to_datetime(conv['timestamp']) >= week_ago
            ]
        elif filter_option == "month":
            month_ago = now - timedelta(days=30)
            filtered_conversations = [
                conv for conv in filtered_conversations
                if pd.to_datetime(conv['timestamp']) >= month_ago
            ]
    
    # Retorna apenas os itens das conversas
    return [
        render_conversation_card(
            conv['id'],
            conv.get('summary'),
            conv.get('last_message'),
            conv['timestamp'],
            conv.get('total_messages', 0),
            conv.get('customer_name')  # Passa o nome do cliente
        ) for conv in filtered_conversations
    ]

def render_chat_view(conversation_id, customer_name=None):
    """Renderiza a view de chat ativo"""
    messages = get_conversation_messages(conversation_id)
    
    # Define o nome a ser exibido no header do chat
    chat_title = customer_name or f"Cliente #{conversation_id}"
    
    return html.Div([
        # Header do chat
        html.Div([
            html.Button([
                html.I(className="fas fa-arrow-left")
            ], className="back-button", id="back-to-conversations"),
            
            html.Div([
                html.Div("AI", className="chat-avatar", style={
                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                }),
                html.Div([
                    html.H4(chat_title, className="chat-title"),  # Nome do cliente
                    html.P("Online agora", className="chat-status")
                ], className="chat-info")
            ], className="chat-header-content", style={"display": "flex", "alignItems": "center"}),
            
            html.Div([
                html.Button([html.I(className="fas fa-search")], className="chat-action-btn"),
                html.Button([html.I(className="fas fa-ellipsis-v")], className="chat-action-btn")
            ], className="chat-actions")
        ], className="chat-header"),
        
        # Mensagens
        html.Div([
            render_message_bubble(message, message['is_user'])
            for message in messages
        ], className="messages-area", id="chat-messages"),
        
        # Input de nova mensagem
        html.Div([
            html.Button([
                html.I(className="fas fa-paperclip")
            ], className="attach-btn"),
            
            html.Button([
                html.I(className="fas fa-smile")
            ], className="emoji-btn"),
            
            dcc.Textarea(
                placeholder="Digite sua mensagem...",
                className="message-input",
                id="new-message-input",
                style={"height": "40px", "resize": "none"}
            ),
            
            html.Button([
                html.I(className="fas fa-paper-plane")
            ], className="send-btn", id="send-message-btn")
        ], className="message-input-area")
    ], className="chat-content")

def create_conversas_layout():
    """Função principal que cria o layout das conversas"""
    try:
        conversations = get_conversations()
    except Exception as e:
        print(f"Erro ao carregar conversas: {e}")
        # Fallback se houver erro na database
        conversations = []
    
    return html.Div([
        # Header da página
        html.Div([
            html.Div([
                html.Div([
                    html.H1([
                        html.I(className="fas fa-comments", style={"marginRight": "12px"}),
                        "Minhas Conversas"
                    ], className="conversations-title"),
                    html.P(
                        f"Gerencie suas {len(conversations)} conversas com a IA",
                        className="conversations-subtitle"
                    )
                ], style={"flex": "1"}),
                
                # Botão nova conversa
                html.Div([
                    html.Button([
                        html.I(className="fas fa-plus", style={"marginRight": "8px"}),
                        "Nova Conversa"
                    ], className="btn-primary", id="new-conversation-btn")
                ], className="header-actions")
            ], style={
                "display": "flex", 
                "justifyContent": "space-between", 
                "alignItems": "center",
                "width": "100%"
            })
        ], className="conversations-page-header"),
        
        # Filtros e busca
        html.Div([
            # Busca
            html.Div([
                html.Div([
                    html.I(className="fas fa-search search-icon"),
                    dcc.Input(
                        placeholder="Buscar conversas...",
                        className="search-input",
                        id="search-conversations",
                        style={"paddingLeft": "40px"}
                    )
                ], className="search-container", style={
                    "position": "relative",
                    "flex": "1",
                    "maxWidth": "400px"
                })
            ], style={"display": "flex", "alignItems": "center"}),
            
            # Filtros por tabs
            html.Div([
                html.Button("Todas", className="filter-tab active", id="filter-all"),
                html.Button("Hoje", className="filter-tab", id="filter-today"),
                html.Button("Semana", className="filter-tab", id="filter-week"),
                html.Button("Mês", className="filter-tab", id="filter-month")
            ], className="filter-tabs")
        ], className="filters-section", style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "20px",
            "flexWrap": "wrap"
        }),
        
        # Layout principal
        html.Div([
            # Painel das conversas
            html.Div([
                html.Div([
                    html.H3([
                        "Conversas ",
                        html.Span(f"({len(conversations)})", className="list-count")
                    ], className="list-title"),
                    html.Button([
                        html.I(className="fas fa-refresh")
                    ], className="refresh-button")
                ], className="conversations-list-header"),
                
                html.Div(
                    render_conversations_grid(conversations), 
                    id="conversations-content",
                    className="conversations-list"
                )
            ], className="conversations-panel"),
            
            # Painel do chat
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-comments empty-icon"),
                        html.H2("Selecione uma conversa", className="empty-title"),
                        html.P("Escolha uma conversa à esquerda para iniciar", className="empty-subtitle")
                    ], className="empty-chat-state")
                ], id="chat-panel-content")
            ], className="chat-panel")
        ], className="conversations-layout"),
        
        # Modal para nova conversa
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Nova Conversa", className="modal-title"),
                    html.Button("×", className="modal-close", id="close-modal")
                ], className="modal-header"),
                
                html.Div([
                    html.Label("Assunto da conversa:", className="input-label"),
                    dcc.Input(
                        placeholder="Digite o assunto...",
                        className="modal-input",
                        id="new-conversation-subject"
                    ),
                    
                    html.Label("Primeira mensagem:", className="input-label"),
                    dcc.Textarea(
                        placeholder="Digite sua mensagem...",
                        className="modal-textarea",
                        id="new-conversation-message"
                    )
                ], className="modal-body"),
                
                html.Div([
                    html.Button("Cancelar", className="btn-secondary", id="cancel-new-conversation"),
                    html.Button("Criar Conversa", className="btn-primary", id="create-new-conversation")
                ], className="modal-footer")
            ], className="modal-content")
        ], className="modal", id="new-conversation-modal", style={"display": "none"}),
        
        # Stores para dados
        dcc.Store(id="active-conversation", data=None),
        dcc.Store(id="conversations-data", data=conversations),
        
        # Dropdown escondido para manter compatibilidade com callbacks
        html.Div([
            dcc.Dropdown(
                options=[
                    {"label": "Todas", "value": "all"},
                    {"label": "Hoje", "value": "today"},
                    {"label": "Esta semana", "value": "week"},
                    {"label": "Este mês", "value": "month"}
                ],
                value="all",
                id="filter-conversations",
                style={"display": "none"}
            )
        ])
    ], className="page-conversations")
