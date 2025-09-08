'use client'

import React from 'react'
import { useOfflineData } from '@/lib/offline-storage'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  Database, 
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface OfflineIndicatorProps {
  className?: string
  showDetails?: boolean
}

export function OfflineIndicator({ className = '', showDetails = false }: OfflineIndicatorProps) {
  const { isOnline, hasOfflineData, pendingActions, isInitialized } = useOfflineData()

  // Não mostrar nada se ainda não inicializou
  if (!isInitialized) {
    return null
  }

  // Se está online e não tem dados offline/pendentes, não mostrar
  if (isOnline && !hasOfflineData && pendingActions === 0) {
    return null
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  const handleClearOfflineData = async () => {
    if (confirm('Limpar todos os dados offline? Esta ação não pode ser desfeita.')) {
      const { offlineStorage } = await import('@/lib/offline-storage')
      await offlineStorage.clearAllData()
      window.location.reload()
    }
  }

  // Versão compacta (barra superior)
  if (!showDetails) {
    return (
      <div className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${className}`}>
        <div className={`px-4 py-2 text-center text-sm font-medium ${
          isOnline 
            ? 'bg-green-500 text-white' 
            : 'bg-red-500 text-white'
        }`}>
          <div className="flex items-center justify-center gap-2">
            {isOnline ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <WifiOff className="h-4 w-4" />
            )}
            
            {isOnline ? (
              pendingActions > 0 ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Sincronizando {pendingActions} ações pendentes...
                </>
              ) : (
                'Conectado e sincronizado'
              )
            ) : (
              <>
                Modo offline
                {hasOfflineData && (
                  <>
                    <span className="mx-2">•</span>
                    <Database className="h-4 w-4" />
                    Dados locais disponíveis
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Versão detalhada (card)
  return (
    <div className={`bg-white border rounded-lg shadow-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isOnline ? (
            <Wifi className="h-5 w-5 text-green-500" />
          ) : (
            <WifiOff className="h-5 w-5 text-red-500" />
          )}
          <h3 className="font-semibold">
            Status da Conexão
          </h3>
        </div>
        
        <Badge variant={isOnline ? 'default' : 'destructive'}>
          {isOnline ? 'Online' : 'Offline'}
        </Badge>
      </div>

      <div className="space-y-3">
        {/* Status atual */}
        <div className="flex items-center gap-2 text-sm">
          {isOnline ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-500" />
          )}
          <span>
            {isOnline 
              ? 'Conectado à internet - Dados em tempo real' 
              : 'Sem conexão - Funcionando com dados locais'
            }
          </span>
        </div>

        {/* Dados offline */}
        {hasOfflineData && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <Database className="h-4 w-4" />
            <span>Dados offline disponíveis</span>
          </div>
        )}

        {/* Ações pendentes */}
        {pendingActions > 0 && (
          <div className="flex items-center gap-2 text-sm text-orange-600">
            <Clock className="h-4 w-4" />
            <span>
              {pendingActions} {pendingActions === 1 ? 'ação pendente' : 'ações pendentes'} 
              {isOnline && (
                <span className="ml-1">
                  <RefreshCw className="inline h-3 w-3 animate-spin ml-1" />
                  sincronizando...
                </span>
              )}
            </span>
          </div>
        )}

        {/* Ações */}
        <div className="flex gap-2 pt-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleRefresh}
            className="flex items-center gap-1"
          >
            <RefreshCw className="h-3 w-3" />
            Atualizar
          </Button>
          
          {(hasOfflineData || pendingActions > 0) && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleClearOfflineData}
              className="flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50"
            >
              <Database className="h-3 w-3" />
              Limpar Dados
            </Button>
          )}
        </div>

        {/* Dicas de uso offline */}
        {!isOnline && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
            <div className="font-medium text-blue-800 mb-1">Modo Offline:</div>
            <ul className="text-blue-700 space-y-1 text-xs">
              <li>• Você pode visualizar dados já carregados</li>
              <li>• Algumas ações serão sincronizadas quando reconectar</li>
              <li>• Recursos em tempo real não funcionarão</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

// Hook para status da rede simples
export function useNetworkStatus() {
  const { isOnline } = useOfflineData()
  return isOnline
}

// Componente para mostrar status de sync
export function SyncStatus({ className = '' }: { className?: string }) {
  const { isOnline, pendingActions } = useOfflineData()
  
  if (!isOnline || pendingActions === 0) return null
  
  return (
    <div className={`flex items-center gap-2 text-sm text-blue-600 ${className}`}>
      <RefreshCw className="h-4 w-4 animate-spin" />
      <span>Sincronizando {pendingActions} itens...</span>
    </div>
  )
}
