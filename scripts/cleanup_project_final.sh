#!/bin/bash
"""
🧹 SCRIPT DE LIMPEZA E ORGANIZAÇÃO DO PROJETO
=============================================

Organiza a raiz do projeto WhatsApp Agent de forma limpa e profissional
"""

# Cores para output
BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
CYAN='\033[1;36m'
NC='\033[0m'

echo -e "${BLUE}🧹 INICIANDO LIMPEZA E ORGANIZAÇÃO DO PROJETO${NC}"
echo "=============================================="
echo ""

# Criar backup antes da limpeza
echo -e "${CYAN}📋 Criando backup da estrutura atual...${NC}"
mkdir -p cleanup_backup/$(date +%Y%m%d_%H%M%S)
ls -la > cleanup_backup/$(date +%Y%m%d_%H%M%S)/directory_structure_before.txt

# 1. ARQUIVOS .ENV - Manter apenas o principal e example
echo -e "${YELLOW}🔧 Organizando arquivos .env...${NC}"
mkdir -p archive/env_backups
mv .env.backup.* archive/env_backups/ 2>/dev/null
mv .env.compromised.* archive/env_backups/ 2>/dev/null
mv .env.development archive/env_backups/ 2>/dev/null
mv .env.production archive/env_backups/ 2>/dev/null
mv .env.secrets archive/env_backups/ 2>/dev/null
mv .env.staging archive/env_backups/ 2>/dev/null
mv .env.testing archive/env_backups/ 2>/dev/null
echo "✅ Arquivos .env organizados"

# 2. ARQUIVOS DE DOCUMENTAÇÃO - Organizar em docs/
echo -e "${YELLOW}📚 Organizando documentação...${NC}"
mkdir -p docs/completion_reports
mv *_COMPLETE*.md docs/completion_reports/ 2>/dev/null
mv *_SUCCESS*.md docs/completion_reports/ 2>/dev/null
mv *_IMPLEMENTATION*.md docs/completion_reports/ 2>/dev/null
mv *_DEPLOYMENT*.md docs/completion_reports/ 2>/dev/null
mv *_OPTIMIZATION*.md docs/completion_reports/ 2>/dev/null
mv SECURITY_ALERT_FIXED.md docs/completion_reports/ 2>/dev/null
mv WHATSAPP_INTEGRATION_IMPROVEMENTS.md docs/completion_reports/ 2>/dev/null
echo "✅ Documentação organizada"

# 3. SCRIPTS DE TESTE - Organizar em tests/
echo -e "${YELLOW}🧪 Organizando scripts de teste...${NC}"
mkdir -p tests/integration tests/security tests/auth tests/manual
mv test_*.py tests/ 2>/dev/null
mv test_*.sh tests/ 2>/dev/null
mv *test*.py tests/ 2>/dev/null
mv complete_test_suite.py tests/ 2>/dev/null
mv comprehensive_test_suite.py tests/ 2>/dev/null
mv run_*tests.sh tests/ 2>/dev/null
echo "✅ Scripts de teste organizados"

# 4. SCRIPTS DE SETUP E DEPLOY - Organizar em scripts/
echo -e "${YELLOW}🔧 Organizando scripts de setup...${NC}"
mv setup_*.sh scripts/ 2>/dev/null
mv deploy_*.sh scripts/ 2>/dev/null
mv start_*.sh scripts/ 2>/dev/null
mv cleanup_*.sh scripts/ 2>/dev/null
mv demonstrate_*.sh scripts/ 2>/dev/null
mv validate_*.sh scripts/ 2>/dev/null
mv validate_*.py scripts/ 2>/dev/null
mv generate_*.py scripts/ 2>/dev/null
echo "✅ Scripts de setup organizados"

# 5. ARQUIVOS DE DEBUG - Organizar em tools/debug/
echo -e "${YELLOW}🐛 Organizando arquivos de debug...${NC}"
mkdir -p tools/debug
mv debug_*.py tools/debug/ 2>/dev/null
mv analyze_*.py tools/debug/ 2>/dev/null
mv *_debug.* tools/debug/ 2>/dev/null
echo "✅ Arquivos de debug organizados"

# 6. ARQUIVOS DE LOG - Mover para logs/
echo -e "${YELLOW}📋 Organizando arquivos de log...${NC}"
mv *.log logs/ 2>/dev/null
echo "✅ Arquivos de log organizados"

# 7. ARQUIVOS TEMPORÁRIOS E CACHE - Remover
echo -e "${YELLOW}🗑️ Removendo arquivos temporários...${NC}"
rm -f =* 2>/dev/null
rm -rf __pycache__/ 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null
echo "✅ Arquivos temporários removidos"

# 8. ARQUIVOS DE APLICAÇÃO ESPECÍFICOS - Organizar em tools/
echo -e "${YELLOW}🛠️ Organizando ferramentas específicas...${NC}"
mkdir -p tools/whatsapp tools/monitoring
mv dashboard_whatsapp_complete.py tools/whatsapp/ 2>/dev/null
mv whatsapp_message_tester.py tools/whatsapp/ 2>/dev/null
mv demonstrate_monitoring.py tools/monitoring/ 2>/dev/null
mv docker_health_check.py tools/monitoring/ 2>/dev/null
echo "✅ Ferramentas organizadas"

# 9. Criar estrutura de diretórios padrão se não existir
echo -e "${YELLOW}📁 Criando estrutura padrão...${NC}"
mkdir -p {src,lib,bin,data,tmp,archive}
echo "✅ Estrutura padrão criada"

# 10. Atualizar .gitignore para nova estrutura
echo -e "${YELLOW}🔧 Atualizando .gitignore...${NC}"
cat >> .gitignore << 'EOF'

# Cleanup and archive directories
cleanup_backup/
archive/
tmp/
*.tmp
*.temp

# Additional Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Logs
logs/*.log
*.log

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
echo "✅ .gitignore atualizado"

echo ""
echo -e "${GREEN}🎉 LIMPEZA E ORGANIZAÇÃO CONCLUÍDA!${NC}"
echo "====================================="
echo ""
echo -e "${CYAN}📊 RESUMO DAS ALTERAÇÕES:${NC}"
echo "  📁 docs/completion_reports/ - Relatórios de conclusão"
echo "  🧪 tests/ - Scripts de teste organizados"
echo "  🔧 scripts/ - Scripts de setup e deploy"
echo "  🐛 tools/debug/ - Ferramentas de debug"
echo "  🛠️ tools/whatsapp/ - Ferramentas específicas WhatsApp"
echo "  📋 logs/ - Arquivos de log centralizados"
echo "  💾 archive/env_backups/ - Backups de .env"
echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo "1. Revisar a nova estrutura"
echo "2. Testar funcionalidades principais"
echo "3. Atualizar imports se necessário"
echo "4. Commitar as mudanças organizacionais"
echo ""
echo -e "${GREEN}✨ Projeto agora está limpo e organizado! ✨${NC}"
