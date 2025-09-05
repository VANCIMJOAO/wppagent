#!/bin/bash

echo "🚀 Configurando Dashboard Next.js + WhatsApp..."

# Instalar dependências
echo "📦 Instalando dependências..."
npm install

# Verificar se o Tailwind está configurado
if [ ! -f "tailwind.config.js" ]; then
    echo "⚙️ Configurando Tailwind CSS..."
    npx tailwindcss init -p
fi

echo "✅ Setup completo!"
echo ""
echo "🎯 Para executar o projeto:"
echo "   npm run dev"
echo ""
echo "🌐 Acesse: http://localhost:3000"
echo ""
echo "📋 Funcionalidades implementadas:"
echo "   ✅ Sistema de Login/Autenticação"
echo "   ✅ Dashboard com métricas"
echo "   ✅ Página de Conversas (chat completo)"
echo "   ✅ Página de Perfil (configurações do usuário)"
echo "   ✅ Página de Relatórios (gráficos e analytics)"
echo "   ✅ Layout responsivo"
echo "   ✅ Sidebar com navegação"
echo "   ✅ Componentes modernos (Shadcn/ui)"
echo ""