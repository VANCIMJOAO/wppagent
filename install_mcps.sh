#!/bin/bash

# 🚀 Script de Instalação dos MCPs Essenciais para WhatsApp Agent
# Autor: Claude Assistant
# Data: $(date)

echo "🚀 Instalando MCPs essenciais para o projeto WhatsApp Agent..."

# Criar diretório para MCPs se não existir
mkdir -p ~/.config/claude-mcps

# Fase 1 - MCPs Essenciais
echo "📥 Instalando MCPs da Fase 1 (Essenciais)..."

# GitHub MCP
echo "  - Instalando GitHub MCP..."
npm install -g @modelcontextprotocol/server-github

# Postgres MCP  
echo "  - Instalando Postgres MCP..."
npm install -g @modelcontextprotocol/server-postgres

# Docker MCP
echo "  - Instalando Docker MCP..."
npm install -g @modelcontextprotocol/server-docker

# Fase 2 - MCPs de Desenvolvimento
echo "📥 Instalando MCPs da Fase 2 (Desenvolvimento)..."

# Testing MCP
echo "  - Instalando Testing MCP..."
npm install -g @modelcontextprotocol/server-testing

# Time MCP
echo "  - Instalando Time MCP..."
npm install -g @modelcontextprotocol/server-time

# Memory MCP
echo "  - Instalando Memory MCP..."
npm install -g @modelcontextprotocol/server-memory

# Criar arquivo de configuração
echo "⚙️ Criando arquivo de configuração..."

cat > ~/.config/claude-mcps/config.json << EOF
{
  "mcps": {
    "github": {
      "repository": "vancim/whats_agent",
      "default_branch": "main"
    },
    "postgres": {
      "host": "localhost",
      "port": 5432,
      "database": "whatsapp_agent",
      "user": "vancimj"
    },
    "docker": {
      "socket": "/var/run/docker.sock",
      "compose_file": "/home/vancim/whats_agent/docker-compose.yml"
    },
    "project": {
      "name": "WhatsApp Agent",
      "type": "fastapi",
      "tech_stack": ["python", "fastapi", "postgresql", "redis", "docker"],
      "monitoring": ["grafana", "prometheus"],
      "deployment": "railway"
    }
  }
}
EOF

echo "✅ Instalação concluída!"
echo ""
echo "🔧 Próximos passos:"
echo "1. Configure suas credenciais do GitHub"
echo "2. Teste a conexão com PostgreSQL"
echo "3. Verifique se o Docker está rodando"
echo ""
echo "💡 Agora você pode usar comandos como:"
echo "  - 'Claude, faça commit das mudanças'"
echo "  - 'Claude, analise a performance do banco'"
echo "  - 'Claude, verifique os containers Docker'"
echo ""
echo "🚀 Seu projeto WhatsApp Agent está agora super-powered com MCPs!"
