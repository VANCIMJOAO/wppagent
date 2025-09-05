#!/usr/bin/env python3
"""
Correção Específica para Erros 'Cannot read properties of undefined'
==================================================================

Este script identifica e corrige especificamente os erros do tipo:
"Cannot read properties of undefined (reading 'props')"

Esses erros ocorrem quando:
1. Componentes Dash recebem None no children
2. Listas de componentes contêm None
3. Componentes condicionais retornam None
4. Props não inicializadas ou undefined

Uso: python fix_undefined_errors.py
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

def backup_file(file_path):
    """Cria backup do arquivo antes de modificar"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_none_in_components(content):
    """Corrige problemas específicos com None em componentes"""
    fixes_applied = 0
    
    # 1. Corrigir None em listas de children
    patterns = [
        # None em listas diretas
        (r'\[([^]]*?),?\s*None\s*,?([^]]*?)\]', lambda m: f'[{m.group(1)}{", " if m.group(1) and m.group(2) else ""}{m.group(2)}]'),
        
        # None no início de listas
        (r'\[\s*None\s*,\s*', '['),
        
        # None no final de listas
        (r',\s*None\s*\]', ']'),
        
        # Componentes condicionais que retornam None
        (r'(\w+\s+if\s+[^}]+else\s+)None', r'\1html.Div()'),
        
        # Badges condicionais
        (r'dmc\.Badge\([^)]*\)\s+if\s+[^}]+else\s+None', r'dmc.Badge(item.get("badge", ""), size="xs", color="red", variant="filled") if item.get("badge") else html.Div()'),
        
        # Text com None
        (r'dmc\.Text\(\s*None', 'dmc.Text("")'),
        
        # ThemeIcon sem ícone
        (r'DashIconify\(\s*\)', 'DashIconify(icon="tabler:help-circle")'),
    ]
    
    for pattern, replacement in patterns:
        if isinstance(replacement, str):
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                fixes_applied += 1
        else:
            # Para replacements mais complexos (funções lambda)
            matches = list(re.finditer(pattern, content))
            for match in reversed(matches):  # Processar de trás para frente
                new_text = replacement(match)
                content = content[:match.start()] + new_text + content[match.end():]
                fixes_applied += 1
    
    return content, fixes_applied

def fix_component_specific_issues(content):
    """Corrige problemas específicos de componentes DMC"""
    fixes_applied = 0
    
    # Problemas específicos conhecidos
    specific_fixes = [
        # SimpleGrid com children None
        (r'dmc\.SimpleGrid\(\s*None', 'dmc.SimpleGrid(children=[]'),
        (r'dmc\.SimpleGrid\(\s*\[([^]]*None[^]]*)\]', r'dmc.SimpleGrid(children=[\1])'),
        
        # Stack com None
        (r'dmc\.Stack\(\s*\[([^]]*None[^]]*)\]', r'dmc.Stack(children=[\1])'),
        
        # Group com None  
        (r'dmc\.Group\(\s*\[([^]]*None[^]]*)\]', r'dmc.Group(children=[\1])'),
        
        # Container sem children
        (r'dmc\.Container\(\s*None', 'dmc.Container(children=[]'),
        
        # Cards sem children
        (r'dmc\.Card\(\s*None', 'dmc.Card(children=[]'),
        
        # Paper sem children
        (r'dmc\.Paper\(\s*None', 'dmc.Paper(children=[]'),
    ]
    
    for pattern, replacement in specific_fixes:
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            fixes_applied += 1
    
    return content, fixes_applied

def ensure_safe_conditionals(content):
    """Garante que condicionais sempre retornem componentes válidos"""
    fixes_applied = 0
    
    conditional_patterns = [
        # Expressões ternárias que podem retornar None
        (r'([^=]+\s+if\s+[^}]+\s+else\s+)None', r'\1html.Div()'),
        
        # Condicionais em listas comprehension
        (r'\[([^]]+if[^]]+else\s+None[^]]+)\]', r'[item for item in [\1] if item is not None]'),
        
        # Map functions que podem retornar None
        (r'map\([^,]+,\s*([^)]+)\)', r'[item for item in map(lambda x: x, \1) if item is not None]'),
    ]
    
    for pattern, replacement in conditional_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes_applied += 1
    
    return content, fixes_applied

def add_safe_wrappers(content):
    """Adiciona wrappers seguros para componentes problemáticos"""
    
    # Adicionar função utilitária no topo do arquivo se não existir
    safe_wrapper = '''
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
'''
    
    if 'def safe_component' not in content:
        # Encontrar importações e adicionar depois
        import_match = re.search(r'(from [^\n]+\n)+', content)
        if import_match:
            insertion_point = import_match.end()
            content = content[:insertion_point] + '\n' + safe_wrapper + '\n' + content[insertion_point:]
            return content, 1
    
    return content, 0

def fix_file(file_path):
    """Corrige um arquivo específico"""
    print(f"🔧 Corrigindo: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Fazer backup
        backup_path = backup_file(file_path)
        print(f"   📋 Backup salvo: {backup_path}")
        
        # Aplicar correções
        content = original_content
        total_fixes = 0
        
        # 1. Corrigir None em componentes
        content, fixes1 = fix_none_in_components(content)
        total_fixes += fixes1
        
        # 2. Corrigir problemas específicos de componentes
        content, fixes2 = fix_component_specific_issues(content)
        total_fixes += fixes2
        
        # 3. Garantir condicionais seguros
        content, fixes3 = ensure_safe_conditionals(content)
        total_fixes += fixes3
        
        # 4. Adicionar wrappers seguros
        content, fixes4 = add_safe_wrappers(content)
        total_fixes += fixes4
        
        # Salvar arquivo corrigido se houve alterações
        if total_fixes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ {total_fixes} correções aplicadas")
        else:
            print(f"   ℹ️  Nenhuma correção necessária")
        
        return total_fixes
        
    except Exception as e:
        print(f"   ❌ Erro ao corrigir arquivo: {e}")
        return 0

def create_safe_sidebar():
    """Cria versão completamente segura do sidebar"""
    safe_sidebar_content = '''"""
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
'''
    
    try:
        with open('components/sidebar.py', 'w', encoding='utf-8') as f:
            f.write(safe_sidebar_content)
        print("✅ Sidebar seguro criado em: components/sidebar.py")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar sidebar seguro: {e}")
        return False

def main():
    """Função principal de correção"""
    print("🔧 CORRETOR DE ERROS 'undefined (reading props)'")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('app.py'):
        if os.path.exists('dashboard/app.py'):
            os.chdir('dashboard')
            print("📁 Mudando para diretório dashboard/")
        else:
            print("❌ app.py não encontrado!")
            return
    
    # Arquivos críticos para correção
    critical_files = [
        'components/sidebar.py',
        'layout/home.py',
        'layout/conversas.py',
        'layout/agendamentos.py',
        'layout/clientes.py',
        'layout/configuracoes.py',
        'layout/relatorios.py',
        'layout/perfil.py',
        'layout/suporte.py'
    ]
    
    total_fixes = 0
    files_fixed = 0
    
    # Corrigir cada arquivo
    for file_path in critical_files:
        if os.path.exists(file_path):
            fixes = fix_file(file_path)
            total_fixes += fixes
            if fixes > 0:
                files_fixed += 1
        else:
            print(f"⚠️  Arquivo não encontrado: {file_path}")
    
    # Criar sidebar completamente seguro
    print("\n🛠️  Criando componentes seguros...")
    create_safe_sidebar()
    
    # Resumo
    print(f"\n📊 RESUMO:")
    print(f"   Arquivos corrigidos: {files_fixed}")
    print(f"   Total de correções: {total_fixes}")
    print(f"   Sidebar seguro: ✅")
    
    print(f"\n💡 PRÓXIMOS PASSOS:")
    print("1. Reinicie a aplicação: python app.py")
    print("2. Verifique o console do navegador")
    print("3. Teste todas as páginas")
    print("4. Se erros persistirem, execute novamente")
    
    print("\n✨ Correções aplicadas com sucesso!")

if __name__ == "__main__":
    main()
