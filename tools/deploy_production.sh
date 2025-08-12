#!/bin/bash
# Script de deploy completo para produção
# WhatsApp Agent - Docker Compose com SSL

set -e

echo "🚀 DEPLOY COMPLETO DO WHATSAPP AGENT"
echo "===================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instalando..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker instalado"
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose instalado"
fi

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado"
    if [ -f ".env.example" ]; then
        echo "📝 Copiando .env.example para .env"
        cp .env.example .env
        echo "⚠️  Configure as variáveis em .env antes de continuar"
        exit 1
    else
        echo "❌ Arquivo .env.example também não encontrado"
        exit 1
    fi
fi

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p logs/nginx
mkdir -p config/nginx/ssl
mkdir -p backups/database

# Gerar certificados SSL se não existirem
if [ ! -f "config/nginx/ssl/server.crt" ] || [ ! -f "config/nginx/ssl/server.key" ]; then
    echo "🔐 Gerando certificados SSL..."
    ./scripts/generate_ssl_certs.sh
fi

# Construir e iniciar containers
echo "🏗️  Construindo containers..."
docker-compose build --no-cache

echo "🚀 Iniciando serviços..."
docker-compose up -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 30

# Verificar status dos serviços
echo "📊 Verificando status dos serviços..."
docker-compose ps

# Executar migrações do banco
echo "🔄 Executando migrações do banco..."
docker-compose exec app python manage.py migrate

# Criar usuário admin se não existir
echo "👤 Verificando usuário admin..."
docker-compose exec app python scripts/create_admin_user.py

# Verificar health checks
echo "🏥 Verificando health checks..."
sleep 10

# Testar endpoints
echo "🧪 Testando endpoints..."

# Test API health
if curl -f -k https://localhost/health &> /dev/null; then
    echo "✅ API health check: OK"
else
    echo "❌ API health check: FALHOU"
fi

# Test dashboard
if curl -f -k https://localhost/dashboard/ &> /dev/null; then
    echo "✅ Dashboard: OK"
else
    echo "❌ Dashboard: FALHOU"
fi

# Mostrar logs se houver problemas
if [ $? -ne 0 ]; then
    echo "❌ Alguns serviços falharam. Verificando logs..."
    docker-compose logs --tail=20
fi

echo ""
echo "🎉 DEPLOY FINALIZADO!"
echo "===================="
echo ""
echo "🌐 URLs disponíveis:"
echo "   📡 API Principal: https://localhost/api/"
echo "   📊 Dashboard: https://localhost/dashboard/"
echo "   📈 Prometheus: http://localhost:9090"
echo "   📊 Grafana: http://localhost:3000"
echo ""
echo "🔧 Comandos úteis:"
echo "   docker-compose logs -f                 # Ver logs em tempo real"
echo "   docker-compose restart                 # Reiniciar todos os serviços"
echo "   docker-compose down                    # Parar todos os serviços"
echo "   docker-compose exec app bash           # Acessar container da aplicação"
echo "   docker-compose exec postgres psql -U vancimj whatsapp_agent  # Acessar banco"
echo ""
echo "📚 Documentação:"
echo "   /docs     - Swagger UI da API"
echo "   /redoc    - ReDoc da API"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Configure seu domínio no nginx.conf para produção"
echo "   - Use certificados Let's Encrypt para produção"
echo "   - Configure firewall adequadamente"
echo "   - Monitore logs regularmente"
