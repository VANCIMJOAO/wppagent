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
