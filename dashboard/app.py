"""
WPPAgent Dashboard - Versão com Autenticação
=============================================

Dashboard moderno e elegante para clientes finais.
Agora com sistema completo de autenticação e autorização.

Para executar:
    python app.py

Configuração inicial:
    python auth_setup.py setup
"""

import os
import dash
from dash import html, dcc, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv()

print("🔐 Iniciando WppAgent Dashboard com autenticação...")

# Importa sistema de autenticação
try:
    from auth.auth_service import AuthService
    from auth.layouts import (
        create_login_layout, 
        create_access_denied_layout,
        create_session_expired_layout,
        create_protected_layout_wrapper
    )
    from auth.callbacks import register_auth_callbacks
    from auth.middleware import auth_middleware
    print("✅ Sistema de autenticação carregado")
except ImportError as e:
    print(f"❌ Erro ao carregar sistema de autenticação: {e}")
    raise

# Inicializa serviço de autenticação
auth_service = AuthService()

# Para desenvolvimento, não requer DATABASE_URL obrigatória
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    print(f"✅ DATABASE_URL carregada: {DATABASE_URL[:30]}...")
else:
    print("⚠️  Executando em modo desenvolvimento (sem DATABASE_URL)")

# Importa layouts das páginas com fallbacks
try:
    from layout.home import create_home_layout
except ImportError:
    def create_home_layout():
        return dmc.Alert("Layout Home não disponível", color="yellow")

try:
    from layout.conversas import create_conversas_layout
except ImportError:
    def create_conversas_layout():
        return dmc.Alert("Layout Conversas não disponível", color="yellow")

try:
    from layout.agendamentos import create_agendamentos_layout
except ImportError:
    def create_agendamentos_layout():
        return dmc.Alert("Layout Agendamentos não disponível", color="yellow")

try:
    from layout.clientes import create_clientes_layout
except ImportError:
    def create_clientes_layout():
        return dmc.Alert("Layout Clientes não disponível", color="yellow")

try:
    from layout.configuracoes import create_configuracoes_layout
except ImportError:
    def create_configuracoes_layout():
        return dmc.Alert("Layout Configurações não disponível", color="yellow")

try:
    from layout.relatorios import create_relatorios_layout
except ImportError:
    def create_relatorios_layout():
        return dmc.Alert("Layout Relatórios não disponível", color="yellow")

try:
    from layout.perfil import create_perfil_layout
except ImportError:
    def create_perfil_layout():
        return dmc.Alert("Layout Perfil não disponível", color="yellow")

try:
    from layout.suporte import create_suporte_layout
except ImportError:
    def create_suporte_layout():
        return dmc.Alert("Layout Suporte não disponível", color="yellow")

# Importa componentes
from components.sidebar import create_sidebar, register_sidebar_callbacks

# Importa callbacks com fallbacks
try:
    from callbacks.home_callbacks import register_all_home_callbacks
except ImportError:
    def register_all_home_callbacks(app):
        pass

try:
    from callbacks.conversas_callbacks import register_all_conversas_callbacks
except ImportError:
    def register_all_conversas_callbacks(app):
        pass

try:
    from callbacks.agendamentos_callbacks import register_all_agendamentos_callbacks
except ImportError:
    def register_all_agendamentos_callbacks(app):
        pass

try:
    from callbacks.clientes_callbacks import register_clientes_callbacks
except ImportError:
    def register_clientes_callbacks(app):
        pass

try:
    from callbacks.configuracoes_callbacks import register_configuracoes_callbacks
except ImportError:
    def register_configuracoes_callbacks(app):
        pass

try:
    from callbacks.relatorios_callbacks import register_relatorios_callbacks
except ImportError:
    def register_relatorios_callbacks(app):
        pass

try:
    from callbacks.perfil_callbacks import register_perfil_callbacks
except ImportError:
    def register_perfil_callbacks(app):
        pass

try:
    from callbacks.suporte_callbacks import register_all_suporte_callbacks
except ImportError:
    def register_all_suporte_callbacks(app):
        pass

# Configuração do tema DMC
DMC_THEME = {
    "colorScheme": "light",
    "primaryColor": "dark",
    "primaryShade": {"light": 5, "dark": 3},
    "fontFamily": "var(--font-body)",
    "headings": {"fontFamily": "var(--font-title)"},
    "defaultRadius": 8,
    "shadows": {
        "sm": "var(--shadow-1)",
        "md": "var(--shadow-2)"
    }
}

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;500;600&display=swap",
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="WPPAgent Dashboard",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Dashboard moderno para gestão de atendimentos WhatsApp"}
    ]
)

server = app.server

# Adiciona CSS customizado
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="/assets/home_elegant.css">
        <link rel="stylesheet" href="/assets/auth.css">
        <link rel="stylesheet" href="/assets/sidebar.css">
        <link rel="stylesheet" href="/assets/conversations.css">
        <link rel="stylesheet" href="/assets/home_modern.css">
        <link rel="stylesheet" href="/assets/agendamentos_modern.css">
        <link rel="stylesheet" href="/assets/clientes_modern.css">
        <link rel="stylesheet" href="/assets/configuracoes_styles.css">
        <link rel="stylesheet" href="/assets/relatorios_modern.css">
        <link rel="stylesheet" href="/assets/perfil_modern.css">
        <link rel="stylesheet" href="/assets/suporte_modern.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout principal da aplicação com autenticação
app.layout = dmc.MantineProvider(
    theme=DMC_THEME,
    children=[
        dcc.Location(id='url', refresh=False),
        
        # Stores para dados de autenticação
        dcc.Store(id='session-store', storage_type='local'),
        dcc.Store(id='current-user', storage_type='session'),
        
        # Interval para verificar sessão periodicamente
        dcc.Interval(
            id='session-check-interval',
            interval=5*60*1000,  # 5 minutos
            n_intervals=0
        ),
        
        # Container principal
        html.Div(id='main-content')
    ]
)

# Callback principal para controle de autenticação e navegação
@app.callback(
    Output('main-content', 'children'),
    [Input('url', 'pathname'),
     Input('session-store', 'data')]
)
def display_page_with_auth(pathname, session_data):
    """Controla a exibição de páginas baseado na autenticação"""
    # Páginas públicas
    public_pages = ['/login', '/session-expired']
    
    if pathname in public_pages:
        if pathname == '/login':
            # Se já está logado, redireciona para home
            if session_data and session_data.get('session_id'):
                user = auth_service.get_user_by_session(session_data['session_id'])
                if user:
                    return html.Script("window.location.href = '/home';")
            return create_login_layout()
        elif pathname == '/session-expired':
            return create_session_expired_layout()
    
    # Verifica autenticação
    if not session_data or not session_data.get('session_id'):
        return html.Script("window.location.href = '/login';")
    
    # Valida sessão
    try:
        user = auth_service.get_user_by_session(session_data['session_id'])
        if not user:
            return html.Script("window.location.href = '/session-expired';")
    except Exception as e:
        print(f"Erro ao validar sessão: {e}")
        return html.Script("window.location.href = '/login';")
    
    # Verifica permissões
    page_name = pathname.lstrip('/') if pathname != '/' else 'home'
    if not user.can_access_page(page_name):
        return create_main_layout_with_content(create_access_denied_layout(), user)
    
    # Exibe página
    try:
        content = get_page_content(pathname)
        return create_main_layout_with_content(content, user)
    except Exception as e:
        error_content = dmc.Center([
            dmc.Alert(
                f"Erro ao carregar página: {str(e)[:100]}",
                title="Erro",
                color="red",
                icon=DashIconify(icon="tabler:exclamation-circle")
            )
        ])
        return create_main_layout_with_content(error_content, user)

def create_main_layout_with_content(content, user):
    """Cria layout principal com sidebar e conteúdo"""
    return html.Div([
        # Sidebar
        html.Div([
            create_sidebar_with_user(user)
        ], style={
            "position": "fixed",
            "left": 0,
            "top": 0,
            "width": "280px",
            "height": "100vh",
            "backgroundColor": "white",
            "borderRight": "1px solid var(--mantine-color-gray-3)",
            "zIndex": 100,
            "overflow": "auto"
        }),
        
        # Conteúdo principal
        html.Div([
            dmc.Container(
                content,
                size="xl",
                px="md",
                py="lg"
            )
        ], style={
            "marginLeft": "280px",
            "minHeight": "100vh",
            "backgroundColor": "#fafafa"
        }),
        
        # Elementos invisíveis para callbacks
        html.Div(id='current-user-info', style={'display': 'none'}),
        html.Div(id='user-role-badge', style={'display': 'none'}),
    ])

def create_sidebar_with_user(user):
    """Cria sidebar com informações do usuário"""
    # Usa a nova sidebar que já inclui seção de usuário integrada
    return create_sidebar(user)

def get_page_content(pathname):
    """Obtém conteúdo da página baseado no pathname"""
    if pathname == '/' or pathname == '/home':
        return create_home_layout()
    elif pathname == '/conversas':
        return create_conversas_layout()
    elif pathname == '/agendamentos':
        return create_agendamentos_layout()
    elif pathname == '/clientes':
        return create_clientes_layout()
    elif pathname == '/configuracoes':
        return create_configuracoes_layout()
    elif pathname == '/relatorios':
        return create_relatorios_layout()
    elif pathname == '/perfil':
        return create_perfil_layout()
    elif pathname == '/suporte':
        return create_suporte_layout()
    elif pathname == '/access-denied':
        return create_access_denied_layout()
    else:
        # Página 404
        return dmc.Center([
            dmc.Stack([
                dmc.Title("404 - Página não encontrada", order=1, ta="center"),
                dmc.Text("A página que você está procurando não existe.", ta="center", c="dimmed"),
                dmc.Button(
                    "Voltar ao início",
                    variant="light",
                    leftIcon=DashIconify(icon="tabler:home"),
                    id="go-home-btn"
                )
            ], align="center", spacing="md")
        ], style={"minHeight": "60vh"})

# Registra callbacks de autenticação
register_auth_callbacks(app)

# Registra callbacks das páginas
try:
    register_all_home_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks home: {e}")

try:
    register_all_conversas_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks conversas: {e}")

try:
    register_all_agendamentos_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks agendamentos: {e}")

try:
    register_clientes_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks clientes: {e}")

try:
    register_configuracoes_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks configurações: {e}")

try:
    register_relatorios_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks relatórios: {e}")

try:
    register_perfil_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks perfil: {e}")

try:
    register_all_suporte_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks suporte: {e}")

# Registra callbacks do sidebar
try:
    register_sidebar_callbacks(app)
except Exception as e:
    print(f"Aviso: Callbacks sidebar: {e}")

if __name__ == '__main__':
    # Configurações
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 8050))
    HOST = os.getenv('HOST', '127.0.0.1')
    
    print(f"""
    🚀 WppAgent Dashboard iniciando...
    
    📍 URL: http://{HOST}:{PORT}
    🛠️  Modo: {'Desenvolvimento' if DEBUG else 'Produção'}
    🔐 Autenticação: Habilitada
    
    👤 Credenciais padrão (desenvolvimento):
       Email: admin@exemplo.com
       Senha: admin123
    
    📋 Páginas disponíveis:
       • /login - Página de login
       • /home - Dashboard principal  
       • /conversas - Gestão de conversas WhatsApp
       • /agendamentos - Gestão de agendamentos
       • /clientes - Gestão de clientes
       • /configuracoes - Configurações (Admin+)
       • /relatorios - Relatórios (Manager+)
       • /perfil - Perfil do usuário
       • /suporte - Central de suporte
    
    🔧 Para configurar o banco de dados:
       python auth_setup.py setup
    """)
    
    app.run(
        debug=DEBUG,
        host=HOST,
        port=PORT,
        dev_tools_hot_reload=DEBUG,
        dev_tools_props_check=DEBUG
    )
