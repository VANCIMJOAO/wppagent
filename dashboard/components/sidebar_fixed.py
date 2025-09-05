"""
Sidebar Component - Versão 100% Corrigida
========================================

Todas as condições que podem retornar None foram substituídas por html.Div().
Garantia total contra erros 'Cannot read properties of undefined'.
"""

import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, callback, no_update
from dash_iconify import DashIconify

def create_sidebar(user=None):
    """
    Cria sidebar completamente segura contra erros de componentes None.
    
    Args:
        user: Objeto User (opcional, para controle de permissões)
    
    Returns:
        html.Div: Sidebar com proteção total contra None
    """
    
    # Dados do usuário com verificação de segurança
    if not user:
        user_info = {
            'name': 'Usuário',
            'email': 'user@exemplo.com',
            'role': 'admin',
            'avatar_url': None
        }
    else:
        user_info = {
            'name': getattr(user, 'name', 'Usuário'),
            'email': getattr(user, 'email', 'user@exemplo.com'),
            'role': getattr(user.role, 'value', 'admin') if hasattr(user, 'role') and user.role else 'admin',
            'avatar_url': getattr(user, 'avatar_url', None)
        }
    
    return html.Div([
        create_elegant_header(),
        create_elegant_user_section(user_info),
        create_elegant_navigation(user),
        create_quick_tools(),
        create_elegant_footer(),
    ], className="sidebar-elegant", id="sidebar-container")

def create_elegant_header():
    """Cria cabeçalho elegante com gradiente sutil - SEGURO"""
    return html.Div([
        html.Div(className="header-gradient"),
        dmc.Group([
            dmc.ThemeIcon(
                DashIconify(
                    icon="tabler:brand-whatsapp", 
                    width=26
                ),
                size=44,
                radius="lg",
                variant="gradient",
                gradient={"from": "teal.4", "to": "green.6", "deg": 45},
                className="logo-elegant",
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"}
            ),
            html.Div([
                dmc.Text(
                    "WppAgent",
                    size="xl",
                    fw=700,
                    className="brand-text-elegant"
                ),
                dmc.Text(
                    "Dashboard Pro",
                    size="xs",
                    c="dimmed",
                    className="brand-subtitle"
                )
            ])
        ], spacing="sm", align="center")
    ], className="header-elegant")

def create_elegant_user_section(user_info):
    """Cria seção do usuário com card elegante - SEGURO"""
    return html.Div([
        dmc.Paper([
            html.Div([
                dmc.Group([
                    html.Div([
                        dmc.Avatar(
                            src=user_info.get('avatar_url'),
                            size="lg",
                            radius="xl",
                            color="blue",
                            className="user-avatar-elegant"
                        ),
                        html.Div(className="online-indicator")
                    ], className="avatar-container"),
                    
                    html.Div([
                        dmc.Text(
                            str(user_info.get('name', 'Usuário')),
                            size="sm",
                            fw=600,
                            c="dark",
                            className="user-name-elegant"
                        ),
                        dmc.Group([
                            get_elegant_role_badge(user_info.get('role', 'admin')),
                            dmc.Badge(
                                "Online",
                                size="xs",
                                color="green",
                                variant="dot",
                                className="status-badge"
                            )
                        ], spacing="xs")
                    ], style={"flex": 1})
                ], align="center", spacing="md")
            ], className="user-card-header"),
            
            dmc.Group([
                dmc.Button(
                    "Perfil",
                    variant="light",
                    size="compact-sm",
                    color="blue",
                    id="user-profile-btn",
                    className="user-action-elegant",
                    leftIcon=DashIconify(
                        icon="tabler:user", 
                        width=14
                    )
                ),
                dmc.Button(
                    "Sair",
                    variant="light",
                    size="compact-sm",
                    color="gray",
                    id="logout-button",
                    className="user-action-elegant",
                    leftIcon=DashIconify(
                        icon="tabler:logout", 
                        width=14
                    )
                )
            ], position="apart", mt="sm")
            
        ], p="md", radius="xl", className="user-card-elegant", withBorder=True)
    ], className="user-section-elegant")

def create_elegant_navigation(user=None):
    """Cria menu de navegação com detalhes elegantes - SEGURO"""
    
    nav_items = [
        {
            "id": "nav-home",
            "label": "Dashboard", 
            "icon": "tabler:layout-dashboard",
            "href": "/home",
            "description": "Visão geral e métricas",
            "color": "blue"
        },
        {
            "id": "nav-conversas",
            "label": "Conversas",
            "icon": "tabler:message-circle-2",
            "href": "/conversas",
            "description": "Atendimentos WhatsApp",
            "badge": "12",
            "color": "green"
        },
        {
            "id": "nav-clientes",
            "label": "Clientes",
            "icon": "tabler:users-group",
            "href": "/clientes",
            "description": "Base de clientes",
            "color": "violet"
        },
        {
            "id": "nav-agendamentos",
            "label": "Agendamentos",
            "icon": "tabler:calendar-event",
            "href": "/agendamentos",
            "description": "Agenda e compromissos",
            "badge": "3",
            "color": "orange"
        },
        {
            "id": "nav-relatorios",
            "label": "Relatórios",
            "icon": "tabler:chart-area-line",
            "href": "/relatorios",
            "description": "Analytics e insights",
            "color": "teal"
        },
        {
            "id": "nav-configuracoes",
            "label": "Configurações",
            "icon": "tabler:settings-2",
            "href": "/configuracoes",
            "description": "Sistema e empresa",
            "color": "gray"
        }
    ]
    
    return html.Div([
        html.Div([
            dmc.Text(
                "Navegação",
                size="xs",
                c="dimmed",
                fw=600,
                tt="uppercase",
                className="section-title"
            ),
            html.Div(className="title-underline")
        ], className="section-header"),
        
        html.Div([
            create_elegant_nav_item(item) for item in nav_items
        ], className="nav-list")
        
    ], className="navigation-elegant")

def create_elegant_nav_item(item):
    """Cria item de navegação com detalhes elegantes - CORRIGIDO PARA NUNCA RETORNAR None"""
    
    # CORRIGIDO: Badge sempre retorna um componente válido
    badge_component = html.Div()  # Componente vazio por padrão
    if item.get("badge"):
        badge_component = dmc.Badge(
            str(item["badge"]),  # Garantir que é string
            size="xs",
            color="red",
            variant="filled",
            className="nav-badge-elegant pulse-animation"
        )
    
    return html.Div([
        dmc.Anchor([
            html.Div(className="nav-indicator"),
            
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(
                        icon=item.get("icon", "tabler:help-circle"), 
                        width=18
                    ),
                    size="sm",
                    variant="light",
                    color=item.get("color", "blue"),
                    className="nav-icon-elegant"
                ),
                
                html.Div([
                    dmc.Group([
                        dmc.Text(
                            str(item.get("label", "Item")),
                            size="sm",
                            fw=500,
                            className="nav-label-elegant"
                        ),
                        badge_component  # SEMPRE um componente válido
                    ], position="apart", align="center"),
                    
                    dmc.Text(
                        str(item.get("description", "")),
                        size="xs",
                        c="dimmed",
                        className="nav-description"
                    )
                ], style={"flex": 1})
                
            ], align="center", spacing="md", style={"width": "100%"})
        ],
        href=item.get("href", "/"),
        id=item.get("id", "nav-item"),
        className="nav-item-elegant",
        td="none"
        )
    ], className="nav-item-container")

def create_quick_tools():
    """Cria seção de ferramentas rápidas - SEGURO"""
    
    tools = [
        {
            "icon": "tabler:message-plus", 
            "label": "Nova Conversa", 
            "color": "green",
            "id": "quick-nova-conversa"
        },
        {
            "icon": "tabler:calendar-plus", 
            "label": "Novo Agendamento", 
            "color": "blue",
            "id": "quick-novo-agendamento"
        },
        {
            "icon": "tabler:user-plus", 
            "label": "Novo Cliente", 
            "color": "violet",
            "id": "quick-novo-cliente"
        },
        {
            "icon": "tabler:file-export", 
            "label": "Exportar Dados", 
            "color": "orange",
            "id": "quick-exportar"
        }
    ]
    
    return html.Div([
        html.Div([
            dmc.Text(
                "Ações Rápidas",
                size="xs",
                c="dimmed",
                fw=600,
                tt="uppercase",
                className="section-title"
            ),
            html.Div(className="title-underline")
        ], className="section-header"),
        
        html.Div([
            html.Div([
                dmc.Button([
                    dmc.Group([
                        dmc.ThemeIcon(
                            DashIconify(
                                icon=tool.get("icon", "tabler:help-circle"),
                                width=14,
                                height=14
                            ),
                            size="sm",
                            variant="light",
                            color=tool.get("color", "blue"),
                            radius="sm"
                        ),
                        dmc.Text(
                            str(tool.get("label", "Ação")),
                            size="xs",
                            fw=500,
                            c="dark",
                            style={
                                "fontSize": "10px",
                                "lineHeight": "1.2",
                                "flex": 1
                            }
                        )
                    ], spacing="xs", align="center", style={"width": "100%"})
                ],
                id=tool.get("id", f"tool-{i}"),
                className="quick-action-fixed",
                style={
                    "width": "100%",
                    "padding": "6px 8px",
                    "borderRadius": "6px",
                    "border": "1px solid var(--border-color)",
                    "backgroundColor": "white",
                    "cursor": "pointer",
                    "transition": "all 0.2s ease",
                    "marginBottom": "4px"
                })
            ]) for i, tool in enumerate(tools)
        ], style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "2px",
            "padding": "0 4px"
        })
        
    ], className="quick-tools-section")

def create_elegant_footer():
    """Cria rodapé elegante com status - SEGURO"""
    return html.Div([
        html.Div(className="footer-divider"),
        
        dmc.Paper([
            dmc.Group([
                html.Div([
                    dmc.ThemeIcon(
                        DashIconify(
                            icon="tabler:server-2", 
                            width=14
                        ),
                        size="xs",
                        variant="light",
                        color="green",
                        className="system-icon"
                    ),
                    html.Div(className="pulse-dot")
                ], className="status-indicator-container"),
                
                html.Div([
                    dmc.Text("Sistema Online", size="xs", fw=500, c="dark"),
                    dmc.Text("Última atualização: agora", size="xs", c="dimmed")
                ])
            ], align="center", spacing="sm")
        ], p="sm", radius="md", className="status-card"),
        
        html.Div([
            dmc.Text(
                "© 2024 WppAgent Dashboard",
                size="xs",
                c="dimmed",
                ta="center",
                className="copyright-text"
            )
        ], className="copyright-section")
        
    ], className="footer-elegant")

def get_elegant_role_badge(role):
    """Retorna badge elegante baseada na role - SEGURO"""
    role_config = {
        'super_admin': {'label': 'Super Admin', 'gradient': {"from": "red.4", "to": "pink.4"}},
        'admin': {'label': 'Admin', 'gradient': {"from": "blue.4", "to": "cyan.4"}},
        'manager': {'label': 'Manager', 'gradient': {"from": "green.4", "to": "teal.4"}},
        'operator': {'label': 'Operador', 'gradient': {"from": "orange.4", "to": "yellow.4"}},
        'viewer': {'label': 'Viewer', 'gradient': {"from": "gray.4", "to": "gray.6"}}
    }
    
    # Garantir que role é string válida
    safe_role = str(role) if role else 'viewer'
    config = role_config.get(safe_role, role_config['viewer'])
    
    return dmc.Badge(
        config['label'],
        size="xs",
        variant="gradient",
        gradient=config['gradient'],
        className="role-badge-elegant"
    )

def register_sidebar_callbacks(app):
    """Registra callbacks da sidebar elegante - SEGURO"""
    
    nav_ids = [
        "nav-home", "nav-conversas", "nav-clientes", 
        "nav-agendamentos", "nav-relatorios", "nav-configuracoes"
    ]
    
    @app.callback(
        [Output(nav_id, "className") for nav_id in nav_ids],
        Input("url", "pathname")
    )
    def update_active_nav(pathname):
        """Atualiza item ativo baseado na URL"""
        
        base_class = "nav-item-elegant"
        active_class = "nav-item-elegant nav-item-active-elegant"
        
        classes = [base_class] * len(nav_ids)
        
        path_mapping = {
            "/": 0, "/home": 0,
            "/conversas": 1,
            "/clientes": 2, 
            "/agendamentos": 3,
            "/relatorios": 4,
            "/configuracoes": 5
        }
        
        active_index = path_mapping.get(pathname)
        if active_index is not None:
            classes[active_index] = active_class
        
        return classes
    
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input("user-profile-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def redirect_to_profile(n_clicks):
        """Redireciona para página de perfil"""
        if n_clicks:
            return "/perfil"
        return no_update
