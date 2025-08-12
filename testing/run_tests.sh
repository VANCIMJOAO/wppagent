#!/bin/bash
# Script para executar a suite completa de testes do WhatsApp Agent

echo "🧪 WhatsApp Agent - Comprehensive Test Suite"
echo "============================================="
echo ""

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Execute primeiro:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Verificar se o PostgreSQL está rodando
if ! pgrep -x "postgres" > /dev/null; then
    echo "⚠️ PostgreSQL não está rodando. Iniciando..."
    sudo systemctl start postgresql || {
        echo "❌ Falha ao iniciar PostgreSQL"
        exit 1
    }
fi

# Criar diretórios necessários
mkdir -p logs test_reports

# Instalar dependências de teste se necessário
echo "📦 Verificando dependências de teste..."
./venv/bin/pip install -q -r requirements-test.txt

# Executar os testes
echo "🚀 Iniciando execução dos testes..."
echo ""

./venv/bin/python comprehensive_test_suite.py

echo ""
echo "✅ Testes concluídos!"
echo "📋 Verifique os relatórios em: test_reports/"
echo "📝 Logs em: logs/test_suite.log"
