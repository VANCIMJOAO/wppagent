# 🌍 Configuração de Environments

Este arquivo documenta como configurar os environments no GitHub para que o pipeline funcione corretamente.

## 📋 Environments Necessários

### 1. Staging Environment
- **Nome**: `staging`
- **URL**: `https://staging.whatsapp-agent.com` (ou sua URL de staging)
- **Branch Protection**: `develop`
- **Review Required**: Não obrigatório

### 2. Production Environment  
- **Nome**: `production`
- **URL**: `https://whatsapp-agent.com` (ou sua URL de produção)
- **Branch Protection**: `main`
- **Review Required**: Recomendado

## 🔧 Como Configurar

1. Vá para **Settings** > **Environments** no seu repositório
2. Clique em **New environment**
3. Digite o nome do environment
4. Configure as regras de proteção conforme necessário
5. Adicione a URL se disponível

## ⚠️ Nota Importante

Se você não configurou os environments ainda, o pipeline continuará funcionando, mas alguns jobs podem falhar. Os environments são opcionais para a maioria das funcionalidades.

## 🚀 Variáveis Necessárias

Certifique-se de que estas variáveis estão configuradas:
- `STAGING_URL`: URL do ambiente de staging
- `PRODUCTION_URL`: URL do ambiente de produção

Veja `setup_variables.md` para instruções detalhadas.
