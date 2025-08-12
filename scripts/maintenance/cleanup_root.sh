#!/bin/bash

# Script de limpeza e organização da raiz do projeto WhatsApp Agent
# Data: $(date)

echo "🧹 Iniciando limpeza e organização da raiz do projeto..."

# Criar diretórios organizacionais se não existirem
mkdir -p docs/generated
mkdir -p scripts/tests
mkdir -p scripts/debug
mkdir -p scripts/deployment
mkdir -p scripts/maintenance
mkdir -p archive/old_files
mkdir -p testing/integration
mkdir -p testing/debug

echo "📁 Movendo arquivos de documentação..."
# Mover documentações geradas para docs/generated
mv *.md docs/generated/ 2>/dev/null || true
# Manter apenas README.md principal na raiz
cp docs/generated/README.md . 2>/dev/null || true
cp docs/generated/README_NEW.md README.md 2>/dev/null || true

echo "🧪 Organizando arquivos de teste..."
# Mover scripts de teste para scripts/tests
mv test_*.py scripts/tests/ 2>/dev/null || true
mv test_*.sh scripts/tests/ 2>/dev/null || true
mv *_test*.py scripts/tests/ 2>/dev/null || true
mv run_*tests*.sh scripts/tests/ 2>/dev/null || true
mv complete_test_suite.py scripts/tests/ 2>/dev/null || true
mv comprehensive_test_suite.py scripts/tests/ 2>/dev/null || true

echo "🔧 Organizando scripts de debug..."
# Mover scripts de debug para scripts/debug
mv debug_*.py scripts/debug/ 2>/dev/null || true
mv check_*.py scripts/debug/ 2>/dev/null || true
mv analyze_*.py scripts/debug/ 2>/dev/null || true
mv validate_*.py scripts/debug/ 2>/dev/null || true
mv validate_*.sh scripts/debug/ 2>/dev/null || true
mv demonstrate_*.py scripts/debug/ 2>/dev/null || true
mv demonstrate_*.sh scripts/debug/ 2>/dev/null || true
mv generate_*.py scripts/debug/ 2>/dev/null || true

echo "🚀 Organizando scripts de deployment..."
# Mover scripts de deployment para scripts/deployment
mv deploy_*.sh scripts/deployment/ 2>/dev/null || true
mv setup_*.sh scripts/deployment/ 2>/dev/null || true
mv start_*.sh scripts/deployment/ 2>/dev/null || true

echo "🔧 Organizando scripts de manutenção..."
# Mover scripts de manutenção para scripts/maintenance
mv cleanup_*.sh scripts/maintenance/ 2>/dev/null || true
mv create_*.py scripts/maintenance/ 2>/dev/null || true
mv quick_*.py scripts/maintenance/ 2>/dev/null || true
mv manage.py scripts/maintenance/ 2>/dev/null || true
mv whatsapp_agent_manager.sh scripts/maintenance/ 2>/dev/null || true

echo "📊 Organizando dashboards temporários..."
# Mover dashboards de debug para testing/debug
mv dashboard_debug.py testing/debug/ 2>/dev/null || true
mv dashboard_temp_*.py testing/debug/ 2>/dev/null || true

echo "🗂️ Organizando arquivos de backup do Docker..."
# Mover backups antigos para archive
mv docker-compose.yml.backup.* archive/old_files/ 2>/dev/null || true
mv docker-compose.v2.yml archive/old_files/ 2>/dev/null || true

echo "📋 Criando arquivo de estrutura do projeto..."
cat > PROJECT_STRUCTURE.md << 'EOF'
# Estrutura do Projeto WhatsApp Agent

## Diretórios Principais

### `/app/` - Código principal da aplicação
- Core da aplicação WhatsApp Agent
- Módulos principais, middleware, utilitários

### `/scripts/` - Scripts organizados por categoria
- `deployment/` - Scripts de deployment e setup
- `tests/` - Scripts e arquivos de teste
- `debug/` - Scripts de debug e validação
- `maintenance/` - Scripts de manutenção

### `/docs/` - Documentação
- `generated/` - Documentações automáticas geradas

### `/testing/` - Arquivos de teste
- `debug/` - Dashboards e ferramentas de debug
- `integration/` - Testes de integração

### `/config/` - Arquivos de configuração
### `/docker/` - Arquivos Docker específicos
### `/logs/` - Logs da aplicação
### `/data/` - Dados da aplicação
### `/archive/` - Arquivos antigos e backups

## Arquivos na Raiz
- `README.md` - Documentação principal
- `docker-compose.yml` - Configuração principal do Docker
- `requirements.txt` - Dependências Python
- `pyproject.toml` - Configuração do projeto Python
- `alembic.ini` - Configuração de migração do banco
- `dashboard_whatsapp_complete.py` - Dashboard principal
- Arquivos de configuração (.env.example, .gitignore, etc.)
EOF

echo "✅ Limpeza concluída!"
echo ""
echo "📁 Nova estrutura criada:"
echo "   - scripts/deployment/ ($(ls scripts/deployment/ 2>/dev/null | wc -l) arquivos)"
echo "   - scripts/tests/ ($(ls scripts/tests/ 2>/dev/null | wc -l) arquivos)"  
echo "   - scripts/debug/ ($(ls scripts/debug/ 2>/dev/null | wc -l) arquivos)"
echo "   - scripts/maintenance/ ($(ls scripts/maintenance/ 2>/dev/null | wc -l) arquivos)"
echo "   - docs/generated/ ($(ls docs/generated/ 2>/dev/null | wc -l) arquivos)"
echo "   - testing/debug/ ($(ls testing/debug/ 2>/dev/null | wc -l) arquivos)"
echo "   - archive/old_files/ ($(ls archive/old_files/ 2>/dev/null | wc -l) arquivos)"
echo ""
echo "✨ Projeto organizado com sucesso!"
