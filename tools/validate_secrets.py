#!/usr/bin/env python3
"""
Validação do Sistema de Secrets Management
"""
import asyncio
import sys
import os

# Adicionar diretório do projeto ao Python path
sys.path.append('/home/vancim/whats_agent')

async def validate_secrets():
    """Validar sistema de secrets"""
    try:
        print("🔐 Validando Sistema de Secrets...")
        
        # Importar módulos
        from app.services.secrets_manager import secrets_manager
        from app.config.secure_config import config_manager
        
        # Testar inicialização
        print("📋 Testando inicialização...")
        success = await config_manager.load_configuration()
        
        if success:
            print("✅ Configuração carregada com sucesso")
            
            # Status dos provedores
            status = secrets_manager.get_provider_status()
            print(f"📊 Provedores ativos: {list(status['providers'].keys())}")
            
            # Health check
            health = await config_manager.health_check()
            print(f"🏥 Status geral: {health['status']}")
            
            if health['issues']:
                print("⚠️ Problemas encontrados:")
                for issue in health['issues']:
                    print(f"   - {issue}")
        
        else:
            print("❌ Falha na inicialização")
            return False
        
        print("✅ Validação concluída com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            await secrets_manager.close()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(validate_secrets())
    sys.exit(0 if result else 1)
