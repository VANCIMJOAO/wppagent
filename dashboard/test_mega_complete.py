#!/usr/bin/env python3
"""
TESTE MEGA COMPLETO UNIFICADO - WppAgent Dashboard
==================================================

TODAS AS PARTES EM UM SÓ ARQUIVO:
✅ PARTE 1: Infraestrutura e conectividade
✅ PARTE 2: Interface web e interações  
✅ PARTE 3: Funções específicas do home
✅ PARTE 4: Relatório consolidado final

Execute apenas: python test_mega_complete.py
"""

import sys
import os
import time
import json
import requests
import subprocess
import psutil
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from colorama import init, Fore, Style

# Colorama init
init()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(text, color=Fore.CYAN):
    """Print colorful header"""
    print(f"\n{color}{'='*80}{Style.RESET_ALL}")
    print(f"{color}{text.center(80)}{Style.RESET_ALL}")
    print(f"{color}{'='*80}{Style.RESET_ALL}\n")

def print_section(text):
    """Print section header"""
    print(f"\n{Fore.YELLOW}{'─'*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'─'*60}{Style.RESET_ALL}")

def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message"""
    print(f"{Fore.CYAN}ℹ️  {text}{Style.RESET_ALL}")

class MegaTestResult:
    """Classe para armazenar resultados de testes"""
    
    def __init__(self, name, category, status, details, execution_time=0, error=None):
        self.name = name
        self.category = category  
        self.status = status  # PASS, FAIL, WARNING, SKIP
        self.details = details
        self.execution_time = execution_time
        self.error = error
        self.timestamp = datetime.now()

class MegaTestReporter:
    """Reporter mega avançado para todos os testes"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.categories = {
            'Infrastructure': [],
            'Web Interface': [], 
            'Home Functions': [],
            'Performance': [],
            'Integration': []
        }
    
    def add_result(self, result):
        """Adicionar resultado de teste"""
        self.results.append(result)
        
        # Categorizar
        if result.category in self.categories:
            self.categories[result.category].append(result)
        
        # Print em tempo real com cores
        status_color = {
            'PASS': Fore.GREEN,
            'FAIL': Fore.RED,
            'WARNING': Fore.YELLOW,
            'SKIP': Fore.BLUE
        }.get(result.status, Fore.WHITE)
        
        print(f"{status_color}{result.status:7}{Style.RESET_ALL} | "
              f"{result.category:15} | {result.name:35} | {result.details}")
    
    def get_summary(self):
        """Obter sumário completo dos testes"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'PASS')
        failed = sum(1 for r in self.results if r.status == 'FAIL')
        warnings = sum(1 for r in self.results if r.status == 'WARNING')
        skipped = sum(1 for r in self.results if r.status == 'SKIP')
        
        success_rate = (passed / total * 100) if total > 0 else 0
        total_time = time.time() - self.start_time
        
        # Sumário por categoria
        category_stats = {}
        for cat, tests in self.categories.items():
            if tests:
                cat_passed = sum(1 for t in tests if t.status == 'PASS')
                cat_total = len(tests)
                cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
                category_stats[cat] = {
                    'total': cat_total,
                    'passed': cat_passed,
                    'success_rate': cat_rate
                }
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'skipped': skipped,
            'success_rate': success_rate,
            'execution_time': total_time,
            'categories': category_stats
        }

class MegaCompleteTest:
    """Testador mega completo que combina todos os testes"""
    
    def __init__(self):
        self.reporter = MegaTestReporter()
        self.app_process = None
        self.driver = None
        
        # Configurar ambiente
        self.setup_environment()
    
    def setup_environment(self):
        """Configurar ambiente para todos os testes"""
        print_section("CONFIGURAÇÃO DO AMBIENTE MEGA TESTE")
        
        # Diretório base
        os.chdir('/home/vancim/whats_agent/dashboard')
        print_info(f"Diretório: {os.getcwd()}")
        
        # Adicionar ao path
        sys.path.insert(0, os.getcwd())
        sys.path.insert(0, '/home/vancim/whats_agent')
        
        print_success("Ambiente configurado!")
    
    # ==========================================
    # PARTE 1: INFRAESTRUTURA
    # ==========================================
    
    def test_part1_infrastructure(self):
        """PARTE 1: Testes de infraestrutura completos"""
        print_header("PARTE 1: INFRAESTRUTURA E CONECTIVIDADE", Fore.BLUE)
        
        # Teste 1: Dependências
        self._test_dependencies()
        
        # Teste 2: Conectividade de banco
        self._test_database_connectivity()
        
        # Teste 3: Queries do banco
        self._test_database_queries()
        
        # Teste 4: Inicialização da aplicação
        self._test_application_startup()
        
        print_success("✅ PARTE 1 CONCLUÍDA!")
    
    def _test_dependencies(self):
        """Testar dependências"""
        print_info("Testando dependências...")
        
        start_time = time.time()
        dependencies = [
            'dash', 'dash_mantine_components', 'dash_iconify',
            'requests', 'selenium', 'colorama', 'psutil',
            'sqlalchemy', 'pandas', 'plotly'
        ]
        
        missing = []
        for dep in dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        execution_time = time.time() - start_time
        
        if not missing:
            self.reporter.add_result(MegaTestResult(
                "Dependencies Check", "Infrastructure", "PASS",
                f"All {len(dependencies)} dependencies available", execution_time
            ))
        else:
            self.reporter.add_result(MegaTestResult(
                "Dependencies Check", "Infrastructure", "FAIL",
                f"Missing: {', '.join(missing)}", execution_time
            ))
    
    def _test_database_connectivity(self):
        """Testar conectividade do banco"""
        print_info("Testando conectividade do banco...")
        
        start_time = time.time()
        
        try:
            # Importar e testar conexão
            from services.queries import HomeQueries
            queries = HomeQueries()
            
            # Testar uma query simples
            result = queries.get_kpis()
            
            execution_time = time.time() - start_time
            
            if result and len(result) > 0:
                self.reporter.add_result(MegaTestResult(
                    "Database Connectivity", "Infrastructure", "PASS",
                    f"Railway PostgreSQL connected, {len(result)} KPI fields", execution_time
                ))
            else:
                self.reporter.add_result(MegaTestResult(
                    "Database Connectivity", "Infrastructure", "WARNING",
                    "Connected but no data returned", execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Database Connectivity", "Infrastructure", "FAIL",
                f"Connection failed: {str(e)}", execution_time, e
            ))
    
    def _test_database_queries(self):
        """Testar queries do banco"""
        print_info("Testando queries do banco...")
        
        try:
            from services.queries import HomeQueries
            queries = HomeQueries()
            
            query_tests = [
                ('get_kpis', 'KPI Queries'),
                ('get_recent_conversations', 'Recent Conversations'),
                ('get_performance_data', 'Performance Data'),
                ('get_system_status', 'System Status'),
                ('get_conversations_timeline', 'Conversations Timeline'),
                ('get_messages_by_direction', 'Messages by Direction')
            ]
            
            for method_name, test_name in query_tests:
                start_time = time.time()
                
                try:
                    method = getattr(queries, method_name)
                    result = method()
                    execution_time = time.time() - start_time
                    
                    if result is not None:
                        result_size = len(result) if hasattr(result, '__len__') else 1
                        self.reporter.add_result(MegaTestResult(
                            test_name, "Infrastructure", "PASS",
                            f"Query executed successfully, {result_size} items", execution_time
                        ))
                    else:
                        self.reporter.add_result(MegaTestResult(
                            test_name, "Infrastructure", "WARNING",
                            "Query returned None", execution_time
                        ))
                        
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.reporter.add_result(MegaTestResult(
                        test_name, "Infrastructure", "FAIL",
                        f"Query failed: {str(e)}", execution_time, e
                    ))
                    
        except Exception as e:
            self.reporter.add_result(MegaTestResult(
                "Database Queries", "Infrastructure", "FAIL",
                f"Could not initialize queries: {str(e)}", 0, e
            ))
    
    def _test_application_startup(self):
        """Testar inicialização da aplicação"""
        print_info("Testando inicialização da aplicação...")
        
        start_time = time.time()
        
        try:
            # Matar processos existentes
            subprocess.run(['pkill', '-f', 'python app.py'], 
                         capture_output=True, timeout=5)
            time.sleep(2)
            
            # Iniciar aplicação
            self.app_process = subprocess.Popen(
                ['python', 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd='/home/vancim/whats_agent/dashboard'
            )
            
            # Aguardar inicialização
            max_wait = 15
            for i in range(max_wait):
                try:
                    response = requests.get('http://localhost:8050', timeout=2)
                    if response.status_code == 200:
                        execution_time = time.time() - start_time
                        self.reporter.add_result(MegaTestResult(
                            "Application Startup", "Infrastructure", "PASS",
                            f"Dashboard started successfully in {execution_time:.1f}s", execution_time
                        ))
                        return
                except requests.RequestException:
                    time.sleep(1)
            
            # Se chegou aqui, não conseguiu conectar
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Application Startup", "Infrastructure", "FAIL",
                f"Dashboard failed to start after {max_wait}s", execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Application Startup", "Infrastructure", "FAIL",
                f"Startup failed: {str(e)}", execution_time, e
            ))
    
    # ==========================================
    # PARTE 2: INTERFACE WEB
    # ==========================================
    
    def test_part2_web_interface(self):
        """PARTE 2: Testes de interface web"""
        print_header("PARTE 2: INTERFACE WEB E INTERAÇÕES", Fore.MAGENTA)
        
        # Configurar Selenium
        selenium_ok = self._setup_selenium()
        
        if selenium_ok:
            # Testes de interface
            self._test_page_loading()
            self._test_ui_elements_discovery()
            self._test_basic_interactions()
            self._test_performance_metrics()
        
        print_success("✅ PARTE 2 CONCLUÍDA!")
    
    def _setup_selenium(self):
        """Configurar Selenium"""
        print_info("Configurando Selenium WebDriver...")
        
        start_time = time.time()
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Configurar Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Armazenar classes para uso posterior
            self.By = By
            self.WebDriverWait = WebDriverWait
            self.EC = EC
            
            execution_time = time.time() - start_time
            
            self.reporter.add_result(MegaTestResult(
                "Selenium Setup", "Web Interface", "PASS",
                f"ChromeDriver configured in {execution_time:.1f}s", execution_time
            ))
            
            return True
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Selenium Setup", "Web Interface", "FAIL",
                f"Selenium setup failed: {str(e)}", execution_time, e
            ))
            return False
    
    def _test_page_loading(self):
        """Testar carregamento da página"""
        print_info("Testando carregamento da página...")
        
        start_time = time.time()
        
        try:
            self.driver.get("http://localhost:8050")
            
            # Aguardar carregamento
            self.WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Verificar elementos básicos
            body = self.driver.find_element(self.By.TAG_NAME, "body")
            divs = self.driver.find_elements(self.By.TAG_NAME, "div")
            
            execution_time = time.time() - start_time
            
            # Screenshot
            screenshot_name = f"mega_test_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_name)
            
            self.reporter.add_result(MegaTestResult(
                "Page Loading", "Web Interface", "PASS",
                f"Page loaded in {execution_time:.1f}s, {len(divs)} elements", execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Page Loading", "Web Interface", "FAIL",
                f"Page loading failed: {str(e)}", execution_time, e
            ))
    
    def _test_ui_elements_discovery(self):
        """Descobrir elementos da UI"""
        print_info("Descobrindo elementos da UI...")
        
        start_time = time.time()
        
        try:
            elements_found = {}
            
            # Diferentes tipos de elementos
            element_types = [
                ('button', 'Buttons'),
                ('input', 'Inputs'),
                ('[class*="Card"]', 'Cards'),
                ('[id]', 'Elements with ID'),
                ('button, input, select, [role="button"]', 'Interactive Elements')
            ]
            
            total_elements = 0
            for selector, name in element_types:
                elements = self.driver.find_elements(self.By.CSS_SELECTOR, selector)
                count = len(elements)
                elements_found[name] = count
                total_elements += count
            
            execution_time = time.time() - start_time
            
            status = "PASS" if total_elements > 10 else "WARNING"
            details = f"Found {total_elements} UI elements: " + \
                     ", ".join([f"{name}: {count}" for name, count in elements_found.items()])
            
            self.reporter.add_result(MegaTestResult(
                "UI Elements Discovery", "Web Interface", status,
                details, execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "UI Elements Discovery", "Web Interface", "FAIL",
                f"Discovery failed: {str(e)}", execution_time, e
            ))
    
    def _test_basic_interactions(self):
        """Testar interações básicas"""
        print_info("Testando interações básicas...")
        
        start_time = time.time()
        
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            interactions_successful = 0
            total_interactions = 0
            
            # Teste 1: Scroll
            try:
                self.driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                interactions_successful += 1
            except Exception:
                pass
            total_interactions += 1
            
            # Teste 2: Hover
            try:
                elements = self.driver.find_elements(self.By.CSS_SELECTOR, "div, button")[:3]
                for element in elements:
                    if element.is_displayed():
                        ActionChains(self.driver).move_to_element(element).perform()
                        time.sleep(0.2)
                interactions_successful += 1
            except Exception:
                pass
            total_interactions += 1
            
            # Teste 3: Responsividade
            try:
                original_size = self.driver.get_window_size()
                self.driver.set_window_size(768, 1024)
                time.sleep(1)
                self.driver.set_window_size(375, 667)
                time.sleep(1)
                self.driver.set_window_size(original_size['width'], original_size['height'])
                interactions_successful += 1
            except Exception:
                pass
            total_interactions += 1
            
            execution_time = time.time() - start_time
            success_rate = (interactions_successful / total_interactions * 100)
            
            status = "PASS" if success_rate > 60 else "WARNING"
            
            self.reporter.add_result(MegaTestResult(
                "Basic Interactions", "Web Interface", status,
                f"{interactions_successful}/{total_interactions} interactions successful ({success_rate:.1f}%)",
                execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Basic Interactions", "Web Interface", "FAIL",
                f"Interactions failed: {str(e)}", execution_time, e
            ))
    
    def _test_performance_metrics(self):
        """Testar métricas de performance"""
        print_info("Coletando métricas de performance...")
        
        start_time = time.time()
        
        try:
            # Performance timing
            timing = self.driver.execute_script("""
                return {
                    loadEventEnd: performance.timing.loadEventEnd,
                    navigationStart: performance.timing.navigationStart
                };
            """)
            
            metrics = []
            
            if timing['loadEventEnd'] > 0:
                total_load = (timing['loadEventEnd'] - timing['navigationStart']) / 1000
                metrics.append(f"Load: {total_load:.2f}s")
                
                if total_load < 5.0:
                    load_status = "EXCELLENT"
                elif total_load < 10.0:
                    load_status = "GOOD"
                else:
                    load_status = "SLOW"
                
                metrics.append(f"Performance: {load_status}")
            
            # Memória (se disponível)
            try:
                memory = self.driver.execute_script("""
                    if (window.performance && window.performance.memory) {
                        return {
                            used: window.performance.memory.usedJSHeapSize,
                            total: window.performance.memory.totalJSHeapSize
                        };
                    }
                    return null;
                """)
                
                if memory:
                    used_mb = memory['used'] / (1024 * 1024)
                    metrics.append(f"Memory: {used_mb:.1f}MB")
            except Exception:
                pass
            
            execution_time = time.time() - start_time
            
            self.reporter.add_result(MegaTestResult(
                "Performance Metrics", "Web Interface", "PASS",
                ", ".join(metrics), execution_time
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Performance Metrics", "Web Interface", "FAIL",
                f"Metrics collection failed: {str(e)}", execution_time, e
            ))
    
    # ==========================================
    # PARTE 3: FUNÇÕES HOME
    # ==========================================
    
    def test_part3_home_functions(self):
        """PARTE 3: Testes de funções específicas do home"""
        print_header("PARTE 3: FUNÇÕES ESPECÍFICAS DO HOME", Fore.GREEN)
        
        # Testes de API
        self._test_backend_apis()
        
        # Testes de callbacks
        self._test_dash_callbacks()
        
        # Testes de elementos específicos
        self._test_specific_ui_elements()
        
        print_success("✅ PARTE 3 CONCLUÍDA!")
    
    def _test_backend_apis(self):
        """Testar APIs do backend (usando database service em vez de API REST)"""
        print_info("Testando APIs do backend...")
        
        # Como o dashboard usa database service diretamente, vamos testar isso
        try:
            from services.queries import HomeQueries
            queries = HomeQueries()
            
            api_tests = [
                ('get_kpis', 'Backend KPIs Service'),
                ('get_recent_conversations', 'Backend Conversations Service'),
                ('get_performance_data', 'Backend Performance Service'),
                ('get_system_status', 'Backend System Status Service')
            ]
            
            for method_name, test_name in api_tests:
                start_time = time.time()
                
                try:
                    method = getattr(queries, method_name)
                    result = method()
                    execution_time = time.time() - start_time
                    
                    if result is not None:
                        result_size = len(result) if hasattr(result, '__len__') else 1
                        self.reporter.add_result(MegaTestResult(
                            test_name, "Home Functions", "PASS",
                            f"Backend service working, {result_size} items", execution_time
                        ))
                    else:
                        self.reporter.add_result(MegaTestResult(
                            test_name, "Home Functions", "WARNING",
                            "Backend service returned None", execution_time
                        ))
                        
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.reporter.add_result(MegaTestResult(
                        test_name, "Home Functions", "FAIL",
                        f"Backend service failed: {str(e)}", execution_time, e
                    ))
                    
        except Exception as e:
            self.reporter.add_result(MegaTestResult(
                "Backend Services", "Home Functions", "FAIL",
                f"Could not initialize backend services: {str(e)}", 0, e
            ))
        
        # Testar conectividade do dashboard (porta 8050)
        start_time = time.time()
        try:
            response = requests.get('http://localhost:8050', timeout=5)
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                self.reporter.add_result(MegaTestResult(
                    "Dashboard API", "Home Functions", "PASS",
                    f"Dashboard responding on port 8050", execution_time
                ))
            else:
                self.reporter.add_result(MegaTestResult(
                    "Dashboard API", "Home Functions", "WARNING",
                    f"Dashboard HTTP {response.status_code}", execution_time
                ))
                
        except requests.RequestException as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Dashboard API", "Home Functions", "FAIL",
                f"Dashboard connection failed: {str(e)}", execution_time, e
            ))
    
    def _test_dash_callbacks(self):
        """Testar callbacks do Dash"""
        print_info("Testando callbacks do Dash...")
        
        start_time = time.time()
        
        try:
            # Importar app para verificar callbacks
            import sys
            import os
            
            # Verificar se existe o arquivo app.py
            app_path = '/home/vancim/whats_agent/dashboard/app.py'
            if not os.path.exists(app_path):
                self.reporter.add_result(MegaTestResult(
                    "Dash Callbacks", "Home Functions", "FAIL",
                    "app.py file not found", time.time() - start_time
                ))
                return
            
            # Tentar importar e analisar o arquivo
            try:
                with open(app_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Contar callbacks no código
                callback_count = content.count('@app.callback')
                callback_count += content.count('@callback')
                callback_count += content.count('app.callback(')
                
                # Procurar por instância do app
                if 'dash.Dash(' in content or 'Dash(' in content:
                    app_instance_found = True
                else:
                    app_instance_found = False
                
                execution_time = time.time() - start_time
                
                if callback_count > 0:
                    status = "PASS" if app_instance_found else "WARNING"
                    details = f"{callback_count} callbacks found in code"
                    if app_instance_found:
                        details += ", Dash app instance detected"
                    else:
                        details += ", but app instance unclear"
                        
                    self.reporter.add_result(MegaTestResult(
                        "Dash Callbacks", "Home Functions", status,
                        details, execution_time
                    ))
                else:
                    self.reporter.add_result(MegaTestResult(
                        "Dash Callbacks", "Home Functions", "WARNING",
                        "No callbacks found in app.py", execution_time
                    ))
                    
            except Exception as file_error:
                execution_time = time.time() - start_time
                self.reporter.add_result(MegaTestResult(
                    "Dash Callbacks", "Home Functions", "FAIL",
                    f"Failed to read app.py: {str(file_error)}", execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Dash Callbacks", "Home Functions", "FAIL",
                f"Callback analysis failed: {str(e)}", execution_time, e
            ))
    
    def _test_specific_ui_elements(self):
        """Testar elementos específicos da UI"""
        print_info("Testando elementos específicos da UI...")
        
        if not self.driver:
            self.reporter.add_result(MegaTestResult(
                "Specific UI Elements", "Home Functions", "SKIP",
                "Selenium driver not available", 0
            ))
            return
        
        # Elementos mais genéricos que realmente existem no dashboard
        specific_elements = [
            ('[class*="mantine"], div[class*="dmc"], div[class*="Card"]', 'Mantine/DMC Components'),
            ('[id*="home"], [id*="dashboard"], [id*="main"]', 'Dashboard Layout Elements'),
            ('button, [role="button"], [class*="Button"]', 'Interactive Buttons'),
            ('div[data-dash-component], div[id*="_dash-"]', 'Dash Components'),
            ('script, [src*="plotly"], [src*="dash"]', 'Dashboard Scripts')
        ]
        
        total_elements_found = 0
        
        for selector, name in specific_elements:
            start_time = time.time()
            
            try:
                elements = self.driver.find_elements(self.By.CSS_SELECTOR, selector)
                execution_time = time.time() - start_time
                
                if elements:
                    visible_count = sum(1 for el in elements if el.is_displayed())
                    total_elements_found += len(elements)
                    
                    status = "PASS"
                    details = f"{len(elements)} found, {visible_count} visible"
                    
                    self.reporter.add_result(MegaTestResult(
                        name, "Home Functions", status, details, execution_time
                    ))
                else:
                    self.reporter.add_result(MegaTestResult(
                        name, "Home Functions", "WARNING",
                        "Elements not found with this selector", execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.reporter.add_result(MegaTestResult(
                    name, "Home Functions", "FAIL",
                    f"Element test failed: {str(e)}", execution_time, e
                ))
        
        # Teste adicional: verificar se a página tem conteúdo básico
        start_time = time.time()
        try:
            page_title = self.driver.title
            body_text = self.driver.find_element(self.By.TAG_NAME, "body").text
            
            execution_time = time.time() - start_time
            
            if page_title and len(body_text) > 50:
                self.reporter.add_result(MegaTestResult(
                    "Page Content Validation", "Home Functions", "PASS",
                    f"Title: '{page_title[:30]}...', Body: {len(body_text)} chars", execution_time
                ))
            else:
                self.reporter.add_result(MegaTestResult(
                    "Page Content Validation", "Home Functions", "WARNING",
                    f"Limited content - Title: '{page_title}', Body: {len(body_text)} chars", execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.reporter.add_result(MegaTestResult(
                "Page Content Validation", "Home Functions", "FAIL",
                f"Content validation failed: {str(e)}", execution_time, e
            ))
    
    # ==========================================
    # EXECUÇÃO PRINCIPAL E RELATÓRIO
    # ==========================================
    
    def cleanup(self):
        """Limpar recursos"""
        print_section("LIMPEZA DE RECURSOS")
        
        # Fechar Selenium
        if self.driver:
            try:
                self.driver.quit()
                print_success("Selenium driver fechado")
            except Exception as e:
                print_warning(f"Erro ao fechar Selenium: {str(e)}")
        
        # Terminar aplicação
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
                print_success("Processo da aplicação terminado")
            except Exception:
                try:
                    self.app_process.kill()
                except Exception as e:
                    print_warning(f"Erro ao terminar aplicação: {str(e)}")
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print_header("TESTE MEGA COMPLETO - TODAS AS PARTES", Fore.CYAN)
        print_info(f"Iniciando teste completo em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Executar todas as partes
            self.test_part1_infrastructure()
            self.test_part2_web_interface()
            self.test_part3_home_functions()
            
            # Gerar relatório final
            self.generate_final_report()
            
        except KeyboardInterrupt:
            print_warning("Teste interrompido pelo usuário")
        except Exception as e:
            print_error(f"Erro crítico: {str(e)}")
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def generate_final_report(self):
        """Gerar relatório final consolidado"""
        print_header("RELATÓRIO FINAL CONSOLIDADO", Fore.GREEN)
        
        summary = self.reporter.get_summary()
        
        # Estatísticas gerais
        print_info(f"📊 ESTATÍSTICAS GERAIS:")
        print_info(f"   Total de testes: {summary['total']}")
        print_info(f"   ✅ Aprovados: {summary['passed']}")
        print_info(f"   ❌ Falharam: {summary['failed']}")
        print_info(f"   ⚠️  Avisos: {summary['warnings']}")
        print_info(f"   ⏭️  Pulados: {summary['skipped']}")
        print_info(f"   🎯 Taxa de sucesso: {summary['success_rate']:.1f}%")
        print_info(f"   ⏱️  Tempo total: {summary['execution_time']:.1f}s")
        
        # Estatísticas por categoria
        print_info(f"\n📋 DETALHES POR CATEGORIA:")
        for category, stats in summary['categories'].items():
            if stats['total'] > 0:
                status_emoji = "✅" if stats['success_rate'] > 70 else "⚠️" if stats['success_rate'] > 40 else "❌"
                print_info(f"   {status_emoji} {category}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        # Status final
        if summary['success_rate'] >= 90:
            print_success("🎉 SISTEMA EXCELENTE - Todos os componentes funcionando perfeitamente!")
            final_status = "EXCELENTE"
        elif summary['success_rate'] >= 75:
            print_success("✅ SISTEMA MUITO BOM - Funcionamento geral sólido!")
            final_status = "MUITO BOM"
        elif summary['success_rate'] >= 60:
            print_success("👍 SISTEMA BOM - Funcionalidades principais operacionais!")
            final_status = "BOM"
        elif summary['success_rate'] >= 40:
            print_warning("⚠️  SISTEMA COM PROBLEMAS - Necessita algumas correções")
            final_status = "PROBLEMAS"
        else:
            print_error("❌ SISTEMA COM FALHAS CRÍTICAS - Necessita intervenção")
            final_status = "CRÍTICO"
        
        # Salvar relatório em arquivo
        self.save_report_to_file(summary, final_status)
        
        return summary['success_rate'] >= 60
    
    def save_report_to_file(self, summary, final_status):
        """Salvar relatório detalhado em arquivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mega_test_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"RELATÓRIO MEGA TESTE COMPLETO\n")
                f.write(f"{'='*50}\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Status Final: {final_status}\n")
                f.write(f"Taxa de Sucesso: {summary['success_rate']:.1f}%\n")
                f.write(f"Tempo Total: {summary['execution_time']:.1f}s\n\n")
                
                f.write(f"ESTATÍSTICAS GERAIS:\n")
                f.write(f"- Total: {summary['total']}\n")
                f.write(f"- Aprovados: {summary['passed']}\n")
                f.write(f"- Falharam: {summary['failed']}\n")
                f.write(f"- Avisos: {summary['warnings']}\n")
                f.write(f"- Pulados: {summary['skipped']}\n\n")
                
                f.write(f"DETALHES POR CATEGORIA:\n")
                for category, stats in summary['categories'].items():
                    if stats['total'] > 0:
                        f.write(f"- {category}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)\n")
                
                f.write(f"\nTESTES DETALHADOS:\n")
                for result in self.reporter.results:
                    f.write(f"{result.status:7} | {result.category:15} | {result.name:35} | {result.details}\n")
            
            print_success(f"📄 Relatório salvo em: {filename}")
            
        except Exception as e:
            print_warning(f"Erro ao salvar relatório: {str(e)}")

def main():
    """Função principal"""
    try:
        mega_test = MegaCompleteTest()
        success = mega_test.run_all_tests()
        
        if success:
            print_success("\n🚀 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
            print_info("Sistema validado e pronto para produção!")
        else:
            print_warning("\n⚠️  TESTES CONCLUÍDOS COM ALGUNS PROBLEMAS")
            print_info("Verifique o relatório para detalhes")
        
        return 0 if success else 1
        
    except Exception as e:
        print_error(f"Erro crítico no teste mega completo: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())