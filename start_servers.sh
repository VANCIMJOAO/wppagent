#!/bin/bash

# Script para iniciar ambos os servidores (Backend FastAPI + Frontend Next.js)

echo "🚀 Iniciando servidores WhatsApp Agent..."

# Configurar variáveis de ambiente
export DATABASE_URL="postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
export REDIS_URL="redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"
export JWT_SECRET="your_jwt_secret_here_change_in_production"

echo "✅ Variáveis de ambiente configuradas"

# Verificar se o backend já está rodando
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ Backend já está rodando na porta 8000"
else
    echo "🔧 Iniciando backend FastAPI..."
    cd /home/vancim/whats_agent
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo "✅ Backend iniciado com PID: $BACKEND_PID"
fi

# Aguardar o backend inicializar
echo "⏳ Aguardando backend inicializar..."
sleep 5

# Verificar se o frontend já está rodando
if pgrep -f "next.*dev" > /dev/null; then
    echo "✅ Frontend já está rodando na porta 3000"
else
    echo "🔧 Iniciando frontend Next.js..."
    cd /home/vancim/whats_agent/nextjs_dashboard
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend iniciado com PID: $FRONTEND_PID"
fi

echo ""
echo "🎉 Servidores iniciados com sucesso!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 Docs:     http://localhost:8000/docs"
echo ""
echo "Para parar os servidores, use: pkill -f 'uvicorn\|next'"
echo "Ou pressione Ctrl+C neste terminal"
