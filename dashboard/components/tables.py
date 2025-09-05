"""
Table Components
================

Componentes de tabelas reutilizáveis com paginação, ordenação e filtros.
Design consistente com o tema Anthropic-light.
"""

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html, dash_table
from dash_iconify import DashIconify
from typing import List, Dict, Any, Optional
from datetime import datetime
import math

def create_data_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    table_id: str,
    page_size: int = 10,
    sortable: bool = True,
    filterable: bool = False,
    selectable: bool = False,
    export_csv: bool = False
):
    """
    Tabela de dados com funcionalidades avançadas usando dash_table.
    
    Args:
        data: Lista de dicionários com os dados
        columns: Lista de dicts com 'name', 'id', 'type' (opcional)
        table_id: ID único da tabela
        page_size: Itens por página
        sortable: Habilita ordenação
        filterable: Habilita filtros
        selectable: Habilita seleção de linhas
        export_csv: Habilita export CSV
    """
    
    # Configuração das colunas
    table_columns = []
    for col in columns:
        column_config = {
            "name": col["name"],
            "id": col["id"],
            "type": col.get("type", "text")
        }
        
        # Formatação específica por tipo
        if col.get("type") == "numeric":
            column_config["format"] = {"specifier": ".2f"}
        elif col.get("type") == "datetime":
            column_config["format"] = {"specifier": "%d/%m/%Y %H:%M"}
        
        table_columns.append(column_config)
    
    # Configuração da tabela
    table_props = {
        "id": table_id,
        "data": data,
        "columns": table_columns,
        "page_size": page_size,
        "page_action": "native",
        "style_table": {
            "overflowX": "auto",
            "backgroundColor": "var(--surface)"
        },
        "style_header": {
            "backgroundColor": "var(--surface-2)",
            "color": "var(--text)",
            "fontWeight": "600",
            "border": "1px solid var(--border)",
            "textAlign": "left",
            "padding": "12px 16px"
        },
        "style_cell": {
            "backgroundColor": "var(--surface)",
            "color": "var(--text)",
            "border": "1px solid var(--border-light)",
            "textAlign": "left",
            "padding": "12px 16px",
            "fontFamily": "var(--font-body)"
        },
        "style_data_conditional": [
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "var(--surface-2)"
            }
        ]
    }
    
    # Adiciona funcionalidades opcionais
    if sortable:
        table_props["sort_action"] = "native"
        table_props["sort_mode"] = "multi"
    
    if filterable:
        table_props["filter_action"] = "native"
    
    if selectable:
        table_props["row_selectable"] = "multi"
    
    if export_csv:
        table_props["export_format"] = "csv"
        table_props["export_headers"] = "display"
    
    table = dash_table.DataTable(**table_props)
    
    return dmc.Card([
        table
    ], shadow="sm", p="md", radius="md", className="data-table-card")

def create_simple_table(
    data: List[Dict[str, Any]],
    headers: List[str],
    title: str = None,
    max_rows: int = None,
    striped: bool = True,
    hover: bool = True
):
    """
    Tabela simples usando DBC Table para exibição básica.
    
    Args:
        data: Lista de dicionários
        headers: Lista de cabeçalhos
        title: Título da tabela
        max_rows: Máximo de linhas a exibir
        striped: Linhas zebradas
        hover: Hover effect
    """
    
    if not data:
        empty_content = dmc.Center([
            dmc.Stack([
                DashIconify(icon="tabler:table", width=48, height=48, color="gray"),
                dmc.Text("Nenhum dado disponível", c="dimmed")
            ], align="center", spacing="sm")
        ], py="xl")
        
        return dmc.Card([
            dmc.Stack([
                dmc.Text(title, size="lg", fw=600, className="heading") if title else html.Div(),
                empty_content
            ], spacing="md")
        ], shadow="sm", p="md", radius="md")
    
    # Limita as linhas se especificado
    display_data = data[:max_rows] if max_rows else data
    
    # Cria as linhas da tabela
    table_rows = []
    for row_data in display_data:
        cells = []
        for header in headers:
            value = row_data.get(header, "")
            
            # Formatação básica por tipo
            if isinstance(value, datetime):
                value = value.strftime("%d/%m/%Y %H:%M")
            elif isinstance(value, (int, float)):
                value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
            
            cells.append(html.Td(str(value)))
        
        table_rows.append(html.Tr(cells))
    
    # Tabela
    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th(header) for header in headers
            ])
        ]),
        html.Tbody(table_rows)
    ], striped=striped, hover=hover, responsive=True, className="custom-table")
    
    content = [table]
    
    # Adiciona indicador se há mais dados
    if max_rows and len(data) > max_rows:
        content.append(
            dmc.Text(
                f"Exibindo {max_rows} de {len(data)} registros",
                size="sm",
                c="dimmed",
                ta="center",
                mt="md"
            )
        )
    
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading") if title else html.Div(),
            *content
        ], spacing="md")
    ], shadow="sm", p="md", radius="md", className="simple-table-card")

def create_comparison_table(
    data: List[Dict[str, Any]],
    title: str = "Comparação",
    metric_column: str = "metric",
    value_columns: List[str] = None
):
    """
    Tabela de comparação (ex: atual vs anterior).
    
    Args:
        data: Dados com métricas e valores
        title: Título da tabela
        metric_column: Coluna com nome das métricas
        value_columns: Colunas com valores a comparar
    """
    
    if not value_columns:
        value_columns = ["atual", "anterior"]
    
    rows = []
    for item in data:
        cells = [html.Td(item.get(metric_column, ""))]
        
        for col in value_columns:
            value = item.get(col, 0)
            
            # Formatação do valor
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,.0f}" if isinstance(value, float) and value.is_integer() else f"{value:,.2f}"
            else:
                formatted_value = str(value)
            
            cells.append(html.Td(formatted_value))
        
        # Adiciona coluna de variação se tiver 2 valores
        if len(value_columns) == 2:
            atual = item.get(value_columns[0], 0)
            anterior = item.get(value_columns[1], 0)
            
            if anterior != 0:
                variacao = ((atual - anterior) / anterior) * 100
                cor = "success" if variacao >= 0 else "red"
                sinal = "+" if variacao >= 0 else ""
                
                cells.append(html.Td([
                    dmc.Text(f"{sinal}{variacao:.1f}%", c=cor, fw=500)
                ]))
            else:
                cells.append(html.Td("-"))
        
        rows.append(html.Tr(cells))
    
    headers = [metric_column.title()] + [col.title() for col in value_columns]
    if len(value_columns) == 2:
        headers.append("Variação")
    
    table = dbc.Table([
        html.Thead([
            html.Tr([html.Th(header) for header in headers])
        ]),
        html.Tbody(rows)
    ], hover=True, className="comparison-table")
    
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading"),
            table
        ], spacing="md")
    ], shadow="sm", p="md", radius="md")

def create_status_table(
    data: List[Dict[str, Any]],
    title: str = "Status",
    status_column: str = "status",
    status_colors: Dict[str, str] = None
):
    """
    Tabela com coluna de status destacada.
    
    Args:
        data: Dados da tabela
        title: Título
        status_column: Nome da coluna de status
        status_colors: Mapeamento status -> cor
    """
    
    if not status_colors:
        status_colors = {
            "ativo": "green",
            "inativo": "red",
            "pendente": "yellow",
            "concluido": "blue",
            "processando": "orange"
        }
    
    rows = []
    for item in data:
        cells = []
        
        for key, value in item.items():
            if key == status_column:
                # Status com badge colorido
                color = status_colors.get(value, "gray")
                badge = dmc.Badge(
                    value,
                    color=color,
                    variant="light",
                    size="sm"
                )
                cells.append(html.Td(badge))
            else:
                # Formatação padrão
                if isinstance(value, datetime):
                    value = value.strftime("%d/%m/%Y %H:%M")
                
                cells.append(html.Td(str(value)))
        
        rows.append(html.Tr(cells))
    
    # Cabeçalhos
    headers = []
    if data:
        headers = [key.replace("_", " ").title() for key in data[0].keys()]
    
    table = dbc.Table([
        html.Thead([
            html.Tr([html.Th(header) for header in headers])
        ]),
        html.Tbody(rows)
    ], hover=True, striped=True, className="status-table")
    
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="lg", fw=600, className="heading"),
            table
        ], spacing="md")
    ], shadow="sm", p="md", radius="md")

def create_pagination_controls(
    current_page: int,
    total_pages: int,
    total_items: int,
    page_size: int,
    pagination_id: str
):
    """
    Controles de paginação customizados.
    
    Args:
        current_page: Página atual
        total_pages: Total de páginas
        total_items: Total de itens
        page_size: Itens por página
        pagination_id: ID base para os controles
    """
    
    # Informação de itens
    start_item = (current_page - 1) * page_size + 1
    end_item = min(current_page * page_size, total_items)
    
    info_text = f"Exibindo {start_item}-{end_item} de {total_items} itens"
    
    # Botões de navegação
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages
    
    controls = dmc.Group([
        # Info dos itens
        dmc.Text(info_text, size="sm", c="dimmed"),
        
        # Controles de navegação
        dmc.Group([
            dmc.ActionIcon(
                DashIconify(icon="tabler:chevronleft", width=16, height=16),
                variant="light",
                disabled=prev_disabled,
                id=f"{pagination_id}-prev"
            ),
            
            dmc.Text(f"Página {current_page} de {total_pages}", size="sm", fw=500),
            
            dmc.ActionIcon(
                DashIconify(icon="tabler:chevronright", width=16, height=16),
                variant="light", 
                disabled=next_disabled,
                id=f"{pagination_id}-next"
            )
        ], spacing="xs")
        
    ], position="space-between", className="pagination-controls")
    
    return controls

def create_table_filters(
    filters: List[Dict[str, Any]],
    filter_id_prefix: str = "filter"
):
    """
    Cria filtros para tabelas.
    
    Args:
        filters: Lista de filtros com 'type', 'label', 'options' etc
        filter_id_prefix: Prefixo para IDs dos filtros
    """
    
    filter_components = []
    
    for i, filter_config in enumerate(filters):
        filter_id = f"{filter_id_prefix}-{i}"
        filter_type = filter_config.get("type", "select")
        
        if filter_type == "select":
            component = dmc.Select(
                label=filter_config.get("label", "Filtro"),
                data=filter_config.get("options", []),
                placeholder=filter_config.get("placeholder", "Selecione..."),
                clearable=True,
                id=filter_id,
                style={"minWidth": "200px"}
            )
        
        elif filter_type == "date":
            component = dmc.DatePicker(
                label=filter_config.get("label", "Data"),
                placeholder=filter_config.get("placeholder", "Selecione a data"),
                clearable=True,
                id=filter_id,
                style={"minWidth": "180px"}
            )
        
        elif filter_type == "text":
            component = dmc.TextInput(
                label=filter_config.get("label", "Buscar"),
                placeholder=filter_config.get("placeholder", "Digite para buscar..."),
                id=filter_id,
                style={"minWidth": "200px"}
            )
        
        else:
            continue
        
        filter_components.append(component)
    
    if not filter_components:
        return html.Div()
    
    return dmc.Group(
        filter_components,
        spacing="md",
        className="table-filters"
    )

def create_export_button(
    table_data: List[Dict[str, Any]],
    filename: str = "export",
    button_id: str = "export-btn"
):
    """
    Botão de exportação de dados da tabela.
    
    Args:
        table_data: Dados para exportar
        filename: Nome do arquivo
        button_id: ID do botão
    """
    
    return dmc.Button(
        "Exportar CSV",
        leftIcon=DashIconify(icon="tabler:download", width=16, height=16),
        variant="light",
        color="blue",
        id=button_id,
        className="export-button"
    )
