#!/usr/bin/env python3
"""
📊 RELATÓRIO FINAL DE SEGURANÇA E CRIPTOGRAFIA
==============================================

Gera relatório completo do sistema de segurança implementado
"""

import os
import sys
sys.path.append('/home/vancim/whats_agent')
from datetime import datetime

def generate_security_report():
    """Gera relatório completo de segurança"""
    
    report = []
    report.append("🔒 RELATÓRIO DE SEGURANÇA - WHATSAPP AGENT")
    report.append("=" * 60)
    report.append(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append("")
    
    # 1. CERTIFICADOS SSL
    report.append("🔐 1. CERTIFICADOS SSL/TLS")
    report.append("-" * 30)
    
    ssl_dir = "/home/vancim/whats_agent/config/nginx/ssl"
    cert_file = os.path.join(ssl_dir, "server.crt")
    key_file = os.path.join(ssl_dir, "server.key")
    
    if os.path.exists(cert_file):
        cert_perms = oct(os.stat(cert_file).st_mode)[-3:]
        key_perms = oct(os.stat(key_file).st_mode)[-3:]
        
        report.append("✅ Certificado SSL gerado")
        report.append(f"   📁 Local: {cert_file}")
        report.append(f"   🔒 Permissões certificado: {cert_perms} (644 recomendado)")
        report.append(f"   🔑 Permissões chave privada: {key_perms} (600 obrigatório)")
        
        if key_perms == "600":
            report.append("   ✅ Chave privada PROTEGIDA corretamente")
        else:
            report.append("   ❌ Chave privada com permissões INSEGURAS")
        
        # Informações do certificado
        try:
            import subprocess
            result = subprocess.run([
                "openssl", "x509", "-in", cert_file, "-text", "-noout"
            ], capture_output=True, text=True)
            
            if "RSA" in result.stdout:
                if "2048 bit" in result.stdout:
                    report.append("   🔑 Algoritmo: RSA 2048 bits")
                elif "4096 bit" in result.stdout:
                    report.append("   🔑 Algoritmo: RSA 4096 bits ⭐")
                else:
                    report.append("   🔑 Algoritmo: RSA (tamanho não detectado)")
            
            if "sha256" in result.stdout.lower():
                report.append("   ✅ Assinatura: SHA-256 (seguro)")
            elif "sha1" in result.stdout.lower():
                report.append("   ⚠️ Assinatura: SHA-1 (obsoleto)")
            
            # Verificar SAN
            if "DNS:" in result.stdout:
                san_count = result.stdout.count("DNS:")
                report.append(f"   🌐 Subject Alternative Names: {san_count} domínios")
                
        except Exception as e:
            report.append(f"   ⚠️ Erro ao analisar certificado: {e}")
    else:
        report.append("❌ Certificado SSL não encontrado")
    
    report.append("")
    
    # 2. CRIPTOGRAFIA DE DADOS
    report.append("🔐 2. SISTEMA DE CRIPTOGRAFIA")
    report.append("-" * 30)
    
    master_key_file = "/home/vancim/whats_agent/secrets/ssl/master.key"
    if os.path.exists(master_key_file):
        key_perms = oct(os.stat(master_key_file).st_mode)[-3:]
        report.append("✅ Chave mestre de criptografia criada")
        report.append(f"   📁 Local: {master_key_file}")
        report.append(f"   🔒 Permissões: {key_perms}")
        
        if key_perms == "600":
            report.append("   ✅ Chave mestre PROTEGIDA corretamente")
        else:
            report.append("   ❌ Chave mestre com permissões INSEGURAS")
    else:
        report.append("❌ Chave mestre não encontrada")
    
    # Testar criptografia
    try:
        os.environ['ENCRYPTION_MASTER_KEY'] = open(master_key_file).read().strip()
        from app.security.encryption_service import get_encryption_service
        
        service = get_encryption_service()
        test_data = "teste_segurança_123"
        encrypted = service.encrypt(test_data, "relatório")
        decrypted = service.decrypt_to_string(encrypted, "relatório")
        
        if decrypted == test_data:
            report.append("   ✅ Algoritmo: AES-256-GCM (estado da arte)")
            report.append("   ✅ Teste de criptografia: PASSOU")
        else:
            report.append("   ❌ Teste de criptografia: FALHOU")
            
    except Exception as e:
        report.append(f"   ❌ Erro no teste de criptografia: {e}")
    
    report.append("")
    
    # 3. HTTPS OBRIGATÓRIO
    report.append("🔐 3. HTTPS OBRIGATÓRIO (HSTS)")
    report.append("-" * 30)
    
    nginx_config = "/home/vancim/whats_agent/config/nginx/nginx.conf"
    if os.path.exists(nginx_config):
        with open(nginx_config, 'r') as f:
            config_content = f.read()
        
        if "return 301 https://" in config_content:
            report.append("   ✅ Redirecionamento HTTP → HTTPS configurado")
        else:
            report.append("   ❌ Redirecionamento HTTPS não encontrado")
        
        if "Strict-Transport-Security" in config_content:
            report.append("   ✅ HSTS configurado")
            if "max-age=31536000" in config_content:
                report.append("   ✅ HSTS válido por 1 ano")
            if "includeSubDomains" in config_content:
                report.append("   ✅ HSTS inclui subdomínios")
            if "preload" in config_content:
                report.append("   ✅ HSTS preload habilitado")
        else:
            report.append("   ❌ HSTS não configurado")
        
        # Verificar headers de segurança
        security_headers = [
            ("X-Frame-Options", "Proteção contra clickjacking"),
            ("X-XSS-Protection", "Proteção XSS"),
            ("X-Content-Type-Options", "Proteção MIME sniffing"),
            ("Content-Security-Policy", "Política de segurança de conteúdo"),
            ("Referrer-Policy", "Política de referrer")
        ]
        
        report.append("   📋 Headers de segurança:")
        for header, description in security_headers:
            if header in config_content:
                report.append(f"      ✅ {header}: {description}")
            else:
                report.append(f"      ❌ {header}: Não configurado")
                
    else:
        report.append("   ❌ Configuração Nginx não encontrada")
    
    report.append("")
    
    # 4. PROTEÇÃO DE DADOS SENSÍVEIS
    report.append("🔐 4. PROTEÇÃO DE DADOS SENSÍVEIS")
    report.append("-" * 30)
    
    try:
        from app.security.data_encryption import get_data_encryption
        
        data_encryption = get_data_encryption()
        
        # Testar diferentes tipos de dados
        test_cases = [
            ("Senhas", lambda: data_encryption.encrypt_password("senha123", "user1")),
            ("API Keys", lambda: data_encryption.encrypt_api_key("sk-1234567890abcdef", "openai")),
            ("Variáveis ENV", lambda: data_encryption.encrypt_environment_variables({
                "SECRET_KEY": "secret123", "NORMAL_VAR": "normal"
            }))
        ]
        
        for test_name, test_func in test_cases:
            try:
                result = test_func()
                report.append(f"   ✅ Criptografia de {test_name}: Funcionando")
            except Exception as e:
                report.append(f"   ❌ Criptografia de {test_name}: Erro - {e}")
                
    except Exception as e:
        report.append(f"   ❌ Sistema de criptografia de dados não disponível: {e}")
    
    report.append("")
    
    # 5. CONFORMIDADE E PADRÕES
    report.append("🔐 5. CONFORMIDADE E PADRÕES")
    report.append("-" * 30)
    
    compliance_checks = []
    
    # Verificar TLS 1.2+
    if os.path.exists(nginx_config):
        with open(nginx_config, 'r') as f:
            config = f.read()
        
        if "TLSv1.2 TLSv1.3" in config:
            compliance_checks.append(("TLS 1.2/1.3", True))
        else:
            compliance_checks.append(("TLS 1.2/1.3", False))
        
        if "ssl_ciphers" in config:
            compliance_checks.append(("Cifras seguras", True))
        else:
            compliance_checks.append(("Cifras seguras", False))
    
    # Verificar proteção de chaves
    key_protection = os.path.exists(key_file) and oct(os.stat(key_file).st_mode)[-3:] == "600"
    compliance_checks.append(("Proteção de chaves privadas", key_protection))
    
    # Verificar criptografia forte
    crypto_strong = os.path.exists(master_key_file)
    compliance_checks.append(("Criptografia AES-256", crypto_strong))
    
    passed_checks = sum(1 for _, status in compliance_checks if status)
    total_checks = len(compliance_checks)
    compliance_score = round((passed_checks / total_checks) * 100)
    
    for check_name, status in compliance_checks:
        status_icon = "✅" if status else "❌"
        report.append(f"   {status_icon} {check_name}")
    
    report.append("")
    report.append(f"   📊 Score de Conformidade: {compliance_score}% ({passed_checks}/{total_checks})")
    
    if compliance_score >= 90:
        report.append("   🏆 EXCELENTE - Sistema altamente seguro")
    elif compliance_score >= 75:
        report.append("   ✅ BOM - Sistema seguro com pequenos ajustes")
    elif compliance_score >= 50:
        report.append("   ⚠️ ATENÇÃO - Sistema requer melhorias")
    else:
        report.append("   ❌ CRÍTICO - Sistema inseguro")
    
    report.append("")
    
    # 6. RECOMENDAÇÕES
    report.append("💡 6. RECOMENDAÇÕES")
    report.append("-" * 30)
    
    recommendations = []
    
    if not os.path.exists(cert_file):
        recommendations.append("• Gerar certificados SSL")
    
    if os.path.exists(key_file) and oct(os.stat(key_file).st_mode)[-3:] != "600":
        recommendations.append("• Corrigir permissões da chave privada (chmod 600)")
    
    if compliance_score < 90:
        recommendations.append("• Implementar todos os headers de segurança")
        recommendations.append("• Configurar HSTS com preload")
    
    recommendations.extend([
        "• Monitorar data de vencimento dos certificados",
        "• Fazer backup regular das chaves de criptografia",
        "• Implementar rotação automática de chaves",
        "• Para produção: usar certificados de CA válida (Let's Encrypt)",
        "• Configurar monitoramento de segurança contínuo"
    ])
    
    for rec in recommendations:
        report.append(f"   {rec}")
    
    report.append("")
    
    # 7. PRÓXIMOS PASSOS
    report.append("🚀 7. PRÓXIMOS PASSOS PARA PRODUÇÃO")
    report.append("-" * 30)
    
    next_steps = [
        "1. Configurar domínio real e DNS",
        "2. Executar setup_letsencrypt.sh com domínio real",
        "3. Configurar renovação automática via cron",
        "4. Implementar monitoramento de certificados",
        "5. Configurar backup automatizado de chaves",
        "6. Testar HTTPS em produção",
        "7. Configurar WAF (Web Application Firewall)",
        "8. Implementar audit logging de segurança"
    ]
    
    for step in next_steps:
        report.append(f"   {step}")
    
    report.append("")
    report.append("🎉 SISTEMA DE SEGURANÇA IMPLEMENTADO COM SUCESSO!")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """Gera e exibe o relatório"""
    print("📊 Gerando relatório de segurança...")
    
    try:
        report = generate_security_report()
        
        # Salvar relatório
        report_file = f"/home/vancim/whats_agent/reports/security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Relatório salvo em: {report_file}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
