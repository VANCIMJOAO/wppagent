#!/usr/bin/env python3
"""
Teste Simples de Debug - Verificar se os elementos estão na página
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_login_and_elements():
    print("🔍 Teste de Debug - Verificar Login e Elementos")
    
    # Configurar Chrome
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    try:
        # Ir para login
        print("📱 Navegando para login...")
        driver.get("http://localhost:8050/login")
        time.sleep(3)
        
        # Fazer login simples
        print("🔑 Fazendo login...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        if len(inputs) >= 2 and buttons:
            inputs[0].send_keys("admin@exemplo.com")
            inputs[1].send_keys("admin123")
            buttons[0].click()
            time.sleep(5)
            print("✅ Login realizado")
        
        # Ir para home
        print("🏠 Navegando para /home...")
        driver.get("http://localhost:8050/home")
        time.sleep(8)  # Aguardar mais tempo para callbacks
        
        # Debugar página
        print("🔍 Verificando elementos na página...")
        
        # Verificar se há algum elemento com texto relacionado aos KPIs
        page_source = driver.page_source
        print(f"📄 Tamanho da página: {len(page_source)} chars")
        
        # Procurar por números grandes (possíveis KPIs)
        import re
        numbers = re.findall(r'\b(?:[1-9]\d{2,}|[4-9]\d)\b', page_source)
        print(f"🔢 Números encontrados na página: {numbers[:10]}")  # Primeiros 10
        
        # Verificar elementos por tag
        divs_with_text = []
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        for div in all_divs[:20]:  # Verificar primeiro 20 divs
            try:
                text = div.text.strip()
                if text and any(char.isdigit() for char in text):
                    divs_with_text.append(text[:50])  # Primeiros 50 chars
            except:
                pass
        
        print(f"📝 Divs com texto numérico: {divs_with_text}")
        
        # Procurar elementos que podem conter KPIs
        kpi_terms = ["conversa", "usuário", "agendamento", "mensagem", "40", "12", "2074"]
        found_elements = []
        
        for term in kpi_terms:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{term}')]")
                if elements:
                    found_elements.append(f"{term}: {len(elements)} elementos")
            except:
                pass
        
        print(f"🎯 Elementos com termos KPI: {found_elements}")
        
        # Salvar screenshot para debug
        try:
            driver.save_screenshot("/tmp/dashboard_debug.png")
            print("📸 Screenshot salva em /tmp/dashboard_debug.png")
        except:
            pass
        
        # Verificar se callbacks foram executados
        try:
            # Procurar por qualquer elemento que possa indicar dados carregados
            all_text = driver.find_element(By.TAG_NAME, "body").text
            print(f"📑 Primeiros 500 chars da página:\n{all_text[:500]}")
        except Exception as e:
            print(f"❌ Erro ao capturar texto: {e}")
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
    
    finally:
        driver.quit()
        print("🚪 Driver fechado")

if __name__ == "__main__":
    test_login_and_elements()
