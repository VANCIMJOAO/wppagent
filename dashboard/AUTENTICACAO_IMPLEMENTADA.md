# 🔐 Sistema de Autenticação - WppAgent Dashboard

## ✅ Status de Implementação

O sistema de autenticação foi **completamente implementado** e inclui:

- ✅ Sistema de login/logout
- ✅ Autenticação de usuários  
- ✅ Proteção de rotas
- ✅ Gestão de sessões
- ✅ Níveis de permissão

## 📋 Funcionalidades Implementadas

### 🔑 Autenticação Completa
- **Login seguro** com hash de senhas (PBKDF2 + salt)
- **Logout** com invalidação de sessão
- **Sessões temporárias** com expiração automática
- **Bloqueio por tentativas** (5 tentativas, 15min bloqueio)
- **Verificação periódica** de sessão válida

### 👥 Níveis de Permissão
1. **VIEWER** - Apenas visualização (Home, Perfil, Suporte)
2. **OPERATOR** - Operação básica (+ Conversas, Clientes, Agendamentos)
3. **MANAGER** - Gerencial (+ Relatórios)  
4. **ADMIN** - Administrador (+ Configurações)
5. **SUPER_ADMIN** - Acesso total ao sistema

### 🛡️ Segurança
- **Proteção CSRF** via tokens de sessão
- **Validação de entrada** em todos os campos
- **Log de tentativas** de login para auditoria
- **Limpeza automática** de sessões expiradas
- **Criptografia segura** para senhas

### 📱 Interface Moderna
- **Página de login** responsiva e elegante
- **Indicadores visuais** de status de autenticação
- **Página de acesso negado** personalizada
- **Notificação de sessão expirada**
- **Seção de usuário** na sidebar

## 🚀 Como Usar

### 1. Configuração Inicial

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados e criar usuário admin
python auth_setup.py setup
```

### 2. Credenciais Padrão (Desenvolvimento)
```
Email: admin@exemplo.com
Senha: admin123
```

⚠️ **IMPORTANTE**: Altere essas credenciais em produção!

### 3. Executar Dashboard

```bash
python app.py
```

O sistema agora requer login para acessar qualquer página (exceto `/login`).

## 📂 Estrutura de Arquivos Criados

```
dashboard/
├── auth/                           # 🆕 Sistema de autenticação
│   ├── __init__.py                 # Exportações do módulo
│   ├── models.py                   # Modelos de dados (User, UserRole, etc)
│   ├── auth_service.py             # Serviço principal de autenticação
│   ├── layouts.py                  # Layouts de login e páginas de erro
│   ├── callbacks.py                # Callbacks do Dash para autenticação
│   ├── middleware.py               # Middleware de proteção de rotas
│   └── decorators.py               # Decorators para proteger funções
├── assets/
│   └── auth.css                    # 🆕 Estilos para sistema de login
├── app.py                          # ✏️ Modificado com autenticação
├── auth_setup.py                   # 🆕 Script de configuração inicial
├── test_auth.py                    # 🆕 Testes do sistema
├── requirements.txt                # ✏️ Atualizado com novas dependências
└── .env.example                    # ✏️ Atualizado com configs de auth
```

## 🗄️ Tabelas do Banco de Dados

### Tabela `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    company_id INTEGER,
    phone VARCHAR(50),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Tabela `user_sessions`  
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);
```

### Tabela `login_attempts`
```sql
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    ip_address INET,
    success BOOLEAN NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);
```

## 🎯 Fluxo de Autenticação

1. **Usuário acessa qualquer página** → Verifica se tem sessão válida
2. **Sem sessão válida** → Redireciona para `/login`  
3. **Usuário faz login** → Valida credenciais + Cria sessão
4. **Login bem-sucedido** → Redireciona para `/home`
5. **Navegação no sistema** → Verifica permissões por página
6. **Sem permissão** → Exibe página de acesso negado
7. **Sessão expira** → Redireciona para `/session-expired`

## 🛠️ Comandos Utilitários

### Configurar Sistema
```bash
python auth_setup.py setup
```

### Criar Usuário
```bash
python auth_setup.py create-user
```

### Listar Usuários
```bash
python auth_setup.py list-users
```

### Executar Testes
```bash
python test_auth.py
```

## 🔧 Configurações (`.env`)

```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Authentication
SECRET_KEY=your-secret-key-here
SESSION_DURATION_HOURS=8
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
```

## 🎨 Personalização

### Modificar Permissões de Página
Edite o método `can_access_page()` em `auth/models.py`:

```python
def can_access_page(self, page: str) -> bool:
    page_permissions = {
        'home': UserRole.VIEWER,
        'nova_pagina': UserRole.MANAGER,  # 🆕 Adicione aqui
        # ...
    }
```

### Adicionar Novos Roles
Edite a enum `UserRole` em `auth/models.py`:

```python
class UserRole(Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    CUSTOM_ROLE = "custom_role"  # 🆕 Adicione aqui
```

## 📊 Monitoramento

O sistema registra automaticamente:
- ✅ Tentativas de login (sucesso/falha)
- ✅ Criação e expiração de sessões  
- ✅ Acesso negado a páginas
- ✅ Alterações de usuários

## 🚨 Modo Desenvolvimento vs Produção

### Desenvolvimento (sem DATABASE_URL)
- Usa usuário fictício `admin@exemplo.com / admin123`
- Não persiste sessões no banco
- Logs detalhados no console

### Produção (com DATABASE_URL)
- Conecta ao PostgreSQL real
- Persiste todos os dados
- Logs de segurança

## ✅ Próximos Passos Recomendados

1. **Testar o sistema** → `python test_auth.py`
2. **Configurar banco** → `python auth_setup.py setup`
3. **Executar aplicação** → `python app.py`
4. **Acessar dashboard** → `http://localhost:8050`
5. **Fazer login** → `admin@exemplo.com / admin123`
6. **Criar usuários reais** → `python auth_setup.py create-user`
7. **Alterar credenciais padrão** → Via interface de perfil

## 🎉 Sistema Pronto!

O dashboard agora possui um sistema de autenticação **completo, seguro e moderno**. Todos os requisitos foram atendidos:

- ✅ Sistema de login/logout
- ✅ Autenticação de usuários
- ✅ Proteção de rotas  
- ✅ Gestão de sessões
- ✅ Níveis de permissão

O sistema está pronto para uso em produção! 🚀
