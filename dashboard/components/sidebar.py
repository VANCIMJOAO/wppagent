"""
Sidebar Component - Versão 100% Segura
=====================================
"""

import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, callback, no_update
from dash_iconify import DashIconify

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

def create_sidebar(user=None):
    """Cria sidebar com proteção total contra None"""
    
    user_info = {
        'name': getattr(user, 'name', 'Usuário') if user else 'Usuário',
        'email': getattr(user, 'email', 'user@exemplo.com') if user else 'user@exemplo.com',
        'role': getattr(user, 'role', type('Role', (), {'value': 'admin'})) if user else type('Role', (), {'value': 'admin'}),
        'avatar_url': getattr(user, 'avatar_url', None) if user else None
    }
    
    # Garantir que role.value existe
    try:
        role_value = user_info['role'].value if hasattr(user_info['role'], 'value') else 'admin'
    except:
        role_value = 'admin'
    
    return html.Div(safe_children([
        create_elegant_header(),
        create_elegant_user_section(user_info, role_value),
        create_elegant_navigation(user),
        create_quick_tools(),
        create_elegant_footer(),
    ]), className="sidebar-elegant", id="sidebar-container")

def create_elegant_header():
    """Header seguro"""
    return html.Div(safe_children([
        html.Div(className="header-gradient"),
        dmc.Group(safe_children([
            dmc.ThemeIcon(
                DashIconify(icon="tabler:brand-whatsapp", width=26),
                size=44,
                radius="lg",
                variant="gradient",
                gradient={"from": "teal.4", "to": "green.6", "deg": 45},
                className="logo-elegant"
            ),
            html.Div(safe_children([
                dmc.Text("WppAgent", size="xl", fw=700, className="brand-text-elegant"),
                dmc.Text("Dashboard Pro", size="xs", c="dimmed", className="brand-subtitle")
            ]))
        ]), spacing="sm", align="center")
    ]), className="header-elegant")

def create_elegant_user_section(user_info, role_value):
    """Seção de usuário segura"""
    return html.Div(safe_children([
        dmc.Paper(safe_children([
            html.Div(safe_children([
                dmc.Group(safe_children([
                    html.Div(safe_children([
                        dmc.Avatar(
                            src=user_info.get('avatar_url'),
                            size="lg",
                            radius="xl",
                            color="blue",
                            className="user-avatar-elegant"
                        ),
                        html.Div(className="online-indicator")
                    ]), className="avatar-container"),
                    html.Div(safe_children([
                        dmc.Text(user_info.get('name', 'Usuário'), size="sm", fw=600, c="dark", className="user-name-elegant"),
                        dmc.Group(safe_children([
                            get_elegant_role_badge(role_value),
                            dmc.Badge("Online", size="xs", color="green", variant="dot", className="status-badge")
                        ]), spacing="xs")
                    ]))
                ]), align="center", spacing="md")
            ]), className="user-card-header"),
            
            dmc.Group(safe_children([
                dmc.Button("Perfil", variant="light", size="compact-sm", color="blue", id="user-profile-btn", 
                          className="user-action-elegant", leftIcon=DashIconify(icon="tabler:user", width=14)),
                dmc.Button("Sair", variant="light", size="compact-sm", color="gray", id="logout-button",
                          className="user-action-elegant", leftIcon=DashIconify(icon="tabler:logout", width=14))
            ]), position="apart", mt="sm")
            
        ]), p="md", radius="xl", className="user-card-elegant", withBorder=True)
    ]), className="user-section-elegant")

def create_elegant_navigation(user=None):
    """Navegação segura"""
    nav_items = [
        {"id": "nav-home", "label": "Dashboard", "icon": "tabler:layout-dashboard", "href": "/home", "description": "Visão geral", "color": "blue"},
        {"id": "nav-conversas", "label": "Conversas", "icon": "tabler:message-circle-2", "href": "/conversas", "description": "WhatsApp", "badge": "12", "color": "green"},
        {"id": "nav-clientes", "label": "Clientes", "icon": "tabler:users-group", "href": "/clientes", "description": "Base", "color": "violet"},
        {"id": "nav-agendamentos", "label": "Agendamentos", "icon": "tabler:calendar-event", "href": "/agendamentos", "description": "Agenda", "badge": "3", "color": "orange"},
        {"id": "nav-relatorios", "label": "Relatórios", "icon": "tabler:chart-area-line", "href": "/relatorios", "description": "Analytics", "color": "teal"},
        {"id": "nav-configuracoes", "label": "Configurações", "icon": "tabler:settings-2", "href": "/configuracoes", "description": "Sistema", "color": "gray"}
    ]
    
    return html.Div(safe_children([
        html.Div(safe_children([
            dmc.Text("Navegação", size="xs", c="dimmed", fw=600, tt="uppercase", className="section-title"),
            html.Div(className="title-underline")
        ]), className="section-header"),
        
        html.Div(safe_children([
            create_elegant_nav_item(item) for item in nav_items
        ]), className="nav-list")
        
    ]), className="navigation-elegant")

def create_elegant_nav_item(item):
    """Item de navegação seguro"""
    badge_component = html.Div()
    if item.get("badge"):
        badge_component = dmc.Badge(
            str(item["badge"]),
            size="xs",
            color="red", 
            variant="filled",
            className="nav-badge-elegant pulse-animation"
        )
    
    return html.Div(safe_children([
        dmc.Anchor(safe_children([
            html.Div(className="nav-indicator"),
            dmc.Group(safe_children([
                dmc.ThemeIcon(
                    DashIconify(icon=item.get("icon", "tabler:help-circle"), width=18),
                    size="sm",
                    variant="light",
                    color=item.get("color", "blue"),
                    className="nav-icon-elegant"
                ),
                html.Div(safe_children([
                    dmc.Group(safe_children([
                        dmc.Text(item.get("label", "Item"), size="sm", fw=500, className="nav-label-elegant"),
                        badge_component
                    ]), position="apart", align="center"),
                    dmc.Text(item.get("description", ""), size="xs", c="dimmed", className="nav-description")
                ]))
            ]), align="center", spacing="md")
        ]), href=item.get("href", "/"), id=item.get("id", "nav-item"), className="nav-item-elegant", td="none")
    ]), className="nav-item-container")

def create_quick_tools():
    """Ferramentas rápidas seguras"""
    tools = [
        {"icon": "tabler:message-plus", "label": "Nova Conversa", "color": "green", "id": "quick-nova-conversa"},
        {"icon": "tabler:calendar-plus", "label": "Novo Agendamento", "color": "blue", "id": "quick-novo-agendamento"},
        {"icon": "tabler:user-plus", "label": "Novo Cliente", "color": "violet", "id": "quick-novo-cliente"},
        {"icon": "tabler:file-export", "label": "Exportar", "color": "orange", "id": "quick-exportar"}
    ]
    
    return html.Div(safe_children([
        html.Div(safe_children([
            dmc.Text("Ações Rápidas", size="xs", c="dimmed", fw=600, tt="uppercase", className="section-title"),
            html.Div(className="title-underline")
        ]), className="section-header"),
        
        html.Div(safe_children([
            html.Div(safe_children([
                dmc.Button(safe_children([
                    dmc.Group(safe_children([
                        dmc.ThemeIcon(
                            DashIconify(icon=tool.get("icon", "tabler:help-circle"), width=14),
                            size="sm",
                            variant="light",
                            color=tool.get("color", "blue"),
                            radius="sm"
                        ),
                        dmc.Text(tool.get("label", "Ação"), size="xs", fw=500, c="dark")
                    ]), spacing="xs", align="center")
                ]), id=tool.get("id", f"tool-{i}"), className="quick-action-fixed")
            ])) for i, tool in enumerate(tools)
        ]))
    ]), className="quick-tools-section")

def create_elegant_footer():
    """Footer seguro"""
    return html.Div(safe_children([
        html.Div(className="footer-divider"),
        dmc.Paper(safe_children([
            dmc.Group(safe_children([
                html.Div(safe_children([
                    dmc.ThemeIcon(
                        DashIconify(icon="tabler:server-2", width=14),
                        size="xs",
                        variant="light",
                        color="green",
                        className="system-icon"
                    ),
                    html.Div(className="pulse-dot")
                ]), className="status-indicator-container"),
                html.Div(safe_children([
                    dmc.Text("Sistema Online", size="xs", fw=500, c="dark"),
                    dmc.Text("Atualizado agora", size="xs", c="dimmed")
                ]))
            ]), align="center", spacing="sm")
        ]), p="sm", radius="md", className="status-card"),
        
        html.Div(safe_children([
            dmc.Text("© 2024 WppAgent", size="xs", c="dimmed", ta="center", className="copyright-text")
        ]), className="copyright-section")
        
    ]), className="footer-elegant")

def get_elegant_role_badge(role):
    """Badge segura para role"""
    role_config = {
        'super_admin': {'label': 'Super Admin', 'gradient': {"from": "red.4", "to": "pink.4"}},
        'admin': {'label': 'Admin', 'gradient': {"from": "blue.4", "to": "cyan.4"}},
        'manager': {'label': 'Manager', 'gradient': {"from": "green.4", "to": "teal.4"}},
        'operator': {'label': 'Operador', 'gradient': {"from": "orange.4", "to": "yellow.4"}},
        'viewer': {'label': 'Viewer', 'gradient': {"from": "gray.4", "to": "gray.6"}}
    }
    
    config = role_config.get(role, role_config['viewer'])
    return dmc.Badge(
        config['label'],
        size="xs", 
        variant="gradient",
        gradient=config['gradient'],
        className="role-badge-elegant"
    )

def register_sidebar_callbacks(app):
    """Callbacks seguros do sidebar"""
    nav_ids = ["nav-home", "nav-conversas", "nav-clientes", "nav-agendamentos", "nav-relatorios", "nav-configuracoes"]
    
    @app.callback(
        [Output(nav_id, "className") for nav_id in nav_ids],
        Input("url", "pathname")
    )
    def update_active_nav(pathname):
        base_class = "nav-item-elegant"
        active_class = "nav-item-elegant nav-item-active-elegant"
        
        classes = [base_class] * len(nav_ids)
        path_mapping = {"/": 0, "/home": 0, "/conversas": 1, "/clientes": 2, "/agendamentos": 3, "/relatorios": 4, "/configuracoes": 5}
        
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
        if n_clicks:
            return "/perfil"
        return no_update
