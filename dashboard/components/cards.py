"""
Card Components
===============

Componentes de cards reutilizáveis para KPIs, métricas e conteúdo geral.
Seguem o design system Anthropic-light inspired.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from dash_iconify import DashIconify
from typing import Any, Optional, Dict, List

def create_kpi_card(
    title: str,
    value: Any,
    subtitle: str = None,
    icon: str = None,
    color: str = "blue",
    trend: Optional[Dict] = None,
    loading: bool = False
):
    """
    Card para exibir KPIs/métricas principais.
    
    Args:
        title: Título do KPI
        value: Valor principal (número, texto, etc)
        subtitle: Subtítulo/descrição
        icon: Nome do ícone (DMC)
        color: Cor do tema
        trend: Dict com 'value', 'direction' ('up'|'down'), 'period'
        loading: Estado de carregamento
    """
    
    # Ícone baseado no nome
    icon_component = None
    if icon == "users":
        icon_component = DashIconify(icon="tabler:users", width=20)
    elif icon == "messages":
        icon_component = DashIconify(icon="tabler:message", width=20)
    elif icon == "clock":
        icon_component = DashIconify(icon="tabler:clock", width=20)
    elif icon == "check":
        icon_component = DashIconify(icon="tabler:check", width=20)
    elif icon == "trending-up":
        icon_component = DashIconify(icon="tabler:trending-up", width=20)
    else:
        icon_component = DashIconify(icon="tabler:info-circle", width=20)
    
    # Componente de trend
    trend_component = None
    if trend:
        trend_color = "green" if trend.get("direction") == "up" else "red"
        trend_icon = DashIconify(icon="tabler:trending-up", width=14) if trend.get("direction") == "up" else DashIconify(icon="tabler:trending-down", width=14)
        
        trend_component = dmc.Group([
            dmc.Group([
                trend_icon,
                dmc.Text(f"{trend.get('value', 0)}%", size="sm", fw=500, c=trend_color)
            ], spacing="xs"),
            dmc.Text(trend.get("period", "vs período anterior"), size="xs", c="dimmed")
        ], spacing="xs")
    
    card_content = [
        # Header com ícone e título
        dmc.Group([
            # Renderiza ícone apenas se existir - CORRIGIDO
            dmc.ThemeIcon(
                icon_component,
                color=color,
                variant="light",
                size="lg"
            ) if icon_component else html.Div(),
            dmc.Stack([
                dmc.Text(title, size="sm", fw=500, c="dimmed"),
                # Renderiza subtitle apenas se existir - CORRIGIDO
                dmc.Text(subtitle, size="xs", c="dimmed") if subtitle else html.Div()
            ], spacing="xs")
        ], position="space-between", align="flex-start"),
        
        # Valor principal
        dmc.Text(
            str(value) if not loading else "---",
            size="xl",
            fw=700,
            className="heading"
        ),
        
        # Trend/comparação
        trend_component
    ]
    
    return dmc.Card([
        dmc.Stack([comp for comp in card_content if comp is not None], spacing="sm")
    ], shadow="sm", p="md", radius="md", className="kpi-card")

def create_stat_card(
    title: str,
    stats: List[Dict[str, Any]],
    color: str = "blue"
):
    """
    Card com múltiplas estatísticas pequenas.
    
    Args:
        title: Título do card
        stats: Lista de dicts com 'label', 'value', 'color' (opcional)
        color: Cor principal
    """
    
    stat_items = []
    for stat in stats:
        stat_items.append(
            dmc.Group([
                dmc.Text(stat["label"], size="sm", c="dimmed"),
                dmc.Badge(
                    stat["value"],
                    color=stat.get("color", color),
                    variant="light"
                )
            ], position="space-between")
        )
    
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading"),
            dmc.Stack(stat_items, spacing="xs")
        ], spacing="md")
    ], shadow="sm", p="md", radius="md", className="stat-card")

def create_chart_card(
    title: str,
    chart_component: Any,
    subtitle: str = None,
    actions: List[Any] = None,
    loading: bool = False
):
    """
    Card para gráficos e visualizações.
    
    Args:
        title: Título do gráfico
        chart_component: Componente do gráfico (Plotly, etc)
        subtitle: Subtítulo/período
        actions: Lista de botões/controles
        loading: Estado de carregamento
    """
    
    header = dmc.Group([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading"),
            # Renderiza subtitle apenas se existir - CORRIGIDO
            dmc.Text(subtitle, size="sm", c="dimmed") if subtitle else html.Div()
        ], spacing="xs"),
        
        # Renderiza actions apenas se existir - CORRIGIDO
        dmc.Group(actions or [], spacing="sm") if actions else html.Div()
    ], position="space-between", align="flex-start")
    
    content = chart_component
    
    if loading:
        content = dmc.Center([
            dmc.Loader(color="blue", size="lg")
        ], style={"minHeight": "300px"})
    
    return dmc.Card([
        dmc.Stack([
            header,
            content
        ], spacing="md")
    ], shadow="sm", p="md", radius="md", className="chart-card")

def create_info_card(
    title: str,
    content: Any,
    icon: str = None,
    color: str = "blue",
    variant: str = "default"
):
    """
    Card informativo genérico.
    
    Args:
        title: Título
        content: Conteúdo (texto, componentes)
        icon: Ícone opcional
        color: Cor do tema
        variant: 'default', 'outline', 'light'
    """
    
    # Ícones disponíveis
    icon_map = {
        "info": DashIconify(icon="tabler:info-circle", width=20),
        "warning": DashIconify(icon="tabler:alert-triangle", width=20),
        "success": DashIconify(icon="tabler:check", width=20),
        "error": DashIconify(icon="tabler:x", width=20),
        "settings": DashIconify(icon="tabler:settings", width=20),
        "database": DashIconify(icon="tabler:database", width=20)
    }
    
    header_content = [
        # Renderiza ícone apenas se existir - CORRIGIDO
        dmc.ThemeIcon(
            icon_map.get(icon, DashIconify(icon="tabler:info-circle", width=20)),
            color=color,
            variant="light",
            size="lg"
        ) if icon else html.Div(),
        dmc.Text(title, size="lg", fw=600, className="heading")
    ]
    
    card_props = {
        "shadow": "sm",
        "p": "md", 
        "radius": "md",
        "className": "info-card"
    }
    
    if variant == "outline":
        card_props["withBorder"] = True
    elif variant == "light":
        card_props["className"] += " info-card-light"
    
    return dmc.Card([
        dmc.Stack([
            dmc.Group([comp for comp in header_content if comp is not None], spacing="sm"),
            content if isinstance(content, (list, tuple)) else dmc.Text(content)
        ], spacing="md")
    ], **card_props)

def create_action_card(
    title: str,
    description: str,
    action_text: str,
    action_href: str = None,
    action_id: str = None,
    icon: str = None,
    color: str = "blue"
):
    """
    Card com call-to-action.
    
    Args:
        title: Título principal
        description: Descrição
        action_text: Texto do botão
        action_href: Link (se for navegação)
        action_id: ID do botão (se for callback)
        icon: Ícone opcional
        color: Cor do tema
    """
    
    icon_component = None
    if icon:
        icon_map = {
            "arrow-right": DashIconify(icon="tabler:arrow-right", width=16),
            "download": DashIconify(icon="tabler:download", width=16),
            "external": DashIconify(icon="tabler:external-link", width=16),
            "plus": DashIconify(icon="tabler:plus", width=16)
        }
        icon_component = icon_map.get(icon)
    
    button_props = {
        "color": color,
        "variant": "light",
        "rightIcon": icon_component
    }
    
    if action_href:
        button = dmc.Anchor(
            dmc.Button(action_text, **button_props),
            href=action_href,
            td="none"
        )
    else:
        button = dmc.Button(
            action_text,
            id=action_id,
            **button_props
        )
    
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading"),
            dmc.Text(description, c="dimmed"),
            button
        ], spacing="md")
    ], shadow="sm", p="md", radius="md", className="action-card")

def create_list_card(
    title: str,
    items: List[Dict[str, Any]],
    show_all_href: str = None,
    empty_message: str = "Nenhum item encontrado"
):
    """
    Card com lista de itens (ex: últimas atividades).
    
    Args:
        title: Título do card
        items: Lista de dicts com 'title', 'subtitle', 'time', 'status' etc
        show_all_href: Link para "ver todos"
        empty_message: Mensagem quando lista vazia
    """
    
    header = dmc.Group([
        dmc.Text(title, size="lg", fw=600, className="heading"),
        # Renderiza link apenas se existir - CORRIGIDO
        dmc.Anchor(
            "Ver todos",
            href=show_all_href,
            size="sm",
            td="none"
        ) if show_all_href else html.Div()
    ], position="space-between")
    
    if not items:
        content = dmc.Center([
            dmc.Text(empty_message, c="dimmed", size="sm")
        ], py="xl")
    else:
        list_items = []
        for item in items[:5]:  # Limita a 5 itens
            
            # Status badge se existir
            status_badge = None
            if item.get("status"):
                status_colors = {
                    "ativo": "green",
                    "pendente": "yellow", 
                    "concluido": "blue",
                    "erro": "red"
                }
                status_badge = dmc.Badge(
                    item["status"],
                    color=status_colors.get(item["status"], "gray"),
                    size="sm",
                    variant="light"
                )
            
            list_items.append(
                dmc.Group([
                    dmc.Stack([
                        dmc.Text(item["title"], size="sm", fw=500),
                        dmc.Text(item.get("subtitle", ""), size="xs", c="dimmed")
                    ], spacing="xs"),
                    
                    # Só renderiza se houver status_badge ou time - CORRIGIDO
                    dmc.Stack([
                        status_badge,
                        dmc.Text(item.get("time", ""), size="xs", c="dimmed")
                    ], spacing="xs", align="flex-end") if (status_badge or item.get("time")) else html.Div()
                    
                ], position="space-between", align="flex-start")
            )
        
        content = dmc.Stack(list_items, spacing="md")
    
    return dmc.Card([
        dmc.Stack([header, content], spacing="md")
    ], shadow="sm", p="md", radius="md", className="list-card")

def create_metric_grid(metrics: List[Dict[str, Any]], columns: int = 4):
    """
    Grid responsivo de métricas/KPIs.
    
    Args:
        metrics: Lista de métricas (para create_kpi_card)
        columns: Número de colunas no desktop
    """
    
    cards = [
        create_kpi_card(**metric) for metric in metrics
    ]
    
    return dmc.SimpleGrid(
        cards,
        cols={"base": 1, "sm": 2, "md": columns},
        spacing="md",
        className="metric-grid"
    )
