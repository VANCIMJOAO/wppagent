"""
Clientes Layout - Design Moderno & Responsivo
===========================================

Interface renovada para gerenciamento de clientes com:
- Hero section com gradiente
- Cards KPI modernos
- Layout grid responsivo
- Lista compacta e elegante
- Perfil detalhado do cliente
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime, timedelta


def safe_component(component):
    """Wrapper seguro para componentes que podem ser None"""
    return component if component is not None else html.Div()

def safe_children(children_list):
    """Garante que lista de children não contém None"""
    if not children_list:
        return []
    if isinstance(children_list, list):
        return [child for child in children_list if child is not None]
    return [children_list] if children_list is not None else []


from services.queries import ClientesQueries

def create_clientes_layout():
    """
    Layout moderno da página de clientes com design premium.
    """
    
    # Busca dados dos clientes
    try:
        clients = ClientesQueries.get_clients()
        stats = ClientesQueries.get_client_stats()
        recent_clients = ClientesQueries.get_recent_clients(limit=5)
    except Exception as e:
        print(f"Erro ao buscar clientes: {e}")
        # Dados de exemplo para demonstração
        clients = [
            {
                "id": 1,
                "name": "Maria Silva",
                "phone_number": "11987654321",
                "email": "maria.silva@email.com",
                "status": "active",
                "total_conversations": 15,
                "total_appointments": 3,
                "total_messages": 47,
                "last_interaction_date": "2025-08-27T10:30:00",
                "created_at": "2025-07-15T09:00:00"
            },
            {
                "id": 2,
                "name": "João Santos",
                "phone_number": "11976543210", 
                "email": "joao.santos@email.com",
                "status": "vip",
                "total_conversations": 25,
                "total_appointments": 8,
                "total_messages": 102,
                "last_interaction_date": "2025-08-26T16:45:00",
                "created_at": "2025-06-20T14:30:00"
            },
            {
                "id": 3,
                "name": "Ana Costa",
                "phone_number": "11965432109",
                "email": "ana.costa@email.com", 
                "status": "new",
                "total_conversations": 2,
                "total_appointments": 1,
                "total_messages": 8,
                "last_interaction_date": "2025-08-27T08:15:00",
                "created_at": "2025-08-25T11:00:00"
            }
        ]
        recent_clients = clients
        stats = {
            "total": 112,
            "active": 85,
            "new_this_month": 23,
            "with_appointments": 45,
            "vip_clients": 12
        }
    
    return dmc.Container([
        # Hero Section Moderna
        html.Div([
            html.Div([
                dmc.Group([
                    dmc.Stack([
                        dmc.Group([
                            DashIconify(
                                icon="tabler:users",
                                width=32,
                                height=32,
                                color="white"
                            ),
                            dmc.Title(
                                "Clientes",
                                order=2,
                                style={
                                    "color": "white",
                                    "fontFamily": "Space Grotesk, system-ui, sans-serif",
                                    "fontWeight": "700",
                                    "fontSize": "2rem",
                                    "textShadow": "0 2px 4px rgba(0,0,0,0.3)"
                                }
                            )
                        ], align="center"),
                        
                        dmc.Text(
                            f"Gerencie seus {stats['total']} clientes • {stats['new_this_month']} novos este mês",
                            size="md",
                            style={
                                "color": "rgba(255, 255, 255, 0.9)",
                                "fontWeight": "500",
                                "textShadow": "0 1px 2px rgba(0,0,0,0.3)"
                            }
                        )
                    ], spacing="sm"),
                    
                    dmc.Group([
                        dmc.Button(
                            "Novo Cliente",
                            leftIcon=DashIconify(icon="tabler:user-plus", width=18),
                            size="md",
                            radius="lg",
                            variant="white",
                            color="dark",
                            id="new-client-btn",
                            style={
                                "fontWeight": "600",
                                "boxShadow": "0 4px 16px rgba(255, 255, 255, 0.3)"
                            }
                        ),
                        dmc.Button(
                            "Importar",
                            leftIcon=DashIconify(icon="tabler:upload", width=18),
                            size="md",
                            radius="lg",
                            variant="outline",
                            color="white",
                            id="import-clients-btn",
                            style={
                                "borderColor": "rgba(255, 255, 255, 0.5)",
                                "color": "white",
                                "fontWeight": "500"
                            }
                        ),
                        dmc.Button(
                            "Exportar",
                            leftIcon=DashIconify(icon="tabler:download", width=18),
                            size="md",
                            radius="lg",
                            variant="outline",
                            color="white",
                            id="export-clients-btn",
                            style={
                                "borderColor": "rgba(255, 255, 255, 0.5)",
                                "color": "white",
                                "fontWeight": "500"
                            }
                        )
                    ], spacing="sm")
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
            ], className="hero-content")
        ], className="clients-hero", style={
            "background": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
            "color": "white",
            "margin": "-24px -16px 24px -16px",
            "padding": "32px 24px",
            "borderRadius": "0 0 16px 16px"
        }),
        
        # Cards KPI Modernos
        dmc.SimpleGrid(
            cols=4,
            spacing="md",
            breakpoints=[
                {"maxWidth": "md", "cols": 2},
                {"maxWidth": "sm", "cols": 1}
            ],
            style={"marginBottom": "24px"},
            children=[
                create_client_kpi_card(
                    "Total de Clientes",
                    stats['total'],
                    "users",
                    "#3b82f6",
                    "Clientes cadastrados"
                ),
                create_client_kpi_card(
                    "Clientes Ativos",
                    stats['active'],
                    "user-check",
                    "#10b981", 
                    "Com interações recentes"
                ),
                create_client_kpi_card(
                    "Novos Este Mês",
                    stats['new_this_month'],
                    "user-plus",
                    "#f59e0b",
                    "Cadastrados em agosto"
                ),
                create_client_kpi_card(
                    "Com Agendamentos",
                    stats['with_appointments'],
                    "calendar-user",
                    "#8b5cf6",
                    "Possuem agendamentos"
                )
            ]
        ),
        
        # Filtros Modernos
        dmc.Paper([
            dmc.Group([
                dmc.TextInput(
                    placeholder="Buscar por nome, telefone ou email...",
                    icon=DashIconify(icon="tabler:search", width=16),
                    size="sm",
                    style={"width": "350px"},
                    id="search-clients"
                ),
                
                dmc.Group([
                    dmc.Select(
                        placeholder="Status",
                        data=[
                            {"value": "all", "label": "Todos"},
                            {"value": "active", "label": "Ativos"},
                            {"value": "inactive", "label": "Inativos"},
                            {"value": "new", "label": "Novos"},
                            {"value": "vip", "label": "VIP"}
                        ],
                        value="all",
                        size="sm",
                        style={"width": "120px"},
                        id="status-filter"
                    ),
                    dmc.Select(
                        placeholder="Ordenar",
                        data=[
                            {"value": "name_asc", "label": "Nome ↑"},
                            {"value": "name_desc", "label": "Nome ↓"},
                            {"value": "recent", "label": "Recentes"},
                            {"value": "oldest", "label": "Antigos"}
                        ],
                        value="name_asc",
                        size="sm",
                        style={"width": "120px"},
                        id="sort-clients"
                    )
                ], spacing="sm")
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
        ], p="md", radius="lg", shadow="sm", style={"marginBottom": "24px"}),
        
        # Layout Principal com Sidebar + Lista + Perfil
        html.Div([
            # Sidebar Esquerda - Filtros Rápidos
            html.Div([
                dmc.Paper([
                    dmc.Stack([
                        # Status Rápido
                        dmc.Stack([
                            dmc.Text("Filtros Rápidos", fw=600, size="sm"),
                            dmc.Stack([
                                create_quick_filter("Todos", stats['total'], "users", True),
                                create_quick_filter("Ativos", stats['active'], "user-check"),
                                create_quick_filter("Novos", stats['new_this_month'], "user-plus"),
                                create_quick_filter("VIP", stats.get('vip_clients', 12), "crown")
                            ], spacing="xs")
                        ], spacing="sm"),
                        
                        dmc.Divider(),
                        
                        # Estatísticas Rápidas
                        dmc.Stack([
                            dmc.Text("Estatísticas", fw=600, size="sm"),
                            dmc.Stack([
                                dmc.Group([
                                    DashIconify(icon="tabler:message-circle", width=16, color="#6b7280"),
                                    dmc.Text("5.2", size="sm", fw=500),
                                    dmc.Text("conversas/cliente", size="xs", c="dimmed")
                                ], spacing="xs"),
                                dmc.Group([
                                    DashIconify(icon="tabler:calendar", width=16, color="#6b7280"),
                                    dmc.Text(f"{stats['with_appointments']}", size="sm", fw=500),
                                    dmc.Text("com agendamentos", size="xs", c="dimmed")
                                ], spacing="xs")
                            ], spacing="sm")
                        ], spacing="sm")
                    ], spacing="lg")
                ], p="md", radius="lg", shadow="sm")
            ], style={"width": "250px", "marginRight": "20px"}),
            
            # Lista de Clientes - Centro
            html.Div([
                dmc.Paper([
                    dmc.Stack([
                        dmc.Group([
                            dmc.Text("Lista de Clientes", fw=600, size="md"),
                            dmc.Badge(f"{len(clients)}", color="blue", size="sm")
                        ], style={"display": "flex", "justifyContent": "space-between"}),
                        
                        html.Div(
                            id="clients-list",
                            children=[
                                create_modern_client_item(client) for client in clients
                            ] if clients else [
                                dmc.Center([
                                    dmc.Stack([
                                        DashIconify(icon="tabler:user-search", width=48, color="#9ca3af"),
                                        dmc.Text("Nenhum cliente encontrado", fw=500, c="dimmed"),
                                        dmc.Text("Use os filtros ou cadastre um novo cliente", size="sm", c="dimmed", style={"textAlign": "center"})
                                    ], align="center", spacing="md")
                                ], p="xl")
                            ],
                            style={"maxHeight": "500px", "overflowY": "auto"}
                        )
                    ], spacing="md")
                ], p="md", radius="lg", shadow="sm")
            ], style={"flex": "1", "marginRight": "20px"}),
            
            # Perfil do Cliente - Direita
            html.Div([
                dmc.Paper([
                    html.Div(id="client-profile", children=[
                        create_empty_client_profile()
                    ])
                ], p="md", radius="lg", shadow="sm")
            ], style={"width": "350px"})
        ], style={
            "display": "flex",
            "alignItems": "flex-start",
            "gap": "0px"
        }),
        
        # Modal para criar/editar cliente
        dmc.Modal(
            title="Novo Cliente",
            size="lg",
            id="client-modal",
            children=[create_client_form()]
        ),
        
        # Stores
        dcc.Store(id="clients-data", data=clients),
        dcc.Store(id="selected-client", data=None),
        dcc.Store(id="client-modal-mode", data="create")
        
    ], size="xl", px="md", py="sm")

def create_client_kpi_card(title, value, icon, color, description):
    """
    Card KPI moderno para clientes.
    """
    return dmc.Paper([
        dmc.Group([
            dmc.ThemeIcon(
                DashIconify(icon=f"tabler:{icon}", width=20),
                size="lg",
                color="white",
                style={
                    "background": f"linear-gradient(135deg, {color}, {color}aa)",
                    "border": "none"
                }
            ),
            dmc.Stack([
                dmc.Text(title, size="xs", c="dimmed", fw=500),
                dmc.Text(
                    str(value),
                    fw=700,
                    size="xl",
                    style={"color": color, "lineHeight": 1}
                )
            ], spacing="xs", style={"flex": 1})
        ], align="center"),
        dmc.Text(description, size="xs", c="dimmed", style={"marginTop": "8px"})
    ], p="md", radius="lg", shadow="sm", style={
        "background": f"linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.95))",
        "border": f"1px solid {color}22",
        "transition": "all 0.3s ease",
        "cursor": "pointer"
    })

def create_quick_filter(label, count, icon, active=False):
    """
    Filtro rápido na sidebar.
    """
    return dmc.Group([
        DashIconify(
            icon=f"tabler:{icon}",
            width=16,
            color="#4f46e5" if active else "#6b7280"
        ),
        dmc.Text(label, fw=600 if active else 500, size="sm"),
        dmc.Badge(str(count), size="xs", color="blue" if active else "gray")
    ], style={
        "padding": "8px 12px",
        "borderRadius": "8px",
        "backgroundColor": "#f8fafc" if active else "transparent",
        "border": "1px solid #e2e8f0" if active else "1px solid transparent",
        "cursor": "pointer",
        "transition": "all 0.2s ease"
    })

def create_modern_client_item(client):
    """
    Item moderno de cliente na lista.
    """
    name = client.get('name', 'Nome não informado')
    phone = client.get('phone_number', '')
    email = client.get('email', '')
    status = client.get('status', 'active')
    total_conversations = client.get('total_conversations', 0)
    total_appointments = client.get('total_appointments', 0)
    last_interaction = client.get('last_interaction_date')
    
    # Formata última interação
    try:
        if isinstance(last_interaction, str):
            last_interaction = datetime.fromisoformat(last_interaction.replace('Z', '+00:00'))
        
        if last_interaction:
            time_diff = datetime.now(last_interaction.tzinfo) - last_interaction
            if time_diff.days > 7:
                time_str = f"{time_diff.days}d"
            elif time_diff.days > 0:
                time_str = f"{time_diff.days}d"
            elif time_diff.seconds > 3600:
                time_str = f"{time_diff.seconds // 3600}h"
            else:
                time_str = "agora"
        else:
            time_str = "nunca"
    except:
        time_str = "--"
    
    # Status config
    status_config = {
        'active': {'color': '#10b981', 'label': 'Ativo', 'bg': 'rgba(16, 185, 129, 0.1)'},
        'inactive': {'color': '#6b7280', 'label': 'Inativo', 'bg': 'rgba(107, 114, 128, 0.1)'},
        'new': {'color': '#3b82f6', 'label': 'Novo', 'bg': 'rgba(59, 130, 246, 0.1)'},
        'vip': {'color': '#f59e0b', 'label': 'VIP', 'bg': 'rgba(245, 158, 11, 0.1)'}
    }
    
    config = status_config.get(status, status_config['active'])
    
    return dmc.Paper([
        dmc.Group([
            # Avatar
            dmc.Avatar(
                name[0].upper() if name else "?",
                size="md",
                radius="xl",
                style={
                    "background": "linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)",
                    "color": "white",
                    "fontWeight": "600"
                }
            ),
            
            # Info principal
            dmc.Stack([
                dmc.Group([
                    dmc.Text(name, fw=600, size="sm", style={"flex": 1}),
                    dmc.Badge(
                        config['label'],
                        size="xs",
                        style={"background": config['bg'], "color": config['color']}
                    )
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
                
                dmc.Group([
                    dmc.Text(f"...{phone[-4:]}" if len(phone) > 4 else phone, size="xs", c="dimmed"),
                    dmc.Text(f"há {time_str}", size="xs", c="dimmed")
                ], style={"display": "flex", "justifyContent": "space-between"}),
                
                dmc.Group([
                    dmc.Group([
                        DashIconify(icon="tabler:message-circle", width=12),
                        dmc.Text(str(total_conversations), size="xs")
                    ], spacing="2px"),
                    dmc.Group([
                        DashIconify(icon="tabler:calendar", width=12),
                        dmc.Text(str(total_appointments), size="xs")
                    ], spacing="2px")
                ], spacing="sm")
            ], style={"flex": 1}, spacing="xs"),
            
            # Ações
            dmc.Group([
                dmc.ActionIcon(
                    DashIconify(icon="tabler:brand-whatsapp", width=14),
                    size="sm",
                    variant="light",
                    color="green"
                ),
                dmc.ActionIcon(
                    DashIconify(icon="tabler:phone", width=14),
                    size="sm",
                    variant="light", 
                    color="blue"
                )
            ], spacing="xs")
        ], align="center")
    ], 
    p="sm",
    mb="xs", 
    radius="lg",
    style={
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "borderLeft": f"4px solid {config['color']}",
        "border": "1px solid #e5e7eb"
    },
    id={"type": "client-item", "index": client.get('id', 0)})

def create_empty_client_profile():
    """
    Estado vazio do perfil do cliente.
    """
    return dmc.Center([
        dmc.Stack([
            DashIconify(icon="tabler:user-circle", width=64, color="#9ca3af"),
            dmc.Text("Selecione um cliente", fw=600, size="lg", c="dimmed"),
            dmc.Text("Escolha um cliente da lista para ver o perfil completo", c="dimmed", style={"textAlign": "center"}),
            dmc.Button(
                "Cadastrar Novo Cliente",
                leftIcon=DashIconify(icon="tabler:user-plus"),
                variant="light",
                size="sm"
            )
        ], align="center", spacing="md")
    ], style={"height": "400px"})

def create_client_form():
    """
    Formulário moderno para criar/editar cliente.
    """
    return dmc.Stack([
        # Nome e Status
        html.Div([
            html.Div([
                dmc.TextInput(
                    label="Nome Completo",
                    placeholder="Nome do cliente",
                    required=True,
                    id="client-name",
                    size="sm"
                )
            ], style={"width": "70%", "marginRight": "4%"}),
            html.Div([
                dmc.Select(
                    label="Status",
                    data=[
                        {"value": "active", "label": "Ativo"},
                        {"value": "inactive", "label": "Inativo"},
                        {"value": "new", "label": "Novo"},
                        {"value": "vip", "label": "VIP"}
                    ],
                    value="active",
                    id="client-status",
                    size="sm"
                )
            ], style={"width": "26%"})
        ], style={"display": "flex", "marginBottom": "16px"}),
        
        # Telefone e Email
        html.Div([
            html.Div([
                dmc.TextInput(
                    label="Telefone",
                    placeholder="(11) 99999-9999",
                    required=True,
                    id="client-phone",
                    size="sm"
                )
            ], style={"width": "48%", "marginRight": "4%"}),
            html.Div([
                dmc.TextInput(
                    label="Email",
                    placeholder="cliente@email.com",
                    type="email",
                    id="client-email",
                    size="sm"
                )
            ], style={"width": "48%"})
        ], style={"display": "flex", "marginBottom": "16px"}),
        
        # Observações
        dmc.Textarea(
            label="Observações",
            placeholder="Informações adicionais sobre o cliente...",
            autosize=True,
            minRows=3,
            id="client-notes",
            size="sm"
        ),
        
        # Botões
        dmc.Group([
            dmc.Button(
                "Cancelar",
                variant="outline",
                id="cancel-client",
                size="sm"
            ),
            dmc.Button(
                "Salvar Cliente",
                leftIcon=DashIconify(icon="tabler:check"),
                id="save-client",
                size="sm"
            )
        ], style={"display": "flex", "justifyContent": "flex-end"})
    ], spacing="md")
