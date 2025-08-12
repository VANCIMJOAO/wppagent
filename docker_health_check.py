#!/usr/bin/env python3
"""
Health check script para containers Docker
Verifica se a aplicação está respondendo corretamente
"""

import requests
import sys
import os
from urllib.parse import urljoin
import urllib3
import socket

# Suprimir warnings de SSL não verificado em desenvolvimento
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_port():
    """Verifica se a porta está aberta"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_health():
    """
    Verifica a saúde da aplicação fazendo uma requisição HTTP
    """
    # Primeiro, verificar se a porta está aberta
    if not check_port():
        print("❌ Porta 8000 não está disponível")
        return 1
    
    # URL para tentar (apenas HTTP, seguir redirects)
    url = 'http://localhost:8000/health'
    
    try:
        # Configurar session para seguir redirects e ignorar SSL em dev
        session = requests.Session()
        session.verify = False  # Ignorar verificação SSL em desenvolvimento
        
        response = session.get(url, timeout=10, allow_redirects=True)
        
        # Verificar se a resposta é 200 OK ou redirecionamento seguido com sucesso
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status') == 'healthy':
                    print(f"✅ Aplicação saudável via {response.url}")
                    return 0
                else:
                    print(f"⚠️ Status da aplicação: {data.get('status', 'unknown')}")
                    return 1
            except ValueError:
                # Se não for JSON, mas status 200, consideramos OK
                print(f"✅ Aplicação respondendo (não-JSON) via {response.url}")
                return 0
        elif response.status_code in [301, 302, 307, 308]:
            # Se é redirecionamento mas chegamos aqui, algo pode estar errado
            print(f"⚠️ Redirecionamento detectado para {response.url}, mas falhou")
            return 1
        else:
            print(f"⚠️ Status HTTP {response.status_code} em {response.url}")
            return 1
            
    except requests.exceptions.ConnectionError as e:
        print(f"⚠️ Erro de conexão: {e}")
        return 1
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout na conexão")
        return 1
    except requests.exceptions.SSLError as e:
        print(f"⚠️ Erro SSL: {e}")
        return 1
    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(check_health())
