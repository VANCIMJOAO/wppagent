
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
