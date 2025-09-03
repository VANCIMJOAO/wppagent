"""
Agendamentos Layout - Design Moderno & Compatível
================================================

Interface modernizada para gerenciamento de agendamentos com:
- Hero section com gradiente
- Cards KPI modernos bem formatados
- Layout responsivo compacto
- Compatibilidade com dmc 0.12.1
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime, timedelta

from services.queries import AgendamentosQueries

def create_agendamentos_layout():
    """
    Layout moderno da página de agendamentos com design premium.
    """
    
    # Busca dados reais dos agendamentos
    try:
        appointments = AgendamentosQueries.get_appointments()
        stats = AgendamentosQueries.get_appointment_stats()
        today_appointments = AgendamentosQueries.get_appointments_by_date(datetime.now().date())
    except Exception as e:
        print(f"Erro ao buscar agendamentos: {e}")
        # Dados de exemplo para visualização quando a database não funciona
        appointments = [
            {
                "id": 1,
                "customer_name": "Maria Silva",
                "phone_number": "11987654321",
                "appointment_datetime": "2025-08-27T10:00:00",
                "service_type": "Limpeza de Pele Profunda",
                "status": "confirmed",
                "notes": "Cliente preferencial, primeira consulta"
            },
            {
                "id": 2,
                "customer_name": "João Santos",
                "phone_number": "11976543210",
                "appointment_datetime": "2025-08-27T14:30:00",
                "service_type": "Consulta Dermatológica",
                "status": "pending",
                "notes": "Indicação médica para tratamento de acne"
            },
            {
                "id": 3,
                "customer_name": "Ana Costa",
                "phone_number": "11965432109",
                "appointment_datetime": "2025-08-28T09:15:00",
                "service_type": "Hidratação Facial",
                "status": "confirmed",
                "notes": "Pele sensível, evitar produtos com álcool"
            }
        ]
        today_appointments = appointments[:2]  # Primeiros 2 para hoje
        stats = {
            "total": 17,
            "confirmed": 12,
            "pending": 3,
            "cancelled": 2,
            "today": 2,
            "tomorrow": 4,
            "this_week": 8
        }
    
    return dmc.Container(
        children=[
            # Hero Section Compacta
            html.Div([
                html.Div([
                    dmc.Group([
                        dmc.Stack([
                            dmc.Group([
                                DashIconify(
                                    icon="tabler:calendar-event",
                                    width=32,
                                    height=32,
                                    color="white"
                                ),
                                dmc.Title(
                                    "Agendamentos",
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
                                f"Gerencie seus {stats['total']} agendamentos • {stats['today']} para hoje",
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
                                "Novo Agendamento",
                                leftIcon=DashIconify(icon="tabler:plus", width=18),
                                size="md",
                                radius="lg",
                                variant="white",
                                color="dark",
                                id="new-appointment-btn",
                                style={
                                    "fontWeight": "600",
                                    "boxShadow": "0 4px 16px rgba(255, 255, 255, 0.3)"
                                }
                            ),
                            dmc.Button(
                                "Exportar",
                                leftIcon=DashIconify(icon="tabler:download", width=18),
                                size="md",
                                radius="lg",
                                variant="outline",
                                color="white",
                                id="export-appointments-btn",
                                style={
                                    "borderColor": "rgba(255, 255, 255, 0.5)",
                                    "color": "white",
                                    "fontWeight": "500"
                                }
                            )
                        ], spacing="sm")
                    ], position="apart", align="center")
                ], className="hero-content")
            ], className="appointments-hero", style={
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "margin": "-24px -16px 24px -16px",
                "padding": "32px 24px",
                "borderRadius": "0 0 16px 16px"
            }),
            
            # Cards KPI Compactos e Bem Formatados
            dmc.SimpleGrid(
                cols=4,
                spacing="md",
                breakpoints=[
                    {"maxWidth": "md", "cols": 2},
                    {"maxWidth": "sm", "cols": 1}
                ],
                style={"marginBottom": "16px"},
                children=[
                    create_compact_kpi_card(
                        "Hoje", 
                        stats['today'], 
                        "calendar-check", 
                        "#10b981",
                        "Agendamentos para hoje"
                    ),
                    create_compact_kpi_card(
                        "Amanhã", 
                        stats['tomorrow'], 
                        "calendar-plus", 
                        "#3b82f6",
                        "Próximos agendamentos"
                    ),
                    create_compact_kpi_card(
                        "Pendentes", 
                        stats['pending'], 
                        "calendar-time", 
                        "#f59e0b",
                        "Aguardando confirmação"
                    ),
                    create_compact_kpi_card(
                        "Esta Semana", 
                        stats['this_week'], 
                        "calendar-stats", 
                        "#8b5cf6",
                        "Total da semana"
                    )
                ]
            ),
            
            # Filtros Compactos
            dmc.Paper([
                dmc.Group([
                    dmc.SegmentedControl(
                        data=[
                            {"label": f"Todos ({stats['total']})", "value": "all"},
                            {"label": f"Confirmados ({stats['confirmed']})", "value": "confirmed"},
                            {"label": f"Pendentes ({stats['pending']})", "value": "pending"},
                            {"label": f"Cancelados ({stats['cancelled']})", "value": "cancelled"}
                        ],
                        value="all",
                        id="appointments-filter",
                        size="sm"
                    ),
                    
                    dmc.Group([
                        dmc.DatePicker(
                            placeholder="Data inicial",
                            id="start-date-filter",
                            size="sm",
                            style={"minWidth": "140px"}
                        ),
                        dmc.DatePicker(
                            placeholder="Data final",
                            id="end-date-filter", 
                            size="sm",
                            style={"minWidth": "140px"}
                        ),
                        dmc.Button(
                            "Filtrar",
                            leftIcon=DashIconify(icon="tabler:filter", width=16),
                            variant="light",
                            color="blue",
                            id="apply-date-filter",
                            size="sm"
                        )
                    ], spacing="sm")
                ], position="apart", align="center")
            ], p="md", radius="lg", shadow="sm", style={"marginBottom": "16px"}),
            
            # Layout Principal Otimizado
            html.Div([
                # Sidebar Compacta
                html.Div([
                    dmc.Stack([
                        # Calendário Compacto
                        dmc.Paper([
                            dmc.Stack([
                                dmc.Group([
                                    DashIconify(icon="tabler:calendar", width=20, color="#667eea"),
                                    dmc.Text("Calendário", weight=600, size="sm")
                                ], align="center"),
                                dmc.Text(
                                    f"Hoje: {datetime.now().strftime('%d/%m/%Y')}",
                                    size="xs",
                                    color="dimmed",
                                    align="center"
                                )
                            ], spacing="sm")
                        ], p="md", radius="lg", shadow="sm"),
                        
                        # Agendamentos Hoje Compactos
                        dmc.Paper([
                            dmc.Stack([
                                dmc.Group([
                                    dmc.Text("Agendamentos Hoje", weight=600, size="sm"),
                                    dmc.Badge(
                                        f"{len(today_appointments)}",
                                        color="green",
                                        size="sm"
                                    )
                                ], position="apart"),
                                
                                dmc.Stack([
                                    create_compact_today_item(apt) 
                                    for apt in today_appointments[:3]
                                ] if today_appointments else [
                                    dmc.Text(
                                        "Nenhum agendamento hoje",
                                        color="dimmed",
                                        size="xs",
                                        align="center"
                                    )
                                ], spacing="xs")
                            ], spacing="sm")
                        ], p="md", radius="lg", shadow="sm")
                    ], spacing="md")
                ], style={
                    "width": "300px", 
                    "marginRight": "24px",
                    "display": "none" if "mobile" in str(datetime.now()) else "block"  # Placeholder para responsividade
                }),
                
                # Lista Principal Compacta
                html.Div([
                    dmc.Paper([
                        dmc.Stack([
                            # Header Compacto
                            dmc.Group([
                                dmc.Text("Lista de Agendamentos", weight=600, size="md"),
                                dmc.Group([
                                    dmc.ActionIcon(
                                        DashIconify(icon="tabler:refresh", width=18),
                                        variant="light",
                                        color="blue",
                                        size="md",
                                        id="refresh-appointments"
                                    ),
                                    dmc.Select(
                                        data=[
                                            {"value": "date_desc", "label": "Data ↓"},
                                            {"value": "date_asc", "label": "Data ↑"},
                                            {"value": "status", "label": "Status"}
                                        ],
                                        value="date_desc",
                                        placeholder="Ordenar",
                                        style={"width": "120px"},
                                        id="sort-appointments",
                                        size="sm"
                                    )
                                ], spacing="sm")
                            ], position="apart"),
                            
                            # Lista Compacta
                            html.Div(
                                id="appointments-list",
                                children=[
                                    create_compact_appointment_item(apt) for apt in appointments[:20]
                                ] if appointments else [
                                    dmc.Center([
                                        dmc.Stack([
                                            DashIconify(
                                                icon="tabler:calendar-plus",
                                                width=48,
                                                color="#667eea"
                                            ),
                                            dmc.Text(
                                                "Nenhum agendamento encontrado",
                                                weight=500,
                                                align="center"
                                            ),
                                            dmc.Text(
                                                "Clique em 'Novo Agendamento' para criar o primeiro",
                                                color="dimmed",
                                                size="sm",
                                                align="center"
                                            )
                                        ], align="center", spacing="md")
                                    ], p="xl")
                                ],
                                style={"maxHeight": "500px", "overflowY": "auto"}
                            )
                        ], spacing="md")
                    ], p="md", radius="lg", shadow="sm")
                ], style={"flex": "1"})
            ], style={
                "display": "flex",
                "gap": "24px",
                "alignItems": "flex-start",
                "flexWrap": "wrap"
            }),
            
            # Modal
            dmc.Modal(
                title="Novo Agendamento",
                size="lg",
                id="appointment-modal",
                children=[create_appointment_form_modern()]
            ),
            
            # Stores
            dcc.Store(id="appointments-data", data=appointments),
            dcc.Store(id="current-appointment", data=None),
            dcc.Store(id="modal-mode", data="create")
        ],
        size="xl",
        px="md",
        py="sm"
    )

def create_compact_kpi_card(title, value, icon, color, description):
    """
    Card KPI compacto e bem formatado - compatível com dmc 0.12.1
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
                dmc.Text(title, size="xs", color="dimmed", weight=500),
                dmc.Text(
                    str(value),
                    weight=700,
                    size="xl",
                    style={"color": color, "lineHeight": 1}
                )
            ], spacing="xs", style={"flex": 1})
        ], align="center"),
        dmc.Text(description, size="xs", color="dimmed", style={"marginTop": "8px"})
    ], p="md", radius="lg", shadow="sm", style={
        "background": f"linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.95))",
        "border": f"1px solid {color}22",
        "transition": "all 0.3s ease",
        "cursor": "pointer"
    })

def create_compact_appointment_item(appointment):
    """
    Item de agendamento compacto - compatível com dmc 0.12.1
    """
    # Extrai dados reais da database baseado na estrutura atual
    customer_name = appointment.get('customer_name', 'Cliente Desconhecido')
    phone = appointment.get('phone_number', '')
    
    # Dados do agendamento (campos reais da tabela appointments)
    appointment_date = appointment.get('appointment_datetime')
    status = appointment.get('status', 'pending')
    service_name = appointment.get('service_type', 'Limpeza de Pele Profunda')
    notes = appointment.get('notes', '')
    appointment_id = appointment.get('id', 0)
    
    # Formatação de data/hora otimizada
    try:
        if appointment_date:
            if isinstance(appointment_date, str):
                date_obj = datetime.fromisoformat(appointment_date.replace('Z', '+00:00'))
            else:
                date_obj = appointment_date
            
            today = datetime.now().date()
            apt_date = date_obj.date()
            
            if apt_date == today:
                date_display = "HOJE"
                date_color = "#10b981"
            elif apt_date == today + timedelta(days=1):
                date_display = "AMANHÃ"
                date_color = "#3b82f6"
            else:
                date_display = date_obj.strftime('%d/%m')
                date_color = "#6b7280"
                
            time_str = date_obj.strftime('%H:%M')
        else:
            date_display = "??"
            time_str = "--:--"
            date_color = "#ef4444"
    except Exception as e:
        print(f"Erro ao formatar data: {e}")
        date_display = "ERRO"
        time_str = "--:--"
        date_color = "#ef4444"
    
    # Formatação do telefone
    formatted_phone = phone if phone else 'Sem telefone'
    if phone and len(phone) >= 10:
        formatted_phone = f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    
    # Config de status
    status_config = {
        'confirmed': {'color': '#10b981', 'label': 'Confirmado', 'bg': 'rgba(16, 185, 129, 0.1)'},
        'pending': {'color': '#f59e0b', 'label': 'Pendente', 'bg': 'rgba(245, 158, 11, 0.1)'},
        'cancelled': {'color': '#ef4444', 'label': 'Cancelado', 'bg': 'rgba(239, 68, 68, 0.1)'},
        'completed': {'color': '#3b82f6', 'label': 'Concluído', 'bg': 'rgba(59, 130, 246, 0.1)'}
    }
    
    config = status_config.get(status, {'color': '#6b7280', 'label': status.upper(), 'bg': 'rgba(107, 114, 128, 0.1)'})
    
    return dmc.Paper([
        dmc.Group([
            # Indicador de data compacto
            dmc.Stack([
                dmc.Text(
                    date_display, 
                    weight=700, 
                    size="xs", 
                    style={"color": date_color, "textAlign": "center"}
                ),
                dmc.Text(
                    time_str, 
                    weight=500, 
                    size="xs", 
                    color="dimmed",
                    style={"textAlign": "center"}
                )
            ], spacing="xs", align="center", style={"minWidth": "70px"}),
            
            # Info principal
            dmc.Stack([
                dmc.Group([
                    dmc.Text(customer_name, weight=600, size="sm", style={"flex": 1}),
                    dmc.Badge(
                        config['label'],
                        size="sm",
                        style={"background": config['bg'], "color": config['color']}
                    )
                ], position="apart", align="center"),
                
                dmc.Text(service_name, size="xs", style={"color": "#667eea"}),
                
                dmc.Group([
                    dmc.Text(
                        f"Tel: ...{phone[-4:]}" if len(phone) > 4 else f"Tel: {phone}",
                        color="dimmed",
                        size="xs"
                    ),
                    dmc.Text(
                        notes[:25] + "..." if notes and len(notes) > 25 else notes,
                        color="dimmed",
                        size="xs"
                    ) if notes else None
                ], spacing="md")
            ], style={"flex": 1}, spacing="xs"),
            
            # Ações compactas
            dmc.Group([
                dmc.ActionIcon(
                    DashIconify(icon="tabler:edit", width=14),
                    size="sm",
                    variant="light",
                    color="blue",
                    id={"type": "edit-appointment", "index": appointment_id}
                ),
                dmc.ActionIcon(
                    DashIconify(icon="tabler:brand-whatsapp", width=14),
                    size="sm", 
                    variant="light",
                    color="green"
                ),
                dmc.ActionIcon(
                    DashIconify(icon="tabler:trash", width=14),
                    size="sm",
                    variant="light", 
                    color="red",
                    id={"type": "delete-appointment", "index": appointment_id}
                )
            ], spacing="xs")
        ], align="center")
    ], 
    p="sm", 
    mb="xs",
    radius="lg", 
    shadow="xs",
    style={
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "borderLeft": f"4px solid {config['color']}",
        "marginBottom": "8px"
    },
    id={"type": "appointment-item", "index": appointment_id})

def create_compact_today_item(appointment):
    """
    Item ultra compacto para agendamentos de hoje - compatível com dmc 0.12.1
    """
    customer_name = appointment.get('customer_name', 'Cliente')
    appointment_date = appointment.get('appointment_datetime')
    
    try:
        if appointment_date and isinstance(appointment_date, str):
            appointment_date = datetime.fromisoformat(appointment_date.replace('Z', '+00:00'))
        time_str = appointment_date.strftime('%H:%M') if appointment_date else '--:--'
    except:
        time_str = '--:--'
    
    return dmc.Group([
        dmc.Text(time_str, weight=600, size="xs", style={"minWidth": "40px"}),
        dmc.Text(customer_name, size="xs", color="dimmed", style={"flex": 1})
    ], align="center", spacing="sm")

def create_appointment_form_modern():
    """
    Formulário moderno compacto - compatível com dmc 0.12.1
    """
    return dmc.Stack([
        # Primeira linha: Nome e Telefone
        html.Div([
            html.Div([
                dmc.TextInput(
                    label="Nome do Cliente",
                    placeholder="Nome completo",
                    required=True,
                    id="appointment-customer-name",
                    size="sm"
                )
            ], style={"width": "48%", "marginRight": "4%"}),
            html.Div([
                dmc.TextInput(
                    label="Telefone",
                    placeholder="(11) 99999-9999",
                    id="appointment-phone",
                    size="sm"
                )
            ], style={"width": "48%"})
        ], style={"display": "flex", "marginBottom": "16px"}),
        
        # Segunda linha: Data e Horário
        html.Div([
            html.Div([
                dmc.DatePicker(
                    label="Data",
                    required=True,
                    id="appointment-date",
                    size="sm"
                )
            ], style={"width": "48%", "marginRight": "4%"}),
            html.Div([
                dmc.TextInput(
                    label="Horário",
                    placeholder="14:30",
                    required=True,
                    id="appointment-time",
                    size="sm",
                    icon=DashIconify(icon="tabler:clock")
                )
            ], style={"width": "48%"})
        ], style={"display": "flex", "marginBottom": "16px"}),
        
        # Terceira linha: Serviço e Status
        html.Div([
            html.Div([
                dmc.Select(
                    label="Serviço",
                    data=[
                        {"value": "limpeza", "label": "Limpeza de Pele"},
                        {"value": "consulta", "label": "Consulta"},
                        {"value": "procedimento", "label": "Procedimento"}
                    ],
                    value="limpeza",
                    id="appointment-service-type",
                    size="sm"
                )
            ], style={"width": "48%", "marginRight": "4%"}),
            html.Div([
                dmc.Select(
                    label="Status",
                    data=[
                        {"value": "pending", "label": "Pendente"},
                        {"value": "confirmed", "label": "Confirmado"}
                    ],
                    value="pending", 
                    id="appointment-status",
                    size="sm"
                )
            ], style={"width": "48%"})
        ], style={"display": "flex", "marginBottom": "16px"}),
        
        # Observações
        dmc.Textarea(
            label="Observações",
            placeholder="Observações sobre o agendamento...",
            id="appointment-notes",
            size="sm",
            autosize=True,
            minRows=2
        ),
        
        # Botões
        dmc.Group([
            dmc.Button(
                "Cancelar",
                variant="outline",
                id="cancel-appointment",
                size="sm"
            ),
            dmc.Button(
                "Salvar",
                leftIcon=DashIconify(icon="tabler:check"),
                id="save-appointment",
                size="sm"
            )
        ], position="right")
    ], spacing="md")
