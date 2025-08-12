#!/usr/bin/env python3
"""
Health check script for Docker container
Verifica se a aplicação está respondendo corretamente
"""
import sys
import requests
import os


def health_check():
    """Verificar saúde da aplicação"""
    try:
        # Verificar se a aplicação está respondendo
        response = requests.get(
            "http://localhost:8000/health", 
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Health check passed")
                return True
        
        print(f"❌ Health check failed - Status: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Health check failed - Error: {e}")
        return False


if __name__ == "__main__":
    if health_check():
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
