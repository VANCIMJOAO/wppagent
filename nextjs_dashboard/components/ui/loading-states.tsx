import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, Wifi, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

/**
 * 🔄 Estados Loading/Erro Padronizados
 * ===================================
 * 
 * Componentes reutilizáveis para estados de loading, erro e vazio.
 * Padroniza a UX em todo o dashboard.
 * 
 * Autor: Claude AI
 * Data: 2025-09-07
 * Status: Componentes base para UX consistente
 */

// ✅ Loading universal
export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8", 
    lg: "w-12 h-12"
  }
  
  return (
    <div className="flex items-center justify-center p-4">
      <RefreshCw className={`${sizeClasses[size]} animate-spin text-blue-500`} />
    </div>
  )
}

// ✅ Error universal
export function ErrorFallback({ 
  error, 
  retry, 
  title = "Algo deu errado" 
}: { 
  error: Error | string
  retry?: () => void
  title?: string 
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-4 max-w-md">
        {typeof error === 'string' ? error : error.message}
      </p>
      {retry && (
        <Button onClick={retry} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar Novamente
        </Button>
      )}
    </div>
  )
}

// ✅ Empty state universal
export function EmptyState({ 
  title, 
  description, 
  action 
}: { 
  title: string
  description: string
  action?: React.ReactNode 
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Wifi className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-4 max-w-md">{description}</p>
      {action}
    </div>
  )
}

// ✅ Skeleton para tabelas
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number, cols?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex space-x-4">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

// ✅ Skeleton para cards
export function CardSkeleton({ 
  showHeader = true, 
  showFooter = false,
  lines = 3 
}: { 
  showHeader?: boolean
  showFooter?: boolean
  lines?: number 
}) {
  return (
    <div className="border border-gray-200 rounded-lg p-6 space-y-4">
      {showHeader && (
        <div className="space-y-2">
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}
      
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
      
      {showFooter && (
        <div className="flex space-x-2 pt-4">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-24" />
        </div>
      )}
    </div>
  )
}

// ✅ Loading overlay para páginas inteiras
export function PageLoadingOverlay({ message = "Carregando..." }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-75 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="flex flex-col items-center space-y-4">
        <RefreshCw className="w-12 h-12 animate-spin text-blue-500" />
        <p className="text-lg font-medium text-gray-700">{message}</p>
      </div>
    </div>
  )
}

// ✅ Inline loading para botões
export function ButtonLoading({ 
  children, 
  loading = false,
  size = "sm"
}: { 
  children: React.ReactNode
  loading?: boolean
  size?: "sm" | "md"
}) {
  const iconSize = size === "sm" ? "w-4 h-4" : "w-5 h-5"
  
  return (
    <>
      {loading && <RefreshCw className={`${iconSize} animate-spin mr-2`} />}
      {children}
    </>
  )
}

// ✅ Loading state para listas
export function ListSkeleton({ 
  items = 5,
  showAvatar = false 
}: { 
  items?: number
  showAvatar?: boolean 
}) {
  return (
    <div className="space-y-4">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
          {showAvatar && <Skeleton className="w-10 h-10 rounded-full" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-3 w-3/4" />
          </div>
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  )
}

// ✅ Error boundary wrapper
export function ErrorBoundaryFallback({ 
  error, 
  resetError 
}: { 
  error: Error
  resetError: () => void 
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full">
        <ErrorFallback
          error={error}
          retry={resetError}
          title="Ops! Algo deu errado"
        />
        
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-6 p-4 bg-gray-100 rounded-lg">
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              Detalhes técnicos (desenvolvimento)
            </summary>
            <pre className="mt-2 text-xs text-gray-600 whitespace-pre-wrap">
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
}

// ✅ Network status indicator
export function NetworkStatus({ isOnline }: { isOnline: boolean }) {
  if (isOnline) return null
  
  return (
    <div className="fixed top-0 left-0 right-0 bg-red-500 text-white px-4 py-2 text-center text-sm z-50">
      <div className="flex items-center justify-center space-x-2">
        <Wifi className="w-4 h-4" />
        <span>Sem conexão com a internet</span>
      </div>
    </div>
  )
}

// ✅ Data state wrapper - combina loading, error e empty
export function DataStateWrapper<T>({
  data,
  loading,
  error,
  children,
  emptyTitle = "Nenhum dado encontrado",
  emptyDescription = "Não há informações para exibir no momento.",
  emptyAction,
  retry
}: {
  data: T[] | T | null | undefined
  loading: boolean
  error: Error | string | null
  children: (data: NonNullable<T>) => React.ReactNode
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: React.ReactNode
  retry?: () => void
}) {
  // Estado de loading
  if (loading) {
    return <LoadingSpinner />
  }
  
  // Estado de erro
  if (error) {
    return <ErrorFallback error={error} retry={retry} />
  }
  
  // Estado vazio
  if (!data || (Array.isArray(data) && data.length === 0)) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={emptyAction}
      />
    )
  }
  
  // Renderizar dados
  return <>{children(data as NonNullable<T>)}</>
}
