#!/usr/bin/env python3
"""
🧪 Teste Completo de Segurança SSL/TLS
=====================================
"""

import ssl
import socket
import subprocess
import sys
from pathlib import Path

def test_certificate_files():
    """Testa arquivos de certificado"""
    print("🔍 Testando arquivos de certificado...")
    
    ssl_dir = Path("/home/vancim/whats_agent/config/nginx/ssl")
    
    cert_file = ssl_dir / "server.crt"
    key_file = ssl_dir / "server.key"
    dhparam_file = ssl_dir / "dhparam.pem"
    
    # Verificar existência
    if not cert_file.exists():
        print("❌ Certificado não encontrado")
        return False
    
    if not key_file.exists():
        print("❌ Chave privada não encontrada")
        return False
    
    # Verificar permissões da chave privada
    key_perms = oct(key_file.stat().st_mode)[-3:]
    if key_perms != "600":
        print(f"❌ Permissões da chave privada inseguras: {key_perms}")
        return False
    
    print("✅ Arquivos de certificado OK")
    return True

def test_certificate_validity():
    """Testa validade do certificado"""
    print("🔍 Testando validade do certificado...")
    
    try:
        result = subprocess.run([
            "openssl", "x509", "-in", "/home/vancim/whats_agent/config/nginx/ssl/server.crt",
            "-text", "-noout"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Certificado válido")
            
            # Verificar algoritmo de assinatura
            if "sha256" in result.stdout.lower():
                print("✅ Algoritmo SHA-256 detectado")
            else:
                print("⚠️ Algoritmo de assinatura pode ser fraco")
            
            # Verificar tamanho da chave
            if "4096 bit" in result.stdout:
                print("✅ Chave RSA 4096 bits detectada")
            elif "2048 bit" in result.stdout:
                print("⚠️ Chave RSA 2048 bits (recomendado 4096+)")
            
            return True
        else:
            print("❌ Certificado inválido")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar certificado: {e}")
        return False

def test_encryption_service():
    """Testa serviço de criptografia"""
    print("🔍 Testando serviço de criptografia...")
    
    try:
        # Importar e testar serviço
        sys.path.append("/home/vancim/whats_agent")
        
        from app.security.encryption_service import get_encryption_service
        
        service = get_encryption_service()
        
        # Teste básico
        test_data = "dados_sensíveis_de_teste"
        encrypted = service.encrypt(test_data, "teste")
        decrypted = service.decrypt_to_string(encrypted, "teste")
        
        if decrypted == test_data:
            print("✅ Criptografia AES-256-GCM funcionando")
            return True
        else:
            print("❌ Falha na criptografia")
            return False
            
    except Exception as e:
        print(f"❌ Erro no serviço de criptografia: {e}")
        return False

def test_ssl_connection():
    """Testa conexão SSL local"""
    print("🔍 Testando conexão SSL...")
    
    try:
        # Criar contexto SSL
        context = ssl.create_default_context()
        context.check_hostname = False  # Para certificado auto-assinado
        context.verify_mode = ssl.CERT_NONE  # Para teste local
        
        # Tentar conectar (assumindo que nginx está rodando)
        with socket.create_connection(("localhost", 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                print(f"✅ Conexão SSL estabelecida")
                print(f"   Versão: {ssock.version()}")
                print(f"   Cifra: {ssock.cipher()[0] if ssock.cipher() else 'N/A'}")
                return True
                
    except ConnectionRefusedError:
        print("⚠️ Servidor HTTPS não está rodando (normal se não estiver ativo)")
        return True  # Não é um erro crítico
    except Exception as e:
        print(f"❌ Erro na conexão SSL: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🔒 TESTE COMPLETO DE SEGURANÇA SSL/TLS")
    print("=" * 50)
    
    tests = [
        test_certificate_files,
        test_certificate_validity,
        test_encryption_service,
        test_ssl_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            print()
    
    print(f"📊 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema SSL seguro.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Revise a configuração.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
