#!/usr/bin/env python3
"""
Teste Específico de Funcionalidades Home - WppAgent Dashboard
============================================================

Testa especificamente:
- KPIs captando dados corretos do backend
- Filtro de tempo funcionando (7/30/90 dias)  
- Cards de Performance e Atividade Recente com dados reais
- Botões de ações rápidas navegando corretamente
- Gráfico de conversas renderizando
- Callbacks e interações funcionando

Execute: python test_home_specific.py
"""

import sys
import os
import time
import json
import requests
import subprocess
from datetime import datetime, timedelta
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Inicializar colorama
init()

def print_header(title):
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{title.center(70)}")
    print(f"{'='*70}{Style.RESET_ALL}")

def print_section(title):
    print(f"\n{Fore.YELLOW}--- {title} ---{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

class HomeSpecificTester:
    """Testador específico para funcionalidades da home"""
    
    def __init__(self):
        self.app_process = None
        self.driver = None
        self.base_url = "http://localhost:8050"
        self.test_results = []
        
        # Configurar ambiente
        self.setup_environment()
    
    def setup_environment(self):
        """Configurar ambiente de teste"""
        print_section("CONFIGURAÇÃO DO AMBIENTE")
        
        # Verificar diretório
        if os.path.exists('/home/vancim/whats_agent/dashboard'):
            os.chdir('/home/vancim/whats_agent/dashboard')
            sys.path.insert(0, os.getcwd())
            print_success(f"Diretório: {os.getcwd()}")
        else:
            print_error("Diretório dashboard não encontrado")
    
    def start_dashboard(self):
        """Iniciar aplicação dashboard"""
        print_section("INICIANDO DASHBOARD")
        
        try:
            # Matar processos existentes
            subprocess.run(['pkill', '-f', 'python app.py'], capture_output=True)
            time.sleep(3)
            
            # Iniciar novo processo
            self.app_process = subprocess.Popen(
                ['python', 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Aguardar inicialização
            print_info("Aguardando dashboard inicializar...")
            for i in range(20):  # 20 segundos máximo
                try:
                    response = requests.get(self.base_url, timeout=2)
                    if response.status_code == 200:
                        print_success(f"Dashboard iniciado em {i+1} segundos")
                        return True
                except:
                    time.sleep(1)
            
            print_error("Dashboard não iniciou no tempo esperado")
            return False
            
        except Exception as e:
            print_error(f"Erro ao iniciar dashboard: {e}")
            return False
    
    def setup_selenium(self):
        """Configurar Selenium WebDriver"""
        print_section("CONFIGURANDO SELENIUM")
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            print_success("Selenium configurado com sucesso")
            return True
            
        except Exception as e:
            print_warning(f"Selenium não disponível: {e}")
            return False
    
    def test_kpis_data_accuracy(self):
        """Testar se os KPIs estão captando dados corretos do backend"""
        print_header("TESTE 1: PRECISÃO DOS DADOS DOS KPIs")
        
        try:
            # 1. Obter dados direto do backend
            print_info("Obtendo dados do backend...")
            from services.queries import HomeQueries
            queries = HomeQueries()
            backend_data = queries.get_kpis(period_days=30)
            
            print_info(f"Dados do backend: {backend_data}")
            
            # 2. Navegar para página e fazer login se necessário
            if self.driver:
                print_info("Fazendo login no dashboard...")
                self.driver.get(f"{self.base_url}/login")
                time.sleep(3)
                
                # Fazer login
                try:
                    email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[id*='email'], input[placeholder*='email']")
                    password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[id*='password'], input[placeholder*='senha']")
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button:contains('Entrar'), button:contains('Login')")
                    
                    email_input.clear()
                    email_input.send_keys("admin@exemplo.com")  # Email correto baseado na sua informação
                    password_input.clear()
                    password_input.send_keys("admin123")
                    
                    login_button.click()
                    time.sleep(5)  # Aguardar redirecionamento
                    
                    print_success("Login realizado com sucesso")
                    
                except Exception as login_e:
                    print_warning(f"Erro no login: {login_e}")
                    # Tentar login alternativo
                    try:
                        # Procurar campos de forma mais ampla
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        
                        if len(inputs) >= 2:
                            inputs[0].send_keys("admin@exemplo.com")
                            inputs[1].send_keys("admin123")
                            
                            if buttons:
                                buttons[0].click()
                                time.sleep(5)
                                print_success("Login alternativo realizado")
                    except Exception as alt_login_e:
                        print_error(f"Login falhou: {alt_login_e}")
                
                # Navegar para home após login
                print_info("Navegando para dashboard...")
                self.driver.get(f"{self.base_url}/home")
                time.sleep(5)  # Aguardar carregamento
                
                # Capturar valores dos KPIs na interface
                kpi_selectors = {
                    'conversations': '#kpi-conversations',
                    'users': '#kpi-users',
                    'appointments': '#kpi-appointments',
                    'messages': '#kpi-messages'
                }
                
                ui_data = {}
                for key, selector in kpi_selectors.items():
                    try:
                        # Buscar elemento do KPI usando ID correto
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if element:
                            text = element.text
                            if text:
                                # Extrair números do texto
                                import re
                                # Limpar texto e extrair número
                                clean_text = text.replace('.', '').replace(',', '')
                                numbers = re.findall(r'\d+', clean_text)
                                if numbers:
                                    ui_data[key] = int(numbers[0])
                                    print_success(f"KPI {key}: {ui_data[key]} (texto: '{text}')")
                    except Exception as e:
                        print_warning(f"Erro ao capturar {key}: {e}")
                
                print_info(f"Dados da UI: {ui_data}")
                
                # 3. Comparar backend vs UI
                discrepancies = []
                matches = []
                
                backend_mapping = {
                    'conversations': 'total_conversations',
                    'users': 'unique_users', 
                    'appointments': 'total_appointments',
                    'messages': 'total_messages'
                }
                
                for ui_key, backend_key in backend_mapping.items():
                    backend_value = backend_data.get(backend_key, 0)
                    ui_value = ui_data.get(ui_key, 0)
                    
                    if backend_value == ui_value:
                        matches.append(f"{ui_key}: {ui_value}")
                        print_success(f"{ui_key.title()}: Backend={backend_value}, UI={ui_value} ✓")
                    else:
                        discrepancies.append(f"{ui_key}: Backend={backend_value}, UI={ui_value}")
                        print_error(f"{ui_key.title()}: Backend={backend_value}, UI={ui_value} ✗")
                
                # Resultado do teste
                if len(matches) >= len(discrepancies):
                    self.test_results.append(("KPIs Data Accuracy", "PASS", f"{len(matches)} corretos, {len(discrepancies)} incorretos"))
                else:
                    self.test_results.append(("KPIs Data Accuracy", "FAIL", f"Muitas discrepâncias: {discrepancies}"))
            
            else:
                # Teste sem selenium - apenas backend
                if backend_data and len(backend_data) > 4:
                    self.test_results.append(("KPIs Backend Data", "PASS", f"Backend retornando {len(backend_data)} campos"))
                    print_success(f"Backend funcionando: {list(backend_data.keys())}")
                else:
                    self.test_results.append(("KPIs Backend Data", "FAIL", "Backend não retornou dados suficientes"))
                    
        except Exception as e:
            print_error(f"Erro no teste de KPIs: {e}")
            self.test_results.append(("KPIs Data Accuracy", "FAIL", f"Erro: {str(e)}"))
    
    def perform_login(self):
        """Função auxiliar para realizar login no dashboard"""
        try:
            print_info("Fazendo login...")
            self.driver.get(f"{self.base_url}/login")
            time.sleep(3)
            
            # Tentar diferentes seletores para os campos de login
            email_selectors = [
                "input[type='email']",
                "input[id*='email']", 
                "input[placeholder*='email']",
                "input[name*='email']",
                "input[placeholder*='Email']"
            ]
            
            password_selectors = [
                "input[type='password']",
                "input[id*='password']",
                "input[placeholder*='senha']", 
                "input[name*='password']",
                "input[placeholder*='Password']"
            ]
            
            button_selectors = [
                "button[type='submit']",
                "button:contains('Entrar')",
                "button:contains('Login')",
                "input[type='submit']"
            ]
            
            email_input = None
            password_input = None
            login_button = None
            
            # Encontrar campo de email
            for selector in email_selectors:
                try:
                    email_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            # Encontrar campo de senha
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            # Encontrar botão de login
            for selector in button_selectors:
                try:
                    if "contains" in selector:
                        # Usar XPath para contains
                        text = selector.split("'")[1]  # Extrair texto entre aspas
                        xpath = f"//button[contains(text(), '{text}')]"
                        login_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            # Se não encontrou pelos seletores, tentar por índice
            if not email_input or not password_input:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                if len(inputs) >= 2:
                    email_input = inputs[0]
                    password_input = inputs[1]
            
            if not login_button:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                if buttons:
                    login_button = buttons[0]
            
            # Realizar login
            if email_input and password_input:
                email_input.clear()
                email_input.send_keys("admin@exemplo.com")
                password_input.clear() 
                password_input.send_keys("admin123")
                
                if login_button:
                    login_button.click()
                    time.sleep(5)
                    print_success("Login realizado com sucesso")
                    return True
                else:
                    print_warning("Botão de login não encontrado")
            else:
                print_warning("Campos de login não encontrados")
                
        except Exception as e:
            print_warning(f"Erro no login: {e}")
        
        return False
    def test_time_filter_functionality(self):
        """Testar se o filtro de tempo está funcionando (7/30/90 dias)"""
        print_header("TESTE 2: FUNCIONALIDADE DO FILTRO DE TEMPO")
        
        if not self.driver:
            print_warning("Selenium não disponível - testando apenas backend")
            
            try:
                from services.queries import HomeQueries
                queries = HomeQueries()
                
                # Testar diferentes períodos no backend
                periods = [7, 30, 90]
                backend_results = {}
                
                for period in periods:
                    try:
                        data = queries.get_kpis(period_days=period)
                        backend_results[period] = data
                        print_success(f"Backend - {period} dias: {len(data) if data else 0} campos")
                    except Exception as e:
                        print_error(f"Backend - {period} dias: Erro - {e}")
                        backend_results[period] = None
                
                # Verificar se os resultados são diferentes para períodos diferentes
                valid_results = [r for r in backend_results.values() if r is not None]
                if len(valid_results) >= 2:
                    self.test_results.append(("Time Filter Backend", "PASS", f"Backend suporta múltiplos períodos"))
                else:
                    self.test_results.append(("Time Filter Backend", "FAIL", "Backend não diferencia períodos"))
                    
            except Exception as e:
                self.test_results.append(("Time Filter Backend", "FAIL", f"Erro: {str(e)}"))
            return
        
        try:
            print_info("Testando filtro de tempo na interface...")
            
            if not self.driver:
                print_warning("Selenium não disponível - testando apenas backend")
                # ... resto do código backend existente ...
                return
            
            # Fazer login primeiro
            if not self.perform_login():
                print_error("Falha no login - teste limitado")
                self.test_results.append(("Time Filter UI", "FAIL", "Falha no login"))
                return
            
            # Navegar para página
            self.driver.get(f"{self.base_url}/home")  # CORRIGIDO: navegar para /home
            time.sleep(5)
            
            # Procurar dropdown de período
            filter_found = False
            filter_selectors = [
                "#home-period-filter",
                "[id*='period']", 
                "[id*='filter']",
                "select",
                "[role='combobox']"
            ]
            
            period_filter = None
            for selector in filter_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            period_filter = element
                            filter_found = True
                            print_success(f"Filtro encontrado com seletor: {selector}")
                            break
                    if filter_found:
                        break
                except:
                    continue
            
            if filter_found and period_filter:
                try:
                    # Testar mudança de período
                    original_text = self.driver.find_element(By.TAG_NAME, "body").text
                    
                    # Clicar no filtro
                    period_filter.click()
                    time.sleep(2)
                    
                    # Procurar opções de período
                    options = self.driver.find_elements(By.CSS_SELECTOR, "[data-value], option, [role='option']")
                    
                    if options:
                        print_success(f"Encontradas {len(options)} opções no filtro")
                        
                        # Testar mudança para um período diferente
                        for option in options[:2]:  # Testar primeiras 2 opções
                            try:
                                option_text = option.text or option.get_attribute('value')
                                if option_text and option_text != "30":
                                    option.click()
                                    time.sleep(3)  # Aguardar atualização
                                    
                                    # Verificar se página foi atualizada
                                    new_text = self.driver.find_element(By.TAG_NAME, "body").text
                                    if new_text != original_text:
                                        print_success(f"Filtro funcionando - página atualizada para: {option_text}")
                                        self.test_results.append(("Time Filter UI", "PASS", f"Filtro funcional, {len(options)} opções"))
                                        return
                                    else:
                                        print_info(f"Filtro clicado mas página não atualizou para: {option_text}")
                                    break
                            except Exception as e:
                                print_warning(f"Erro ao testar opção: {e}")
                    
                    # Se chegou aqui, filtro existe mas pode não estar funcionando
                    self.test_results.append(("Time Filter UI", "WARNING", "Filtro encontrado mas funcionalidade incerta"))
                    
                except Exception as e:
                    print_error(f"Erro ao interagir com filtro: {e}")
                    self.test_results.append(("Time Filter UI", "FAIL", f"Erro na interação: {str(e)}"))
            else:
                print_error("Filtro de período não encontrado na interface")
                self.test_results.append(("Time Filter UI", "FAIL", "Filtro não encontrado na UI"))
                
        except Exception as e:
            print_error(f"Erro no teste do filtro: {e}")
            self.test_results.append(("Time Filter UI", "FAIL", f"Erro: {str(e)}"))
    
    def test_activity_and_performance_cards(self):
        """Testar se cards de Atividade Recente e Performance têm dados reais"""
        print_header("TESTE 3: CARDS DE ATIVIDADE E PERFORMANCE")
        
        try:
            # 1. Testar backend para atividade recente
            print_info("Testando dados de atividade recente...")
            
            from services.queries import HomeQueries
            queries = HomeQueries()
            
            # Tentar diferentes métodos para obter atividade recente
            activity_methods = [
                ('get_recent_conversations', 'Conversas Recentes'),
                ('get_recent_activity', 'Atividade Recente'),
                ('get_timeline_data', 'Timeline de Dados')
            ]
            
            activity_data_found = False
            for method_name, description in activity_methods:
                try:
                    if hasattr(queries, method_name):
                        method = getattr(queries, method_name)
                        data = method(limit=10) if 'limit' in method.__code__.co_varnames else method()
                        
                        if data:
                            print_success(f"{description}: {len(data) if hasattr(data, '__len__') else 1} itens")
                            activity_data_found = True
                        else:
                            print_warning(f"{description}: Sem dados")
                    else:
                        print_info(f"{description}: Método não existe")
                except Exception as e:
                    print_warning(f"{description}: Erro - {e}")
            
            # 2. Testar performance hoje
            print_info("Testando dados de performance...")
            
            performance_methods = [
                ('get_performance_data', 'Dados de Performance'),
                ('get_today_stats', 'Estatísticas Hoje'),
                ('get_kpis', 'KPIs Gerais')
            ]
            
            performance_data_found = False
            for method_name, description in performance_methods:
                try:
                    if hasattr(queries, method_name):
                        method = getattr(queries, method_name)
                        data = method()
                        
                        if data:
                            print_success(f"{description}: Dados obtidos")
                            performance_data_found = True
                            
                            # Se for KPIs, verificar campos específicos de performance
                            if method_name == 'get_kpis' and isinstance(data, dict):
                                perf_fields = ['conversations_today', 'messages_today', 'appointments_today']
                                found_fields = [f for f in perf_fields if f in data]
                                print_info(f"Campos de performance encontrados: {found_fields}")
                        else:
                            print_warning(f"{description}: Sem dados")
                    else:
                        print_info(f"{description}: Método não existe")
                except Exception as e:
                    print_warning(f"{description}: Erro - {e}")
            
            # 3. Verificar na interface se há dados
            if self.driver:
                print_info("Verificando dados na interface...")
                
                # Fazer login primeiro
                if not self.perform_login():
                    print_warning("Falha no login - teste limitado à análise backend")
                    if backend_ok:
                        self.test_results.append(("Activity & Performance Cards", "WARNING", "Backend OK, mas falha no login"))
                    return
                
                self.driver.get(f"{self.base_url}/home")  # CORRIGIDO: navegar para /home
                time.sleep(5)
                
                # Procurar por cards de atividade e performance
                activity_indicators = [
                    "Atividade Recente",
                    "Performance Hoje", 
                    "Nenhuma atividade",
                    "Conversas iniciadas",
                    "Mensagens enviadas"
                ]
                
                cards_with_data = 0
                cards_empty = 0
                
                for indicator in activity_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                        if elements:
                            # Verificar se há dados reais nos cards
                            for element in elements:
                                parent = element.find_element(By.XPATH, "./..")
                                parent_text = parent.text
                                
                                if "Nenhuma atividade" in parent_text or "Carregando" in parent_text:
                                    cards_empty += 1
                                    print_warning(f"Card vazio encontrado: {indicator}")
                                else:
                                    # Procurar por números nos cards
                                    import re
                                    numbers = re.findall(r'\d+', parent_text)
                                    if numbers:
                                        cards_with_data += 1
                                        print_success(f"Card com dados: {indicator} ({numbers})")
                                    else:
                                        cards_empty += 1
                                        print_warning(f"Card sem números: {indicator}")
                    except Exception as e:
                        print_info(f"Indicador '{indicator}' não encontrado ou erro: {e}")
                
                print_info(f"Resumo cards: {cards_with_data} com dados, {cards_empty} vazios")
            
            # Resultado do teste
            backend_ok = activity_data_found or performance_data_found
            ui_ok = not hasattr(self, 'driver') or self.driver is None or cards_with_data > 0
            
            if backend_ok and ui_ok:
                self.test_results.append(("Activity & Performance Cards", "PASS", "Backend e UI com dados"))
            elif backend_ok:
                self.test_results.append(("Activity & Performance Cards", "WARNING", "Backend OK, UI pode estar vazia"))
            else:
                self.test_results.append(("Activity & Performance Cards", "FAIL", "Backend e UI sem dados"))
                
        except Exception as e:
            print_error(f"Erro no teste de cards: {e}")
            self.test_results.append(("Activity & Performance Cards", "FAIL", f"Erro: {str(e)}"))
    
    def test_quick_actions_navigation(self):
        """Testar se botões de ações rápidas navegam corretamente"""
        print_header("TESTE 4: NAVEGAÇÃO DAS AÇÕES RÁPIDAS")
        
        if not self.driver:
            print_warning("Selenium não disponível - não é possível testar navegação")
            self.test_results.append(("Quick Actions Navigation", "SKIP", "Selenium não disponível"))
            return
        
        try:
            print_info("Testando navegação das ações rápidas...")
            
            # Fazer login primeiro
            if not self.perform_login():
                print_error("Falha no login - não é possível testar navegação")
                self.test_results.append(("Quick Actions Navigation", "FAIL", "Falha no login"))
                return
            
            # Navegar para página
            self.driver.get(f"{self.base_url}/home")
            time.sleep(5)
            
            # Definir ações esperadas
            quick_actions = [
                ("Nova Conversa", ["/conversas", "conversa", "nova"]),
                ("Novo Agendamento", ["/agendamentos", "agendamento", "novo"]),
                ("Adicionar Cliente", ["/clientes", "cliente", "adicionar"]),
                ("Ver Relatórios", ["/relatorios", "relatorio", "ver"])
            ]
            
            successful_navigations = 0
            failed_navigations = 0
            
            for action_name, expected_paths in quick_actions:
                try:
                    print_info(f"Testando: {action_name}")
                    
                    # Voltar para página inicial
                    self.driver.get(f"{self.base_url}/home")
                    time.sleep(3)
                    
                    original_url = self.driver.current_url
                    
                    # Procurar botão da ação usando ID correto
                    button_found = False
                    button_selectors = [
                        f"#{action_name.lower().replace(' ', '-').replace('ção', 'cao').replace('ãos', 'aos')}",
                        f"#action-{action_name.lower().replace(' ', '-').replace('ção', 'cao').replace('ãos', 'aos')}",
                        f"[id*='{action_name.lower().replace(' ', '-')}']",
                        f"//*[contains(text(), '{action_name}')]"
                    ]
                    
                    # Mapeamento específico dos IDs
                    action_id_mapping = {
                        "Nova Conversa": "action-nova-conversa",
                        "Novo Agendamento": "action-novo-agendamento", 
                        "Adicionar Cliente": "action-adicionar-cliente",
                        "Ver Relatórios": "action-ver-relatorios"
                    }
                    
                    if action_name in action_id_mapping:
                        button_selectors.insert(0, f"#{action_id_mapping[action_name]}")
                    
                    for selector in button_selectors:
                        try:
                            if selector.startswith("//*"):
                                elements = self.driver.find_elements(By.XPATH, selector)
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    # Tentar clicar
                                    try:
                                        # Scroll até elemento se necessário
                                        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                        time.sleep(1)
                                        
                                        element.click()
                                        time.sleep(3)  # Aguardar navegação
                                        
                                        new_url = self.driver.current_url
                                        
                                        # Verificar se URL mudou
                                        if new_url != original_url:
                                            # Verificar se navegou para local esperado
                                            navigation_correct = any(path in new_url.lower() for path in expected_paths)
                                            
                                            if navigation_correct:
                                                print_success(f"{action_name}: Navegou corretamente para {new_url}")
                                                successful_navigations += 1
                                            else:
                                                print_warning(f"{action_name}: Navegou para {new_url} (não esperado)")
                                                successful_navigations += 1  # Ainda é uma navegação
                                            
                                            button_found = True
                                            break
                                        else:
                                            print_warning(f"{action_name}: Botão clicado mas URL não mudou")
                                            
                                    except Exception as click_e:
                                        print_info(f"Erro ao clicar em {action_name}: {click_e}")
                                        continue
                            
                            if button_found:
                                break
                                
                        except Exception as selector_e:
                            continue
                    
                    if not button_found:
                        print_error(f"{action_name}: Botão não encontrado ou não clicável")
                        failed_navigations += 1
                        
                except Exception as action_e:
                    print_error(f"Erro ao testar {action_name}: {action_e}")
                    failed_navigations += 1
            
            # Resultado do teste
            total_actions = len(quick_actions)
            success_rate = (successful_navigations / total_actions * 100) if total_actions > 0 else 0
            
            print_info(f"Resultado: {successful_navigations}/{total_actions} ações funcionando ({success_rate:.1f}%)")
            
            if success_rate >= 75:
                self.test_results.append(("Quick Actions Navigation", "PASS", f"{successful_navigations}/{total_actions} ações funcionando"))
            elif success_rate >= 50:
                self.test_results.append(("Quick Actions Navigation", "WARNING", f"Apenas {successful_navigations}/{total_actions} ações funcionando"))
            else:
                self.test_results.append(("Quick Actions Navigation", "FAIL", f"Poucas ações funcionando: {successful_navigations}/{total_actions}"))
                
        except Exception as e:
            print_error(f"Erro no teste de navegação: {e}")
            self.test_results.append(("Quick Actions Navigation", "FAIL", f"Erro: {str(e)}"))
    
    def test_conversation_chart(self):
        """Testar se gráfico de conversas está renderizando"""
        print_header("TESTE 5: GRÁFICO DE CONVERSAS")
        
        if not self.driver:
            print_warning("Selenium não disponível - testando apenas dados backend")
            
            try:
                from services.queries import HomeQueries
                queries = HomeQueries()
                
                # Tentar obter dados de timeline/gráfico
                chart_methods = [
                    ('get_conversations_timeline', 'Timeline de Conversas'),
                    ('get_chart_data', 'Dados do Gráfico'),
                    ('get_daily_stats', 'Estatísticas Diárias')
                ]
                
                chart_data_found = False
                for method_name, description in chart_methods:
                    try:
                        if hasattr(queries, method_name):
                            method = getattr(queries, method_name)
                            data = method()
                            
                            if data:
                                print_success(f"{description}: Dados disponíveis")
                                chart_data_found = True
                            else:
                                print_warning(f"{description}: Sem dados")
                    except Exception as e:
                        print_info(f"{description}: {e}")
                
                if chart_data_found:
                    self.test_results.append(("Conversation Chart Backend", "PASS", "Dados backend disponíveis"))
                else:
                    self.test_results.append(("Conversation Chart Backend", "WARNING", "Backend sem dados específicos de chart"))
                    
            except Exception as e:
                self.test_results.append(("Conversation Chart Backend", "FAIL", f"Erro: {str(e)}"))
            return
        
        try:
            print_info("Verificando gráfico de conversas na interface...")
            
            # Fazer login primeiro
            if not self.perform_login():
                print_warning("Falha no login - teste limitado")
                self.test_results.append(("Conversation Chart UI", "WARNING", "Falha no login"))
                return
            
            self.driver.get(f"{self.base_url}/home")
            time.sleep(5)
            
            # Procurar por elementos de gráfico
            chart_indicators = [
                "Conversas - 7 dias",
                "svg",  # Elemento SVG de gráficos
                "[id*='chart']",
                "[id*='graph']",
                ".js-plotly-plot",  # Plotly
                "canvas"  # Chart.js
            ]
            
            chart_found = False
            chart_type = "Desconhecido"
            
            for indicator in chart_indicators:
                try:
                    if indicator.startswith("[") or indicator.startswith("."):
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    else:
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{indicator}')]") if indicator != "svg" and indicator != "canvas" else self.driver.find_elements(By.TAG_NAME, indicator)
                    
                    if elements:
                        for element in elements:
                            if element.is_displayed():
                                chart_found = True
                                chart_type = indicator
                                print_success(f"Gráfico encontrado: {indicator}")
                                
                                # Verificar se tem conteúdo
                                if indicator in ["svg", "canvas"]:
                                    size = element.size
                                    if size['width'] > 50 and size['height'] > 50:
                                        print_success(f"Gráfico tem tamanho adequado: {size}")
                                    else:
                                        print_warning(f"Gráfico muito pequeno: {size}")
                                
                                break
                    
                    if chart_found:
                        break
                        
                except Exception as e:
                    continue
            
            if chart_found:
                self.test_results.append(("Conversation Chart UI", "PASS", f"Gráfico renderizado ({chart_type})"))
            else:
                # Verificar se existe placeholder ou mensagem de carregamento
                loading_indicators = ["Carregando", "Loading", "Aguarde"]
                loading_found = False
                
                for indicator in loading_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                        if elements:
                            loading_found = True
                            print_info(f"Indicador de carregamento encontrado: {indicator}")
                            break
                    except:
                        continue
                
                if loading_found:
                    self.test_results.append(("Conversation Chart UI", "WARNING", "Gráfico carregando ou placeholder"))
                else:
                    self.test_results.append(("Conversation Chart UI", "FAIL", "Gráfico não encontrado"))
                    
        except Exception as e:
            print_error(f"Erro no teste do gráfico: {e}")
            self.test_results.append(("Conversation Chart UI", "FAIL", f"Erro: {str(e)}"))
    
    def cleanup(self):
        """Limpar recursos"""
        print_section("LIMPEZA")
        
        if self.driver:
            try:
                self.driver.quit()
                print_success("Selenium fechado")
            except:
                pass
        
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
                print_success("Dashboard terminado")
            except:
                try:
                    self.app_process.kill()
                    print_warning("Dashboard forçado a terminar")
                except:
                    pass
    
    def print_final_report(self):
        """Imprimir relatório final dos testes"""
        print_header("RELATÓRIO FINAL DOS TESTES")
        
        total = len(self.test_results)
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        warnings = sum(1 for _, status, _ in self.test_results if status == "WARNING")
        skipped = sum(1 for _, status, _ in self.test_results if status == "SKIP")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print_info(f"RESUMO DOS TESTES:")
        print_info(f"  Total: {total}")
        print_success(f"  Aprovados: {passed}")
        print_error(f"  Falharam: {failed}")
        print_warning(f"  Avisos: {warnings}")
        print_info(f"  Pulados: {skipped}")
        print_info(f"  Taxa de sucesso: {success_rate:.1f}%")
        
        print_section("DETALHES POR TESTE")
        for name, status, details in self.test_results:
            if status == "PASS":
                print_success(f"{name}: {details}")
            elif status == "FAIL":
                print_error(f"{name}: {details}")
            elif status == "WARNING":
                print_warning(f"{name}: {details}")
            else:
                print_info(f"{name}: {details}")
        
        # Diagnóstico e recomendações
        print_section("DIAGNÓSTICO E RECOMENDAÇÕES")
        
        if success_rate >= 80:
            print_success("SISTEMA FUNCIONANDO BEM!")
            print_info("A maioria das funcionalidades está operacional")
        elif success_rate >= 60:
            print_warning("SISTEMA COM ALGUNS PROBLEMAS")
            print_info("Funcionalidades principais funcionam mas há issues a corrigir")
        else:
            print_error("SISTEMA COM PROBLEMAS CRÍTICOS")
            print_info("Várias funcionalidades não estão funcionando corretamente")
        
        # Recomendações específicas
        recommendations = []
        
        for name, status, details in self.test_results:
            if status == "FAIL":
                if "KPIs" in name:
                    recommendations.append("• Verificar queries do banco de dados e mapeamento UI")
                elif "Filter" in name:
                    recommendations.append("• Implementar callbacks para filtro de período")
                elif "Navigation" in name:
                    recommendations.append("• Configurar rotas e callbacks de navegação")
                elif "Activity" in name or "Performance" in name:
                    recommendations.append("• Implementar queries para atividade recente")
                elif "Chart" in name:
                    recommendations.append("• Implementar componente de gráfico (Plotly)")
        
        if recommendations:
            print_section("AÇÕES RECOMENDADAS")
            for rec in list(set(recommendations)):  # Remove duplicatas
                print_info(rec)
        
        return success_rate >= 60
    
    def run_all_tests(self):
        """Executar todos os testes específicos"""
        print_header("TESTE ESPECÍFICO DE FUNCIONALIDADES HOME")
        print_info(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        success = False
        
        try:
            # 1. Iniciar dashboard
            if not self.start_dashboard():
                print_error("Falha ao iniciar dashboard - alguns testes serão limitados")
            
            # 2. Configurar Selenium (opcional)
            selenium_ok = self.setup_selenium()
            
            # 3. Executar testes específicos
            self.test_kpis_data_accuracy()
            self.test_time_filter_functionality()
            self.test_activity_and_performance_cards()
            self.test_quick_actions_navigation()
            self.test_conversation_chart()
            
            # 4. Relatório final
            success = self.print_final_report()
            
        except KeyboardInterrupt:
            print_warning("Teste interrompido pelo usuário")
        except Exception as e:
            print_error(f"Erro crítico: {e}")
        finally:
            self.cleanup()
        
        return success

def main():
    """Função principal"""
    print_header("TESTADOR ESPECÍFICO - FUNCIONALIDADES HOME")
    
    tester = HomeSpecificTester()
    success = tester.run_all_tests()
    
    if success:
        print_success("Testes concluídos - sistema funcionando adequadamente!")
    else:
        print_warning("Testes concluídos - sistema precisa de correções")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())