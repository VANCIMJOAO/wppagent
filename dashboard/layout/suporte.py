"""
Suporte Layout - Página de Suporte e Ajuda (CORRIGIDA)
======================================================

Página completa de suporte com:
- Central de ajuda com FAQs
- Formulário de contato/ticket
- Documentação do sistema
- Status de sistema/uptime
- Chat de suporte (se aplicável)
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


def create_faq_item(question, answer, category="geral"):
    """Cria um item FAQ simples usando Paper"""
    
    category_colors = {
        "geral": "blue",
        "tecnico": "orange", 
        "conta": "green",
        "billing": "purple"
    }
    
    return dmc.Paper([
        dmc.Stack([
            # Pergunta
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:help-circle", width=16),
                    variant="light",
                    color=category_colors.get(category, "blue"),
                    size="sm"
                ),
                dmc.Text(question, fw=600, size="sm")
            ], spacing="sm"),
            
            # Resposta
            dmc.Text(answer, size="sm", c="dimmed", pl="lg")
        ], spacing="sm")
    ], withBorder=True, p="md", radius="md", mb="sm")

def create_status_indicator(service, status, uptime="99.9%"):
    """Cria indicador de status do sistema"""
    
    status_config = {
        "online": {"color": "green", "icon": "tabler:circle-check", "text": "Operacional"},
        "warning": {"color": "yellow", "icon": "tabler:alert-circle", "text": "Degradado"},
        "offline": {"color": "red", "icon": "tabler:circle-x", "text": "Indisponível"}
    }
    
    config = status_config.get(status, status_config["online"])
    
    return dmc.Paper([
        dmc.Group([
            dmc.Indicator(
                dmc.ThemeIcon(
                    DashIconify(icon=config["icon"], width=16),
                    variant="light", 
                    color=config["color"],
                    size="sm"
                ),
                color=config["color"],
                size="sm"
            ),
            dmc.Stack([
                dmc.Text(service, size="sm", fw=500),
                dmc.Text(config["text"], size="xs", c="dimmed")
            ], spacing="none"),
            dmc.Stack([
                dmc.Text(uptime, size="xs", fw=600, c=config["color"]),
                dmc.Text("uptime", size="xs", c="dimmed")
            ], spacing="none", align="end")
        ], position="apart", align="center")
    ], p="md", radius="md", withBorder=True)

def create_contact_form():
    """Formulário de contato/ticket"""
    
    return dmc.Card([
        dmc.Stack([
            # Header
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:message-circle-plus", width=20),
                    color="blue",
                    variant="light"
                ),
                dmc.Stack([
                    dmc.Text("Abrir Ticket de Suporte", fw=600, size="lg"),
                    dmc.Text("Descreva seu problema ou dúvida em detalhes", size="sm", c="dimmed")
                ], spacing="xs")
            ], spacing="sm", mb="md"),
            
            # Formulário
            dmc.Grid([
                dmc.Col([
                    dmc.TextInput(
                        label="Nome completo",
                        placeholder="Seu nome",
                        required=True,
                        id="support-form-name"
                    )
                ], span=6),
                
                dmc.Col([
                    dmc.TextInput(
                        label="Email",
                        placeholder="seu@email.com",
                        required=True,
                        id="support-form-email"
                    )
                ], span=6),
                
                dmc.Col([
                    dmc.Select(
                        label="Categoria",
                        placeholder="Selecione a categoria",
                        data=[
                            {"value": "bug", "label": "🐛 Bug/Erro"},
                            {"value": "feature", "label": "💡 Sugestão de funcionalidade"},
                            {"value": "account", "label": "👤 Problema de conta"},
                            {"value": "billing", "label": "💳 Questões de cobrança"},
                            {"value": "integration", "label": "🔌 Problemas de integração"},
                            {"value": "other", "label": "❓ Outros"}
                        ],
                        required=True,
                        id="support-form-category"
                    )
                ], span=6),
                
                dmc.Col([
                    dmc.Select(
                        label="Prioridade",
                        placeholder="Selecione a prioridade",
                        data=[
                            {"value": "low", "label": "🟢 Baixa"},
                            {"value": "medium", "label": "🟡 Média"},
                            {"value": "high", "label": "🟠 Alta"},
                            {"value": "urgent", "label": "🔴 Urgente"}
                        ],
                        value="medium",
                        id="support-form-priority"
                    )
                ], span=6),
                
                dmc.Col([
                    dmc.Textarea(
                        label="Descrição detalhada",
                        placeholder="Descreva o problema ou sua dúvida em detalhes. Inclua passos para reproduzir o erro, se aplicável.",
                        required=True,
                        minRows=4,
                        id="support-form-description"
                    )
                ], span=12),
                
                dmc.Col([
                    dmc.Group([
                        dmc.Button(
                            "Enviar Ticket",
                            leftIcon=DashIconify(icon="tabler:send"),
                            id="support-form-submit",
                            loading=False
                        ),
                        dmc.Button(
                            "Limpar formulário",
                            variant="outline",
                            color="gray",
                            id="support-form-clear"
                        )
                    ], spacing="sm")
                ], span=12)
            ], gutter="md")
        ])
    ], withBorder=True, shadow="sm", p="xl", radius="md")

def create_documentation_section():
    """Seção de documentação"""
    
    doc_items = [
        {
            "title": "Primeiros Passos",
            "description": "Como começar a usar o WPPAgent Dashboard",
            "icon": "tabler:rocket",
            "color": "blue",
            "url": "#getting-started"
        },
        {
            "title": "Configuração do WhatsApp",
            "description": "Como conectar e configurar seu WhatsApp Business",
            "icon": "tabler:brand-whatsapp",
            "color": "green",
            "url": "#whatsapp-setup"
        },
        {
            "title": "Gerenciar Conversas",
            "description": "Como usar as ferramentas de gestão de conversas",
            "icon": "tabler:messages",
            "color": "orange",
            "url": "#conversations"
        },
        {
            "title": "Agendamentos",
            "description": "Sistema de agendamento automático e manual",
            "icon": "tabler:calendar",
            "color": "purple",
            "url": "#appointments"
        },
        {
            "title": "Relatórios e Analytics",
            "description": "Como interpretar métricas e relatórios",
            "icon": "tabler:chart-line",
            "color": "teal",
            "url": "#reports"
        },
        {
            "title": "API e Integrações",
            "description": "Documentação técnica para desenvolvedores",
            "icon": "tabler:api",
            "color": "violet",
            "url": "#api"
        }
    ]
    
    return dmc.SimpleGrid([
        dmc.Paper([
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=item["icon"], width=20),
                    color=item["color"],
                    variant="light",
                    size="lg"
                ),
                dmc.Stack([
                    dmc.Text(item["title"], fw=600, size="sm"),
                    dmc.Text(item["description"], size="xs", c="dimmed", lineClamp=2)
                ], spacing="xs"),
                dmc.ActionIcon(
                    DashIconify(icon="tabler:external-link", width=16),
                    variant="light",
                    color="gray",
                    size="sm"
                )
            ], position="apart", align="center")
        ], 
        p="md", 
        radius="md", 
        withBorder=True,
        className="doc-item-card",
        style={"cursor": "pointer", "transition": "all 0.2s ease"}
        ) for item in doc_items
    ], cols=2, spacing="md")

def create_suporte_layout():
    """
    Layout principal da página de suporte
    """
    
    # Dados de FAQs
    faqs_data = {
        "geral": [
            {
                "question": "Como faço para começar a usar o sistema?",
                "answer": "Para começar, você precisa primeiro conectar sua conta WhatsApp Business na seção Configurações. Depois, configure sua empresa e personalize as mensagens automáticas. O sistema estará pronto para uso em poucos minutos."
            },
            {
                "question": "O sistema funciona com WhatsApp pessoal?",
                "answer": "Não, o sistema é projetado especificamente para WhatsApp Business API. Você precisa de uma conta WhatsApp Business para usar todas as funcionalidades do WPPAgent."
            },
            {
                "question": "Posso usar em múltiplos dispositivos?",
                "answer": "Sim! O dashboard é baseado na web e pode ser acessado de qualquer dispositivo com internet. Suas configurações e dados ficam sincronizados na nuvem."
            }
        ],
        "tecnico": [
            {
                "question": "Como configurar webhooks?",
                "answer": "Os webhooks são configurados automaticamente durante a integração com WhatsApp Business API. Se precisar configurar manualmente, acesse Configurações > Integrações > Webhooks."
            },
            {
                "question": "O que fazer se as mensagens não estão sendo enviadas?",
                "answer": "Primeiro, verifique se sua conta WhatsApp Business está ativa. Depois, confira se há créditos suficientes na sua conta. Se o problema persistir, verifique os logs na seção Configurações > Logs do Sistema."
            },
            {
                "question": "Como fazer backup dos dados?",
                "answer": "O sistema faz backup automático diariamente. Você também pode exportar dados manualmente em Relatórios > Exportar Dados. Os backups incluem conversas, clientes e configurações."
            }
        ],
        "conta": [
            {
                "question": "Como alterar minha senha?",
                "answer": "Acesse seu perfil no canto superior direito, clique em 'Configurações de Conta' e depois em 'Alterar Senha'. Você receberá um email de confirmação."
            },
            {
                "question": "Como adicionar outros usuários?",
                "answer": "Na seção Configurações > Usuários, clique em 'Adicionar Usuário'. Você pode definir diferentes níveis de permissão (Admin, Operador, Visualizador)."
            }
        ]
    }
    
    return html.Div([
        # Header da página
        dmc.Container([
            dmc.Stack([
                # Breadcrumb
                dmc.Breadcrumbs([
                    dmc.Anchor("Home", href="/home"),
                    dmc.Text("Suporte", c="dimmed")
                ], mb="sm"),
                
                # Título principal
                dmc.Group([
                    dmc.Stack([
                        dmc.Title("Central de Suporte", order=1, size="2rem"),
                        dmc.Text(
                            "Encontre respostas, abra tickets de suporte e acesse a documentação completa",
                            size="lg", c="dimmed"
                        )
                    ], spacing="xs"),
                    
                    # Status geral do sistema
                    dmc.Paper([
                        dmc.Group([
                            dmc.Indicator(
                                dmc.ThemeIcon(
                                    DashIconify(icon="tabler:server", width=20),
                                    color="green",
                                    variant="light"
                                ),
                                color="green",
                                size="sm"
                            ),
                            dmc.Stack([
                                dmc.Text("Sistema Operacional", size="sm", fw=600),
                                dmc.Text("Todos os serviços funcionando", size="xs", c="dimmed")
                            ], spacing="xs")
                        ], spacing="sm")
                    ], p="md", radius="md", withBorder=True)
                ], position="apart", align="flex-start", mb="xl")
            ])
        ], size="xl", py="xl"),
        
        dmc.Container([
            # Grid principal
            dmc.Grid([
                # Coluna esquerda - FAQs e Documentação
                dmc.Col([
                    dmc.Stack([
                        # Central de Ajuda - FAQs
                        dmc.Card([
                            dmc.Stack([
                                dmc.Group([
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:help-circle", width=24),
                                        color="blue",
                                        variant="light",
                                        size="lg"
                                    ),
                                    dmc.Stack([
                                        dmc.Text("Perguntas Frequentes", fw=600, size="lg"),
                                        dmc.Text("Respostas para as dúvidas mais comuns", size="sm", c="dimmed")
                                    ], spacing="xs")
                                ], spacing="sm"),
                                
                                # Tabs de categorias
                                dmc.Tabs([
                                    dmc.TabsList([
                                        dmc.Tab("Geral", value="geral"),
                                        dmc.Tab("Técnico", value="tecnico"),
                                        dmc.Tab("Conta", value="conta")
                                    ]),
                                    
                                    # Painel Geral
                                    dmc.TabsPanel([
                                        dmc.Stack([
                                            create_faq_item(faq["question"], faq["answer"], "geral")
                                            for faq in faqs_data["geral"]
                                        ], spacing="sm")
                                    ], value="geral"),
                                    
                                    # Painel Técnico  
                                    dmc.TabsPanel([
                                        dmc.Stack([
                                            create_faq_item(faq["question"], faq["answer"], "tecnico")
                                            for faq in faqs_data["tecnico"]
                                        ], spacing="sm")
                                    ], value="tecnico"),
                                    
                                    # Painel Conta
                                    dmc.TabsPanel([
                                        dmc.Stack([
                                            create_faq_item(faq["question"], faq["answer"], "conta")
                                            for faq in faqs_data["conta"]
                                        ], spacing="sm")
                                    ], value="conta")
                                ], value="geral", orientation="horizontal")
                            ])
                        ], withBorder=True, shadow="sm", p="xl", radius="md", mb="xl"),
                        
                        # Documentação
                        dmc.Card([
                            dmc.Stack([
                                dmc.Group([
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:book", width=24),
                                        color="orange",
                                        variant="light",
                                        size="lg"
                                    ),
                                    dmc.Stack([
                                        dmc.Text("Documentação", fw=600, size="lg"),
                                        dmc.Text("Guias completos para usar o sistema", size="sm", c="dimmed")
                                    ], spacing="xs")
                                ], spacing="sm", mb="md"),
                                
                                create_documentation_section()
                            ])
                        ], withBorder=True, shadow="sm", p="xl", radius="md")
                    ])
                ], span=8),
                
                # Coluna direita - Formulário e Status
                dmc.Col([
                    dmc.Stack([
                        # Formulário de contato
                        create_contact_form(),
                        
                        # Status do Sistema
                        dmc.Card([
                            dmc.Stack([
                                dmc.Group([
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:activity", width=20),
                                        color="green",
                                        variant="light"
                                    ),
                                    dmc.Stack([
                                        dmc.Text("Status do Sistema", fw=600, size="lg"),
                                        dmc.Text("Monitoramento em tempo real", size="sm", c="dimmed")
                                    ], spacing="xs")
                                ], spacing="sm", mb="md"),
                                
                                # Indicadores de status
                                dmc.Stack([
                                    create_status_indicator("WhatsApp API", "online", "99.9%"),
                                    create_status_indicator("Dashboard", "online", "99.8%"),
                                    create_status_indicator("Base de Dados", "online", "99.9%"),
                                    create_status_indicator("Sistema de Backups", "online", "100%")
                                ], spacing="sm"),
                                
                                # Última atualização
                                dmc.Group([
                                    dmc.Text("Última verificação:", size="xs", c="dimmed"),
                                    dmc.Text(datetime.now().strftime("%H:%M - %d/%m/%Y"), size="xs", fw=500)
                                ], position="apart", mt="sm")
                            ])
                        ], withBorder=True, shadow="sm", p="xl", radius="md"),
                        
                        # Chat de suporte (placeholder)
                        dmc.Card([
                            dmc.Stack([
                                dmc.Group([
                                    dmc.ThemeIcon(
                                        DashIconify(icon="tabler:message-chatbot", width=20),
                                        color="purple",
                                        variant="light"
                                    ),
                                    dmc.Stack([
                                        dmc.Text("Chat de Suporte", fw=600),
                                        dmc.Text("Suporte instantâneo", size="sm", c="dimmed")
                                    ], spacing="xs")
                                ], spacing="sm"),
                                
                                dmc.Center([
                                    dmc.Stack([
                                        DashIconify(icon="tabler:clock", width=32, color="gray"),
                                        dmc.Text("Chat disponível das", size="sm", c="dimmed", ta="center"),
                                        dmc.Text("9h às 18h (seg-sex)", size="sm", fw=500, ta="center"),
                                        dmc.Button(
                                            "Iniciar chat",
                                            variant="light",
                                            color="purple",
                                            disabled=True,
                                            size="sm",
                                            leftIcon=DashIconify(icon="tabler:message")
                                        )
                                    ], align="center", spacing="xs")
                                ], py="md")
                            ])
                        ], withBorder=True, shadow="sm", p="xl", radius="md")
                    ])
                ], span=4)
            ], gutter="xl", mb="xl"),
            
            # Footer com informações de contato
            dmc.Card([
                dmc.Group([
                    dmc.Stack([
                        dmc.Text("Precisa de ajuda adicional?", fw=600, size="lg"),
                        dmc.Text("Nossa equipe está pronta para ajudar você", c="dimmed")
                    ], spacing="xs"),
                    
                    dmc.Group([
                        dmc.Button(
                            "Email: suporte@wppagent.com",
                            variant="light",
                            leftIcon=DashIconify(icon="tabler:mail"),
                            color="blue"
                        ),
                        dmc.Button(
                            "WhatsApp: (11) 99999-0000",
                            variant="light", 
                            leftIcon=DashIconify(icon="tabler:brand-whatsapp"),
                            color="green"
                        )
                    ])
                ], position="apart", align="center")
            ], withBorder=True, p="xl", radius="md", style={"background": "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)"})
            
        ], size="xl", px="md"),
        
        # Stores para dados do formulário
        dcc.Store(id="support-form-data"),
        dcc.Store(id="support-system-status")
        
    ], style={"background": "#fafafa", "minHeight": "100vh"})
