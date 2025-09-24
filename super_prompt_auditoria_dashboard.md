# 🚀 SUPER PROMPT - AUDITORIA PROFUNDA DO DASHBOARD WHATSAPP AGENT

## 📋 CONTEXTO DA MISSÃO

Você está sendo convocado para realizar uma **auditoria técnica completa e profunda** do sistema WhatsApp Agent Dashboard. Este é um sistema Next.js com integração PostgreSQL que gerencia conversas WhatsApp, agendamentos e configurações de negócios.

## 🎯 OBJETIVOS DA AUDITORIA

### **PRIMÁRIOS:**
1. **Identificar bugs críticos** que podem quebrar o sistema
2. **Detectar inconsistências de dados** entre frontend e backend
3. **Avaliar segurança** e vulnerabilidades
4. **Verificar performance** e otimizações necessárias
5. **Validar integridade** dos dados e relacionamentos

### **SECUNDÁRIOS:**
1. **Sugerir melhorias** de UX/UI
2. **Otimizar consultas** de banco de dados
3. **Padronizar código** e arquitetura
4. **Documentar problemas** encontrados

## 🔧 FERRAMENTAS DISPONÍVEIS

### **✅ USE ESTAS FERRAMENTAS:**
- **`filesystem`** - Para analisar arquivos do projeto
- **`postgres`** - Para consultar e analisar a database
- **`desktop-commander`** - Para executar comandos no terminal Linux

### **❌ NÃO USE ESTAS:**
- `github` - Não relevante para esta auditoria
- `grafana` - Não relevante para esta auditoria  
- `powerpoint` - Não relevante para esta auditoria

## 🚨 REGRAS CRÍTICAS

### **⚠️ RESTRIÇÕES IMPORTANTES:**
- **NÃO CRIE** novos arquivos
- **NÃO EDITE** arquivos existentes
- **NÃO ESCREVA** código
- **APENAS LEIA** e **ANALISE**
- **RETORNE** apenas relatórios e análises

## 📊 DADOS DA AUDITORIA ANTERIOR

### **Database PostgreSQL:**
```
Connection: postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway
```

### **Problemas Críticos Identificados:**
1. **116 usuários sem email** (100% dos usuários)
2. **2 usuários sem nome**
3. **2,115 mensagens para apenas 39 conversas únicas**
4. **3,971 registros em meta_logs** (volume excessivo)
5. **1,583 sessões de login** (possível vazamento)

### **Estrutura do Banco:**
- **33 tabelas** com relacionamentos complexos
- **Integridade referencial** mantida
- **0 dados órfãos** detectados
- **Timestamps consistentes**

## 🔍 PLANO DE AUDITORIA DETALHADO

### **FASE 1: ANÁLISE DE ARQUIVOS (filesystem)**
1. **Estrutura do Projeto:**
   - Analisar organização de pastas
   - Verificar arquivos de configuração
   - Identificar dependências

2. **Código Frontend:**
   - Analisar componentes React
   - Verificar hooks e estados
   - Identificar problemas de performance

3. **APIs Backend:**
   - Verificar rotas Next.js
   - Analisar validações de dados
   - Identificar vulnerabilidades

4. **Configurações:**
   - Verificar variáveis de ambiente
   - Analisar configurações de banco
   - Identificar secrets expostos

### **FASE 2: ANÁLISE DE DATABASE (postgres)**
1. **Consultas Complexas:**
   - Verificar performance de queries
   - Identificar consultas lentas
   - Analisar índices necessários

2. **Integridade de Dados:**
   - Validar relacionamentos
   - Verificar constraints
   - Identificar dados inconsistentes

3. **Segurança:**
   - Verificar permissões
   - Analisar logs de acesso
   - Identificar tentativas de invasão

### **FASE 3: TESTES DE SISTEMA (desktop-commander)**
1. **Comandos de Verificação:**
   - Testar conectividade com banco
   - Verificar logs do sistema
   - Analisar performance do servidor

2. **Validações:**
   - Verificar integridade de arquivos
   - Testar dependências
   - Validar configurações

## 📋 CHECKLIST DE AUDITORIA

### **🔒 SEGURANÇA:**
- [ ] Verificar exposição de secrets
- [ ] Analisar validações de input
- [ ] Verificar autenticação/autorização
- [ ] Identificar vulnerabilidades SQL injection
- [ ] Verificar CORS e headers de segurança

### **⚡ PERFORMANCE:**
- [ ] Analisar consultas lentas
- [ ] Verificar uso de memória
- [ ] Identificar vazamentos de recursos
- [ ] Analisar bundle size do frontend
- [ ] Verificar otimizações de imagem

### **🐛 BUGS E ERROS:**
- [ ] Verificar tratamento de erros
- [ ] Analisar logs de erro
- [ ] Identificar race conditions
- [ ] Verificar validações de dados
- [ ] Analisar edge cases

### **📊 INTEGRIDADE DE DADOS:**
- [ ] Verificar consistência entre tabelas
- [ ] Analisar dados órfãos
- [ ] Verificar timestamps
- [ ] Validar relacionamentos
- [ ] Identificar dados duplicados

### **🎨 UX/UI:**
- [ ] Verificar responsividade
- [ ] Analisar acessibilidade
- [ ] Identificar problemas de usabilidade
- [ ] Verificar consistência visual
- [ ] Analisar performance de carregamento

## 📝 FORMATO DO RELATÓRIO

### **ESTRUTURA OBRIGATÓRIA:**
```markdown
# 🚨 RELATÓRIO DE AUDITORIA - DASHBOARD WHATSAPP AGENT

## 📊 RESUMO EXECUTIVO
- Problemas críticos encontrados: X
- Problemas de segurança: X
- Problemas de performance: X
- Recomendações prioritárias: X

## 🔥 PROBLEMAS CRÍTICOS
### [Categoria] - [Título]
- **Severidade:** Crítica/Alta/Média/Baixa
- **Localização:** [Arquivo/Query/Componente]
- **Descrição:** [Explicação detalhada]
- **Impacto:** [Consequências]
- **Solução:** [Como corrigir]

## 🔒 PROBLEMAS DE SEGURANÇA
[Detalhes de vulnerabilidades]

## ⚡ PROBLEMAS DE PERFORMANCE
[Detalhes de performance]

## 🐛 BUGS IDENTIFICADOS
[Detalhes de bugs]

## 📊 INCONSISTÊNCIAS DE DADOS
[Detalhes de dados]

## 🎯 RECOMENDAÇÕES PRIORITÁRIAS
1. [Recomendação 1]
2. [Recomendação 2]
3. [Recomendação 3]

## 📈 MÉTRICAS E ESTATÍSTICAS
[Estatísticas do sistema]

## 🔧 COMANDOS EXECUTADOS
[Lista de comandos usados na auditoria]
```

## 🎯 FOCO ESPECIAL

### **PROBLEMAS CONHECIDOS A INVESTIGAR:**
1. **Token expiration** - Verificar se foi corrigido
2. **Avatar do sidebar** - Verificar se está funcionando
3. **APIs de configuração** - Verificar se estão retornando dados corretos
4. **Integração com PostgreSQL** - Verificar se todos os dados estão sendo salvos
5. **Sistema de autenticação** - Verificar se está seguro

### **ÁREAS DE ALTA PRIORIDADE:**
1. **Página de configurações** - Recém integrada com banco
2. **Sistema de suporte** - Recém implementado
3. **APIs de dashboard** - Verificar se estão funcionando
4. **Sistema de agendamentos** - Verificar integridade
5. **Sistema de conversas** - Verificar performance

## 🚀 INSTRUÇÕES FINAIS

1. **Execute a auditoria** seguindo o plano detalhado
2. **Use todas as ferramentas** disponíveis (filesystem, postgres, desktop-commander)
3. **Documente tudo** que encontrar
4. **Priorize problemas críticos** e de segurança
5. **Retorne um relatório completo** e acionável
6. **NÃO modifique** nenhum arquivo ou dado
7. **Foque na qualidade** e profundidade da análise

---

**🎯 MISSÃO:** Realizar a auditoria mais completa e profunda possível do sistema WhatsApp Agent Dashboard, identificando todos os problemas, vulnerabilidades e oportunidades de melhoria.

**⚡ AÇÃO:** Comece imediatamente com a análise de arquivos usando o filesystem, depois consulte a database com postgres, e finalize com testes de sistema usando desktop-commander.

**📋 RESULTADO ESPERADO:** Relatório detalhado com problemas identificados, soluções sugeridas e recomendações prioritárias para melhorar o sistema.
