#!/usr/bin/env python3
"""
Teste específico para verificar se os erros 'undefined' foram corrigidos
=======================================================================
"""

import subprocess
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os

def test_undefined_errors():
    """Testa se ainda há erros 'undefined' no console do navegador"""
    
    print("=" * 70)
    print("           TESTE DE CORREÇÃO DOS ERROS 'UNDEFINED'           ")
    print("=" * 70)
    
    # Iniciar dashboard
    dashboard_process = None
    driver = None
    
    try:
        print("\n--- INICIANDO DASHBOARD ---")
        dashboard_process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd="/home/vancim/whats_agent/dashboard",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Aguardar inicialização
        time.sleep(8)
        
        # Testar se está rodando
        try:
            response = requests.get("http://127.0.0.1:8050", timeout=5)
            print(f"✅ Dashboard respondendo: {response.status_code}")
        except:
            print("❌ Dashboard não está respondendo")
            return False
        
        # Configurar Selenium
        print("\n--- CONFIGURANDO SELENIUM ---")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--log-level=0")  # Capturar todos os logs
        
        # Habilitar captura de logs do console
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Selenium configurado")
        
        # Acessar página de login
        print("\n--- TESTANDO PÁGINA DE LOGIN ---")
        driver.get("http://127.0.0.1:8050/login")
        time.sleep(3)
        
        # Capturar logs do console
        logs = driver.get_log('browser')
        console_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        print(f"📊 Total de logs capturados: {len(logs)}")
        print(f"🔴 Erros graves encontrados: {len(console_errors)}")
        
        # Verificar erros específicos de 'undefined'
        undefined_errors = []
        join_errors = []
        props_errors = []
        
        for log in logs:
            message = log['message'].lower()
            if 'undefined' in message and 'join' in message:
                join_errors.append(log)
            if 'undefined' in message and 'props' in message:
                props_errors.append(log)
            if 'undefined' in message:
                undefined_errors.append(log)
        
        print(f"\n--- ANÁLISE DOS ERROS ---")
        print(f"❌ Erros 'undefined' gerais: {len(undefined_errors)}")
        print(f"❌ Erros 'undefined join': {len(join_errors)}")
        print(f"❌ Erros 'undefined props': {len(props_errors)}")
        
        # Fazer login
        print("\n--- FAZENDO LOGIN ---")
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_input = driver.find_element(By.ID, "password")
            login_button = driver.find_element(By.ID, "login-button")
            
            email_input.send_keys("admin@exemplo.com")
            password_input.send_keys("admin123")
            login_button.click()
            
            print("✅ Login realizado")
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Erro no login: {e}")
        
        # Capturar logs após login
        new_logs = driver.get_log('browser')
        all_logs = logs + new_logs
        
        # Reanalizar todos os logs
        all_undefined_errors = []
        all_join_errors = []
        all_props_errors = []
        
        for log in all_logs:
            message = log['message'].lower()
            if 'undefined' in message and 'join' in message:
                all_join_errors.append(log)
            if 'undefined' in message and 'props' in message:
                all_props_errors.append(log)
            if 'undefined' in message:
                all_undefined_errors.append(log)
        
        print(f"\n--- RESULTADO FINAL ---")
        print(f"📊 Total de logs após login: {len(all_logs)}")
        print(f"❌ Erros 'undefined' totais: {len(all_undefined_errors)}")
        print(f"❌ Erros 'undefined join' totais: {len(all_join_errors)}")
        print(f"❌ Erros 'undefined props' totais: {len(all_props_errors)}")
        
        # Mostrar primeiros 3 erros se existirem
        if all_undefined_errors:
            print(f"\n--- PRIMEIROS ERROS UNDEFINED ---")
            for i, error in enumerate(all_undefined_errors[:3]):
                print(f"{i+1}. {error['message']}")
        
        # Resultado
        if len(all_undefined_errors) == 0:
            print("\n🎉 SUCESSO: Nenhum erro 'undefined' encontrado!")
            return True
        else:
            print(f"\n⚠️ PROBLEMA: Ainda há {len(all_undefined_errors)} erros 'undefined'")
            return False
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
        if dashboard_process:
            dashboard_process.terminate()

if __name__ == "__main__":
    success = test_undefined_errors()
    sys.exit(0 if success else 1)
