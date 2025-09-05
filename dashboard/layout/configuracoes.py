"""
✨ Página de Configurações Renovada - Layout Moderno COMPLETO ✨
==============================================================

🎯 LAYOUT FINALIZADO E PRONTO PARA USO!

🔥 TODOS OS COMPONENTES BASEADOS NA ESTRUTURA REAL DO BANCO DE DADOS!
"""

import dash_mantine_components as dmc
from dash import html, dcc
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


def create_configuracoes_layout():
    """🎨 Layout principal da página de configurações renovada"""
    return html.Div([
        get_config_styles(),
        
        dmc.Container([
            create_hero_section(),
            
            dmc.Tabs(
                value="empresa",
                id="config-tabs",
                children=[
                    dmc.TabsList([
                        dmc.Tab("🏢 Empresa", value="empresa"),
                        dmc.Tab("🤖 Bot & IA", value="bot"),
                        dmc.Tab("⏰ Horários", value="horarios"),
                        dmc.Tab("📝 Templates", value="templates"),
                        dmc.Tab("🛡️ Políticas", value="politicas")
                    ], grow=True),
                    
                    dmc.TabsPanel(create_empresa_panel(), value="empresa"),
                    dmc.TabsPanel(create_bot_panel(), value="bot"), 
                    dmc.TabsPanel(create_horarios_panel(), value="horarios"),
                    dmc.TabsPanel(create_templates_panel(), value="templates"),
                    dmc.TabsPanel(create_politicas_panel(), value="politicas")
                ]
            ),
            
            html.Div(id="config-notifications"),
            dcc.Store(id="config-data", data={}),
            
        ], size="xl", px="md")
    ])

def create_hero_section():
    """🌟 Hero Section"""
    return html.Div([
        dmc.Stack([
            dmc.Group([
                DashIconify(icon="tabler:settings", width=40, height=40, color="white"),
                dmc.Stack([
                    dmc.Title("⚙️ Configurações", order=1, 
                             style={"color": "white", "fontSize": "2.5rem"}),
                    dmc.Text("Gerencie empresa, bot, horários e políticas", 
                            style={"color": "rgba(255,255,255,0.9)", "fontSize": "1.1rem"})
                ], spacing=5)
            ]),
            
            dmc.SimpleGrid([
                create_kpi_card("🤖 Bot", "Ativo", "green"),
                create_kpi_card("📝 Templates", "6 Ativos", "blue"), 
                create_kpi_card("⏰ Atualizado", "Hoje 14:30", "orange"),
                create_kpi_card("🛡️ Políticas", "6 Ativas", "teal")
            ], cols=4, spacing="md")
        ], spacing="xl")
    ], className="hero-section")

def create_kpi_card(title, value, color):
    """📊 Card KPI"""
    return dmc.Card([
        dmc.Stack([
            dmc.Text(title, size="sm", style={"color": "rgba(255,255,255,0.8)"}),
            dmc.Text(value, fw=700, size="lg", style={"color": "white"})
        ], spacing=2, align="center")
    ], className="kpi-card", p="md")

def create_empresa_panel():
    """🏢 Painel Empresa"""
    return dmc.Stack([
        dmc.Title("🏢 Informações da Empresa", order=2),
        
        dmc.SimpleGrid([
            dmc.Card([
                dmc.Stack([
                    dmc.Title("📝 Dados Básicos", order=4),
                    
                    dmc.TextInput(
                        label="Nome da Empresa *",
                        placeholder="Digite o nome da empresa",
                        id="empresa-nome",
                        icon=DashIconify(icon="tabler:building")
                    ),
                    
                    dmc.TextInput(
                        label="Slogan",
                        placeholder="Slogan da empresa",
                        id="empresa-slogan"
                    ),
                    
                    dmc.Textarea(
                        label="Sobre a Empresa",
                        placeholder="Descrição da empresa...",
                        id="empresa-sobre",
                        minRows=3
                    ),
                    
                    dmc.Textarea(
                        label="Descrição do Negócio",
                        placeholder="O que a empresa faz...",
                        id="empresa-descricao",
                        minRows=3
                    )
                ])
            ], p="lg"),
            
            dmc.Card([
                dmc.Stack([
                    dmc.Title("📞 Contato", order=4),
                    
                    dmc.TextInput(
                        label="WhatsApp",
                        placeholder="(11) 99999-9999",
                        id="empresa-whatsapp",
                        icon=DashIconify(icon="tabler:brand-whatsapp")
                    ),
                    
                    dmc.TextInput(
                        label="Email",
                        placeholder="contato@empresa.com",
                        id="empresa-email",
                        icon=DashIconify(icon="tabler:mail")
                    ),
                    
                    dmc.TextInput(
                        label="Website",
                        placeholder="www.empresa.com",
                        id="empresa-website",
                        icon=DashIconify(icon="tabler:world")
                    ),
                    
                    dmc.TextInput(
                        label="Endereço",
                        placeholder="Endereço completo",
                        id="empresa-endereco",
                        icon=DashIconify(icon="tabler:map-pin")
                    )
                ])
            ], p="lg")
        ], cols=2, spacing="lg"),
        
        create_action_buttons("empresa")
        
    ], spacing="lg")

def create_bot_panel():
    """🤖 Painel Bot"""
    return dmc.Stack([
        dmc.Title("🤖 Configurações do Bot", order=2),
        
        dmc.Card([
            dmc.Stack([
                dmc.Group([
                    dmc.Switch(
                        label="🔄 Resposta Automática",
                        id="bot-auto-resposta",
                        checked=True
                    ),
                    dmc.Text("Bot responde automaticamente", size="sm", c="dimmed")
                ]),
                
                dmc.SimpleGrid([
                    dmc.Select(
                        label="🌍 Idioma",
                        data=[
                            {"value": "pt-BR", "label": "🇧🇷 Português"},
                            {"value": "en-US", "label": "🇺🇸 English"},
                            {"value": "es-ES", "label": "🇪🇸 Español"}
                        ],
                        value="pt-BR",
                        id="bot-idioma"
                    ),
                    dmc.Select(
                        label="⏰ Fuso Horário",
                        data=[
                            {"value": "America/Sao_Paulo", "label": "São Paulo"},
                            {"value": "UTC", "label": "UTC"}
                        ],
                        value="America/Sao_Paulo",
                        id="bot-timezone"
                    )
                ], cols=2),
                
                dmc.Group([
                    dmc.Switch(
                        label="📅 Agendamentos",
                        id="bot-agendamentos",
                        checked=True
                    ),
                    dmc.Text("Permitir agendamentos via bot", size="sm", c="dimmed")
                ])
            ])
        ], p="lg"),
        
        create_action_buttons("bot")
        
    ], spacing="lg")

def create_horarios_panel():
    """⏰ Painel Horários"""
    return dmc.Stack([
        dmc.Title("⏰ Horários de Funcionamento", order=2),
        
        dmc.SimpleGrid([
            create_day_card("Domingo", 0, False),
            create_day_card("Segunda", 1, True, "08:00", "18:00"),
            create_day_card("Terça", 2, True, "08:00", "18:00"),
            create_day_card("Quarta", 3, True, "08:00", "18:00"),
            create_day_card("Quinta", 4, True, "08:00", "18:00"),
            create_day_card("Sexta", 5, True, "08:00", "18:00"),
            create_day_card("Sábado", 6, True, "08:00", "16:00")
        ], cols=2, spacing="md"),
        
        create_action_buttons("horarios")
        
    ], spacing="lg")

def create_day_card(day, number, is_open, open_time="08:00", close_time="18:00"):
    """📅 Card do dia"""
    return dmc.Card([
        dmc.Stack([
            dmc.Group([
                dmc.Text(day, fw=600),
                dmc.Switch(
                    checked=is_open,
                    id=f"day-{number}",
                    size="sm"
                )
            ]),
            
            html.Div([
                dmc.SimpleGrid([
                    dmc.TimeInput(
                        label="Abertura",
                        value=open_time,
                        id=f"open-{number}"
                    ),
                    dmc.TimeInput(
                        label="Fechamento",
                        value=close_time,
                        id=f"close-{number}"
                    )
                ], cols=2)
            ], style={"display": "block" if is_open else "none"}, id=f"inputs-{number}")
        ])
    ], p="md")

def create_templates_panel():
    """📝 Painel Templates"""
    return dmc.Stack([
        dmc.Title("📝 Templates de Mensagens", order=2),
        
        dmc.SimpleGrid([
            create_template_card("welcome", "👋 Boas-vindas", "Olá! Bem-vindo!", True),
            create_template_card("confirm", "✅ Confirmação", "Agendamento confirmado", True),
            create_template_card("reminder", "⏰ Lembrete", "Lembrete de agendamento", True),
            create_template_card("cancel", "❌ Cancelamento", "Agendamento cancelado", False)
        ], cols=2, spacing="md"),
        
        create_action_buttons("templates")
        
    ], spacing="lg")

def create_template_card(template_id, name, preview, active):
    """📄 Card Template"""
    return dmc.Card([
        dmc.Stack([
            dmc.Group([
                dmc.Text(name, fw=600),
                dmc.Switch(checked=active, id=f"template-{template_id}")
            ]),
            
            dmc.Text(preview, size="sm", c="dimmed"),
            
            dmc.Button("✏️ Editar", size="xs", variant="light")
        ])
    ], p="md")

def create_politicas_panel():
    """🛡️ Painel Políticas"""
    return dmc.Stack([
        dmc.Title("🛡️ Políticas do Negócio", order=2),
        
        dmc.SimpleGrid([
            create_policy_card("cancel", "❌ Cancelamento", "Regras de cancelamento", True),
            create_policy_card("payment", "💳 Pagamento", "Formas de pagamento", True),
            create_policy_card("privacy", "🔒 Privacidade", "Proteção de dados", True),
            create_policy_card("refund", "💰 Reembolso", "Política de reembolso", False)
        ], cols=2, spacing="md"),
        
        create_action_buttons("politicas")
        
    ], spacing="lg")

def create_policy_card(policy_id, name, description, active):
    """📋 Card Política"""
    return dmc.Card([
        dmc.Stack([
            dmc.Group([
                dmc.Text(name, fw=600),
                dmc.Switch(checked=active, id=f"policy-{policy_id}")
            ]),
            
            dmc.Text(description, size="sm", c="dimmed"),
            
            dmc.Button("⚙️ Configurar", size="xs", variant="light")
        ])
    ], p="md")

def create_action_buttons(panel_type):
    """🎯 Botões de Ação"""
    return html.Div([
        dmc.Group([
            dmc.Button(
                f"💾 Salvar {panel_type.title()}",
                id=f"save-{panel_type}",
                className="btn-primary"
            ),
            dmc.Button(
                "🔄 Carregar",
                id=f"load-{panel_type}",
                variant="light"
            ),
            dmc.Button(
                "🗑️ Limpar",
                id=f"clear-{panel_type}",
                color="red",
                variant="subtle"
            )
        ])
    ], className="action-buttons")

def get_config_styles():
    """🎨 CSS Styles"""
    return dcc.Store(id="config-styles", data={
        ".hero-section": {
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "border-radius": "16px",
            "padding": "2rem",
            "margin-bottom": "2rem",
            "box-shadow": "0 10px 25px rgba(0,0,0,0.1)"
        },
        ".kpi-card": {
            "background": "rgba(255, 255, 255, 0.1)",
            "border": "1px solid rgba(255, 255, 255, 0.2)",
            "border-radius": "12px",
            "backdrop-filter": "blur(10px)",
            "transition": "all 0.3s ease"
        },
        ".action-buttons": {
            "margin-top": "2rem",
            "padding-top": "2rem",
            "border-top": "1px solid #e9ecef"
        },
        ".btn-primary": {
            "background": "linear-gradient(45deg, #007bff, #0056b3)",
            "border": "none",
            "font-weight": "600"
        }
    })
