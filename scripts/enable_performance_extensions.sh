#!/bin/bash
# Script para habilitar extensões necessárias para análise de performance
# WhatsApp Agent - Database Performance Extensions

echo "🔧 Habilitando extensões de performance no PostgreSQL..."

# Configurações do banco
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-whatsapp_agent}"
DB_USER="${DB_USER:-postgres}"

# Verificar se as variáveis estão definidas
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Erro: Defina a variável DB_PASSWORD"
    echo "Exemplo: export DB_PASSWORD='sua_senha'"
    exit 1
fi

echo "🔍 Verificando extensões atuais..."

# Função para executar SQL
execute_sql() {
    local sql="$1"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
}

# Verificar extensões existentes
echo "📋 Extensões atualmente instaladas:"
execute_sql "SELECT extname, extversion FROM pg_extension ORDER BY extname;"

echo ""
echo "🚀 Habilitando pg_stat_statements..."

# Habilitar pg_stat_statements
execute_sql "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

if [ $? -eq 0 ]; then
    echo "✅ pg_stat_statements habilitado com sucesso"
else
    echo "❌ Erro ao habilitar pg_stat_statements"
    echo ""
    echo "🔧 Possíveis soluções:"
    echo "1. Verificar se o módulo está carregado no postgresql.conf:"
    echo "   shared_preload_libraries = 'pg_stat_statements'"
    echo ""
    echo "2. Reiniciar o PostgreSQL após adicionar ao postgresql.conf"
    echo ""
    echo "3. Verificar se o pacote postgresql-contrib está instalado"
    exit 1
fi

echo ""
echo "🔧 Habilitando outras extensões úteis..."

# Habilitar outras extensões úteis
execute_sql "CREATE EXTENSION IF NOT EXISTS pgstattuple;" 2>/dev/null
execute_sql "CREATE EXTENSION IF NOT EXISTS pg_buffercache;" 2>/dev/null
execute_sql "CREATE EXTENSION IF NOT EXISTS pgcrypto;" 2>/dev/null

echo ""
echo "📊 Verificando status final das extensões:"
execute_sql "
SELECT 
    extname as \"Extensão\",
    extversion as \"Versão\",
    CASE 
        WHEN extname = 'pg_stat_statements' THEN '📈 Análise de queries lentas'
        WHEN extname = 'pgstattuple' THEN '📊 Estatísticas de tuplas'
        WHEN extname = 'pg_buffercache' THEN '💾 Análise de cache'
        WHEN extname = 'pgcrypto' THEN '🔐 Funções criptográficas'
        ELSE '⚙️ Outras funcionalidades'
    END as \"Descrição\"
FROM pg_extension 
WHERE extname IN ('pg_stat_statements', 'pgstattuple', 'pg_buffercache', 'pgcrypto')
ORDER BY extname;
"

echo ""
echo "🎯 Extensões de performance configuradas!"
echo ""
echo "📝 Próximos passos:"
echo "1. Execute a análise de performance novamente"
echo "2. As estatísticas de pg_stat_statements começarão a ser coletadas"
echo "3. Aguarde algumas consultas serem executadas para obter dados"

# Verificar se precisa reiniciar
shared_preload=$(execute_sql "SHOW shared_preload_libraries;" 2>/dev/null | grep pg_stat_statements)
if [ -z "$shared_preload" ]; then
    echo ""
    echo "⚠️  IMPORTANTE:"
    echo "Para que pg_stat_statements funcione completamente, adicione ao postgresql.conf:"
    echo "shared_preload_libraries = 'pg_stat_statements'"
    echo "E reinicie o PostgreSQL"
fi

echo ""
echo "✅ Script de extensões concluído!"
