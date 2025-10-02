, password) {
  const response = await fetch('/api/login', {
    method: 'POST',
    credentials: 'include', // ✅ Envia/recebe cookies
    body: JSON.stringify({ email, password })
  });
  
  // Token definido no backend via Set-Cookie HttpOnly
  // Não precisa manipular token no frontend
}

// Backend (API Route)
export async function POST(request: Request) {
  const { email, password } = await request.json();
  
  // Valida credenciais
  const token = generateJWT(user);
  
  // ✅ Define cookie HttpOnly
  return new Response(JSON.stringify({ success: true }), {
    headers: {
      'Set-Cookie': `token=${token}; HttpOnly; Secure; SameSite=Strict; Path=/`
    }
  });
}
```

---

### Problema #10: XSS Vulnerability

#### ❌ ERRADO:
```typescript
function Comment({ text }) {
  // 🚨 Permite execução de scripts maliciosos
  return (
    <div dangerouslySetInnerHTML={{ __html: text }} />
  );
}
```

#### ✅ CORRETO:
```typescript
import DOMPurify from 'dompurify';

function Comment({ text }) {
  // ✅ Sanitiza HTML antes de renderizar
  const sanitized = DOMPurify.sanitize(text);
  
  return (
    <div dangerouslySetInnerHTML={{ __html: sanitized }} />
  );
}

// Ou melhor ainda:
function Comment({ text }) {
  // ✅ Renderiza como texto puro (mais seguro)
  return <div>{text}</div>;
}
```

---

### Problema #11: Secrets no Código

#### ❌ ERRADO:
```typescript
// 🚨 NUNCA faça isso!
const API_KEY = 'sk_live_1234567890abcdef';
const JWT_SECRET = 'my-super-secret-key';

fetch(`https://api.example.com/data?key=${API_KEY}`);
```

#### ✅ CORRETO:
```typescript
// ✅ Use variáveis de ambiente
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

// Para secrets sensíveis, use apenas no backend
// app/api/route.ts
const JWT_SECRET = process.env.JWT_SECRET; // Não tem NEXT_PUBLIC_

fetch(`https://api.example.com/data?key=${API_KEY}`);
```

---

## 🚀 CATEGORIA 4: PROBLEMAS DE PERFORMANCE

### Problema #12: Não usar React.memo

#### ❌ ERRADO:
```typescript
// 🚨 Re-renderiza mesmo sem mudanças nas props
function ExpensiveComponent({ data }) {
  const processedData = expensiveCalculation(data);
  
  return (
    <div>
      {processedData.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

#### ✅ CORRETO:
```typescript
// ✅ Só re-renderiza quando props mudam
const ExpensiveComponent = memo(({ data }) => {
  const processedData = useMemo(
    () => expensiveCalculation(data),
    [data]
  );
  
  return (
    <div>
      {processedData.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
});
```

---

### Problema #13: Não usar Code Splitting

#### ❌ ERRADO:
```typescript
// 🚨 Carrega tudo de uma vez
import HeavyChart from './HeavyChart';
import MassiveTable from './MassiveTable';
import ComplexForm from './ComplexForm';

function Dashboard() {
  const [tab, setTab] = useState('chart');
  
  return (
    <div>
      {tab === 'chart' && <HeavyChart />}
      {tab === 'table' && <MassiveTable />}
      {tab === 'form' && <ComplexForm />}
    </div>
  );
}
```

#### ✅ CORRETO:
```typescript
// ✅ Lazy loading - carrega apenas quando necessário
import { lazy, Suspense } from 'react';

const HeavyChart = lazy(() => import('./HeavyChart'));
const MassiveTable = lazy(() => import('./MassiveTable'));
const ComplexForm = lazy(() => import('./ComplexForm'));

function Dashboard() {
  const [tab, setTab] = useState('chart');
  
  return (
    <div>
      <Suspense fallback={<Loading />}>
        {tab === 'chart' && <HeavyChart />}
        {tab === 'table' && <MassiveTable />}
        {tab === 'form' && <ComplexForm />}
      </Suspense>
    </div>
  );
}
```

---

### Problema #14: Renderizar Lista Grande Sem Virtualização

#### ❌ ERRADO:
```typescript
// 🚨 Renderiza 10.000 itens de uma vez
function MessageList({ messages }) {
  return (
    <div>
      {messages.map(msg => (
        <MessageItem key={msg.id} message={msg} />
      ))}
    </div>
  );
}

// Com 10.000 mensagens = 10.000 DOM nodes = LAG
```

#### ✅ CORRETO:
```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

// ✅ Renderiza apenas itens visíveis
function MessageList({ messages }) {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });
  
  return (
    <div ref={parentRef} style={{ height: '500px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <MessageItem message={messages[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🏗️ CATEGORIA 5: PROBLEMAS DE ARQUITETURA

### Problema #15: Código Duplicado

#### ❌ ERRADO:
```typescript
// hooks/useConversations.ts
export function useConversations() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchConversations = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/conversations');
      const data = await res.json();
      setData(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };
  
  return { data, loading, error, refresh: fetchConversations };
}

// hooks/useAppointments.ts
export function useAppointments() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 🚨 CÓDIGO DUPLICADO - mesma lógica!
  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/appointments');
      const data = await res.json();
      setData(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };
  
  return { data, loading, error, refresh: fetchAppointments };
}
```

#### ✅ CORRETO:
```typescript
// hooks/useApi.ts - Hook genérico reutilizável
function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [url]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refresh: fetchData };
}

// hooks/useConversations.ts
export function useConversations() {
  return useApi<Conversation[]>('/api/conversations');
}

// hooks/useAppointments.ts
export function useAppointments() {
  return useApi<Appointment[]>('/api/appointments');
}
```

---

### Problema #16: God Component

#### ❌ ERRADO:
```typescript
// 🚨 Componente fazendo tudo (800+ linhas)
function Dashboard() {
  // Estado
  const [conversations, setConversations] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [clients, setClients] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Lógica de fetch
  useEffect(() => {
    fetchConversations();
    fetchAppointments();
    fetchClients();
    fetchStats();
  }, []);
  
  // Handlers
  const handleConversationClick = () => { /* ... */ };
  const handleAppointmentCreate = () => { /* ... */ };
  const handleClientUpdate = () => { /* ... */ };
  
  // Renderização gigante com múltiplas seções
  return (
    <div>
      {/* 500 linhas de JSX */}
    </div>
  );
}
```

#### ✅ CORRETO:
```typescript
// ✅ Dividir em componentes menores e focados

// components/dashboard/DashboardStats.tsx
function DashboardStats() {
  const { stats, loading } = useStats();
  
  if (loading) return <StatsSkeleton />;
  
  return (
    <div className="grid grid-cols-4 gap-4">
      <StatCard title="Conversas" value={stats.conversations} />
      <StatCard title="Agendamentos" value={stats.appointments} />
      <StatCard title="Clientes" value={stats.clients} />
      <StatCard title="Taxa" value={stats.rate} />
    </div>
  );
}

// components/dashboard/ConversationsList.tsx
function ConversationsList() {
  const { conversations, loading } = useConversations();
  const handleClick = useConversationClick();
  
  if (loading) return <ConversationsSkeleton />;
  
  return (
    <div>
      {conversations.map(conv => (
        <ConversationItem 
          key={conv.id} 
          conversation={conv}
          onClick={handleClick}
        />
      ))}
    </div>
  );
}

// pages/dashboard/page.tsx - Orquestrador limpo
function Dashboard() {
  return (
    <div className="space-y-6">
      <DashboardHeader />
      <DashboardStats />
      <div className="grid grid-cols-2 gap-6">
        <ConversationsList />
        <AppointmentsList />
      </div>
      <ClientsTable />
    </div>
  );
}
```

---

### Problema #17: Acoplamento Forte

#### ❌ ERRADO:
```typescript
// 🚨 Componente acoplado a implementação específica
function UserProfile() {
  const user = localStorage.getItem('user'); // Acoplado a localStorage
  const token = localStorage.getItem('token');
  
  // Se mudar de localStorage para cookies, precisa refatorar tudo
  
  return <div>{user.name}</div>;
}
```

#### ✅ CORRETO:
```typescript
// ✅ Desacoplado via abstração (Context/Hook)

// contexts/AuthContext.tsx
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  
  // Implementação interna pode mudar (localStorage, cookies, API)
  // sem afetar componentes que usam o context
  
  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

// components/UserProfile.tsx
function UserProfile() {
  const { user } = useAuth(); // ✅ Desacoplado
  
  return <div>{user.name}</div>;
}
```

---

## 📝 CATEGORIA 6: PROBLEMAS DE TIPAGEM

### Problema #18: Uso Excessivo de `any`

#### ❌ ERRADO:
```typescript
// 🚨 Perde toda segurança de tipos
function fetchData(url: string): Promise<any> {
  return fetch(url).then(res => res.json());
}

function processUser(user: any) {
  return user.name.toUpperCase(); // Pode quebrar em runtime
}
```

#### ✅ CORRETO:
```typescript
// ✅ Tipos específicos e seguros
interface User {
  id: string;
  name: string;
  email: string;
}

function fetchData<T>(url: string): Promise<T> {
  return fetch(url).then(res => res.json());
}

function processUser(user: User): string {
  return user.name.toUpperCase(); // TypeScript garante que name existe
}

// Uso
const user = await fetchData<User>('/api/user');
processUser(user); // Type-safe!
```

---

### Problema #19: Type Assertions Perigosos

#### ❌ ERRADO:
```typescript
// 🚨 Afirma tipo sem validação
function getUser() {
  const data = localStorage.getItem('user');
  return JSON.parse(data) as User; // Pode não ser User!
}
```

#### ✅ CORRETO:
```typescript
import { z } from 'zod';

// ✅ Schema de validação
const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
});

type User = z.infer<typeof UserSchema>;

function getUser(): User | null {
  const data = localStorage.getItem('user');
  if (!data) return null;
  
  try {
    const parsed = JSON.parse(data);
    return UserSchema.parse(parsed); // Valida em runtime
  } catch {
    return null;
  }
}
```

---

## 🧪 CATEGORIA 7: PROBLEMAS DE TESTE

### Problema #20: Código Não Testável

#### ❌ ERRADO:
```typescript
// 🚨 Difícil de testar - acoplado a DOM e fetch
function LoginButton() {
  const handleClick = () => {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
      localStorage.setItem('token', data.token);
      window.location.href = '/dashboard';
    });
  };
  
  return <button onClick={handleClick}>Login</button>;
}
```

#### ✅ CORRETO:
```typescript
// ✅ Testável - dependências injetadas

// hooks/useAuth.ts (testável isoladamente)
export function useAuth() {
  const login = async (email: string, password: string) => {
    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (!res.ok) throw new Error('Login failed');
    return res.json();
  };
  
  return { login };
}

// components/LoginButton.tsx (testável com mock)
interface LoginButtonProps {
  email: string;
  password: string;
  onSuccess: () => void;
  onError: (error: Error) => void;
}

function LoginButton({ email, password, onSuccess, onError }: LoginButtonProps) {
  const { login } = useAuth();
  
  const handleClick = async () => {
    try {
      await login(email, password);
      onSuccess();
    } catch (error) {
      onError(error);
    }
  };
  
  return <button onClick={handleClick}>Login</button>;
}

// Teste
test('LoginButton calls onSuccess after successful login', async () => {
  const onSuccess = jest.fn();
  const { getByText } = render(
    <LoginButton 
      email="test@test.com"
      password="123"
      onSuccess={onSuccess}
      onError={jest.fn()}
    />
  );
  
  fireEvent.click(getByText('Login'));
  await waitFor(() => expect(onSuccess).toHaveBeenCalled());
});
```

---

## 🎯 CHECKLIST RÁPIDO DE PROBLEMAS

Use este checklist ao revisar cada arquivo:

### Hooks
- [ ] Todas as dependências estão declaradas?
- [ ] Há cleanup adequado (return function)?
- [ ] Evita infinite loops?
- [ ] Trata race conditions?
- [ ] Usa useCallback/useMemo apropriadamente?

### Componentes
- [ ] Componente tem < 200 linhas?
- [ ] Lógica de negócio está em hooks?
- [ ] Props estão bem tipadas?
- [ ] Usa memo() se necessário?
- [ ] Keys corretas em listas?

### Segurança
- [ ] Sem tokens em localStorage?
- [ ] Input está sanitizado?
- [ ] Sem secrets hardcoded?
- [ ] CORS configurado corretamente?
- [ ] Cookies são HttpOnly?

### Performance
- [ ] Usa code splitting?
- [ ] Lista grande usa virtualização?
- [ ] Imagens otimizadas?
- [ ] Bundle size razoável?
- [ ] Evita re-renders desnecessários?

### Tipagem
- [ ] Evita `any`?
- [ ] Types assertions são seguros?
- [ ] Interfaces bem definidas?
- [ ] Runtime validation se necessário?

### Arquitetura
- [ ] Sem código duplicado?
- [ ] Separação de concerns clara?
- [ ] Componentes pequenos e focados?
- [ ] Baixo acoplamento?
- [ ] Alta coesão?

---

## 🚨 RED FLAGS - Identifique Imediatamente

Ao auditar, fique atento a estes sinais de alerta:

### 🔴 CRÍTICO
- `localStorage.setItem('token', ...)` - Token inseguro
- `dangerouslySetInnerHTML` sem sanitização - XSS
- `useEffect(() => {...}, [])` com dependências externas - Bug
- WebSocket sem `.close()` no cleanup - Memory leak
- Senha hardcoded no código - Segurança

### 🟡 MÉDIO
- Componente com 500+ linhas - God component
- Hook com 10+ dependências no useEffect - Complexidade
- `any` como tipo - Falta de type safety
- Código duplicado em múltiplos arquivos - DRY violation
- Fetch sem tratamento de erro - UX ruim

### 🟢 BAIXO
- console.log em produção - Limpeza de código
- Comentários desatualizados - Manutenibilidade
- Nomenclatura inconsistente - Code style
- Imports não utilizados - Code cleanliness

---

**Use este guia como referência durante a auditoria para identificar problemas similares no projeto!**
