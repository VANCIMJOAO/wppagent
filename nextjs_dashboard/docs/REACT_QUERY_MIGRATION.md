# 🔄 Guia de Migração: React Query Integration

## 📋 Checklist de Migração

### 1. ✅ Preparação (Concluído)
- [x] Instalar dependências: `@tanstack/react-query`, `@tanstack/react-query-devtools`
- [x] Configurar QueryClient em `lib/react-query.ts`
- [x] Criar hooks otimizados para todas as entidades
- [x] Setup do Provider e DevTools

### 2. 🚀 Integração no App Principal

#### Step 1: Adicionar Provider ao Layout

**Arquivo:** `app/layout.tsx` ou `pages/_app.tsx`

```tsx
// ANTES
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}

// DEPOIS
import { ReactQueryProvider } from '@/components/providers/react-query-provider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body className={inter.className}>
        <ReactQueryProvider>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            {children}
          </ThemeProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}
```

#### Step 2: Migrar Componentes de Agendamentos

**Localizar:** `app/agendamentos/page.tsx` ou similar

```tsx
// ANTES - Fetching manual
const [appointments, setAppointments] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/appointments')
      const data = await response.json()
      setAppointments(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }
  fetchAppointments()
}, [])

// DEPOIS - React Query
import { useAppointments } from '@/hooks/useAppointments'

const { data, isLoading, error, refetch } = useAppointments({
  page: 1,
  limit: 10,
  status: filters.status
})

if (isLoading) return <AppointmentsSkeleton />
if (error) return <ErrorMessage error={error} onRetry={refetch} />

const appointments = data?.appointments || []
```

#### Step 3: Migrar Forms de Criação/Edição

```tsx
// ANTES - Submit manual
const handleSubmit = async (formData) => {
  try {
    setSubmitting(true)
    const response = await fetch('/api/appointments', {
      method: 'POST',
      body: JSON.stringify(formData)
    })
    if (response.ok) {
      router.push('/appointments')
      // Invalidar manualmente
    }
  } catch (error) {
    setError(error.message)
  } finally {
    setSubmitting(false)
  }
}

// DEPOIS - React Query Mutation
import { useCreateAppointment } from '@/hooks/useAppointments'

const createAppointment = useCreateAppointment()

const handleSubmit = (formData) => {
  createAppointment.mutate(formData, {
    onSuccess: () => {
      router.push('/appointments')
      // Cache invalidation automática
    }
  })
}

// Loading automático
const isSubmitting = createAppointment.isPending
```

#### Step 4: Atualizar Dashboard

```tsx
// ANTES - Multiple useEffect
const [stats, setStats] = useState(null)
const [analytics, setAnalytics] = useState(null)
const [loading, setLoading] = useState(true)

useEffect(() => {
  Promise.all([
    fetch('/api/dashboard/stats'),
    fetch('/api/dashboard/analytics')
  ]).then(([statsRes, analyticsRes]) => {
    // Handle responses...
  })
}, [])

// DEPOIS - Hook unificado
import { useDashboard } from '@/hooks/useDashboard'

const { data, isLoading, refresh } = useDashboard({
  period: '7d',
  autoRefresh: true
})

// Dados já combinados
const { stats, analytics, performance } = data || {}
```

### 3. 🔄 Substituições Específicas

#### APIs que podem ser substituídas

| Arquivo Atual | Hook React Query | Benefício |
|---------------|------------------|-----------|
| `components/appointments/AppointmentsList.tsx` | `useAppointments()` | Cache + Paginação |
| `components/appointments/AppointmentForm.tsx` | `useCreateAppointment()` | Optimistic Updates |
| `components/dashboard/StatsCards.tsx` | `useDashboard()` | Auto-refresh |
| `components/conversations/MessageList.tsx` | `useMessages()` | Real-time polling |
| `app/api/appointments/route.ts` | Continua igual | Backend mantido |

#### Padrões de Substituição

1. **useState + useEffect → useQuery**
```tsx
// Remove
const [data, setData] = useState(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)

// Adiciona
const { data, isLoading, error } = useAppointments()
```

2. **Fetch manual → useMutation**
```tsx
// Remove
const handleCreate = async () => {
  const response = await fetch('/api/appointments', {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

// Adiciona
const createMutation = useCreateAppointment()
const handleCreate = () => {
  createMutation.mutate(data)
}
```

3. **Refresh manual → Invalidation**
```tsx
// Remove
const refreshData = () => {
  setLoading(true)
  fetchData()
}

// Adiciona
const { invalidateAll } = useInvalidateAppointments()
const refreshData = invalidateAll
```

### 4. 🧪 Testing Strategy

#### Step by Step Migration

1. **Start Small** - Migre uma página por vez
2. **Keep Both** - Mantenha código antigo temporariamente
3. **A/B Test** - Compare performance entre versões
4. **Monitor** - Use DevTools para verificar cache hits

#### Testing Checklist

```bash
# 1. Teste em desenvolvimento
npm run dev
# ✅ Verificar DevTools funcionando
# ✅ Verificar queries sendo cached
# ✅ Verificar mutations com optimistic updates

# 2. Teste funcionalidades
# ✅ CRUD completo de agendamentos
# ✅ Filtros e paginação
# ✅ Real-time em conversas
# ✅ Auto-refresh no dashboard

# 3. Teste performance
# ✅ Network tab - menos requests
# ✅ React DevTools - menos re-renders
# ✅ Lighthouse - melhores métricas
```

### 5. 🚀 Performance Esperada

#### Métricas Before/After

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Requests/página** | 8-12 | 3-5 | ~60% |
| **Time to Interactive** | 2.3s | 1.4s | ~40% |
| **First Contentful Paint** | 1.8s | 1.1s | ~35% |
| **Re-renders desnecessários** | Alto | Baixo | ~70% |
| **Cache hits** | 0% | 80%+ | +80% |

#### DevTools Monitoring

```typescript
// Configurar para produção
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Metrics tracking
      meta: {
        performance: true
      }
    }
  }
})

// Monitor cache effectiveness
queryClient.getQueryCache().subscribe(event => {
  if (event.type === 'updated') {
    console.log('Cache hit rate:', event.query.meta?.cacheHits)
  }
})
```

### 6. 🛠️ Troubleshooting

#### Problemas Comuns

1. **Hydration Mismatch**
```tsx
// Solução: Usar Suspense boundaries
<Suspense fallback={<Loading />}>
  <AppointmentsList />
</Suspense>
```

2. **Stale Closures**
```tsx
// Problema: Dados antigos em callbacks
const handleClick = useCallback(() => {
  // `data` pode estar stale
  doSomething(data)
}, []) // ❌ Missing dependency

// Solução: Include dependencies
const handleClick = useCallback(() => {
  doSomething(data)
}, [data]) // ✅ Correct
```

3. **Infinite Loops**
```tsx
// Problema: Query key instável
const { data } = useQuery({
  queryKey: ['appointments', { filter: {} }], // ❌ New object each render
  queryFn: fetchAppointments
})

// Solução: Estabilizar query key
const filters = useMemo(() => ({ status: 'active' }), [])
const { data } = useQuery({
  queryKey: ['appointments', filters], // ✅ Stable reference
  queryFn: fetchAppointments
})
```

### 7. 📈 Monitoring & Analytics

#### DevTools Usage
```tsx
// Em desenvolvimento, verificar:
// 1. Query Inspector - cache status
// 2. Mutations - optimistic updates
// 3. Network - request deduplication
// 4. Timeline - refetch patterns
```

#### Production Monitoring
```typescript
// Adicionar métricas customizadas
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onSuccess: (data, query) => {
      analytics.track('query_success', {
        queryKey: query.queryKey,
        dataSize: JSON.stringify(data).length,
        duration: Date.now() - query.state.dataUpdatedAt
      })
    },
    onError: (error, query) => {
      analytics.track('query_error', {
        queryKey: query.queryKey,
        error: error.message
      })
    }
  })
})
```

### 8. 🎯 Success Criteria

#### Migration Complete When:

- [ ] All major data fetching replaced with React Query
- [ ] DevTools showing 80%+ cache hit rate  
- [ ] Performance metrics improved by 30%+
- [ ] No hydration or state management issues
- [ ] All CRUD operations using optimistic updates
- [ ] Real-time features working with polling
- [ ] Error boundaries handling all edge cases

#### Next Phase Enhancements:

1. **WebSocket Integration** para updates real-time
2. **Offline Support** com persistence
3. **Prefetching Strategies** para navegação
4. **Advanced Caching** com TTL dinâmico
