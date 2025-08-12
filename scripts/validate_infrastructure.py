#!/usr/bin/env python3
"""
🏗️ VALIDADOR DE INFRAESTRUTURA SEGURA
=====================================

Valida todas as configurações de segurança de infraestrutura
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_command(cmd, capture=True):
    """Executa comando e retorna resultado"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_non_root_containers():
    """Verifica se containers não executam como root"""
    print("🔒 1. VERIFICANDO CONTAINERS NÃO-ROOT...")
    
    checks = []
    
    # Verificar Dockerfile principal
    dockerfile_path = "/home/vancim/whats_agent/Dockerfile"
    if os.path.exists(dockerfile_path):
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        if "USER appuser" in content:
            checks.append(("✅", "Dockerfile principal usa usuário não-root (appuser)"))
        else:
            checks.append(("❌", "Dockerfile principal executa como root"))
        
        if "groupadd --gid 1000 appuser" in content:
            checks.append(("✅", "Usuário não-root criado corretamente"))
        else:
            checks.append(("❌", "Usuário não-root não encontrado"))
    else:
        checks.append(("❌", "Dockerfile principal não encontrado"))
    
    # Verificar Dockerfile Streamlit
    dockerfile_streamlit = "/home/vancim/whats_agent/Dockerfile.streamlit"
    if os.path.exists(dockerfile_streamlit):
        with open(dockerfile_streamlit, 'r') as f:
            content = f.read()
        
        if "USER streamlituser" in content:
            checks.append(("✅", "Dockerfile Streamlit usa usuário não-root (streamlituser)"))
        else:
            checks.append(("❌", "Dockerfile Streamlit executa como root"))
    else:
        checks.append(("❌", "Dockerfile Streamlit não encontrado"))
    
    return checks

def check_network_segmentation():
    """Verifica segmentação de rede"""
    print("🌐 2. VERIFICANDO SEGMENTAÇÃO DE REDE...")
    
    checks = []
    
    # Verificar docker-compose.yml
    compose_path = "/home/vancim/whats_agent/docker-compose.yml"
    if os.path.exists(compose_path):
        with open(compose_path, 'r') as f:
            content = f.read()
        
        networks = ["frontend_network", "backend_network", "database_network"]
        for network in networks:
            if network in content:
                checks.append(("✅", f"Rede {network} configurada"))
            else:
                checks.append(("❌", f"Rede {network} não encontrada"))
        
        # Verificar se database network é internal
        if "internal: true" in content:
            checks.append(("✅", "Rede de banco de dados é interna (sem internet)"))
        else:
            checks.append(("❌", "Rede de banco de dados não está isolada"))
        
        # Verificar se portas de serviços internos não estão expostas
        if "5432:5432" not in content:
            checks.append(("✅", "PostgreSQL não exposto externamente"))
        else:
            checks.append(("❌", "PostgreSQL exposto externamente"))
        
        if "6379:6379" not in content:
            checks.append(("✅", "Redis não exposto externamente"))
        else:
            checks.append(("❌", "Redis exposto externamente"))
    else:
        checks.append(("❌", "docker-compose.yml não encontrado"))
    
    return checks

def check_firewall():
    """Verifica configuração do firewall"""
    print("🔥 3. VERIFICANDO FIREWALL...")
    
    checks = []
    
    # Verificar se UFW está instalado
    success, output, error = run_command("which ufw")
    if success:
        checks.append(("✅", "UFW instalado"))
        
        # Verificar status do UFW
        success, output, error = run_command("sudo ufw status")
        if "Status: active" in output:
            checks.append(("✅", "UFW ativo"))
            
            # Verificar regras básicas
            if "22/tcp" in output or "ssh" in output:
                checks.append(("✅", "SSH permitido"))
            else:
                checks.append(("⚠️", "SSH não configurado no firewall"))
            
            if "80/tcp" in output and "443/tcp" in output:
                checks.append(("✅", "HTTP/HTTPS permitidos"))
            else:
                checks.append(("❌", "HTTP/HTTPS não configurados"))
                
        else:
            checks.append(("❌", "UFW não está ativo"))
    else:
        checks.append(("❌", "UFW não instalado"))
    
    # Verificar Fail2Ban
    success, output, error = run_command("which fail2ban-server")
    if success:
        checks.append(("✅", "Fail2Ban instalado"))
        
        success, output, error = run_command("sudo fail2ban-client status")
        if success and "SSH" in output.upper():
            checks.append(("✅", "Fail2Ban protegendo SSH"))
        else:
            checks.append(("❌", "Fail2Ban não configurado para SSH"))
    else:
        checks.append(("❌", "Fail2Ban não instalado"))
    
    # Verificar script de configuração
    firewall_script = "/home/vancim/whats_agent/scripts/setup_firewall.sh"
    if os.path.exists(firewall_script) and os.access(firewall_script, os.X_OK):
        checks.append(("✅", "Script de configuração do firewall disponível"))
    else:
        checks.append(("❌", "Script de configuração do firewall não encontrado"))
    
    return checks

def check_security_updates():
    """Verifica sistema de updates de segurança"""
    print("🔄 4. VERIFICANDO UPDATES DE SEGURANÇA...")
    
    checks = []
    
    # Verificar script de updates
    update_script = "/home/vancim/whats_agent/scripts/apply_security_updates.sh"
    if os.path.exists(update_script) and os.access(update_script, os.X_OK):
        checks.append(("✅", "Script de updates de segurança disponível"))
    else:
        checks.append(("❌", "Script de updates de segurança não encontrado"))
    
    # Verificar unattended-upgrades
    success, output, error = run_command("which unattended-upgrade")
    if success:
        checks.append(("✅", "Unattended-upgrades instalado"))
    else:
        checks.append(("⚠️", "Unattended-upgrades não instalado"))
    
    # Verificar cron jobs
    success, output, error = run_command("crontab -l")
    if success:
        if "apply_security_updates.sh" in output:
            checks.append(("✅", "Updates automáticos configurados no cron"))
        else:
            checks.append(("❌", "Updates automáticos não configurados"))
        
        if "check_certificates.sh" in output:
            checks.append(("✅", "Verificação de certificados configurada"))
        else:
            checks.append(("❌", "Verificação de certificados não configurada"))
    else:
        checks.append(("❌", "Nenhum cron job configurado"))
    
    # Verificar logs de updates
    update_log = "/var/log/security-updates.log"
    if os.path.exists(update_log):
        checks.append(("✅", "Log de updates de segurança configurado"))
    else:
        checks.append(("⚠️", "Log de updates não encontrado"))
    
    # Verificar backup automático
    backup_dir = "/home/vancim/whats_agent/backups"
    if os.path.exists(backup_dir):
        checks.append(("✅", "Diretório de backup configurado"))
    else:
        checks.append(("❌", "Diretório de backup não encontrado"))
    
    return checks

def check_additional_hardening():
    """Verifica configurações de hardening adicional"""
    print("🛡️ 5. VERIFICANDO HARDENING ADICIONAL...")
    
    checks = []
    
    # Verificar configurações sysctl
    sysctl_configs = [
        ("net.ipv4.tcp_syncookies", "1", "Proteção SYN flood"),
        ("net.ipv4.conf.all.rp_filter", "1", "Proteção IP spoofing"),
        ("kernel.randomize_va_space", "2", "ASLR ativado"),
        ("fs.suid_dumpable", "0", "Core dumps desabilitados")
    ]
    
    for config, expected, description in sysctl_configs:
        success, output, error = run_command(f"sysctl {config}")
        if success and expected in output:
            checks.append(("✅", f"{description}"))
        else:
            checks.append(("❌", f"{description} não configurado"))
    
    # Verificar auditd
    success, output, error = run_command("which auditd")
    if success:
        checks.append(("✅", "Auditd instalado"))
        
        # Verificar regras de auditoria
        audit_rules = "/etc/audit/rules.d/whatsapp.rules"
        if os.path.exists(audit_rules):
            checks.append(("✅", "Regras de auditoria configuradas"))
        else:
            checks.append(("❌", "Regras de auditoria não configuradas"))
    else:
        checks.append(("❌", "Auditd não instalado"))
    
    # Verificar permissões de arquivos críticos
    critical_files = [
        ("/home/vancim/whats_agent/.env", "600"),
        ("/home/vancim/whats_agent/secrets", "700"),
        ("/home/vancim/whats_agent/config/nginx/ssl/server.key", "600")
    ]
    
    for file_path, expected_perm in critical_files:
        if os.path.exists(file_path):
            actual_perm = oct(os.stat(file_path).st_mode)[-3:]
            if actual_perm == expected_perm:
                checks.append(("✅", f"Permissões corretas: {file_path} ({actual_perm})"))
            else:
                checks.append(("❌", f"Permissões incorretas: {file_path} ({actual_perm}, esperado {expected_perm})"))
        else:
            checks.append(("⚠️", f"Arquivo não encontrado: {file_path}"))
    
    return checks

def generate_report(all_checks):
    """Gera relatório final"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE INFRAESTRUTURA SEGURA")
    print("="*60)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    total_checks = 0
    passed_checks = 0
    
    for category, checks in all_checks.items():
        print(f"🔹 {category}")
        print("-" * 40)
        
        for status, description in checks:
            print(f"   {status} {description}")
            total_checks += 1
            if status == "✅":
                passed_checks += 1
        print()
    
    # Calcular score
    score = round((passed_checks / total_checks) * 100) if total_checks > 0 else 0
    
    print("📊 SCORE DE INFRAESTRUTURA SEGURA")
    print("-" * 40)
    print(f"   Passou: {passed_checks}/{total_checks} verificações")
    print(f"   Score: {score}%")
    print()
    
    if score >= 90:
        print("   🏆 EXCELENTE - Infraestrutura altamente segura")
    elif score >= 75:
        print("   ✅ BOM - Infraestrutura segura com pequenos ajustes")
    elif score >= 50:
        print("   ⚠️ ATENÇÃO - Infraestrutura requer melhorias")
    else:
        print("   ❌ CRÍTICO - Infraestrutura insegura")
    
    print()
    print("💡 PRÓXIMOS PASSOS:")
    print("   1. Corrigir itens marcados com ❌")
    print("   2. Revisar itens marcados com ⚠️")
    print("   3. Executar scripts de configuração disponíveis")
    print("   4. Monitorar logs de segurança regularmente")
    print()
    
    # Salvar relatório
    report_file = f"/home/vancim/whats_agent/reports/infrastructure_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write(f"RELATÓRIO DE INFRAESTRUTURA SEGURA\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        for category, checks in all_checks.items():
            f.write(f"{category}\n")
            f.write("-" * 40 + "\n")
            for status, description in checks:
                f.write(f"{status} {description}\n")
            f.write("\n")
        
        f.write(f"SCORE: {score}% ({passed_checks}/{total_checks})\n")
    
    print(f"📄 Relatório salvo em: {report_file}")
    
    return score

def main():
    """Função principal"""
    print("🏗️ VALIDADOR DE INFRAESTRUTURA SEGURA")
    print("=" * 60)
    print()
    
    all_checks = {
        "CONTAINERS NÃO-ROOT": check_non_root_containers(),
        "SEGMENTAÇÃO DE REDE": check_network_segmentation(),
        "FIREWALL": check_firewall(),
        "UPDATES DE SEGURANÇA": check_security_updates(),
        "HARDENING ADICIONAL": check_additional_hardening()
    }
    
    score = generate_report(all_checks)
    
    # Retornar código de saída baseado no score
    if score >= 75:
        return 0  # Sucesso
    else:
        return 1  # Precisa melhorias

if __name__ == "__main__":
    sys.exit(main())
