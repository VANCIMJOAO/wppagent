"""
Sidebar Component - Versão Clean com Frufruzinhos
================================================

Sidebar minimalista mas com detalhes elegantes e charme visual.
O equilíbrio perfeito entre simplicidade e personalidade.
"""

import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, callback, no_update
from dash_iconify import DashIconify

def create_sidebar(user=None):
    """
    Cria sidebar clean com detalhes elegantes.
    
    Args:
        user: Objeto User (opcional, para controle de permissões)
    
    Returns:
        html.Div: Sidebar com frufruzinhos elegantes
    """
    
    # Dados do usuário (placeholder se não fornecido)
    if not user:
        user_info = {
            'name': 'Usuário',
            'email': 'user@exemplo.com',
            'role': 'admin',
            'avatar_url': None
        }
    else:
        user_info = {
            'name': user.name,
            'email': user.email, 
            'role': user.role.value,
            'avatar_url': user.avatar_url
        }
    
    return html.Div([
        # Header com gradiente sutil
        create_elegant_header(),
        
        # Seção do usuário com card elegante
        create_elegant_user_section(user_info),
        
        # Menu de navegação com detalhes
        create_elegant_navigation(user),
        
        # Seção de ferramentas rápidas
        create_quick_tools(),
        
        # Rodapé com status elegante
        create_elegant_footer(),
        
    ], className="sidebar-elegant", id="sidebar-container")

def create_elegant_header():
    """Cria cabeçalho elegante com gradiente sutil"""
    return html.Div([
        # Gradiente de fundo sutil
        html.Div(className="header-gradient"),
        
        dmc.Group([
            # Logo com efeito hover
            dmc.ThemeIcon(
                DashIconify(icon="tabler:brand-whatsapp", width=26),
                size=44,
                radius="lg",
                variant="gradient",
                gradient={"from": "teal.4", "to": "green.6", "deg": 45},
                className="logo-elegant"
            ),
            
            # Branding com subtítulo
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
    """Cria seção do usuário com card elegante"""
    return html.Div([
        dmc.Paper([
            # Header do card com gradiente
            html.Div([
                dmc.Group([
                    # Avatar com anel de status
                    html.Div([
                        dmc.Avatar(
                            src=user_info['avatar_url'],
                            size="lg",
                            radius="xl",
                            color="blue",
                            className="user-avatar-elegant"
                        ),
                        # Indicador online
                        html.Div(className="online-indicator")
                    ], className="avatar-container"),
                    
                    # Info do usuário
                    html.Div([
                        dmc.Text(
                            user_info['name'],
                            size="sm",
                            fw=600,
                            c="dark",
                            className="user-name-elegant"
                        ),
                        dmc.Group([
                            get_elegant_role_badge(user_info['role']),
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
            
            # Ações rápidas elegantes
            dmc.Group([
                dmc.Button(
                    [DashIconify(icon="tabler:user", width=14), "Perfil"],
                    variant="light",
                    size="compact-sm",
                    color="blue",
                    id="user-profile-btn",
                    className="user-action-elegant",
                    leftSection=DashIconify(icon="tabler:user", width=14)
                ),
                dmc.Button(
                    [DashIconify(icon="tabler:logout", width=14), "Sair"],
                    variant="light",
                    size="compact-sm",
                    color="gray",
                    id="logout-button",
                    className="user-action-elegant",
                    leftSection=DashIconify(icon="tabler:logout", width=14)
                )
            ], justify="space-between", mt="sm")
            
        ], p="md", radius="xl", className="user-card-elegant", withBorder=True)
    ], className="user-section-elegant")

def create_elegant_navigation(user=None):
    """Cria menu de navegação com detalhes elegantes"""
    
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
            "color": "purple"
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
        # Título da seção
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
        
        # Items de navegação
        html.Div([
            create_elegant_nav_item(item) for item in nav_items
        ], className="nav-list")
        
    ], className="navigation-elegant")

def create_elegant_nav_item(item):
    """Cria item de navegação com detalhes elegantes"""
    return html.Div([
        dmc.Anchor([
            # Indicador lateral (aparece quando ativo)
            html.Div(className="nav-indicator"),
            
            dmc.Group([
                # Ícone com container colorido
                dmc.ThemeIcon(
                    DashIconify(icon=item["icon"], width=18),
                    size="sm",
                    variant="light",
                    color=item["color"],
                    className="nav-icon-elegant"
                ),
                
                # Conteúdo do item
                html.Div([
                    dmc.Group([
                        dmc.Text(
                            item["label"],
                            size="sm",
                            fw=500,
                            className="nav-label-elegant"
                        ),
                        
                        # Badge animada
                        dmc.Badge(
                            item["badge"],
                            size="xs",
                            color="red",
                            variant="filled",
                            className="nav-badge-elegant pulse-animation"
                        ) if item.get("badge") else None
                    ], justify="space-between", align="center"),
                    
                    # Descrição elegante
                    dmc.Text(
                        item["description"],
                        size="xs",
                        c="dimmed",
                        className="nav-description"
                    )
                ], style={"flex": 1})
                
            ], align="center", spacing="md", style={"width": "100%"})
        ],
        href=item["href"],
        id=item["id"],
        className="nav-item-elegant",
        td="none"
        )
    ], className="nav-item-container")

def create_quick_tools():
    """Cria seção de ferramentas rápidas"""
    tools = [
        {"icon": "tabler:plus", "label": "Nova Conversa", "color": "green"},
        {"icon": "tabler:calendar-plus", "label": "Novo Agendamento", "color": "blue"},
        {"icon": "tabler:user-plus", "label": "Novo Cliente", "color": "purple"},
        {"icon": "tabler:download", "label": "Exportar Dados", "color": "orange"}
    ]
    
    return html.Div([
        # Título da seção
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
        
        # Grid de ferramentas
        dmc.SimpleGrid([
            dmc.UnstyledButton([
                dmc.Stack([
                    dmc.ThemeIcon(
                        DashIconify(icon=tool["icon"], width=16),
                        size="sm",
                        variant="light",
                        color=tool["color"],
                        className="tool-icon"
                    ),
                    dmc.Text(
                        tool["label"],
                        size="xs",
                        ta="center",
                        className="tool-label"
                    )
                ], spacing="xs", align="center")
            ], className="quick-tool-btn")
            for tool in tools
        ], cols=2, spacing="xs")
        
    ], className="quick-tools-section")

def create_elegant_footer():
    """Cria rodapé elegante com status"""
    return html.Div([
        # Divider elegante
        html.Div(className="footer-divider"),
        
        # Status do sistema com animação
        dmc.Paper([
            dmc.Group([
                # Indicador com pulsação
                html.Div([
                    dmc.ThemeIcon(
                        DashIconify(icon="tabler:server-2", width=14),
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
        
        # Copyright com gradiente
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
    """Retorna badge elegante baseada na role"""
    role_config = {
        'super_admin': {'label': 'Super Admin', 'color': 'red', 'gradient': {"from": "red.4", "to": "pink.4"}},
        'admin': {'label': 'Admin', 'color': 'blue', 'gradient': {"from": "blue.4", "to": "cyan.4"}},
        'manager': {'label': 'Manager', 'color': 'green', 'gradient': {"from": "green.4", "to": "teal.4"}},
        'operator': {'label': 'Operador', 'color': 'orange', 'gradient': {"from": "orange.4", "to": "yellow.4"}},
        'viewer': {'label': 'Viewer', 'color': 'gray', 'gradient': {"from": "gray.4", "to": "gray.6"}}
    }
    
    config = role_config.get(role, role_config['viewer'])
    
    return dmc.Badge(
        config['label'],
        size="xs",
        variant="gradient",
        gradient=config['gradient'],
        className="role-badge-elegant"
    )

# Callbacks para funcionalidade da sidebar elegante
def register_sidebar_callbacks(app):
    """Registra callbacks da sidebar elegante"""
    
    # Callback para destacar item ativo
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
        
        # Classe base e ativa
        base_class = "nav-item-elegant"
        active_class = "nav-item-elegant nav-item-active-elegant"
        
        # Lista de classes
        classes = [base_class] * len(nav_ids)
        
        # Define ativo baseado no pathname
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
    
    # Callback para redirecionamento do botão perfil
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
