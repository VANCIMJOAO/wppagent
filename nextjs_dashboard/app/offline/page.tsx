'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useOfflineData } from '@/lib/offline-storage'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Wifi,
  WifiOff,
  RefreshCw,
  Database,
  Calendar,
  MessageCircle,
  BarChart3,
  Home,
  Smartphone,
  LogIn
} from 'lucide-react'

export default function OfflinePage() {
  const { isOnline, hasOfflineData, pendingActions, storageStats } = useOfflineData()

  // H005: Detectar se está offline por questões de autenticação
  const [isAuthRequired, setIsAuthRequired] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search)
      setIsAuthRequired(urlParams.get('auth') === 'required')

      // H005: Log para debug do auth bypass
      if (urlParams.get('auth') === 'required') {
        console.log('H005: Offline page - auth=required bypass detected')
      }
    }
  }, [])

  const handleRefresh = () => {
    window.location.reload()
  }

  const handleRetry = async () => {
    // Verificar conectividade
    try {
      await fetch('/api/health', { method: 'HEAD' })
      window.location.href = '/dashboard'
    } catch {
      alert('Ainda sem conexão. Tente novamente em alguns momentos.')
    }
  }

  // Se ficou online, redirecionar
  React.useEffect(() => {
    if (isOnline) {
      setTimeout(() => {
        window.location.href = '/dashboard'
      }, 1000)
    }
  }, [isOnline])

  // H005: Função para ir para login
  const handleGoToLogin = () => {
    window.location.href = '/login'
  }

  // H005: Se é uma requisição de auth, mostrar interface específica
  if (isAuthRequired) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
          <div className="mb-6">
            <LogIn className="mx-auto h-16 w-16 text-yellow-500" />
          </div>

          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Login Necessário
          </h1>

          <p className="text-gray-600 mb-6">
            Para acessar esta funcionalidade, você precisa estar logado e conectado à internet.
            O PWA funciona offline, mas o login requer conexão.
          </p>

          <div className="space-y-3">
            <Button
              onClick={handleRetry}
              className="w-full flex items-center justify-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Tentar Novamente
            </Button>

            <Button
              onClick={handleGoToLogin}
              variant="outline"
              className="w-full flex items-center justify-center gap-2"
            >
              <LogIn className="h-4 w-4" />
              Ir para Login
            </Button>
          </div>

          <div className="mt-6 text-sm text-gray-500">
            <p>H005: PWA com bypass de autenticação</p>
            <p className="mt-1">
              Status: {navigator?.onLine ? '🟢 Online' : '🔴 Offline'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full space-y-6">

        {/* Header Card */}
        <Card className="text-center">
          <CardHeader className="pb-4">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              {isOnline ? (
                <Wifi className="h-8 w-8 text-green-500" />
              ) : (
                <WifiOff className="h-8 w-8 text-red-500" />
              )}
            </div>

            <CardTitle className="text-2xl">
              {isOnline ? 'Reconectando...' : 'Você está offline'}
            </CardTitle>

            <CardDescription className="text-base">
              {isOnline ? (
                <span className="text-green-600">
                  Conexão restaurada! Redirecionando...
                </span>
              ) : (
                'Verifique sua conexão com a internet. Algumas funcionalidades estão limitadas.'
              )}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Status da conexão */}
            <div className="flex justify-center">
              <Badge variant={isOnline ? 'default' : 'destructive'} className="text-sm px-3 py-1">
                {isOnline ? (
                  <>
                    <Wifi className="h-4 w-4 mr-1" />
                    Online
                  </>
                ) : (
                  <>
                    <WifiOff className="h-4 w-4 mr-1" />
                    Offline
                  </>
                )}
              </Badge>
            </div>

            {/* Ações pendentes */}
            {pendingActions > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <div className="flex items-center justify-center gap-2 text-orange-700">
                  <RefreshCw className={`h-4 w-4 ${isOnline ? 'animate-spin' : ''}`} />
                  <span className="text-sm font-medium">
                    {pendingActions} {pendingActions === 1 ? 'ação será sincronizada' : 'ações serão sincronizadas'}
                    quando reconectar
                  </span>
                </div>
              </div>
            )}

            {/* Botões de ação */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={handleRetry} className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                Tentar Reconectar
              </Button>

              <Button variant="outline" onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Recarregar Página
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Dados offline disponíveis */}
        {hasOfflineData && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Database className="h-5 w-5 text-blue-500" />
                Dados Offline Disponíveis
              </CardTitle>
              <CardDescription>
                Você pode continuar trabalhando com os dados em cache
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid sm:grid-cols-2 gap-4">
                {/* Links para páginas com dados offline */}
                <Link href="/dashboard">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="flex items-center gap-3 p-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <BarChart3 className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-medium">Dashboard</div>
                        <div className="text-sm text-gray-500">Ver estatísticas em cache</div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>

                <Link href="/agendamentos">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="flex items-center gap-3 p-4">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <Calendar className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <div className="font-medium">Agendamentos</div>
                        <div className="text-sm text-gray-500">Visualizar offline</div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>

                <Link href="/conversas">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="flex items-center gap-3 p-4">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                        <MessageCircle className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <div className="font-medium">Conversas</div>
                        <div className="text-sm text-gray-500">Dados locais</div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>

                <Link href="/">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="flex items-center gap-3 p-4">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <Home className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <div className="font-medium">Página Inicial</div>
                        <div className="text-sm text-gray-500">Voltar ao início</div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </div>

              {/* Estatísticas de storage */}
              {storageStats && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-2">Dados armazenados localmente:</div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex justify-between">
                      <span>Agendamentos:</span>
                      <span className="font-medium">{storageStats.appointments}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Conversas:</span>
                      <span className="font-medium">{storageStats.conversations}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cache Dashboard:</span>
                      <span className="font-medium">{storageStats.dashboard_cache}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ações Pendentes:</span>
                      <span className="font-medium">{storageStats.pending_actions}</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Dicas de uso offline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Smartphone className="h-5 w-5 text-gray-600" />
              Funcionalidades Offline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-green-700 mb-2 flex items-center gap-2">
                  ✅ Disponível Offline
                </h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Visualizar dados em cache</li>
                  <li>• Navegar entre páginas</li>
                  <li>• Ler conversas salvas</li>
                  <li>• Ver agendamentos locais</li>
                  <li>• Dashboard com dados cached</li>
                </ul>
              </div>

              <div>
                <h4 className="font-medium text-red-700 mb-2 flex items-center gap-2">
                  ❌ Requer Conexão
                </h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Dados em tempo real</li>
                  <li>• Criar novos agendamentos</li>
                  <li>• Enviar mensagens</li>
                  <li>• Atualizar configurações</li>
                  <li>• Push notifications</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  💡
                </div>
                <div className="text-sm">
                  <div className="font-medium text-blue-800 mb-1">Dica:</div>
                  <div className="text-blue-700">
                    Suas ações serão automaticamente sincronizadas quando a conexão for restaurada.
                    O app continuará funcionando normalmente com os dados já carregados.
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          WhatsApp Agent Dashboard - Modo PWA Offline
        </div>
      </div>
    </div>
  )
}
