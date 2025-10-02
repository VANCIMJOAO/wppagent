#!/bin/bash

# Script para iniciar o servidor WhatsApp Agent em background
# Este script garante que o servidor rode independentemente do terminal

echo "🚀 Iniciando WhatsApp Agent Server..."

# Parar processos existentes
echo "🛑 Parando processos existentes..."
pkill -f uvicorn 2>/dev/null || true
sleep 2

# Navegar para o diretório do projeto
cd /home/vancim/whats_agent

# Verificar se o ambiente virtual está ativo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Ambiente virtual não detectado. Ativando..."
    source /home/vancim/anaconda3/bin/activate
fi

# Criar arquivo de log com timestamp
LOG_FILE="logs/server_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "📝 Logs serão salvos em: $LOG_FILE"

# Configurar variáveis de ambiente
export REDIS_URL="redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"
export DATABASE_URL="postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
export ENVIRONMENT="development"
export SECRET_KEY="dev-secret-key"
export JWT_SECRET="dev-jwt-secret"
export DEBUG="True"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"

# Iniciar servidor em background com nohup
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &

# Salvar PID do processo
SERVER_PID=$!
echo "$SERVER_PID" > server.pid

echo "✅ Servidor iniciado com PID: $SERVER_PID"
echo "🌐 URL: http://localhost:8000"
echo "📱 Webhook: http://localhost:8000/webhook"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Para parar o servidor: ./stop_server.sh"
echo "Para ver logs: tail -f $LOG_FILE"
echo "Para verificar status: ./check_server.sh"

# Aguardar um pouco para verificar se iniciou corretamente
sleep 3

# Verificar se o processo ainda está rodando
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Servidor iniciado com sucesso!"
    
    # Testar se está respondendo
    echo "🔍 Testando conectividade..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Servidor respondendo corretamente!"
    else
        echo "⚠️  Servidor iniciado mas não está respondendo ainda. Aguarde alguns segundos."
    fi
else
    echo "❌ Erro ao iniciar servidor. Verifique os logs: $LOG_FILE"
    exit 1
fi
