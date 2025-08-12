#!/usr/bin/env python3
"""
Sistema de Monitoramento de Segurança
Detecta uso de credenciais antigas comprometidas
"""

import os
import re
import logging
from datetime import datetime

# Padrões genéricos para monitorar (apenas credenciais antigas comprometidas)
COMPROMISED_PATTERNS = [
    r'admin123',
    r'password123', 
    r'K12network',
    r'EAAI4WnfpZAe0BPEo8vwjU7RCZBuaFeuNqzKkJaCtTY4p',  # Token Meta antigo específico
    r'sk-1c561[A-Za-z0-9]{40,}',  # Token OpenAI de teste antigo específico
    r'27fbf4a[A-Za-z0-9]{20,}',   # Token Ngrok de teste antigo específico
    r'2mLND[A-Za-z0-9]{20,}'      # Outros tokens antigos específicos
]

def scan_for_compromised_credentials(directory):
    """Escaneia diretório por credenciais comprometidas"""
    alerts = []
    
    for root, dirs, files in os.walk(directory):
        # Ignorar diretórios seguros
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'vault', 'backups/security']):
            continue
            
        for file in files:
            # Ignorar arquivos de sistema de segurança
            if any(security_file in file for security_file in ['security_monitor', 'security_cleaner', 'security_remediation', 'SECURITY_ALERT']):
                continue
                
            if file.endswith(('.py', '.sh', '.md', '.env', '.yml', '.yaml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in COMPROMISED_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            alerts.append({
                                'file': file_path,
                                'pattern': pattern[:20] + "...",  # Truncar padrão
                                'timestamp': datetime.now().isoformat()
                            })
                except Exception:
                    continue
    
    return alerts

if __name__ == '__main__':
    alerts = scan_for_compromised_credentials('/home/vancim/whats_agent')
    
    if alerts:
        print(f"🚨 CREDENCIAIS COMPROMETIDAS DETECTADAS: {len(alerts)} ocorrências")
        for alert in alerts:
            print(f"  ❌ {alert['file']} - padrão: {alert['pattern']}")
    else:
        print("✅ Nenhuma credencial comprometida detectada")
