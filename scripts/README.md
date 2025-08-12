# 🚀 WhatsApp Agent - Scripts de Gestão Completa

Este diretório contém todos os scripts necessários para gerenciar completamente a aplicação WhatsApp Agent.

## 📋 Scripts Disponíveis

### 🎯 Script Principal
- **`whatsapp_agent_manager.sh`** - Menu interativo completo para gestão da aplicação

### 🔧 Scripts de Operação
- **`start_complete_application.sh`** - Inicia toda a aplicação (todos os componentes)
- **`stop_complete_application.sh`** - Para toda a aplicação com opções de limpeza
- **`monitor_application.sh`** - Monitor em tempo real de todos os componentes
- **`quick_status.sh`** - Status rápido da aplicação

### 🛠️ Scripts de Utilidade
- **`cleanup_project_final.sh`** - Organização e limpeza do projeto
- **`analyze_database.py`** - Análise da estrutura do banco de dados

## 🚀 Uso Rápido

### Menu Interativo (Recomendado)
```bash
cd /home/vancim/whats_agent
./whatsapp_agent_manager.sh
```

### Comandos Diretos
```bash
# Iniciar aplicação completa
./whatsapp_agent_manager.sh start

# Parar aplicação
./whatsapp_agent_manager.sh stop

# Status rápido
./whatsapp_agent_manager.sh status

# Monitor em tempo real
./whatsapp_agent_manager.sh monitor

# Ver logs
./whatsapp_agent_manager.sh logs
```

### Scripts Individuais
```bash
# Iniciar tudo
./scripts/start_complete_application.sh

# Monitor completo
./scripts/monitor_application.sh

# Monitor específico
./scripts/monitor_application.sh containers  # Apenas containers
./scripts/monitor_application.sh resources   # Apenas recursos
./scripts/monitor_application.sh logs       # Apenas logs

# Parar com opções
./scripts/stop_complete_application.sh --force    # Parada forçada
./scripts/stop_complete_application.sh --clean    # Remove dados

# Análise do banco
python scripts/analyze_database.py
```

---

**🎉 WhatsApp Agent está pronto para uso!**

*Desenvolvido com ❤️ para automação empresarial inteligente.*
