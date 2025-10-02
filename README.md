# WhatsApp Agent API

Sistema completo de integração com WhatsApp Business API com dashboard web e funcionalidades avançadas.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.8+
- PostgreSQL
- Node.js 18+ (para dashboard)

### Instalação

#### Backend
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
alembic upgrade head

# Executar servidor
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (Dashboard)
```bash
cd nextjs_dashboard
npm install
npm run dev
```

## 📁 Estrutura do Projeto

```
whats_agent/
├── app/                    # Código principal do backend
├── nextjs_dashboard/       # Dashboard web (Next.js)
├── docs/                  # Documentação
├── config/                # Configurações
├── archive/               # Arquivos arquivados
└── backup/                # Backups de segurança
```

## 🔧 Comandos Disponíveis

- `start_server.sh` - Iniciar servidor
- `stop_server.sh` - Parar servidor

## 📚 Documentação

- `docs/` - Documentação completa
- `docs/reports/` - Relatórios de auditoria
- `docs/audit/` - Documentação de auditoria

## 🔒 Segurança

O sistema possui score de segurança de 88.89% com:
- Credenciais seguras
- Logs sanitizados
- Webhooks consolidados
- Performance otimizada

## 📊 Monitoramento

- Métricas em tempo real
- Logs estruturados
- Alertas automáticos
- Dashboard de performance

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.
