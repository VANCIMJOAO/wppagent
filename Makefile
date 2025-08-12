# WhatsApp Agent - Makefile
.PHONY: help setup start stop status

help:
	@echo "WhatsApp Agent - Comandos Disponiveis"
	@echo "====================================="
	@echo "  help        Mostra esta ajuda"
	@echo "  setup       Configura projeto"
	@echo "  start       Inicia servicos"
	@echo "  stop        Para servicos"
	@echo "  status      Mostra status"
	@echo "  quick-start Configuracao rapida"
	@echo ""
	@echo "Comandos com LOGS visiveis:"
	@echo "  logs            FastAPI com logs"
	@echo "  logs-dashboard  Dashboard com logs"
	@echo "  logs-costs      Custos com logs"
	@echo "  logs-tail       Segue logs existentes"
	@echo "  logs-tmux       Inicia em tmux"

setup:
	@echo "Configurando projeto..."
	@mkdir -p logs .pids
	@echo "Projeto configurado"

start:
	@echo "Iniciando WhatsApp Agent..."
	@./manage.py start

stop:
	@echo "Parando servicos..."
	@./manage.py stop

status:
	@./manage.py status

quick-start: setup start
	@echo "Dashboard: http://localhost:8501"
	@echo "Custos: http://localhost:8502"
	@echo "API: http://localhost:8000/docs"

logs:
	@echo "🚀 FastAPI com logs - http://localhost:8000/docs"
	@./start_logs.py fastapi

logs-dashboard:
	@echo "📊 Dashboard com logs - http://localhost:8501"
	@./start_logs.py dashboard

logs-costs:
	@echo "💰 Custos com logs - http://localhost:8502"
	@./start_logs.py costs

logs-tail:
	@echo "📋 Seguindo logs..."
	@./start_logs.py tail

logs-tmux:
	@echo "🚀 Iniciando em tmux..."
	@./start_with_logs.sh tmux
