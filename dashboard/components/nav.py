"""
Navigation Component
===================

Componente de navegação principal com estilo glass/backdrop-filter.
Design inspirado no Anthropic-light com foco em UX limpa.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from dash_iconify import DashIconify

def create_navigation():
    """
    Cria a navegação principal do dashboard.
    
    Features:
    - Design glass com backdrop-filter
    - Responsiva (colapsa em mobile)
    - Indicador de página ativa
    - Logo/brand area
    """
    
    # Links de navegação
    nav_links = [
        {
            "label": "Visão Geral",
            "href": "/home",
            "icon": "home",
            "id": "nav-home"
        },
        {
            "label": "Relatórios", 
            "href": "/relatorios",
            "icon": "chart-bar",
            "id": "nav-relatorios"
        },
        {
            "label": "Perfil",
            "href": "/perfil", 
            "icon": "user",
            "id": "nav-perfil"
        }
    ]
    
    # Navbar usando DBC com classe custom
    navbar = dbc.Navbar(
        dbc.Container([
            # Brand/Logo
            dbc.NavbarBrand([
                dmc.Group([
                    dmc.ThemeIcon(
                        DashIconify(icon="tabler:brand-whatsapp", width=24),
                        color="teal",
                        variant="light",
                        size="lg"
                    ),
                    dmc.Text(
                        "WPPAgent",
                        size="lg",
                        fw=700,
                        className="heading"
                    )
                ], spacing="sm")
            ], href="/home", className="navbar-brand-custom"),
            
            # Toggle para mobile
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            
            # Collapse menu
            dbc.Collapse(
                dbc.Nav([
                    # Links principais
                    *[
                        dbc.NavItem(
                            dbc.NavLink(
                                dmc.Group([
                                    DashIconify(icon="tabler:home", width=18) if link["icon"] == "home" else
                                    DashIconify(icon="tabler:chart-bar", width=18) if link["icon"] == "chart-bar" else
                                    DashIconify(icon="tabler:user", width=18),
                                    dmc.Text(link["label"], size="sm", fw=500)
                                ], spacing="xs"),
                                href=link["href"],
                                id=link["id"],
                                className="nav-link-custom"
                            )
                        ) for link in nav_links
                    ],
                    
                    # Separator
                    html.Div(className="nav-separator"),
                    
                    # Status/Health indicator
                    dbc.NavItem([
                        dmc.Indicator(
                            dmc.ActionIcon(
                                DashIconify(icon="tabler:database", width=18),
                                variant="light",
                                color="gray",
                                id="health-indicator"
                            ),
                            color="green",
                            size="sm",
                            processing=False,
                            id="health-indicator-dot"
                        )
                    ])
                    
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                is_open=False,
                navbar=True
            )
        ], fluid=True),
        className="navbar-glass fixed-top",
        color="light",
        sticky="top"
    )
    
    return navbar

def create_breadcrumb(current_page: str, parent_page: str = None):
    """
    Cria breadcrumb para navegação secundária.
    
    Args:
        current_page: Nome da página atual
        parent_page: Página pai (opcional)
    """
    
    items = [
        dmc.Anchor("Início", href="/home", c="dimmed", td="none")
    ]
    
    if parent_page:
        items.append(dmc.Text("/", c="dimmed", span=True))
        items.append(dmc.Anchor(parent_page, c="dimmed", td="none"))
    
    items.extend([
        dmc.Text("/", c="dimmed", span=True),
        dmc.Text(current_page, fw=500)
    ])
    
    return dmc.Group(items, spacing="xs", className="breadcrumb-custom")

def create_page_header(title: str, subtitle: str = None, actions: list = None):
    """
    Cria cabeçalho padrão para páginas.
    
    Args:
        title: Título principal
        subtitle: Subtítulo/descrição (opcional)
        actions: Lista de componentes de ação (botões, etc)
    """
    
    header_content = [
        dmc.Group([
            dmc.Stack([
                dmc.Title(title, order=1, className="page-title"),
                dmc.Text(subtitle, c="dimmed") if subtitle else html.Div()
            ], spacing="xs"),
            
            # Actions (botões, filtros, etc)
            dmc.Group(actions or [], spacing="sm") if actions else html.Div()
            
        ], position="space-between", align="flex-start")
    ]
    
    return dmc.Container([
        dmc.Stack(header_content, spacing="md")
    ], size="xl", px="md", py="lg", className="page-header")

def create_mobile_nav():
    """
    Navegação mobile alternativa (bottom tabs) - opcional
    """
    return dmc.Group([
        dmc.Anchor([
            dmc.Stack([
                DashIconify(icon="tabler:home", width=20),
                dmc.Text("Início", size="xs")
            ], align="center", spacing="xs")
        ], href="/home", td="none", c="dimmed"),
        
        dmc.Anchor([
            dmc.Stack([
                DashIconify(icon="tabler:chart-bar", width=20),
                dmc.Text("Relatórios", size="xs")
            ], align="center", spacing="xs")
        ], href="/relatorios", td="none", c="dimmed"),
        
        dmc.Anchor([
            dmc.Stack([
                DashIconify(icon="tabler:user", width=20),
                dmc.Text("Perfil", size="xs")
            ], align="center", spacing="xs")
        ], href="/perfil", td="none", c="dimmed")
        
    ], position="space-around", className="mobile-nav d-md-none")
