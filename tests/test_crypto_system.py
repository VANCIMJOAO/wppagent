#!/usr/bin/env python3
"""
🧪 Teste Completo do Sistema de Criptografia e Certificados
==========================================================
"""

import sys
import os
sys.path.append('/home/vancim/whats_agent')

def test_encryption_service():
    """Testa serviço de criptografia"""
    print("🔐 Testando serviço de criptografia...")
    
    try:
        from app.security.encryption_service import get_encryption_service
        
        service = get_encryption_service()
        
        # Teste básico
        test_data = "dados_sensíveis_teste_123"
        print(f"📝 Dados originais: {test_data}")
        
        # Criptografar
        encrypted = service.encrypt(test_data, "teste")
        print(f"🔒 Criptografado: {encrypted[:30]}...")
        
        # Descriptografar
        decrypted = service.decrypt_to_string(encrypted, "teste")
        print(f"🔓 Descriptografado: {decrypted}")
        
        # Verificar
        success = decrypted == test_data
        print(f"✅ Resultado: {'PASSOU' if success else 'FALHOU'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_data_encryption():
    """Testa criptografia de dados específicos"""
    print("\n🔐 Testando criptografia de dados sensíveis...")
    
    try:
        from app.security.data_encryption import get_data_encryption
        
        data_encryption = get_data_encryption()
        
        # Teste de senha
        password_result = data_encryption.encrypt_password("MinhaSenh@123", "user_test")
        print(f"🔑 Senha criptografada: {password_result.is_encrypted}")
        
        # Teste de API key
        api_result = data_encryption.encrypt_api_key("sk-abc123def456789012345", "openai")
        print(f"🔑 API Key criptografada: {api_result.is_encrypted}")
        
        # Teste de variáveis de ambiente
        env_vars = {
            "DATABASE_PASSWORD": "super_secret_db_pass",
            "API_KEY": "api_key_67890",
            "NORMAL_VAR": "not_sensitive"
        }
        
        encrypted_env = data_encryption.encrypt_environment_variables(env_vars)
        decrypted_env = data_encryption.decrypt_environment_variables(encrypted_env)
        
        env_success = decrypted_env == env_vars
        print(f"🌍 Variáveis de ambiente: {'PASSOU' if env_success else 'FALHOU'}")
        
        return all([password_result.is_encrypted, api_result.is_encrypted, env_success])
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_ssl_manager():
    """Testa gerenciador SSL"""
    print("\n🔐 Testando gerenciador SSL...")
    
    try:
        from app.security.ssl_manager import get_ssl_manager
        
        ssl_manager = get_ssl_manager()
        
        # Gerar certificado auto-assinado
        cert_path, key_path = ssl_manager.generate_self_signed_certificate()
        print(f"📜 Certificado gerado: {cert_path}")
        print(f"🔑 Chave privada: {key_path}")
        
        # Validar certificado
        validation = ssl_manager.validate_certificate()
        print(f"✅ Certificado válido: {validation.get('valid', False)}")
        
        return validation.get('valid', False)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🔒 SISTEMA DE CRIPTOGRAFIA E CERTIFICADOS - TESTES")
    print("=" * 60)
    
    tests = [
        ("Serviço de Criptografia", test_encryption_service),
        ("Criptografia de Dados", test_data_encryption),
        ("Gerenciador SSL", test_ssl_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n📊 RESULTADOS FINAIS:")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 TOTAL: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 TODOS OS TESTES PASSARAM! Sistema seguro e funcional.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique a configuração.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
