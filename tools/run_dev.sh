#!/bin/bash

# Script para executar o WhatsApp Agent em desenvolvimento
# run_dev.sh

set -e  # Parar execução se houver erro

echo "🚀 Iniciando WhatsApp Agent - Ambiente de Desenvolvimento"
echo "======================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script do diretório raiz do projeto${NC}"
    exit 1
fi

# Verificar se o venv existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment não encontrado. Criando...${NC}"
    python3.12 -m venv venv
    echo -e "${GREEN}✅ Virtual environment criado${NC}"
fi

# Ativar virtual environment
echo -e "${BLUE}🔧 Ativando virtual environment...${NC}"
source venv/bin/activate

# Verificar se as dependências estão instaladas
echo -e "${BLUE}📦 Verificando dependências...${NC}"
pip install -r requirements.txt --upgrade

# Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Copiando exemplo...${NC}"
    cp .env.example .env
    echo -e "${RED}❌ IMPORTANTE: Configure o arquivo .env antes de continuar!${NC}"
    echo -e "${YELLOW}   Edite as variáveis de ambiente necessárias.${NC}"
    exit 1
fi

# Carregar variáveis de ambiente
source .env

# Verificar variáveis essenciais
if [ -z "$META_ACCESS_TOKEN" ] || [ "$META_ACCESS_TOKEN" = "YOUR_META_TOKEN_HERE" ]; then
    echo -e "${RED}❌ Erro: Configure META_ACCESS_TOKEN no arquivo .env${NC}"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "YOUR_OPENAI_API_KEY_HERE" ]; then
    echo -e "${RED}❌ Erro: Configure OPENAI_API_KEY no arquivo .env${NC}"
    exit 1
fi

# Verificar se PostgreSQL está rodando
echo -e "${BLUE}🗄️  Verificando PostgreSQL...${NC}"
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -q; then
    echo -e "${RED}❌ Erro: PostgreSQL não está acessível${NC}"
    echo -e "${YELLOW}   Verifique se o PostgreSQL está rodando e as credenciais estão corretas${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL conectado${NC}"

# Executar migrações do banco
echo -e "${BLUE}🗄️  Executando migrações do banco...${NC}"
alembic upgrade head

# Iniciar ngrok se NGROK_AUTHTOKEN estiver configurado
NGROK_PID=""
if [ ! -z "$NGROK_AUTHTOKEN" ] && [ "$NGROK_AUTHTOKEN" != "YOUR_NGROK_AUTHTOKEN_HERE" ]; then
    echo -e "${BLUE}🌐 Iniciando ngrok...${NC}"
    
    # Configurar ngrok auth token
    ngrok config add-authtoken $NGROK_AUTHTOKEN
    
    # Iniciar ngrok em background
    ngrok http --domain=testewebhook.ngrok.dev $APP_PORT > /dev/null 2>&1 &
    NGROK_PID=$!
    
    # Aguardar ngrok inicializar
    sleep 3
    
    # Obter URL do ngrok
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('ERROR')
")
    
    if [ "$NGROK_URL" != "ERROR" ]; then
        echo -e "${GREEN}✅ Ngrok iniciado: $NGROK_URL${NC}"
        export WEBHOOK_URL="$NGROK_URL/webhook"
        echo -e "${BLUE}📡 Webhook URL: $WEBHOOK_URL${NC}"
        echo -e "${YELLOW}⚠️  Configure esta URL no Facebook Developer Console${NC}"
    else
        echo -e "${RED}❌ Erro ao iniciar ngrok${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  NGROK_AUTHTOKEN não configurado - ngrok não iniciado${NC}"
    echo -e "${YELLOW}   Configure manualmente o webhook URL: http://localhost:$APP_PORT/webhook${NC}"
fi

# Função para limpeza quando script for interrompido
cleanup() {
    echo -e "\n${YELLOW}🧹 Limpando processos...${NC}"
    
    # Parar FastAPI
    if [ ! -z "$FASTAPI_PID" ]; then
        kill $FASTAPI_PID 2>/dev/null || true
    fi
    
    # Parar Streamlit
    if [ ! -z "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null || true
    fi
    
    # Parar ngrok
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Limpeza concluída${NC}"
    exit 0
}

# Registrar função de limpeza para SIGINT (Ctrl+C)
trap cleanup SIGINT

# Iniciar FastAPI
echo -e "${BLUE}🚀 Iniciando servidor FastAPI na porta $APP_PORT...${NC}"
python -m uvicorn app.main:app --host $APP_HOST --port $APP_PORT --reload > logs/fastapi.log 2>&1 &
FASTAPI_PID=$!

# Aguardar FastAPI inicializar
sleep 5

# Verificar se FastAPI está rodando
if curl -s http://localhost:$APP_PORT/health > /dev/null; then
    echo -e "${GREEN}✅ FastAPI iniciado com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar FastAPI${NC}"
    echo -e "${YELLOW}📄 Verificando logs...${NC}"
    tail -n 20 logs/fastapi.log
    cleanup
    exit 1
fi

# Iniciar Streamlit Dashboard
echo -e "${BLUE}📊 Iniciando dashboard Streamlit na porta $STREAMLIT_PORT...${NC}"
mkdir -p logs
streamlit run dashboard/main.py --server.port $STREAMLIT_PORT --server.headless true > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!

# Aguardar um pouco
sleep 2

echo -e "${GREEN}"
echo "✅ WhatsApp Agent iniciado com sucesso!"
echo "======================================"
echo -e "${NC}"
echo -e "${BLUE}📱 API FastAPI:${NC} http://localhost:$APP_PORT"
echo -e "${BLUE}📊 Dashboard:${NC} http://localhost:$STREAMLIT_PORT"
if [ ! -z "$NGROK_URL" ]; then
    echo -e "${BLUE}🌐 Webhook URL:${NC} $WEBHOOK_URL"
fi
echo ""
echo -e "${YELLOW}📋 Para parar os serviços, pressione Ctrl+C${NC}"
echo -e "${YELLOW}📄 Logs em: logs/fastapi.log e logs/streamlit.log${NC}"
echo ""

# Aguardar indefinidamente (até Ctrl+C)
while true; do
    sleep 1
done
