#!/usr/bin/env python3
"""
Teste simples de importação da configuração
"""

try:
    from app.config import settings
    print("✅ Import de 'app.config.settings' funcionou!")
    print(f"Settings type: {type(settings)}")
    print(f"Settings: {settings}")
except ImportError as e:
    print(f"❌ Erro ao importar 'app.config.settings': {e}")

try:
    from app.config import get_settings
    print("✅ Import de 'app.config.get_settings' funcionou!")
    settings2 = get_settings()
    print(f"get_settings() type: {type(settings2)}")
    print(f"get_settings(): {settings2}")
except ImportError as e:
    print(f"❌ Erro ao importar 'app.config.get_settings': {e}")

try:
    import app.config
    print("✅ Import de 'app.config' módulo funcionou!")
    print(f"Módulo app.config: {dir(app.config)}")
except ImportError as e:
    print(f"❌ Erro ao importar módulo 'app.config': {e}")
