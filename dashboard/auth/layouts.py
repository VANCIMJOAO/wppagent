"""
Layout de Login/Autenticação
============================

Interface moderna para login e autenticação dos usuários.
"""

import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def create_login_layout():
    """Cria layout da página de login"""
    return dmc.Center([
        dmc.Paper([
            dmc.Stack([
                # Logo e título
                dmc.Center([
                    dmc.Stack([
                        dmc.ThemeIcon(
                            DashIconify(icon="tabler:brand-whatsapp", width=40),
                            size=80,
                            radius="xl",
                            color="green",
                            variant="light"
                        ),
                        dmc.Title("WppAgent", order=2, ta="center", c="dark"),
                        dmc.Text("Entre na sua conta", ta="center", c="dimmed", size="sm")
                    ], align="center", spacing="xs")
                ]),
                
                # Formulário de login
                dmc.Stack([
                    dmc.TextInput(
                        id="login-email",
                        label="Email",
                        placeholder="seu@email.com",
                        icon=DashIconify(icon="tabler:mail"),
                        required=True,
                        style={"width": "100%"}
                    ),
                    
                    dmc.PasswordInput(
                        id="login-password",
                        label="Senha",
                        placeholder="Digite sua senha",
                        icon=DashIconify(icon="tabler:lock"),
                        required=True,
                        style={"width": "100%"}
                    ),
                    
                    # Lembrar e esqueci senha
                    dmc.Group([
                        dmc.Checkbox(
                            id="login-remember",
                            label="Lembrar de mim",
                            size="sm"
                        ),
                        dmc.Anchor(
                            "Esqueci minha senha",
                            href="#",
                            size="sm",
                            c="blue"
                        )
                    ], mt="sm"),
                    
                    # Botão de login
                    dmc.Button(
                        "Entrar",
                        id="login-button",
                        fullWidth=True,
                        size="md",
                        mt="lg",
                        leftIcon=DashIconify(icon="tabler:login")
                    ),
                    
                    # Alert para mensagens de erro
                    dmc.Alert(
                        id="login-alert",
                        title="",
                        children="",
                        color="red",
                        style={"display": "none"}
                    )
                    
                ], spacing="md")
                
            ], spacing="xl")
        ], 
        shadow="lg", 
        radius="md", 
        p="xl",
        style={
            "width": "100%",
            "maxWidth": "400px",
            "backgroundColor": "white"
        })
    ], 
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "padding": "20px"
    })

def create_protected_layout_wrapper(content, user=None):
    """
    Wrapper para páginas protegidas que inclui informações do usuário
    """
    return html.Div([
        # Store para dados do usuário logado
        dcc.Store(id='current-user', data=user.to_dict() if user else None),
        
        # Conteúdo da página
        content
    ])

def create_access_denied_layout():
    """Layout para acesso negado"""
    return dmc.Center([
        dmc.Paper([
            dmc.Stack([
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:lock", width=50),
                    size=100,
                    radius="xl",
                    color="red",
                    variant="light"
                ),
                
                dmc.Title("Acesso Negado", order=2, ta="center"),
                
                dmc.Text(
                    "Você não tem permissão para acessar esta página.",
                    ta="center",
                    c="dimmed"
                ),
                
                dmc.Group([
                    dmc.Button(
                        "Voltar",
                        variant="outline",
                        leftIcon=DashIconify(icon="tabler:arrow-left"),
                        id="access-denied-back"
                    ),
                    dmc.Button(
                        "Ir para Home",
                        leftIcon=DashIconify(icon="tabler:home"),
                        id="access-denied-home"
                    )
                ], mt="lg")
                
            ], align="center", spacing="lg")
        ], p="xl", shadow="md", radius="md")
    ], style={"minHeight": "60vh"})

def create_logout_layout():
    """Layout exibido durante logout"""
    return dmc.Center([
        dmc.Paper([
            dmc.Stack([
                dmc.Loader(size="lg", color="blue"),
                dmc.Text("Encerrando sessão...", ta="center", c="dimmed")
            ], align="center", spacing="md")
        ], p="xl", shadow="md", radius="md")
    ], style={"minHeight": "60vh"})

def create_session_expired_layout():
    """Layout para sessão expirada"""
    return dmc.Center([
        dmc.Paper([
            dmc.Stack([
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:clock-x", width=40),
                    size=80,
                    radius="xl",
                    color="orange",
                    variant="light"
                ),
                
                dmc.Title("Sessão Expirada", order=2, ta="center"),
                
                dmc.Text(
                    "Sua sessão expirou por segurança. Faça login novamente.",
                    ta="center",
                    c="dimmed"
                ),
                
                dmc.Button(
                    "Fazer Login",
                    fullWidth=True,
                    leftIcon=DashIconify(icon="tabler:login"),
                    id="session-expired-login",
                    mt="lg"
                )
                
            ], align="center", spacing="lg")
        ], p="xl", shadow="md", radius="md", style={"maxWidth": "400px"})
    ], style={"minHeight": "60vh"})
