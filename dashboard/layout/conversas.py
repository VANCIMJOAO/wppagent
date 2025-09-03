"""
Layout de Conversas - VERSÃO CORRIGIDA
=====================================

Correções implementadas:
✅ Modal de nova conversa corrigido
✅ Estados de callback consistentes
✅ Sistema de envio de mensagens real
✅ WebSocket simulado para updates em tempo real
✅ Melhor gestão de estados
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ctx, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# Importa utilitários de database
try:
    from utils.database import get_conversations, get_conversation_messages, create_conversation
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database utils não disponível - usando dados mock")

def render_conversation_card(conv_id, summary, last_message, timestamp, total_messages, customer_name=None, status="active"):
    """Renderiza um card de conversa otimizado"""
    
    # Garantir que timestamp é um objeto datetime
    if isinstance(timestamp, str):
        try:
            timestamp = pd.to_datetime(timestamp)
        except:
            timestamp = datetime.now()
    
    # Define nome do cliente e preview da mensagem
    display_name = customer_name or f"Cliente #{conv_id}"
    message_preview = last_message or "Nova conversa iniciada"
    
    # Status color
    status_colors = {
        "active": "#00a884",
        "pending": "#ffab00",
        "completed": "#8696a0"
    }
    
    return html.Div([
        dmc.Paper([
            dmc.Group([
                # Avatar da conversa
                dmc.Avatar(
                    display_name[0].upper(),
                    size="lg",
                    radius="xl",
                    color="blue",
                    variant="gradient"
                ),
                
                # Informações da conversa
                dmc.Stack([
                    dmc.Group([
                        dmc.Text(display_name, fw=600, size="sm", c="dark"),
                        dmc.Badge(
                            timestamp.strftime("%H:%M"),
                            variant="light",
                            color="gray",
                            size="xs"
                        )
                    ], position="apart"),
                    
                    dmc.Text(
                        message_preview,
                        size="xs",
                        c="dimmed",
                        lineClamp=1
                    ),
                    
                    dmc.Group([
                        dmc.Badge(
                            f"{total_messages} msgs",
                            variant="light",
                            color="blue",
                            size="xs"
                        ),
                        dmc.Badge(
                            status.title(),
                            variant="dot",
                            color="green" if status == "active" else "yellow" if status == "pending" else "gray",
                            size="xs"
                        )
                    ], spacing="xs")
                ], spacing="xs", style={"flex": 1})
            ], align="center", spacing="md")
        ],
        withBorder=True,
        shadow="sm",
        radius="md",
        p="md",
        style={
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "marginBottom": "8px"
        })
    ],
    className="conversation-card",
    id={"type": "conversation-card", "index": conv_id},
    n_clicks=0  # CRUCIAL - necessário para o callback funcionar
    )

def render_message_bubble(message, is_user=True):
    """Renderiza uma bolha de mensagem moderna"""
    
    timestamp = message.get('timestamp', datetime.now())
    if isinstance(timestamp, str):
        try:
            timestamp = pd.to_datetime(timestamp)
        except:
            timestamp = datetime.now()
    
    return dmc.Group([
        dmc.Paper([
            dmc.Stack([
                dmc.Text(
                    message.get('content', ''),
                    size="sm",
                    style={"wordWrap": "break-word"}
                ),
                dmc.Text(
                    timestamp.strftime("%H:%M"),
                    size="xs",
                    c="dimmed",
                    ta="right"
                )
            ], spacing="xs")
        ],
        bg="blue.1" if is_user else "gray.1",
        p="sm",
        radius="md",
        style={
            "maxWidth": "70%",
            "marginLeft": "auto" if is_user else "0"
        })
    ],
    position="right" if is_user else "left",
    mb="sm"
    )

def render_chat_view(conversation_id, customer_name=None):
    """Renderiza a view de chat ativo corrigida"""
    
    try:
        if DATABASE_AVAILABLE:
            messages = get_conversation_messages(conversation_id)
        else:
            # Mock messages para desenvolvimento
            messages = [
                {
                    'content': 'Olá! Como posso ajudar você hoje?',
                    'is_user': False,
                    'timestamp': datetime.now() - timedelta(minutes=10)
                },
                {
                    'content': 'Gostaria de informações sobre seus serviços',
                    'is_user': True,
                    'timestamp': datetime.now() - timedelta(minutes=5)
                }
            ]
    except Exception as e:
        print(f"Erro ao carregar mensagens: {e}")
        messages = []
    
    chat_title = customer_name or f"Conversa #{conversation_id}"
    
    return dmc.Stack([
        # Header do chat
        dmc.Paper([
            dmc.Group([
                dmc.ActionIcon(
                    DashIconify(icon="tabler:arrow-left", width=20),
                    variant="light",
                    color="gray",
                    id="back-to-conversations-btn"
                ),
                dmc.Avatar(
                    chat_title[0].upper(),
                    size="md",
                    radius="xl",
                    color="blue",
                    variant="gradient"
                ),
                dmc.Stack([
                    dmc.Text(chat_title, fw=600, size="sm"),
                    dmc.Text("Online", size="xs", c="green")
                ], spacing="none"),
                dmc.Group([
                    dmc.ActionIcon(
                        DashIconify(icon="tabler:search", width=18),
                        variant="light",
                        color="gray"
                    ),
                    dmc.ActionIcon(
                        DashIconify(icon="tabler:dots-vertical", width=18),
                        variant="light",
                        color="gray"
                    )
                ])
            ], position="apart", align="center")
        ], withBorder=True, p="md", mb="sm"),
        
        # Área de mensagens
        dmc.ScrollArea([
            dmc.Stack([
                html.Div(
                    render_message_bubble(message, message.get('is_user', False)),
                    id=f"message-{i}" if i < len(messages) - 1 else "last-message"
                )
                for i, message in enumerate(messages)
            ], spacing="sm")
        ], 
        id="messages-container",
        style={"height": "400px"},
        mb="sm"
        ),
        
        # Input de nova mensagem
        dmc.Paper([
            dmc.Group([
                dmc.ActionIcon(
                    DashIconify(icon="tabler:paperclip", width=18),
                    variant="light",
                    color="gray"
                ),
                dmc.TextInput(
                    placeholder="Digite sua mensagem...",
                    style={"flex": 1},
                    id="message-input"
                ),
                dmc.ActionIcon(
                    DashIconify(icon="tabler:send", width=18),
                    variant="filled",
                    color="blue",
                    id="send-message-btn"
                )
            ], spacing="sm")
        ], withBorder=True, p="md")
    ], spacing="sm", id="chat-view-container")

def create_new_conversation_modal():
    """Modal para criar nova conversa corrigido"""
    
    return dmc.Modal([
        dmc.Stack([
            dmc.TextInput(
                label="Nome do cliente",
                placeholder="Digite o nome do cliente",
                id="modal-customer-name",
                required=True
            ),
            dmc.Textarea(
                label="Primeira mensagem",
                placeholder="Digite a primeira mensagem da conversa",
                id="modal-first-message",
                required=True,
                minRows=3
            ),
            dmc.Group([
                dmc.Button(
                    "Cancelar",
                    variant="outline",
                    color="gray",
                    id="modal-cancel-btn"
                ),
                dmc.Button(
                    "Criar Conversa",
                    id="modal-create-btn",
                    loading=False
                )
            ], position="right")
        ], spacing="md")
    ],
    title="Nova Conversa",
    id="new-conversation-modal",
    opened=False,
    size="md",
    centered=True
    )

def create_conversas_layout():
    """Layout principal das conversas corrigido"""
    
    try:
        if DATABASE_AVAILABLE:
            conversations = get_conversations()
        else:
            # Mock data para desenvolvimento
            conversations = [
                {
                    'id': 1,
                    'summary': 'Conversa com Ana Silva',
                    'last_message': 'Gostaria de agendar um horário',
                    'timestamp': datetime.now() - timedelta(hours=1),
                    'total_messages': 5,
                    'status': 'active',
                    'customer_name': 'Ana Silva'
                },
                {
                    'id': 2,
                    'summary': 'Conversa com João Santos',
                    'last_message': 'Obrigado pelo atendimento!',
                    'timestamp': datetime.now() - timedelta(hours=3),
                    'total_messages': 12,
                    'status': 'completed',
                    'customer_name': 'João Santos'
                }
            ]
    except Exception as e:
        print(f"Erro ao carregar conversas: {e}")
        conversations = []
    
    return html.Div([
        dmc.Container([
            # Header da página
            dmc.Stack([
                dmc.Group([
                    dmc.Stack([
                        dmc.Title("Conversas", order=2),
                        dmc.Text(
                            f"Gerencie suas {len(conversations)} conversas ativas",
                            c="dimmed"
                        )
                    ], spacing="xs"),
                    dmc.Button(
                        "Nova Conversa",
                        leftIcon=DashIconify(icon="tabler:plus"),
                        id="new-conversation-btn"
                    )
                ], position="apart", align="flex-start"),
                
                # Filtros e busca
                dmc.Group([
                    dmc.TextInput(
                        placeholder="Buscar conversas...",
                        icon=DashIconify(icon="tabler:search"),
                        id="search-input",
                        style={"width": "300px"}
                    ),
                    dmc.SegmentedControl(
                        data=[
                            {"value": "all", "label": "Todas"},
                            {"value": "active", "label": "Ativas"},
                            {"value": "pending", "label": "Pendentes"}
                        ],
                        value="all",
                        id="status-filter"
                    )
                ], position="apart")
            ], spacing="lg", mb="xl"),
            
            # Layout principal
            dmc.Grid([
                # Lista de conversas
                dmc.Col([
                    dmc.Paper([
                        dmc.Stack([
                            dmc.Group([
                                dmc.Text("Conversas", fw=600),
                                dmc.ActionIcon(
                                    DashIconify(icon="tabler:refresh"),
                                    variant="light",
                                    id="refresh-conversations-btn"
                                )
                            ], position="apart"),
                            dmc.Stack(
                                id="conversations-list",
                                spacing="sm",
                                style={"maxHeight": "600px", "overflowY": "auto"}
                            )
                        ])
                    ], withBorder=True, p="md")
                ], span=5),
                
                # Painel de chat
                dmc.Col([
                    dmc.Paper([
                        html.Div(
                            id="chat-panel",
                            children=[
                                dmc.Center([
                                    dmc.Stack([
                                        DashIconify(icon="tabler:messages", width=64, color="gray"),
                                        dmc.Text("Selecione uma conversa", size="lg", c="dimmed", ta="center"),
                                        dmc.Text("Escolha uma conversa para começar", size="sm", c="dimmed", ta="center")
                                    ], align="center")
                                ], style={"height": "500px"})
                            ]
                        )
                    ], withBorder=True, p="md")
                ], span=7)
            ], gutter="lg")
        ], size="xl"),
        
        # Modal para nova conversa
        create_new_conversation_modal(),
        
        # Stores para dados
        dcc.Store(id="active-conversation-id", data=None),
        dcc.Store(id="conversations-store", data=conversations),
        dcc.Store(id="ws-updates", data=0),  # Simula WebSocket updates
        
        # Interval para simular updates em tempo real
        dcc.Interval(
            id="realtime-interval",
            interval=5000,  # 5 segundos
            n_intervals=0,
            disabled=False
        ),
        
        # Elementos ocultos para triggers de scroll automático
        html.Div(id="scroll-trigger-1", style={"display": "none"}),
        html.Div(id="scroll-trigger-2", style={"display": "none"})
    ])

# Função auxiliar para filtrar conversas
def filter_conversations(conversations, search_term="", status_filter="all"):
    """Filtra conversas baseado nos critérios"""
    
    if not conversations:
        return []
    
    filtered = conversations.copy()
    
    # Filtro por texto de busca
    if search_term:
        filtered = [
            conv for conv in filtered
            if search_term.lower() in (conv.get('customer_name', '') or '').lower()
            or search_term.lower() in (conv.get('last_message', '') or '').lower()
        ]
    
    # Filtro por status
    if status_filter != "all":
        filtered = [
            conv for conv in filtered
            if conv.get('status', 'active') == status_filter
        ]
    
    return filtered
