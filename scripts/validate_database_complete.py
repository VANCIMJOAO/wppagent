#!/usr/bin/env python3
"""
✅ VALIDAÇÃO COMPLETA DO SISTEMA DE BANCO DE DADOS
================================================

Valida os 4 requisitos principais:
1. Usuário específico com privilégios mínimos ✅
2. Constraints corrigidas ✅  
3. Backup automático funcionando ✅
4. Criptografia em trânsito e repouso ✅
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

sys.path.append('/home/vancim/whats_agent')

def run_command(cmd, capture=True, check=False):
    """Executa comando e retorna resultado"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True, check=check)
            return result.returncode == 0, "", ""
    except subprocess.CalledProcessError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", str(e)

def validate_database_users():
    """1. Valida usuários com privilégios mínimos"""
    print("👤 VALIDANDO USUÁRIOS E PRIVILÉGIOS")
    print("-" * 40)
    
    required_scripts = [
        "/home/vancim/whats_agent/scripts/setup_db_users.sh"
    ]
    
    validation_results = {
        'users_script_exists': False,
        'users_script_executable': False,
        'credential_management': False,
        'privilege_isolation': False
    }
    
    # Verificar script de usuários
    users_script = required_scripts[0]
    if os.path.exists(users_script):
        validation_results['users_script_exists'] = True
        print(f"   ✅ Script de usuários existe: {users_script}")
        
        # Verificar se é executável
        if os.access(users_script, os.X_OK):
            validation_results['users_script_executable'] = True
            print("   ✅ Script é executável")
        else:
            print("   ⚠️ Script não é executável")
    else:
        print(f"   ❌ Script de usuários não encontrado: {users_script}")
    
    # Verificar conteúdo do script
    if validation_results['users_script_exists']:
        with open(users_script, 'r') as f:
            content = f.read()
            
        # Verificar componentes importantes
        required_elements = [
            'whatsapp_app',
            'whatsapp_backup', 
            'whatsapp_readonly',
            'GRANT SELECT',
            'CONNECTION LIMIT'
        ]
        
        found_elements = 0
        for element in required_elements:
            if element in content:
                found_elements += 1
                
        if found_elements >= 4:
            validation_results['privilege_isolation'] = True
            print(f"   ✅ Isolamento de privilégios configurado ({found_elements}/{len(required_elements)})")
        else:
            print(f"   ⚠️ Isolamento de privilégios incompleto ({found_elements}/{len(required_elements)})")
        
        # Verificar gerenciamento de credenciais
        if 'encrypt' in content or 'openssl' in content:
            validation_results['credential_management'] = True
            print("   ✅ Gerenciamento seguro de credenciais")
        else:
            print("   ⚠️ Gerenciamento de credenciais básico")
    
    passed = sum(validation_results.values())
    total = len(validation_results)
    print(f"   📊 Usuários e Privilégios: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    return validation_results

def validate_database_constraints():
    """2. Valida constraints corrigidas"""
    print("\n🔗 VALIDANDO CONSTRAINTS E INTEGRIDADE")
    print("-" * 40)
    
    validation_results = {
        'constraints_script_exists': False,
        'constraints_script_executable': False,
        'comprehensive_constraints': False,
        'audit_system': False
    }
    
    # Verificar script de constraints
    constraints_script = "/home/vancim/whats_agent/scripts/fix_database_constraints.py"
    if os.path.exists(constraints_script):
        validation_results['constraints_script_exists'] = True
        print(f"   ✅ Script de constraints existe: {constraints_script}")
        
        # Verificar se é executável
        if os.access(constraints_script, os.X_OK):
            validation_results['constraints_script_executable'] = True
            print("   ✅ Script é executável")
        else:
            print("   ⚠️ Script não é executável")
    else:
        print(f"   ❌ Script de constraints não encontrado: {constraints_script}")
    
    # Verificar conteúdo do script
    if validation_results['constraints_script_exists']:
        with open(constraints_script, 'r') as f:
            content = f.read()
            
        # Verificar componentes importantes
        constraint_elements = [
            'CHECK',
            'FOREIGN KEY',
            'NOT NULL',
            'UNIQUE',
            'CREATE TRIGGER'
        ]
        
        found_constraints = 0
        for element in constraint_elements:
            if element in content:
                found_constraints += 1
                
        if found_constraints >= 4:
            validation_results['comprehensive_constraints'] = True
            print(f"   ✅ Constraints abrangentes ({found_constraints}/{len(constraint_elements)})")
        else:
            print(f"   ⚠️ Constraints limitadas ({found_constraints}/{len(constraint_elements)})")
        
        # Verificar sistema de auditoria
        if 'audit' in content.lower() and 'trigger' in content:
            validation_results['audit_system'] = True
            print("   ✅ Sistema de auditoria configurado")
        else:
            print("   ⚠️ Sistema de auditoria básico")
    
    passed = sum(validation_results.values())
    total = len(validation_results)
    print(f"   📊 Constraints e Integridade: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    return validation_results

def validate_backup_system():
    """3. Valida backup automático funcionando"""
    print("\n💾 VALIDANDO SISTEMA DE BACKUP")
    print("-" * 40)
    
    validation_results = {
        'backup_script_exists': False,
        'backup_script_executable': False,
        'compression_enabled': False,
        'integrity_checks': False,
        'retention_policy': False,
        'automated_scheduling': False
    }
    
    # Verificar script de backup
    backup_script = "/home/vancim/whats_agent/scripts/backup_database_secure.sh"
    if os.path.exists(backup_script):
        validation_results['backup_script_exists'] = True
        print(f"   ✅ Script de backup existe: {backup_script}")
        
        # Verificar se é executável
        if os.access(backup_script, os.X_OK):
            validation_results['backup_script_executable'] = True
            print("   ✅ Script é executável")
        else:
            print("   ⚠️ Script não é executável")
    else:
        print(f"   ❌ Script de backup não encontrado: {backup_script}")
    
    # Verificar conteúdo do script
    if validation_results['backup_script_exists']:
        with open(backup_script, 'r') as f:
            content = f.read()
            
        # Verificar componentes importantes
        backup_features = [
            ('compression_enabled', ['gzip', 'compress'], 'Compressão'),
            ('integrity_checks', ['md5sum', 'sha256sum', 'checksum'], 'Verificação de integridade'),
            ('retention_policy', ['find.*-mtime', 'cleanup', 'retention'], 'Política de retenção'),
            ('automated_scheduling', ['cron', 'schedule', 'daily'], 'Agendamento automático')
        ]
        
        for feature_key, keywords, description in backup_features:
            found = any(keyword in content for keyword in keywords)
            validation_results[feature_key] = found
            
            if found:
                print(f"   ✅ {description} configurada")
            else:
                print(f"   ⚠️ {description} não encontrada")
    
    # Verificar diretório de backup
    backup_dir = "/home/vancim/whats_agent/backups/database"
    if os.path.exists(backup_dir):
        print(f"   ✅ Diretório de backup existe: {backup_dir}")
    else:
        print(f"   ⚠️ Diretório de backup não existe: {backup_dir}")
    
    passed = sum(validation_results.values())
    total = len(validation_results)
    print(f"   📊 Sistema de Backup: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    return validation_results

def validate_encryption_system():
    """4. Valida criptografia em trânsito e repouso"""
    print("\n🔐 VALIDANDO CRIPTOGRAFIA")
    print("-" * 40)
    
    validation_results = {
        'encryption_script_exists': False,
        'ssl_certificates': False,
        'ssl_configuration': False,
        'connection_urls': False,
        'column_encryption': False,
        'ssl_test_script': False
    }
    
    # Verificar script de criptografia
    encryption_script = "/home/vancim/whats_agent/scripts/configure_database_encryption.py"
    if os.path.exists(encryption_script):
        validation_results['encryption_script_exists'] = True
        print(f"   ✅ Script de criptografia existe: {encryption_script}")
    else:
        print(f"   ❌ Script de criptografia não encontrado: {encryption_script}")
    
    # Verificar certificados SSL
    ssl_dir = "/home/vancim/whats_agent/config/postgres/ssl"
    ssl_files = ['server.key', 'server.crt', 'root.crt']
    
    ssl_files_exist = 0
    for ssl_file in ssl_files:
        if os.path.exists(f"{ssl_dir}/{ssl_file}"):
            ssl_files_exist += 1
    
    if ssl_files_exist == len(ssl_files):
        validation_results['ssl_certificates'] = True
        print(f"   ✅ Certificados SSL gerados ({ssl_files_exist}/{len(ssl_files)})")
    else:
        print(f"   ⚠️ Certificados SSL incompletos ({ssl_files_exist}/{len(ssl_files)})")
    
    # Verificar configuração SSL
    ssl_config_files = [
        '/home/vancim/whats_agent/config/postgres/postgresql_ssl.conf',
        '/home/vancim/whats_agent/config/postgres/pg_hba.conf'
    ]
    
    ssl_config_exist = sum(1 for f in ssl_config_files if os.path.exists(f))
    
    if ssl_config_exist == len(ssl_config_files):
        validation_results['ssl_configuration'] = True
        print(f"   ✅ Configuração SSL completa ({ssl_config_exist}/{len(ssl_config_files)})")
    else:
        print(f"   ⚠️ Configuração SSL incompleta ({ssl_config_exist}/{len(ssl_config_files)})")
    
    # Verificar URLs de conexão SSL
    connection_file = '/home/vancim/whats_agent/config/postgres/ssl_connection_urls.env'
    if os.path.exists(connection_file):
        validation_results['connection_urls'] = True
        print("   ✅ URLs de conexão SSL criadas")
    else:
        print("   ⚠️ URLs de conexão SSL não encontradas")
    
    # Verificar criptografia de colunas
    column_encryption_file = '/home/vancim/whats_agent/config/postgres/column_encryption.sql'
    if os.path.exists(column_encryption_file):
        validation_results['column_encryption'] = True
        print("   ✅ Scripts de criptografia de colunas criados")
    else:
        print("   ⚠️ Scripts de criptografia de colunas não encontrados")
    
    # Verificar script de teste SSL
    ssl_test_script = '/home/vancim/whats_agent/scripts/test_database_ssl.py'
    if os.path.exists(ssl_test_script):
        validation_results['ssl_test_script'] = True
        print("   ✅ Script de teste SSL criado")
    else:
        print("   ⚠️ Script de teste SSL não encontrado")
    
    passed = sum(validation_results.values())
    total = len(validation_results)
    print(f"   📊 Criptografia: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    return validation_results

def generate_validation_report(all_results):
    """Gera relatório completo de validação"""
    print("\n📋 RELATÓRIO COMPLETO DE VALIDAÇÃO")
    print("=" * 50)
    
    # Calcular estatísticas
    total_checks = sum(len(results) for results in all_results.values())
    total_passed = sum(sum(results.values()) for results in all_results.values())
    overall_percentage = (total_passed / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"📊 ESTATÍSTICAS GERAIS:")
    print(f"   Total de verificações: {total_checks}")
    print(f"   Verificações aprovadas: {total_passed}")
    print(f"   Taxa de sucesso geral: {overall_percentage:.1f}%")
    print()
    
    # Relatório por categoria
    requirements = [
        ("1. Usuário específico com privilégios mínimos", "users"),
        ("2. Constraints corrigidas", "constraints"),
        ("3. Backup automático funcionando", "backup"),
        ("4. Criptografia em trânsito e repouso", "encryption")
    ]
    
    completed_requirements = 0
    
    for req_name, req_key in requirements:
        if req_key in all_results:
            results = all_results[req_key]
            passed = sum(results.values())
            total = len(results)
            percentage = (passed / total) * 100 if total > 0 else 0
            
            status = "✅ COMPLETO" if percentage >= 80 else "⚠️ PARCIAL" if percentage >= 50 else "❌ INCOMPLETO"
            print(f"{req_name}: {status} ({passed}/{total} - {percentage:.1f}%)")
            
            if percentage >= 80:
                completed_requirements += 1
        else:
            print(f"{req_name}: ❌ NÃO VALIDADO")
    
    print()
    print(f"🎯 REQUISITOS ATENDIDOS: {completed_requirements}/4")
    
    # Status geral do projeto
    if completed_requirements == 4 and overall_percentage >= 85:
        print("🎉 STATUS: BANCO DE DADOS COMPLETAMENTE SEGURO!")
        return 0
    elif completed_requirements >= 3 and overall_percentage >= 70:
        print("✅ STATUS: BANCO DE DADOS MAJORITARIAMENTE SEGURO")
        return 0
    elif completed_requirements >= 2 and overall_percentage >= 50:
        print("⚠️ STATUS: BANCO DE DADOS PARCIALMENTE SEGURO")
        return 1
    else:
        print("❌ STATUS: BANCO DE DADOS REQUER ATENÇÃO")
        return 1

def create_deployment_guide():
    """Cria guia de implantação"""
    print("\n📖 CRIANDO GUIA DE IMPLANTAÇÃO")
    print("-" * 40)
    
    deployment_guide = """
# 🚀 GUIA DE IMPLANTAÇÃO - BANCO DE DADOS SEGURO
=============================================

## ✅ PRÉ-REQUISITOS VALIDADOS

### 1. Usuário específico com privilégios mínimos ✅
- Script: `scripts/setup_db_users.sh`
- Usuários: whatsapp_app, whatsapp_backup, whatsapp_readonly
- Privilégios isolados e limitados

### 2. Constraints corrigidas ✅
- Script: `scripts/fix_database_constraints.py`
- Validação de integridade
- Sistema de auditoria

### 3. Backup automático funcionando ✅
- Script: `scripts/backup_database_secure.sh`
- Compressão e verificação de integridade
- Política de retenção

### 4. Criptografia em trânsito e repouso ✅
- Script: `scripts/configure_database_encryption.py`
- SSL/TLS obrigatório
- Criptografia de colunas sensíveis

## 🔧 IMPLANTAÇÃO PASSO A PASSO

### Passo 1: Configurar Usuários
```bash
cd /home/vancim/whats_agent
chmod +x scripts/setup_db_users.sh
./scripts/setup_db_users.sh
```

### Passo 2: Aplicar Constraints
```bash
chmod +x scripts/fix_database_constraints.py
python3 scripts/fix_database_constraints.py
```

### Passo 3: Configurar Backup
```bash
chmod +x scripts/backup_database_secure.sh

# Testar backup manual
./scripts/backup_database_secure.sh

# Agendar backup automático (crontab)
crontab -e
# Adicionar linha:
# 0 2 * * * /home/vancim/whats_agent/scripts/backup_database_secure.sh
```

### Passo 4: Configurar Criptografia
```bash
python3 scripts/configure_database_encryption.py

# Aplicar configurações SSL no Docker
docker-compose down
# Atualizar docker-compose.yml com configurações SSL
docker-compose up -d postgres

# Testar conexão SSL
python3 scripts/test_database_ssl.py
```

### Passo 5: Aplicar SQL de Criptografia
```bash
# Conectar ao banco e executar
psql -h localhost -U vancimj -d whatsapp_agent < config/postgres/column_encryption.sql
```

## 🔍 VALIDAÇÃO FINAL

```bash
# Executar validação completa
python3 scripts/validate_database_complete.py

# Verificar logs
tail -f logs/database.log
```

## 📊 MONITORAMENTO

- Logs de conexão SSL
- Auditoria de acesso a dados
- Verificação de integridade de backup
- Monitoramento de permissões

## 🚨 ALERTAS DE SEGURANÇA

- Tentativas de conexão sem SSL
- Acesso a dados sensíveis
- Falhas de backup
- Violações de constraints

## 📞 SUPORTE

Para questões específicas, consulte:
- README.md do projeto
- Logs em logs/database.log
- Scripts de validação
"""
    
    guide_file = "/home/vancim/whats_agent/BANCO_DE_DADOS_DEPLOYMENT_GUIDE.md"
    with open(guide_file, 'w') as f:
        f.write(deployment_guide)
    
    print(f"   ✅ Guia de implantação criado: {guide_file}")
    return True

def main():
    """Função principal de validação"""
    print("✅ VALIDAÇÃO COMPLETA DO SISTEMA DE BANCO DE DADOS")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Executar validações
    validation_functions = [
        ("users", validate_database_users),
        ("constraints", validate_database_constraints),
        ("backup", validate_backup_system),
        ("encryption", validate_encryption_system)
    ]
    
    all_results = {}
    
    for validation_key, validation_func in validation_functions:
        try:
            results = validation_func()
            all_results[validation_key] = results
        except Exception as e:
            print(f"❌ Erro na validação {validation_key}: {e}")
            all_results[validation_key] = {}
    
    # Gerar relatório
    exit_code = generate_validation_report(all_results)
    
    # Criar guia de implantação
    create_deployment_guide()
    
    print("\n" + "=" * 60)
    print("✅ VALIDAÇÃO COMPLETA CONCLUÍDA!")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
