#!/usr/bin/env python3
"""
🚀 INICIALIZADOR SIMPLES DA API
==============================

Inicia a aplicação WhatsApp Agent API com configurações básicas.
"""

import uvicorn
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Iniciando WhatsApp Agent API...")
    print("📍 Host: 0.0.0.0")
    print("🔌 Porta: 8000")
    print("🔧 Modo: Development")
    
    try:
        uvicorn.run(
            "app.main:app",  # Formato correto: módulo.py:variável
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)