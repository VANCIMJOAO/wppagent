'use client'

import React, { useState } from 'react'
import { usePWA } from '@/hooks/usePWA'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Smartphone, 
  Download, 
  X, 
  CheckCircle,
  RefreshCw,
  Trash2,
  Settings
} from 'lucide-react'

interface PWAPromptProps {
  className?: string
  variant?: 'banner' | 'card' | 'button'
  autoShow?: boolean
}

export function PWAPrompt({ className = '', variant = 'banner', autoShow = true }: PWAPromptProps) {
  const { 
    isInstallable, 
    isInstalled, 
    installPWA, 
    needsUpdate, 
    updateServiceWorker,
    clearCache,
    isPWAReady
  } = usePWA()
  
  const [isDismissed, setIsDismissed] = useState(false)
  const [isInstalling, setIsInstalling] = useState(false)

  const handleInstall = async () => {
    setIsInstalling(true)
    try {
      const success = await installPWA()
      if (success) {
        setIsDismissed(true)
      }
    } finally {
      setIsInstalling(false)
    }
  }

  const handleDismiss = () => {
    setIsDismissed(true)
    // Salvar no localStorage para não mostrar novamente por um tempo
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString())
  }

  const handleUpdate = () => {
    updateServiceWorker()
  }

  const handleClearCache = async () => {
    if (confirm('Isso irá limpar todos os dados offline e recarregar a página. Continuar?')) {
      await clearCache()
    }
  }

  // Verificar se foi dismissed recentemente
  React.useEffect(() => {
    const dismissedTime = localStorage.getItem('pwa-prompt-dismissed')
    if (dismissedTime) {
      const hoursSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60)
      if (hoursSinceDismissed < 24) { // Não mostrar por 24 horas
        setIsDismissed(true)
      }
    }
  }, [])

  // Banner variant (topo da tela)
  if (variant === 'banner') {
    if (!isInstallable || isDismissed || !autoShow) return null

    return (
      <div className={`fixed top-0 left-0 right-0 z-50 bg-blue-600 text-white shadow-lg ${className}`}>
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Smartphone className="h-5 w-5" />
              <div>
                <div className="font-medium">Instalar WhatsApp Agent</div>
                <div className="text-sm opacity-90">
                  Acesse mais rápido e use offline
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleInstall}
                disabled={isInstalling}
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                {isInstalling ? (
                  <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <Download className="h-4 w-4 mr-1" />
                )}
                {isInstalling ? 'Instalando...' : 'Instalar'}
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismiss}
                className="text-white hover:bg-white/10 p-2"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Card variant (componente independente)
  if (variant === 'card') {
    return (
      <Card className={`${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            Progressive Web App
          </CardTitle>
          <CardDescription>
            Estado atual da aplicação PWA
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Status badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant={isPWAReady ? 'default' : 'secondary'}>
              {isPWAReady ? 'PWA Ativo' : 'PWA Inativo'}
            </Badge>
            
            {isInstalled && (
              <Badge variant="default" className="bg-green-500">
                <CheckCircle className="h-3 w-3 mr-1" />
                Instalado
              </Badge>
            )}
            
            {needsUpdate && (
              <Badge variant="outline" className="border-orange-500 text-orange-500">
                <RefreshCw className="h-3 w-3 mr-1" />
                Atualização Disponível
              </Badge>
            )}
          </div>

          {/* Ações */}
          <div className="space-y-2">
            {isInstallable && !isInstalled && (
              <Button 
                onClick={handleInstall} 
                disabled={isInstalling}
                className="w-full"
              >
                {isInstalling ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    Instalando...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Instalar App
                  </>
                )}
              </Button>
            )}

            {needsUpdate && (
              <Button 
                onClick={handleUpdate}
                variant="outline"
                className="w-full border-orange-500 text-orange-500 hover:bg-orange-50"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Atualizar App
              </Button>
            )}

            <Button 
              onClick={handleClearCache}
              variant="outline"
              className="w-full"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Limpar Cache
            </Button>
          </div>

          {/* Informações */}
          <div className="text-sm space-y-2">
            {isInstalled ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <div className="flex items-center gap-2 text-green-800 font-medium mb-1">
                  <CheckCircle className="h-4 w-4" />
                  App Instalado
                </div>
                <div className="text-green-700">
                  O WhatsApp Agent está instalado como app nativo. 
                  Funciona offline e pode ser acessado pela tela inicial.
                </div>
              </div>
            ) : isInstallable ? (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-blue-800 font-medium mb-1">Instalação Disponível</div>
                <div className="text-blue-700">
                  Instale o app para acesso rápido e funcionalidade offline completa.
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="text-gray-600">
                  PWA funcional. A instalação pode estar disponível em outros momentos.
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Button variant (apenas botão)
  if (variant === 'button') {
    if (!isInstallable && !needsUpdate) return null

    return (
      <div className={`flex gap-2 ${className}`}>
        {isInstallable && !isInstalled && (
          <Button 
            onClick={handleInstall} 
            disabled={isInstalling}
            variant="outline"
            size="sm"
          >
            {isInstalling ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-1" />
            ) : (
              <Download className="h-4 w-4 mr-1" />
            )}
            Instalar
          </Button>
        )}

        {needsUpdate && (
          <Button 
            onClick={handleUpdate}
            variant="outline"
            size="sm"
            className="border-orange-500 text-orange-500"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Atualizar
          </Button>
        )}
      </div>
    )
  }

  return null
}

// Componente para configurações PWA
export function PWASettings({ className = '' }: { className?: string }) {
  const { isInstalled, isPWAReady, clearCache } = usePWA()

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Configurações PWA
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="font-medium">Status PWA:</div>
            <div className={`${isPWAReady ? 'text-green-600' : 'text-gray-500'}`}>
              {isPWAReady ? 'Ativo' : 'Inativo'}
            </div>
          </div>
          
          <div>
            <div className="font-medium">Instalação:</div>
            <div className={`${isInstalled ? 'text-green-600' : 'text-gray-500'}`}>
              {isInstalled ? 'Instalado' : 'Não instalado'}
            </div>
          </div>
          
          <div>
            <div className="font-medium">Service Worker:</div>
            <div className="text-green-600">Ativo</div>
          </div>
          
          <div>
            <div className="font-medium">Cache Offline:</div>
            <div className="text-green-600">Disponível</div>
          </div>
        </div>

        <Button 
          onClick={clearCache}
          variant="outline"
          className="w-full"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Limpar Todos os Dados
        </Button>
      </CardContent>
    </Card>
  )
}
