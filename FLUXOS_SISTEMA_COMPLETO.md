# 🔄 DOCUMENTAÇÃO COMPLETA DE FLUXOS DO SISTEMA

> **Versão:** 1.0.0  
> **Data:** 06/10/2025  
> **Objetivo:** Mapear TODOS os fluxos de ponta a ponta para testes

---

## 📋 ÍNDICE DE FLUXOS

1. [FLUXO 1: Mensagem WhatsApp → Captura Automática](#fluxo-1-mensagem-whatsapp)
2. [FLUXO 2: Login Admin → Dashboard](#fluxo-2-login-admin)
3. [FLUXO 3: Criar Agendamento → Notificação](#fluxo-3-criar-agendamento)
4. [FLUXO 4: Visualizar Conversas → Mensagens](#fluxo-4-visualizar-conversas)
5. [FLUXO 5: Dashboard Stats → Cache → WebSocket](#fluxo-5-dashboard-stats)
6. [FLUXO 6: Analytics → Gráficos](#fluxo-6-analytics)
7. [FLUXO 7: Gestão de Clientes → Histórico](#fluxo-7-gestao-clientes)
8. [FLUXO 8: Templates WhatsApp → Envio](#fluxo-8-templates-whatsapp)
9. [FLUXO 9: WebSocket Tempo Real](#fluxo-9-websocket-tempo-real)
10. [FLUXO 10: Exportação de Relatórios](#fluxo-10-exportacao-relatorios)

---

## FLUXO 1: Mensagem WhatsApp → Captura Automática

### 🎯 **Objetivo:** Cliente envia mensagem no WhatsApp → Sistema captura e responde

### **Sequência Completa:**

```
┌─────────────┐
│   CLIENTE   │ Envia mensagem no WhatsApp
│  WhatsApp   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Meta API   │ POST https://yourdomain.com/webhook/whatsapp
│  Webhook     │
└──────┬──────┘
       │
       ▼ 1. RECEBIMENTO
┌──────────────────────────────────────────┐
│ Backend: app/routes/webhook_unified.py   │
│ POST /webhook/whatsapp                   │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. LOG AUDITORIA
┌──────────────────────────────────────────┐
│ Salva em: meta_logs                      │
│ CREATE meta_logs (webhook_data, ...)     │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. SANITIZAÇÃO
┌──────────────────────────────────────────┐
│ utils/whatsapp_sanitizer.py              │
│ - Extrai: wa_id, content, contact_info   │
│ - Remove: emojis problemáticos           │
│ - Valida: estrutura da mensagem          │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. CONTROLE DE DUPLICATAS
┌──────────────────────────────────────────┐
│ services/unified_response_control.py     │
│ - Verifica: rate limit (100 msgs/min)    │
│ - Bloqueia: spam, duplicatas             │
│ - Redis key: response_control:{wa_id}    │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. CRIAR/BUSCAR USUÁRIO
┌──────────────────────────────────────────┐
│ services/user_service.py                 │
│ UserService.get_or_create_user()         │
│                                          │
│ SELECT * FROM users WHERE wa_id = ?      │
│ Se não existe:                           │
│   INSERT INTO users (wa_id, nome, ...)   │
│                                          │
│ Resultado: User ID                       │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. CRIAR/BUSCAR CONVERSA
┌──────────────────────────────────────────┐
│ services/conversation_service.py         │
│ ConversationService.get_or_create()      │
│                                          │
│ SELECT * FROM conversations              │
│ WHERE user_id = ? AND status = 'active'  │
│ Se não existe:                           │
│   INSERT INTO conversations (...)        │
│                                          │
│ Resultado: Conversation ID               │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. SALVAR MENSAGEM (IN)
┌──────────────────────────────────────────┐
│ services/message_service.py              │
│ MessageService.create_message()          │
│                                          │
│ INSERT INTO messages (                   │
│   user_id,                               │
│   conversation_id,                       │
│   direction = 'in',                      │
│   content,                               │
│   message_type,                          │
│   raw_payload                            │
│ )                                        │
│                                          │
│ Resultado: Message ID                    │
└──────┬───────────────────────────────────┘
       │
       ▼ 8. GERAR RESPOSTA AI
┌──────────────────────────────────────────┐
│ webhook_unified.py                       │
│ SimplifiedResponseGenerator              │
│                                          │
│ - Detecta: palavras-chave                │
│ - Retorna: resposta predefinida          │
│                                          │
│ Keywords:                                │
│ - "oi", "olá" → Saudação                │
│ - "agendar", "horário" → Agendamento     │
│ - "preço", "valor" → Informações         │
│ - default → "Como posso ajudar?"         │
└──────┬───────────────────────────────────┘
       │
       ▼ 9. ENVIAR RESPOSTA WHATSAPP
┌──────────────────────────────────────────┐
│ services/whatsapp_business_service.py    │
│ send_text_message(wa_id, response_text)  │
│                                          │
│ POST https://graph.facebook.com/         │
│      v17.0/{phone_id}/messages           │
│ Body: {                                  │
│   "messaging_product": "whatsapp",       │
│   "to": wa_id,                           │
│   "text": {"body": response_text}        │
│ }                                        │
│ Header: Authorization: Bearer {token}    │
└──────┬───────────────────────────────────┘
       │
       ▼ 10. SALVAR MENSAGEM (OUT)
┌──────────────────────────────────────────┐
│ services/message_service.py              │
│                                          │
│ INSERT INTO messages (                   │
│   conversation_id,                       │
│   direction = 'out',                     │
│   content = response_text,               │
│   message_type = 'text'                  │
│ )                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 11. NOTIFICAÇÃO WEBSOCKET
┌──────────────────────────────────────────┐
│ websocket/event_broadcaster.py           │
│ notify_new_whatsapp_message()            │
│                                          │
│ Broadcast para:                          │
│ - Room: "dashboard"                      │
│ - Event: "new_message"                   │
│ - Data: {conversation_id, content, ...}  │
└──────┬───────────────────────────────────┘
       │
       ▼ 12. FRONTEND ATUALIZA
┌──────────────────────────────────────────┐
│ Frontend recebe via WebSocket            │
│ - Dashboard: atualiza contador msgs      │
│ - Conversas: adiciona nova msg           │
│ - Badge: incrementa unread               │
└──────────────────────────────────────────┘
```

### **Tabelas Afetadas:**
1. ✅ `users` - Novo cliente (se não existe)
2. ✅ `conversations` - Nova conversa (se não existe)
3. ✅ `messages` - 2 registros (in + out)
4. ✅ `meta_logs` - 1 registro (auditoria)

### **APIs Envolvidas:**
- **Backend:** `POST /webhook/whatsapp`
- **Serviços:** UserService, ConversationService, MessageService, WhatsAppBusinessService
- **Cache:** Redis (rate limiting)
- **WebSocket:** Notificação em tempo real

### **Dados Reais:**
- **2.115 mensagens** capturadas até 06/10/2025
- **118 clientes** criados automaticamente
- **41 conversas** ativas

---

## FLUXO 2: Login Admin → Dashboard

### 🎯 **Objetivo:** Admin faz login → Acessa dashboard com métricas reais

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa http://localhost:3000/login
│  Navegador  │
└──────┬──────┘
       │
       ▼ 1. RENDERIZA PÁGINA LOGIN
┌──────────────────────────────────────────┐
│ Frontend: app/login/page.tsx             │
│ Form: username, password                 │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. SUBMIT CREDENCIAIS
┌──────────────────────────────────────────┐
│ POST /api/auth/admin-login               │
│ Body: {                                  │
│   "username": "admin",                   │
│   "password": "admin123"                 │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. NEXT.JS API ROUTE
┌──────────────────────────────────────────┐
│ nextjs_dashboard/app/api/auth/           │
│ admin-login/route.ts                     │
│                                          │
│ - Conecta PostgreSQL via pg              │
│ - Query: SELECT * FROM admin_users       │
│          WHERE username = 'admin'        │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. VERIFICAR SENHA
┌──────────────────────────────────────────┐
│ bcrypt.compare(password, password_hash)  │
│                                          │
│ Se incorreta: 401 Unauthorized           │
│ Se correta: Continua ↓                   │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. GERAR TOKEN JWT
┌──────────────────────────────────────────┐
│ SignJWT (jose library)                   │
│                                          │
│ Payload: {                               │
│   sub: admin.id,         // user_id      │
│   type: "access",        // OBRIGATÓRIO  │
│   username: "admin",                     │
│   role: "admin",                         │
│   full_name: "Admin Principal"           │
│ }                                        │
│                                          │
│ Secret: JWT_SECRET (env)                 │
│ Algorithm: HS256                         │
│ Expiration: 2h                           │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. SET COOKIES
┌──────────────────────────────────────────┐
│ response.cookies.set('access_token', token) │
│                                          │
│ Options:                                 │
│ - httpOnly: true                         │
│ - secure: true (produção)                │
│ - sameSite: 'lax'                        │
│ - maxAge: 7200 (2h)                      │
│ - path: '/'                              │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. RESPOSTA JSON
┌──────────────────────────────────────────┐
│ Response 200 OK:                         │
│ {                                        │
│   "success": true,                       │
│   "access_token": "eyJhbGci...",        │
│   "user": {                              │
│     "id": 1,                             │
│     "username": "admin",                 │
│     "role": "admin",                     │
│     "full_name": "Admin Principal"       │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 8. FRONTEND SALVA TOKEN
┌──────────────────────────────────────────┐
│ contexts/auth-context.tsx                │
│ setUser(data.user)                       │
│ setIsAuthenticated(true)                 │
│ localStorage: user data                  │
└──────┬───────────────────────────────────┘
       │
       ▼ 9. REDIRECT DASHBOARD
┌──────────────────────────────────────────┐
│ router.push('/dashboard')                │
└──────┬───────────────────────────────────┘
       │
       ▼ 10. MIDDLEWARE VALIDA
┌──────────────────────────────────────────┐
│ nextjs_dashboard/middleware.ts           │
│                                          │
│ - Lê cookie: access_token                │
│ - Verifica JWT: jose.jwtVerify()         │
│ - Valida: exp, sub, type                 │
│ - Se válido: permite acesso              │
│ - Se inválido: redirect /login           │
└──────┬───────────────────────────────────┘
       │
       ▼ 11. RENDERIZA DASHBOARD
┌──────────────────────────────────────────┐
│ app/(dashboard)/dashboard/page.tsx       │
│                                          │
│ useRealAnalytics() hook ↓                │
└──────┬───────────────────────────────────┘
       │
       ▼ 12. HOOK CARREGA DADOS
┌──────────────────────────────────────────┐
│ hooks/use-real-analytics.ts              │
│ refreshDashboard(30)                     │
│                                          │
│ ↓ Verifica cache (5min)                  │
│ ↓ Se expirado: fetch API                 │
└──────┬───────────────────────────────────┘
       │
       ▼ 13. PROXY NEXT.JS
┌──────────────────────────────────────────┐
│ GET /api/dashboard?days=30               │
│ nextjs_dashboard/app/api/dashboard/      │
│ route.ts                                 │
│                                          │
│ - Extrai: access_token dos cookies       │
│ - Proxy para: http://localhost:8000      │
│ - Header: Authorization: Bearer {token}  │
└──────┬───────────────────────────────────┘
       │
       ▼ 14. BACKEND VALIDA TOKEN
┌──────────────────────────────────────────┐
│ app/auth/middleware.py                   │
│ get_current_user()                       │
│                                          │
│ - Extrai: token do header                │
│ - Verifica: jwt_manager.verify_token()   │
│ - Valida: type="access", sub existe      │
│ - Retorna: user_id, role, permissions    │
└──────┬───────────────────────────────────┘
       │
       ▼ 15. EXECUTA QUERIES
┌──────────────────────────────────────────┐
│ app/routes/dashboard.py                  │
│ get_dashboard_summary()                  │
│                                          │
│ QUERY 1: SELECT COUNT(*) FROM users     │
│ → total_customers = 118                  │
│                                          │
│ QUERY 2: SELECT COUNT(*) FROM           │
│          conversations WHERE             │
│          created_at >= start_date        │
│ → total_conversations = 41               │
│                                          │
│ QUERY 3: SELECT COUNT(*) FROM messages  │
│          WHERE created_at >= start_date  │
│ → total_messages = 2115                  │
│                                          │
│ QUERY 4: SELECT COUNT(*) FROM           │
│          appointments WHERE              │
│          created_at >= start_date        │
│ → total_appointments = 21                │
│                                          │
│ QUERY 5: Taxa de conversão               │
│ → overall_conversion_rate = 19.0%        │
│                                          │
│ QUERY 6: Tempo médio resposta            │
│ → avg_response_time_minutes = 12.5       │
│                                          │
│ QUERY 7: Score satisfação                │
│ → satisfaction_score = 4.5               │
└──────┬───────────────────────────────────┘
       │
       ▼ 16. CACHE REDIS
┌──────────────────────────────────────────┐
│ Redis SET dashboard_30 {data} EX 30      │
│ TTL: 30 segundos                         │
└──────┬───────────────────────────────────┘
       │
       ▼ 17. RESPOSTA JSON
┌──────────────────────────────────────────┐
│ Response 200 OK:                         │
│ {                                        │
│   "success": true,                       │
│   "data": {                              │
│     "key_metrics": {                     │
│       "total_customers": 118,            │
│       "total_messages": 2115,            │
│       "total_conversations": 41,         │
│       "total_appointments": 21,          │
│       "overall_conversion_rate": 19.0,   │
│       "avg_response_time_minutes": 12.5, │
│       "satisfaction_score": 4.5          │
│     },                                   │
│     "trends": { ... }                    │
│   },                                     │
│   "cached": false                        │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 18. FRONTEND RENDERIZA
┌──────────────────────────────────────────┐
│ Dashboard exibe:                         │
│ - 📊 118 Clientes                        │
│ - 💬 41 Conversas                        │
│ - 📅 21 Agendamentos                     │
│ - 📈 19% Taxa de Conversão               │
│ - ⏱️ 12.5min Tempo Resposta              │
│ - ⭐ 4.5 Satisfação                      │
└──────────────────────────────────────────┘
```

### **Tempo Total:** ~3.1s (primeira carga) / ~40ms (cache)

### **Tabelas Consultadas:**
1. `admin_users` - Autenticação
2. `users` - Total de clientes
3. `conversations` - Total de conversas
4. `messages` - Total de mensagens
5. `appointments` - Total de agendamentos
6. `customer_feedback` - Satisfação

### **Cache Layers:**
1. **Redis:** 30s (backend)
2. **React State:** 5min (frontend)
3. **HTTP:** Via headers

---

## FLUXO 3: Criar Agendamento → Notificação

### 🎯 **Objetivo:** Admin cria agendamento → Sistema salva → Notifica em tempo real

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Clica "Novo Agendamento" na página /agendamentos
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. ABRE MODAL
┌──────────────────────────────────────────┐
│ components/appointments/                 │
│ AppointmentModal.tsx                     │
│                                          │
│ Form fields:                             │
│ - Cliente (select) → user_id             │
│ - Serviço (select) → service_id          │
│ - Data → data_agendamento                │
│ - Hora → hora_agendamento                │
│ - Observações → observacoes              │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. CARREGA DADOS
┌──────────────────────────────────────────┐
│ GET /api/clients → 118 clientes          │
│ GET /api/services → 16 serviços          │
│                                          │
│ Popula dropdowns no form                 │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. ADMIN PREENCHE
┌──────────────────────────────────────────┐
│ Seleções:                                │
│ - Cliente: "João Silva" (ID: 1)          │
│ - Serviço: "Consulta" (ID: 3)            │
│ - Data: "2025-10-15"                     │
│ - Hora: "14:00"                          │
│ - Obs: "Primeira consulta"               │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. SUBMIT FORM
┌──────────────────────────────────────────┐
│ POST /api/appointments                   │
│ Body: {                                  │
│   "user_id": 1,                          │
│   "business_id": 3,                      │
│   "service_id": 3,                       │
│   "data_agendamento": "2025-10-15",      │
│   "hora_agendamento": "14:00",           │
│   "duracao_minutos": 60,                 │
│   "valor": 150.00,                       │
│   "observacoes": "Primeira consulta",    │
│   "status": "agendado"                   │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. NEXT.JS PROXY
┌──────────────────────────────────────────┐
│ nextjs_dashboard/app/api/                │
│ appointments/route.ts                    │
│                                          │
│ Proxy para backend com token             │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. BACKEND VALIDA
┌──────────────────────────────────────────┐
│ app/routes/appointments.py               │
│ create_appointment()                     │
│                                          │
│ Validações:                              │
│ 1. Token JWT válido? ✓                   │
│ 2. User existe? (SELECT users)           │
│ 3. Business existe? (SELECT businesses)  │
│ 4. Service existe? (SELECT services)     │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. CRIAR REGISTRO
┌──────────────────────────────────────────┐
│ INSERT INTO appointments (               │
│   user_id = 1,                           │
│   business_id = 3,                       │
│   service_id = 3,                        │
│   date_time = '2025-10-15 14:00',        │
│   status = 'scheduled',                  │
│   notes = 'Primeira consulta',           │
│   created_at = NOW()                     │
│ )                                        │
│ RETURNING id                             │
│                                          │
│ Resultado: Appointment ID = 22           │
└──────┬───────────────────────────────────┘
       │
       ▼ 8. BUSCAR DADOS COMPLETOS
┌──────────────────────────────────────────┐
│ SELECT a.*, u.nome as user_name,         │
│        s.name as service_name,           │
│        b.company_name as business_name   │
│ FROM appointments a                      │
│ JOIN users u ON a.user_id = u.id         │
│ JOIN services s ON a.service_id = s.id   │
│ JOIN businesses b ON a.business_id = b.id│
│ WHERE a.id = 22                          │
└──────┬───────────────────────────────────┘
       │
       ▼ 9. INVALIDAR CACHE
┌──────────────────────────────────────────┐
│ @invalidate_appointment_cache_on_success │
│ Decorator automático                     │
│                                          │
│ Redis DEL: appointments_*                │
│ Redis DEL: dashboard_*                   │
└──────┬───────────────────────────────────┘
       │
       ▼ 10. WEBSOCKET NOTIFICAÇÃO #1
┌──────────────────────────────────────────┐
│ websocket/event_broadcaster.py           │
│ broadcast_to_topic("appointments")       │
│                                          │
│ Event: APPOINTMENT_CREATED               │
│ Data: {                                  │
│   "appointment": {                       │
│     "id": 22,                            │
│     "client_name": "João Silva",         │
│     "service_name": "Consulta",          │
│     "date_time": "2025-10-15T14:00",     │
│     "status": "scheduled"                │
│   },                                     │
│   "message": "Novo agendamento: João",   │
│   "notification": {                      │
│     "title": "Novo Agendamento",         │
│     "body": "João Silva - Consulta"      │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 11. WEBSOCKET NOTIFICAÇÃO #2
┌──────────────────────────────────────────┐
│ broadcast_to_topic("dashboard")          │
│                                          │
│ Event: DASHBOARD_STATS_UPDATE            │
│ Data: {                                  │
│   "metric": "appointments_today",        │
│   "increment": 1,                        │
│   "action": "created"                    │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 12. FRONTEND RECEBE WEBSOCKET
┌──────────────────────────────────────────┐
│ components/WebSocketProvider.tsx         │
│ useWebSocketRobust("/ws")                │
│                                          │
│ onMessage(event) {                       │
│   if (event.type === "appointment_created") { │
│     // Atualiza lista de agendamentos    │
│     queryClient.invalidateQueries([      │
│       'appointments'                     │
│     ])                                   │
│   }                                      │
│   if (event.type === "dashboard_stats") {│
│     // Atualiza contador dashboard       │
│     setStats(prev => ({                  │
│       ...prev,                           │
│       appointments: prev.appointments + 1│
│     }))                                  │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 13. UI ATUALIZA AUTOMATICAMENTE
┌──────────────────────────────────────────┐
│ Página /agendamentos:                    │
│ - Lista atualiza (novo item aparece)     │
│ - Badge "22 agendamentos"                │
│ - Toast: "Agendamento criado!"           │
│                                          │
│ Dashboard:                               │
│ - Card "Agendamentos" 21 → 22            │
│ - Sem reload!                            │
└──────────────────────────────────────────┘
```

### **Tempo Total:** ~1.5s

### **Tabelas Afetadas:**
1. ✅ `appointments` - INSERT 1 registro
2. ✅ Joins: `users`, `services`, `businesses`

### **APIs Envolvidas:**
- **Frontend:** `POST /api/appointments`
- **Backend:** `POST /api/appointments`
- **Serviços:** AppointmentService
- **Cache:** Invalidação automática
- **WebSocket:** 2 broadcasts (appointments + dashboard)

---

## FLUXO 4: Visualizar Conversas → Mensagens

### 🎯 **Objetivo:** Admin clica em conversa → Vê mensagens completas

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa /conversas
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. RENDERIZA PÁGINA
┌──────────────────────────────────────────┐
│ app/(dashboard)/conversas/page.tsx       │
│                                          │
│ useConversations() hook ↓                │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. CARREGA CONVERSAS
┌──────────────────────────────────────────┐
│ GET /api/conversations                   │
│                                          │
│ nextjs_dashboard/app/api/conversations/  │
│ route.ts                                 │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. QUERY POSTGRESQL (DIRETO)
┌──────────────────────────────────────────┐
│ PostgreSQL via pg (pool)                 │
│                                          │
│ SELECT                                   │
│   c.id,                                  │
│   c.user_id,                             │
│   c.status,                              │
│   c.last_message_at,                     │
│   COALESCE(                              │
│     NULLIF(TRIM(u.nome), ''),            │
│     u.telefone,                          │
│     'Usuário sem identificação'          │
│   ) as user_name,                        │
│   u.telefone as user_phone,              │
│   COUNT(m.id) as total_messages,         │
│   (SELECT m2.content FROM messages m2    │
│    WHERE m2.conversation_id = c.id       │
│    ORDER BY m2.created_at DESC LIMIT 1)  │
│      as last_message_content             │
│ FROM conversations c                     │
│ JOIN users u ON c.user_id = u.id         │
│ LEFT JOIN messages m ON c.id = m.conversation_id │
│ GROUP BY c.id, u.nome, u.telefone        │
│ ORDER BY c.last_message_at DESC          │
│ NULLS LAST                               │
│                                          │
│ Resultado: 41 conversas                  │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. FRONTEND RENDERIZA LISTA
┌──────────────────────────────────────────┐
│ Lista de 41 conversas:                   │
│ - Nome: user_name (ou telefone)          │
│ - Badge: status (active/human/closed)    │
│ - Última mensagem: preview               │
│ - Timestamp: última atualização          │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. ADMIN CLICA EM CONVERSA
┌──────────────────────────────────────────┐
│ setSelectedConversationId(1)             │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. CARREGA MENSAGENS
┌──────────────────────────────────────────┐
│ useMessages(conversationId) hook         │
│                                          │
│ GET /api/conversations/1/messages        │
│     ?limit=50&offset=0                   │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. NEXT.JS API (NOVO - CRIADO)
┌──────────────────────────────────────────┐
│ nextjs_dashboard/app/api/conversations/  │
│ [conversationId]/messages/route.ts       │
│                                          │
│ - Verifica: access_token no cookie       │
│ - Conecta: PostgreSQL via pg             │
│ - Aguarda: await params (Next.js 15)     │
└──────┬───────────────────────────────────┘
       │
       ▼ 8. QUERY MENSAGENS
┌──────────────────────────────────────────┐
│ SELECT                                   │
│   m.id,                                  │
│   m.conversation_id,                     │
│   m.user_id,                             │
│   m.direction,           // 'in' ou 'out'│
│   m.content,                             │
│   m.message_type,                        │
│   m.message_id,                          │
│   m.created_at,                          │
│   u.nome as sender_name,                 │
│   u.telefone as sender_phone             │
│ FROM messages m                          │
│ LEFT JOIN users u ON m.user_id = u.id    │
│ WHERE m.conversation_id = 1              │
│ ORDER BY m.created_at ASC                │
│ LIMIT 50 OFFSET 0                        │
│                                          │
│ Resultado: 1865 mensagens (conversa #1)  │
└──────┬───────────────────────────────────┘
       │
       ▼ 9. RESPOSTA JSON
┌──────────────────────────────────────────┐
│ {                                        │
│   "success": true,                       │
│   "messages": [                          │
│     {                                    │
│       "id": 1,                           │
│       "conversation_id": 1,              │
│       "direction": "in",                 │
│       "content": "Olá!",                 │
│       "sender_name": "João Victor",      │
│       "created_at": "2025-09-01T10:00"   │
│     },                                   │
│     {                                    │
│       "id": 2,                           │
│       "direction": "out",                │
│       "content": "Como posso ajudar?",   │
│       "created_at": "2025-09-01T10:01"   │
│     },                                   │
│     ... (1863 mensagens mais)            │
│   ],                                     │
│   "total": 1865,                         │
│   "has_more": false                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 10. FRONTEND RENDERIZA CHAT
┌──────────────────────────────────────────┐
│ Painel de chat:                          │
│                                          │
│ ┌─── Mensagens ────────────────┐         │
│ │ [IN]  Olá!                   │         │
│ │       10:00                  │         │
│ │                              │         │
│ │ [OUT] Como posso ajudar?     │         │
│ │       10:01                  │         │
│ │                              │         │
│ │ ... (1863 msgs)              │         │
│ └──────────────────────────────┘         │
│                                          │
│ Input: [Digite sua mensagem...] [Enviar]│
└──────────────────────────────────────────┘
```

### **Tempo Total:** ~1.4s (conversas) + ~400ms (mensagens)

### **Tabelas Consultadas:**
1. `conversations` + `users` + `messages` (JOIN)
2. `messages` + `users` (JOIN para nomes)

### **Paginação:**
- Limit: 50 mensagens por vez
- Offset: 0, 50, 100, ...
- Total: 1865 mensagens (conversa #1)

---

## FLUXO 5: Dashboard Stats → Cache → WebSocket

### 🎯 **Objetivo:** Dashboard atualiza automaticamente a cada 30s via cache/WebSocket

### **Sequência Completa:**

```
┌─────────────┐
│  DASHBOARD  │ useRealAnalytics() hook
│   Frontend  │
└──────┬──────┘
       │
       ▼ 1. PRIMEIRA CARGA (Sem cache)
┌──────────────────────────────────────────┐
│ GET /api/dashboard?days=30               │
│ ↓ Backend executa 7 queries              │
│ ↓ Calcula métricas                       │
│ ↓ Salva no Redis (TTL: 30s)              │
│ ↓ Retorna JSON                           │
│                                          │
│ Tempo: ~3.1s (queries lentas)            │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. SEGUNDA CARGA (Com cache - 15s depois)
┌──────────────────────────────────────────┐
│ GET /api/dashboard?days=30               │
│ ↓ Backend verifica cache Redis           │
│ ↓ Cache HIT! (ainda nos 30s)             │
│ ↓ Retorna dados cached                   │
│                                          │
│ Tempo: ~40ms (sem queries)               │
│ Response: { "cached": true }             │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. TERCEIRA CARGA (Cache expirado - 35s depois)
┌──────────────────────────────────────────┐
│ GET /api/dashboard?days=30               │
│ ↓ Backend verifica cache Redis           │
│ ↓ Cache MISS! (TTL expirou)              │
│ ↓ Executa queries novamente              │
│ ↓ Salva novo cache (TTL: 30s)            │
│ ↓ Retorna dados atualizados              │
│                                          │
│ Tempo: ~3.1s (queries lentas)            │
│ Response: { "cached": false }            │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. ATUALIZAÇÃO VIA WEBSOCKET
┌──────────────────────────────────────────┐
│ WebSocket conectado em: ws://host/ws     │
│                                          │
│ Frontend escuta eventos:                 │
│ ws.onmessage = (event) => {              │
│   const data = JSON.parse(event.data)    │
│                                          │
│   if (data.type === "dashboard_stats_update") { │
│     // Atualiza métrica específica       │
│     setStats(prev => ({                  │
│       ...prev,                           │
│       [data.metric]: prev[data.metric] + data.increment │
│     }))                                  │
│     // NÃO precisa refetch da API!       │
│   }                                      │
│                                          │
│   if (data.type === "new_message") {     │
│     // Incrementa contador mensagens     │
│     // Invalida cache                    │
│   }                                      │
│ }                                        │
└──────────────────────────────────────────┘
```

### **Estratégia de Cache (3 Layers):**

1. **Redis (Backend):**
   - TTL: 30s
   - Key: `dashboard_{days}`
   - Invalidação: Automática (criar/editar/deletar)

2. **React State (Frontend):**
   - TTL: 5min (globalState)
   - Shared entre componentes
   - Invalidação: Manual ou WebSocket

3. **HTTP Cache (Headers):**
   - Cache-Control: no-cache
   - ETag: não implementado

### **Gatilhos de Invalidação:**

```python
# Backend automático via decorators
@invalidate_appointment_cache_on_success
@invalidate_conversation_cache_on_success
@invalidate_message_cache_on_success

# Eventos que invalidam:
- Criar agendamento ❌ cache
- Editar agendamento ❌ cache
- Deletar agendamento ❌ cache
- Nova mensagem (webhook) ❌ cache
- Nova conversa ❌ cache
```

---

## FLUXO 6: Analytics → Gráficos

### 🎯 **Objetivo:** Visualizar analytics avançados com gráficos de receita, agendamentos, etc.

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa /analytics
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. RENDERIZA PÁGINA
┌──────────────────────────────────────────┐
│ app/(dashboard)/analytics/page.tsx       │
│                                          │
│ useRealAnalytics() hook                  │
│ - refreshRevenue()                       │
│ - refreshAppointmentsByStatus()          │
│ - refreshAppointmentsByService()         │
│ - refreshAppointmentsByTimeslot()        │
│ - refreshClientsDemographics()           │
│ - refreshClientsRetention()              │
│ - refreshNewClientsDaily()               │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. REQUISIÇÃO #1: RECEITA
┌──────────────────────────────────────────┐
│ GET /api/analytics/revenue               │
│ ↓ Proxy Next.js                          │
│ ↓ Backend: app/routes/analytics_revenue.py │
│                                          │
│ QUERY (SQL direto):                      │
│ SELECT                                   │
│   DATE_TRUNC('day', created_at) as date, │
│   SUM(CAST(valor AS NUMERIC)) as total   │
│ FROM appointments                        │
│ WHERE created_at >= NOW() - INTERVAL '30 days' │
│ AND valor IS NOT NULL                    │
│ GROUP BY DATE_TRUNC('day', created_at)   │
│ ORDER BY date                            │
│                                          │
│ Resultado: R$ 50,00 em Setembro          │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. REQUISIÇÃO #2: STATUS
┌──────────────────────────────────────────┐
│ GET /api/analytics/appointments/by-status│
│                                          │
│ QUERY:                                   │
│ SELECT status, COUNT(*) as count         │
│ FROM appointments                        │
│ WHERE created_at >= start_date           │
│ GROUP BY status                          │
│                                          │
│ Resultado:                               │
│ - scheduled: 4                           │
│ - confirmed: 0                           │
│ - cancelled: 0                           │
│ - completed: 0                           │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. REQUISIÇÃO #3: SERVIÇOS
┌──────────────────────────────────────────┐
│ GET /api/analytics/appointments/by-service│
│                                          │
│ QUERY:                                   │
│ SELECT s.name, COUNT(a.id) as count      │
│ FROM appointments a                      │
│ JOIN services s ON a.service_id = s.id   │
│ WHERE a.created_at >= start_date         │
│ GROUP BY s.name                          │
│ ORDER BY count DESC                      │
│                                          │
│ Resultado:                               │
│ - Consulta Médica: 2                     │
│ - Exame de Sangue: 1                     │
│ - ...                                    │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. REQUISIÇÃO #4: HORÁRIOS
┌──────────────────────────────────────────┐
│ GET /api/analytics/appointments/by-timeslot │
│                                          │
│ QUERY com EXTRACT(hour):                 │
│ SELECT                                   │
│   CASE                                   │
│     WHEN EXTRACT(hour FROM date_time)    │
│       BETWEEN 8 AND 9 THEN '08:00-10:00' │
│     WHEN EXTRACT(hour FROM date_time)    │
│       BETWEEN 10 AND 11 THEN '10:00-12:00'│
│     ... etc                              │
│   END as time_slot,                      │
│   COUNT(*) as count                      │
│ FROM appointments                        │
│ GROUP BY time_slot                       │
│                                          │
│ Resultado:                               │
│ - 08:00-10:00: 1                         │
│ - 14:00-16:00: 2                         │
│ - ...                                    │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. REQUISIÇÃO #5-7: CLIENTES
┌──────────────────────────────────────────┐
│ GET /api/analytics/clients/new-daily     │
│ GET /api/analytics/clients/retention     │
│ GET /api/analytics/clients/demographics  │
│                                          │
│ (Queries similares aos anteriores)       │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. RENDERIZA GRÁFICOS
┌──────────────────────────────────────────┐
│ Recharts components:                     │
│                                          │
│ 📊 Gráfico de Receita (LineChart)        │
│ - Eixo X: Dias                           │
│ - Eixo Y: R$                             │
│ - Data: R$ 50,00 (total Setembro)        │
│                                          │
│ 📊 Agendamentos por Status (PieChart)    │
│ - Agendado: 4 (100%)                     │
│                                          │
│ 📊 Agendamentos por Serviço (BarChart)   │
│ - Consulta: 2                            │
│ - Exame: 1                               │
│                                          │
│ 📊 Horários Populares (BarChart)         │
│ - 08:00-10:00: 1                         │
│ - 14:00-16:00: 2                         │
└──────────────────────────────────────────┘
```

### **Tempo Total:** ~1-2s (7 requisições paralelas)

### **APIs Backend:**
1. `GET /api/analytics/revenue` (analytics_revenue.py)
2. `GET /api/analytics/appointments/by-status` (analytics_appointments.py)
3. `GET /api/analytics/appointments/by-service` (analytics_appointments.py)
4. `GET /api/analytics/appointments/by-timeslot` (analytics_appointments.py)
5. `GET /api/analytics/clients/new-daily` (analytics_clients.py)
6. `GET /api/analytics/clients/retention` (analytics_clients.py)
7. `GET /api/analytics/clients/demographics` (analytics_clients.py)

### **Cache:** 60s TTL (analytics)

---

## FLUXO 7: Gestão de Clientes → Histórico

### 🎯 **Objetivo:** Ver histórico completo de um cliente (mensagens + agendamentos)

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa /clientes
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. LISTA CLIENTES
┌──────────────────────────────────────────┐
│ GET /api/clients                         │
│                                          │
│ SELECT * FROM users                      │
│ ORDER BY created_at DESC                 │
│ LIMIT 100                                │
│                                          │
│ Resultado: 118 clientes                  │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. CLICA "VER HISTÓRICO"
┌──────────────────────────────────────────┐
│ components/clients/                      │
│ ClientHistoryModal.tsx                   │
│                                          │
│ GET /api/clients/1/history               │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. BACKEND BUSCA HISTÓRICO
┌──────────────────────────────────────────┐
│ app/routes/clients_history.py            │
│ get_client_history(client_id=1)          │
│                                          │
│ QUERY 1: Dados do cliente                │
│ SELECT id, nome, telefone, wa_id,        │
│        created_at                        │
│ FROM users WHERE id = 1                  │
│                                          │
│ QUERY 2: Mensagens (últimas 100)         │
│ SELECT id, content, direction,           │
│        message_type, created_at          │
│ FROM messages                            │
│ WHERE user_id = 1                        │
│ ORDER BY created_at DESC                 │
│ LIMIT 100                                │
│                                          │
│ QUERY 3: Agendamentos                    │
│ SELECT a.*, s.name as service_name       │
│ FROM appointments a                      │
│ JOIN services s ON a.service_id = s.id   │
│ WHERE a.user_id = 1                      │
│ ORDER BY a.date_time DESC                │
│                                          │
│ QUERY 4: Conversas                       │
│ SELECT id, status, created_at,           │
│        last_message_at                   │
│ FROM conversations                       │
│ WHERE user_id = 1                        │
│ ORDER BY last_message_at DESC            │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. MONTA RESPOSTA COMPLETA
┌──────────────────────────────────────────┐
│ {                                        │
│   "success": true,                       │
│   "client": {                            │
│     "id": 1,                             │
│     "nome": "João Victor Vancim",        │
│     "telefone": "5516991234567",         │
│     "wa_id": "5516991234567",            │
│     "created_at": "2025-09-01T10:00"     │
│   },                                     │
│   "messages": [ ... 1865 mensagens ],    │
│   "appointments": [ ... 3 agendamentos ],│
│   "conversations": [ ... 2 conversas ],  │
│   "stats": {                             │
│     "total_messages": 1865,              │
│     "total_appointments": 3,             │
│     "total_conversations": 2,            │
│     "first_contact": "2025-09-01",       │
│     "last_contact": "2025-10-05"         │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. MODAL RENDERIZA
┌──────────────────────────────────────────┐
│ ClientHistoryModal exibe:                │
│                                          │
│ ┌─── Histórico de João Victor ───┐      │
│ │                                │      │
│ │ 📊 Estatísticas:               │      │
│ │ - 1865 mensagens               │      │
│ │ - 3 agendamentos               │      │
│ │ - 2 conversas                  │      │
│ │                                │      │
│ │ 💬 Últimas Mensagens:          │      │
│ │ [IN] Olá! (01/09)              │      │
│ │ [OUT] Como posso ajudar?       │      │
│ │ ... (mais 98)                  │      │
│ │                                │      │
│ │ 📅 Agendamentos:               │      │
│ │ - Consulta (15/10 14:00)       │      │
│ │ - Exame (20/10 09:00)          │      │
│ │ - Retorno (25/10 10:00)        │      │
│ └────────────────────────────────┘      │
└──────────────────────────────────────────┘
```

### **Tempo Total:** ~800ms

### **Tabelas Consultadas:**
1. `users` - Dados do cliente
2. `messages` - Histórico de mensagens (1865)
3. `appointments` + `services` - Agendamentos (3)
4. `conversations` - Conversas (2)

---

## FLUXO 8: Templates WhatsApp → Envio

### 🎯 **Objetivo:** Admin usa template aprovado para enviar mensagem

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa /configuracoes/templates
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. LISTA TEMPLATES
┌──────────────────────────────────────────┐
│ GET /api/templates                       │
│                                          │
│ Backend: app/routes/templates.py         │
│ SELECT * FROM templates                  │
│ WHERE is_active = true                   │
│                                          │
│ Resultado: 5 templates                   │
│ - Boas-vindas (approved)                 │
│ - Confirmação Agendamento (approved)     │
│ - Lembrete (approved)                    │
│ - Cancelamento (approved)                │
│ - Feedback (approved)                    │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. ADMIN SELECIONA TEMPLATE
┌──────────────────────────────────────────┐
│ Template: "Confirmação Agendamento"      │
│                                          │
│ Body: "Olá {{1}}, seu agendamento para   │
│        {{2}} está confirmado!"           │
│                                          │
│ Variables:                               │
│ - {{1}} = nome do cliente                │
│ - {{2}} = serviço                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. PREENCHE VARIÁVEIS
┌──────────────────────────────────────────┐
│ Seleciona:                               │
│ - Cliente: João Silva                    │
│ - Serviço: Consulta Médica               │
│                                          │
│ Preview:                                 │
│ "Olá João Silva, seu agendamento para    │
│  Consulta Médica está confirmado!"       │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. ENVIA TEMPLATE
┌──────────────────────────────────────────┐
│ POST /api/templates/send                 │
│ Body: {                                  │
│   "template_name": "confirmacao",        │
│   "to": "5516991234567",                 │
│   "parameters": [                        │
│     "João Silva",                        │
│     "Consulta Médica"                    │
│   ]                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. BACKEND ENVIA VIA META API
┌──────────────────────────────────────────┐
│ services/whatsapp_business_service.py    │
│ send_template()                          │
│                                          │
│ POST https://graph.facebook.com/v17.0/   │
│      {phone_id}/messages                 │
│                                          │
│ {                                        │
│   "messaging_product": "whatsapp",       │
│   "to": "5516991234567",                 │
│   "type": "template",                    │
│   "template": {                          │
│     "name": "confirmacao",               │
│     "language": {"code": "pt_BR"},       │
│     "components": [{                     │
│       "type": "body",                    │
│       "parameters": [                    │
│         {"type": "text", "text": "João Silva"}, │
│         {"type": "text", "text": "Consulta"}    │
│       ]                                  │
│     }]                                   │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. META API ENVIA
┌──────────────────────────────────────────┐
│ WhatsApp Business API processa           │
│ - Valida template aprovado               │
│ - Substitui variáveis                    │
│ - Envia para cliente                     │
│                                          │
│ Response: {                              │
│   "messaging_product": "whatsapp",       │
│   "contacts": [{...}],                   │
│   "messages": [{                         │
│     "id": "wamid.xxx",                   │
│     "message_status": "accepted"         │
│   }]                                     │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 7. SALVA LOG
┌──────────────────────────────────────────┐
│ INSERT INTO messages (                   │
│   conversation_id,                       │
│   direction = 'out',                     │
│   content = "Olá João Silva...",         │
│   message_type = 'template',             │
│   message_id = "wamid.xxx"               │
│ )                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 8. CLIENTE RECEBE
┌──────────────────────────────────────────┐
│ WhatsApp do cliente:                     │
│ "Olá João Silva, seu agendamento para    │
│  Consulta Médica está confirmado!"       │
└──────────────────────────────────────────┘
```

### **Tabelas Afetadas:**
1. `templates` - SELECT (5 templates)
2. `messages` - INSERT (mensagem enviada)

### **APIs Meta:**
- `POST /v17.0/{phone_id}/messages`
- Header: `Authorization: Bearer {META_ACCESS_TOKEN}`

---

## FLUXO 9: WebSocket Tempo Real

### 🎯 **Objetivo:** Manter dashboard sincronizado em tempo real sem reloads

### **Sequência Completa:**

```
┌─────────────┐
│  FRONTEND   │ useWebSocketRobust("/ws")
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. CONECTA WEBSOCKET
┌──────────────────────────────────────────┐
│ hooks/useWebSocketRobust.ts              │
│                                          │
│ const ws = new WebSocket(                │
│   "ws://localhost:8000/ws"               │
│ )                                        │
│                                          │
│ ws.onopen = () => {                      │
│   console.log("✅ WebSocket conectado")  │
│   setIsConnected(true)                   │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. BACKEND ACEITA CONEXÃO
┌──────────────────────────────────────────┐
│ app/websocket/connection_manager.py      │
│ ConnectionManager.connect()              │
│                                          │
│ - await websocket.accept()               │
│ - Cria ConnectionInfo                    │
│ - Adiciona à room "dashboard"            │
│ - Stats: total_connections++             │
│ - Inicia heartbeat monitor               │
│                                          │
│ Envia boas-vindas:                       │
│ {                                        │
│   "type": "connection_success",          │
│   "room": "dashboard",                   │
│   "user_id": "anonymous_xxx"             │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. EVENTO OCORRE (Ex: Novo Agendamento)
┌──────────────────────────────────────────┐
│ POST /api/appointments (criação)         │
│ ↓ Appointment salvo no PostgreSQL        │
│ ↓ Decorator invalida cache               │
│ ↓ Chama broadcast_to_topic()             │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. BROADCAST WEBSOCKET
┌──────────────────────────────────────────┐
│ websocket/event_broadcaster.py           │
│ broadcast_to_topic("dashboard")          │
│                                          │
│ Message: {                               │
│   "type": "dashboard_stats_update",      │
│   "data": {                              │
│     "metric": "appointments_today",      │
│     "increment": 1,                      │
│     "action": "created",                 │
│     "timestamp": "2025-10-06T15:30:00Z"  │
│   }                                      │
│ }                                        │
│                                          │
│ Loop: for conn in room["dashboard"]      │
│   await conn.websocket.send_json(msg)    │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. FRONTEND RECEBE
┌──────────────────────────────────────────┐
│ ws.onmessage = (event) => {              │
│   const data = JSON.parse(event.data)    │
│                                          │
│   switch(data.type) {                    │
│     case "dashboard_stats_update":       │
│       // Atualiza contador                │
│       setAppointmentsToday(prev => prev + 1) │
│       break;                             │
│                                          │
│     case "new_message":                  │
│       // Adiciona badge notification     │
│       // Invalida cache de conversas     │
│       queryClient.invalidateQueries([    │
│         'conversations'                  │
│       ])                                 │
│       break;                             │
│                                          │
│     case "appointment_created":          │
│       // Adiciona na lista               │
│       // Toast: "Novo agendamento!"      │
│       break;                             │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. UI ATUALIZA INSTANTANEAMENTE
┌──────────────────────────────────────────┐
│ Dashboard card "Agendamentos":           │
│ 21 → 22 (SEM RELOAD!)                    │
│                                          │
│ Toast notification:                      │
│ "✅ Novo agendamento criado!"            │
└──────────────────────────────────────────┘
```

### **Heartbeat (Keep-Alive):**

```
Frontend envia a cada 30s:
{
  "type": "heartbeat",
  "timestamp": "2025-10-06T15:30:00Z"
}

Backend responde:
{
  "type": "heartbeat_ack",
  "server_time": "2025-10-06T15:30:01Z"
}
```

### **Reconnect Automático:**

```
ws.onclose = () => {
  console.log("⚠️ WebSocket desconectado")
  setIsConnected(false)
  
  // Tentar reconectar após 3s
  setTimeout(() => {
    connectWebSocket()
  }, 3000)
}
```

### **Rooms Disponíveis:**
- `dashboard` - Updates gerais
- `appointments` - Agendamentos
- `conversations` - Conversas
- `notifications` - Notificações
- `user_{id}` - Usuário específico

---

## FLUXO 10: Exportação de Relatórios

### 🎯 **Objetivo:** Gerar e baixar relatórios em PDF/Excel

### **Sequência Completa:**

```
┌─────────────┐
│   ADMIN     │ Acessa /exportar-relatorios
│  Dashboard  │
└──────┬──────┘
       │
       ▼ 1. SELECIONA PARÂMETROS
┌──────────────────────────────────────────┐
│ components/export-buttons.tsx            │
│                                          │
│ Opções:                                  │
│ - Formato: PDF / Excel / CSV             │
│ - Período: Últimos 7/30/90 dias          │
│ - Tipo: Agendamentos / Conversas / Clientes │
└──────┬───────────────────────────────────┘
       │
       ▼ 2. CLICA "EXPORTAR"
┌──────────────────────────────────────────┐
│ POST /api/reports/export                 │
│ Body: {                                  │
│   "report_type": "appointments",         │
│   "format": "pdf",                       │
│   "start_date": "2025-09-06",            │
│   "end_date": "2025-10-06",              │
│   "filters": {                           │
│     "status": "all"                      │
│   }                                      │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼ 3. BACKEND BUSCA DADOS
┌──────────────────────────────────────────┐
│ app/routes/export.py                     │
│ export_report()                          │
│                                          │
│ SELECT a.*, u.nome, s.name               │
│ FROM appointments a                      │
│ JOIN users u ON a.user_id = u.id         │
│ JOIN services s ON a.service_id = s.id   │
│ WHERE a.created_at BETWEEN start AND end │
│ ORDER BY a.date_time                     │
│                                          │
│ Resultado: 21 agendamentos               │
└──────┬───────────────────────────────────┘
       │
       ▼ 4. GERA PDF
┌──────────────────────────────────────────┐
│ reportlab library                        │
│                                          │
│ - Cria documento PDF                     │
│ - Header: Logo + título                  │
│ - Tabela: Agendamentos                   │
│ - Colunas: Data, Cliente, Serviço, Status│
│ - Footer: Gerado em [data]               │
│                                          │
│ Salva em: /tmp/report_xxx.pdf            │
└──────┬───────────────────────────────────┘
       │
       ▼ 5. RETORNA ARQUIVO
┌──────────────────────────────────────────┐
│ Response:                                │
│ - Content-Type: application/pdf          │
│ - Content-Disposition: attachment;       │
│   filename="agendamentos_2025-10-06.pdf" │
│ - Body: [binary PDF data]                │
└──────┬───────────────────────────────────┘
       │
       ▼ 6. BROWSER BAIXA
┌──────────────────────────────────────────┐
│ Download automático:                     │
│ 📄 agendamentos_2025-10-06.pdf           │
│ 156 KB                                   │
└──────────────────────────────────────────┘
```

### **Formatos Suportados:**
- **PDF:** ReportLab
- **Excel:** OpenPyXL
- **CSV:** Python csv module

---

## 📊 RESUMO DE TODOS OS FLUXOS

### **Fluxos Mapeados: 10**

| # | Fluxo | APIs Envolvidas | Tabelas | Tempo |
|---|-------|-----------------|---------|-------|
| 1 | WhatsApp → Captura | 1 | 4 | ~2s |
| 2 | Login → Dashboard | 3 | 7 | ~3.5s |
| 3 | Criar Agendamento | 2 | 4 | ~1.5s |
| 4 | Ver Conversas/Msgs | 2 | 3 | ~1.8s |
| 5 | Dashboard Cache | 1 | 7 | 40ms |
| 6 | Analytics Gráficos | 7 | 4 | ~2s |
| 7 | Histórico Cliente | 1 | 4 | ~800ms |
| 8 | Templates WhatsApp | 2 | 2 | ~1s |
| 9 | WebSocket Real-time | 1 | 0 | instant |
| 10 | Exportar PDF | 1 | 3 | ~2s |

### **Total de APIs Únicas:** 118
### **Total de Tabelas PostgreSQL:** 20+
### **Total de Serviços:** 70

---

## 🧪 PRÓXIMOS PASSOS - TESTES

### **Fase 1: Testes Unitários (Por Fluxo)**
1. ⏳ Testar FLUXO 1: Webhook (simular mensagem)
2. ⏳ Testar FLUXO 2: Login (credenciais válidas/inválidas)
3. ⏳ Testar FLUXO 3: Agendamentos (CRUD completo)
4. ⏳ Testar FLUXO 4: Conversas (lista + mensagens)
5. ⏳ Testar FLUXO 5: Cache (hit/miss)
6. ⏳ Testar FLUXO 6: Analytics (queries)
7. ⏳ Testar FLUXO 7: Histórico (dados completos)
8. ⏳ Testar FLUXO 8: Templates (envio)
9. ⏳ Testar FLUXO 9: WebSocket (conexão/eventos)
10. ⏳ Testar FLUXO 10: Exportação (PDF/Excel)

### **Fase 2: Testes de Integração (E2E)**
1. ⏳ Fluxo completo: WhatsApp → Dashboard (1+2+9)
2. ⏳ Fluxo completo: Login → Criar Agendamento → Ver (2+3+4)
3. ⏳ Fluxo completo: Analytics → Exportar (6+10)

### **Fase 3: Testes de Performance**
1. ⏳ Stress test: 100 msgs simultâneas (Fluxo 1)
2. ⏳ Load test: 50 admins simultâneos (Fluxo 2)
3. ⏳ Cache test: Hit rate > 80% (Fluxo 5)

---

**📚 Documentação completa de fluxos pronta para testes!** ✅

**Última atualização:** 06/10/2025 às 23:45  
**Versão:** 1.0.0

