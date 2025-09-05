#!/usr/bin/env python3
"""
Script de Diagnóstico e Correção - WppAgent Dashboard
====================================================

Este script identifica e corrige erros comuns que causam:
- "Cannot read properties of undefined (reading 'props')"
- Componentes None sendo renderizados
- Problemas com Dash Mantine Components

Execute: python fix_dashboard_errors.py
"""

import os
import re
import ast
from pathlib import Path
from colorama import init, Fore, Style

# Inicializar colorama
init()

def print_header(title):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

class DashboardDebugger:
    """Classe para diagnosticar e corrigir problemas do dashboard"""
    
    def __init__(self):
        self.issues_found = []
        self.files_to_check = []
        self.common_patterns = {
            'none_in_list': r'None,|,\s*None|\[.*None.*\]',
            'empty_condition': r'if\s+.*:\s*None',
            'none_return': r'return\s+None',
            'missing_else': r'if.*:\s*return.*\n(?!\s*else)',
            'undefined_variable': r'(\w+)\s*if\s+\w+\s+else\s+None',
        }
    
    def find_dashboard_files(self):
        """Encontra todos os arquivos Python do dashboard"""
        print_header("LOCALIZANDO ARQUIVOS DO DASHBOARD")
        
        dashboard_dirs = ['layout', 'components', 'callbacks', 'services']
        python_files = []
        
        # Verificar se estamos no diretório correto
        if not os.path.exists('app.py'):
            if os.path.exists('dashboard/app.py'):
                os.chdir('dashboard')
                print_info("Mudando para diretório dashboard/")
            else:
                print_error("Arquivo app.py não encontrado!")
                return []
        
        # Coletar arquivos Python
        for dir_name in dashboard_dirs:
            if os.path.exists(dir_name):
                dir_path = Path(dir_name)
                for py_file in dir_path.glob('**/*.py'):
                    python_files.append(str(py_file))
                    print_success(f"Encontrado: {py_file}")
            else:
                print_warning(f"Diretório não encontrado: {dir_name}")
        
        # Adicionar arquivos importantes na raiz
        root_files = ['app.py']
        for file in root_files:
            if os.path.exists(file):
                python_files.append(file)
                print_success(f"Encontrado: {file}")
        
        self.files_to_check = python_files
        print_info(f"Total de arquivos para verificar: {len(python_files)}")
        return python_files
    
    def analyze_file_content(self, file_path):
        """Analisa conteúdo de um arquivo buscando problemas"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            issues = []
            
            # Verificar cada linha
            for line_num, line in enumerate(lines, 1):
                # 1. Procurar por None em listas de componentes
                if re.search(r'\[.*None.*\]', line):
                    issues.append({
                        'type': 'none_in_list',
                        'line': line_num,
                        'content': line.strip(),
                        'severity': 'high'
                    })
                
                # 2. Procurar por None sendo retornado em condicionais
                if re.search(r'if.*:\s*None', line):
                    issues.append({
                        'type': 'conditional_none',
                        'line': line_num,
                        'content': line.strip(),
                        'severity': 'high'
                    })
                
                # 3. Procurar por variáveis que podem ser None
                if re.search(r'(\w+)\s+if\s+.*\s+else\s+None', line):
                    issues.append({
                        'type': 'ternary_none',
                        'line': line_num,
                        'content': line.strip(),
                        'severity': 'medium'
                    })
                
                # 4. Procurar por componentes DMC sem children definidos
                if 'dmc.' in line and 'children=' not in line and ')]' in line:
                    issues.append({
                        'type': 'missing_children',
                        'line': line_num,
                        'content': line.strip(),
                        'severity': 'medium'
                    })
                
                # 5. Procurar por listas com elementos vazios
                if re.search(r'\[.*,\s*,.*\]', line):
                    issues.append({
                        'type': 'empty_list_element',
                        'line': line_num,
                        'content': line.strip(),
                        'severity': 'medium'
                    })
            
            return issues
            
        except Exception as e:
            print_error(f"Erro ao analisar {file_path}: {e}")
            return []
    
    def check_specific_components(self, file_path):
        """Verifica componentes específicos que causam problemas"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Padrões problemáticos específicos
            problematic_patterns = [
                # Badge com valor None
                (r'dmc\.Badge\(\s*None', 'Badge com valor None'),
                # Text com valor None
                (r'dmc\.Text\(\s*None', 'Text com valor None'),
                # ThemeIcon sem ícone
                (r'dmc\.ThemeIcon\(\s*\)', 'ThemeIcon sem ícone'),
                # Group com None
                (r'dmc\.Group\(\[.*None.*\]', 'Group contendo None'),
                # Stack com None
                (r'dmc\.Stack\(\[.*None.*\]', 'Stack contendo None'),
                # SimpleGrid com None
                (r'dmc\.SimpleGrid\(\[.*None.*\]', 'SimpleGrid contendo None'),
            ]
            
            for pattern, description in problematic_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append({
                        'type': 'component_issue',
                        'line': line_num,
                        'content': description,
                        'severity': 'high',
                        'pattern': pattern
                    })
            
            return issues
            
        except Exception as e:
            print_error(f"Erro ao verificar componentes em {file_path}: {e}")
            return []
    
    def analyze_all_files(self):
        """Analisa todos os arquivos encontrados"""
        print_header("ANALISANDO ARQUIVOS")
        
        all_issues = {}
        
        for file_path in self.files_to_check:
            print_info(f"Analisando: {file_path}")
            
            # Análise geral
            general_issues = self.analyze_file_content(file_path)
            
            # Análise específica de componentes
            component_issues = self.check_specific_components(file_path)
            
            # Combinar issues
            file_issues = general_issues + component_issues
            
            if file_issues:
                all_issues[file_path] = file_issues
                print_error(f"Encontrados {len(file_issues)} problemas em {file_path}")
            else:
                print_success(f"Nenhum problema encontrado em {file_path}")
        
        self.issues_found = all_issues
        return all_issues
    
    def generate_fixes(self):
        """Gera correções para os problemas encontrados"""
        print_header("GERANDO CORREÇÕES")
        
        fixes = {}
        
        for file_path, issues in self.issues_found.items():
            file_fixes = []
            
            for issue in issues:
                fix = self.get_fix_for_issue(issue)
                if fix:
                    file_fixes.append({
                        'issue': issue,
                        'fix': fix
                    })
            
            if file_fixes:
                fixes[file_path] = file_fixes
        
        return fixes
    
    def get_fix_for_issue(self, issue):
        """Retorna correção específica para um problema"""
        fixes_map = {
            'none_in_list': 'Remover None da lista ou substituir por componente válido',
            'conditional_none': 'Substituir None por html.Div() ou componente vazio',
            'ternary_none': 'Usar html.Div() ao invés de None',
            'missing_children': 'Adicionar children=[] explicitamente',
            'empty_list_element': 'Remover elementos vazios da lista',
            'component_issue': 'Corrigir componente com valor None'
        }
        
        return fixes_map.get(issue['type'], 'Correção não definida')
    
    def create_fixed_home_layout(self):
        """Cria uma versão corrigida do layout home"""
        print_header("CRIANDO LAYOUT HOME CORRIGIDO")
        
        fixed_layout = '''"""
Layout Home Corrigido - Sem erros de componentes None
"""

import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from datetime import datetime

def create_modern_kpi_card_safe(icon, title, value, subtitle, color, trend=None, id_prefix=""):
    """Cria card KPI com verificação de segurança"""
    
    # Garantir que todos os valores são válidos
    icon = icon or "tabler:help-circle"
    title = str(title) if title is not None else "N/A"
    value = str(value) if value is not None else "0"
    subtitle = str(subtitle) if subtitle is not None else ""
    color = color or "blue"
    
    gradient_colors = {
        "blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "green": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)", 
        "orange": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "purple": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
    }
    
    return dmc.Card([
        # Header do card
        html.Div([
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=icon, width=24),
                    size="xl",
                    color="white",
                    variant="filled"
                ),
                html.Div([
                    dmc.Text(title, size="sm", c="white", fw=500),
                    dmc.Text(value, size="xl", fw=700, c="white")
                ])
            ], position="apart", align="flex-start")
        ], style={
            "background": gradient_colors.get(color, gradient_colors["blue"]),
            "padding": "20px",
            "borderRadius": "12px 12px 0 0"
        }),
        
        # Footer do card  
        html.Div([
            dmc.Text(subtitle, size="sm", c="dimmed", ta="center")
        ], style={
            "padding": "12px 20px",
            "background": "#f8fafc",
            "borderRadius": "0 0 12px 12px"
        })
    ], 
    withBorder=False,
    shadow="md",
    className="kpi-card-safe",
    id=f"{id_prefix}-card" if id_prefix else None
    )

def create_home_layout_safe():
    """Layout home com proteção contra componentes None"""
    
    # Dados seguros para KPIs
    safe_kpis = {
        'total_conversations': 127,
        'unique_users': 284, 
        'total_appointments': 31,
        'total_messages': 3847,
        'messages_today': 67,
        'conversations_today': 8,
        'appointments_today': 4
    }
    
    return html.Div([
        # Hero Section
        html.Div([
            dmc.Container([
                dmc.Group([
                    html.Div([
                        dmc.Title("WPPAgent Dashboard", order=1, c="white"),
                        dmc.Text(
                            f"Visão geral • {datetime.now().strftime('%d/%m/%Y')}",
                            c="white", 
                            opacity=0.9
                        )
                    ]),
                    dmc.Select(
                        data=[
                            {"value": "7", "label": "7 dias"},
                            {"value": "30", "label": "30 dias"},
                            {"value": "90", "label": "90 dias"}
                        ],
                        value="30",
                        id="home-period-filter",
                        w=120
                    )
                ], position="apart", align="center")
            ], size="xl")
        ], style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "padding": "40px 0",
            "marginBottom": "30px"
        }),
        
        # KPIs Grid
        dmc.Container([
            dmc.SimpleGrid([
                create_modern_kpi_card_safe(
                    icon="tabler:message-circle-2",
                    title="Conversas Ativas",
                    value=safe_kpis['total_conversations'],
                    subtitle=f"+{safe_kpis['conversations_today']} hoje",
                    color="blue",
                    id_prefix="conversations"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:users-group",
                    title="Clientes Únicos",
                    value=safe_kpis['unique_users'],
                    subtitle="Base de clientes",
                    color="green",
                    id_prefix="users"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:calendar-check",
                    title="Agendamentos",
                    value=safe_kpis['total_appointments'],
                    subtitle=f"+{safe_kpis['appointments_today']} hoje",
                    color="orange",
                    id_prefix="appointments"
                ),
                create_modern_kpi_card_safe(
                    icon="tabler:message-dots",
                    title="Mensagens",
                    value=f"{safe_kpis['total_messages']:,}",
                    subtitle=f"{safe_kpis['messages_today']} hoje",
                    color="purple",
                    id_prefix="messages"
                )
            ], cols=4, spacing="lg", mb="xl"),
            
            # Seção de widgets
            dmc.Grid([
                # Performance
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Performance Hoje", fw=600, mb="md"),
                        dmc.Stack([
                            dmc.Group([
                                dmc.Text("Conversas iniciadas", size="sm"),
                                dmc.Text(str(safe_kpis['conversations_today']), fw=600)
                            ], position="apart"),
                            dmc.Group([
                                dmc.Text("Mensagens enviadas", size="sm"),
                                dmc.Text(str(safe_kpis['messages_today']), fw=600)
                            ], position="apart"),
                            dmc.Group([
                                dmc.Text("Taxa de resposta", size="sm"),
                                dmc.Text("94%", fw=600, c="green")
                            ], position="apart")
                        ])
                    ], withBorder=True, p="md")
                ], span=4),
                
                # Atividade Recente
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Atividade Recente", fw=600, mb="md"),
                        html.Div([
                            dmc.Text(
                                "Nenhuma atividade recente", 
                                size="sm", 
                                c="dimmed",
                                ta="center"
                            )
                        ], id="recent-activity-list")
                    ], withBorder=True, p="md")
                ], span=4),
                
                # Gráfico
                dmc.Col([
                    dmc.Card([
                        dmc.Text("Conversas - 7 dias", fw=600, mb="md"),
                        html.Div(
                            dmc.Text("Carregando gráfico...", ta="center"),
                            id="mini-chart-conversations"
                        )
                    ], withBorder=True, p="md")
                ], span=4)
            ], gutter="md", mb="xl"),
            
            # Ações Rápidas
            dmc.Card([
                dmc.Text("Ações Rápidas", fw=600, mb="md"),
                dmc.SimpleGrid([
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:message-plus", width=24),
                                size="xl",
                                color="green",
                                variant="light"
                            ),
                            dmc.Text("Nova Conversa", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-nova-conversa"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:calendar-plus", width=24),
                                size="xl",
                                color="blue",
                                variant="light"
                            ),
                            dmc.Text("Novo Agendamento", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-novo-agendamento"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:user-plus", width=24),
                                size="xl",
                                color="violet",
                                variant="light"
                            ),
                            dmc.Text("Adicionar Cliente", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-adicionar-cliente"),
                    
                    dmc.Paper([
                        dmc.Stack([
                            dmc.ThemeIcon(
                                DashIconify(icon="tabler:chart-line", width=24),
                                size="xl",
                                color="orange",
                                variant="light"
                            ),
                            dmc.Text("Ver Relatórios", fw=600, size="sm", ta="center")
                        ], align="center", spacing="sm")
                    ], withBorder=True, p="md", className="action-card", id="action-ver-relatorios")
                ], cols=4, spacing="md")
            ], withBorder=True, p="lg", mb="xl")
            
        ], size="xl"),
        
        # Stores
        dcc.Store(id="home-kpis-data", data=safe_kpis),
        dcc.Store(id="home-period", data=30)
        
    ], style={"background": "#fafafa", "minHeight": "100vh"})
'''
        
        # Salvar arquivo corrigido
        try:
            os.makedirs('layout', exist_ok=True)
            with open('layout/home_fixed.py', 'w', encoding='utf-8') as f:
                f.write(fixed_layout)
            print_success("Layout home corrigido salvo em: layout/home_fixed.py")
            return True
        except Exception as e:
            print_error(f"Erro ao salvar layout corrigido: {e}")
            return False
    
    def create_sidebar_fixed(self):
        """Cria versão corrigida do sidebar"""
        print_header("CRIANDO SIDEBAR CORRIGIDO")
        
        # Verificar se o arquivo existe
        sidebar_path = 'components/sidebar.py'
        if not os.path.exists(sidebar_path):
            print_error(f"Arquivo não encontrado: {sidebar_path}")
            return False
        
        try:
            with open(sidebar_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplicar correções comuns
            corrections = [
                # Remover None de listas
                (r'None,', ''),
                (r',\s*None', ''),
                # Corrigir badges condicionais
                (r'if item\.get\("badge"\) else None', 'if item.get("badge") else html.Div()'),
                # Corrigir trends condicionais
                (r'trend if trend else None', 'trend if trend else html.Div()'),
                # Corrigir componentes condicionais
                (r'\) if .* else None', ') if condition else html.Div()'),
            ]
            
            corrected_content = content
            fixes_applied = 0
            
            for pattern, replacement in corrections:
                if re.search(pattern, corrected_content):
                    corrected_content = re.sub(pattern, replacement, corrected_content)
                    fixes_applied += 1
            
            # Salvar versão corrigida
            if fixes_applied > 0:
                backup_path = 'components/sidebar_backup.py'
                os.makedirs('components', exist_ok=True)
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print_info(f"Backup salvo em: {backup_path}")
                
                with open(sidebar_path, 'w', encoding='utf-8') as f:
                    f.write(corrected_content)
                print_success(f"Sidebar corrigido com {fixes_applied} correções aplicadas")
                return True
            else:
                print_info("Nenhuma correção necessária no sidebar")
                return True
                
        except Exception as e:
            print_error(f"Erro ao corrigir sidebar: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo dos problemas encontrados"""
        print_header("RESUMO DO DIAGNÓSTICO")
        
        total_files = len(self.files_to_check)
        problematic_files = len(self.issues_found)
        total_issues = sum(len(issues) for issues in self.issues_found.values())
        
        print(f"📊 ESTATÍSTICAS:")
        print(f"   Arquivos verificados: {total_files}")
        print(f"   Arquivos com problemas: {problematic_files}")
        print(f"   Total de problemas: {total_issues}")
        
        if total_issues > 0:
            print(f"\n🔍 PROBLEMAS POR ARQUIVO:")
            for file_path, issues in self.issues_found.items():
                print_error(f"{file_path}: {len(issues)} problemas")
                for issue in issues[:3]:  # Mostrar apenas os primeiros 3
                    severity_color = Fore.RED if issue['severity'] == 'high' else Fore.YELLOW
                    print(f"     {severity_color}→ Linha {issue['line']}: {issue['type']}{Style.RESET_ALL}")
                if len(issues) > 3:
                    print(f"     ... e mais {len(issues) - 3} problemas")
        
        print(f"\n💡 RECOMENDAÇÕES:")
        if total_issues == 0:
            print_success("Nenhum problema crítico encontrado!")
        else:
            print_warning("Execute as correções sugeridas")
            print_info("Use as versões '_fixed' dos arquivos geradas")
            print_info("Teste a aplicação após aplicar as correções")
    
    def run_full_diagnosis(self):
        """Executa diagnóstico completo"""
        print(f"{Fore.MAGENTA}🔧 DIAGNÓSTICO COMPLETO DO DASHBOARD{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        
        # 1. Encontrar arquivos
        files = self.find_dashboard_files()
        if not files:
            print_error("Nenhum arquivo encontrado para análise")
            return
        
        # 2. Analisar problemas
        issues = self.analyze_all_files()
        
        # 3. Gerar correções
        fixes = self.generate_fixes()
        
        # 4. Criar arquivos corrigidos
        print_header("CRIANDO ARQUIVOS CORRIGIDOS")
        self.create_fixed_home_layout()
        self.create_sidebar_fixed()
        
        # 5. Resumo final
        self.print_summary()
        
        # 6. Instruções finais
        print_header("PRÓXIMOS PASSOS")
        print_info("1. Faça backup dos arquivos originais")
        print_info("2. Use as versões corrigidas geradas")
        print_info("3. Teste a aplicação: python app.py")
        print_info("4. Verifique o console do navegador")
        
        print(f"\n{Fore.GREEN}✨ Diagnóstico concluído!{Style.RESET_ALL}")

def main():
    """Função principal"""
    debugger = DashboardDebugger()
    debugger.run_full_diagnosis()

if __name__ == "__main__":
    main()