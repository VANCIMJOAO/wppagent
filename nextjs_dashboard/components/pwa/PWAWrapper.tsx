'use client'

import React, { useEffect } from 'react'
import { PWAPrompt } from '@/components/pwa/PWAPrompt'
import { OfflineIndicator } from '@/components/offline/OfflineIndicator'
import { offlineStorage } from '@/lib/offline-storage'

export function PWAWrapper({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Inicializar storage offline
    const initOfflineStorage = async () => {
      try {
        await offlineStorage.init()
        console.log('✅ PWA: Offline storage initialized')
      } catch (error) {
        console.error('❌ PWA: Failed to initialize offline storage:', error)
      }
    }

    initOfflineStorage()

    // Registrar Service Worker
    const registerSW = async () => {
      console.log('⚠️ PWA: Service Worker temporarily disabled for debugging')
      // TODO: Re-enable after fixing service worker issues
      
      // Also unregister any existing service workers
      if ('serviceWorker' in navigator) {
        try {
          const registrations = await navigator.serviceWorker.getRegistrations()
          for (const registration of registrations) {
            console.log('🗑️ PWA: Unregistering service worker', registration.scope)
            await registration.unregister()
          }
        } catch (error) {
          console.error('❌ PWA: Failed to unregister service workers:', error)
        }
      }
      
      return;
      
      if ('serviceWorker' in navigator) {
        try {
          // Aguardar um pouco para não bloquear o carregamento inicial
          setTimeout(async () => {
            const registration = await navigator.serviceWorker.register('/sw-advanced.js', {
              scope: '/',
              updateViaCache: 'none' // Sempre verificar atualizações
            })

            console.log('✅ PWA: Service Worker registered:', registration.scope)

            // Verificar atualizações periodicamente
            setInterval(() => {
              registration.update()
            }, 60000) // A cada minuto

            // Listener para nova versão disponível
            registration.addEventListener('updatefound', () => {
              const newWorker = registration.installing
              if (newWorker) {
                console.log('🔄 PWA: New version available')
                newWorker.addEventListener('statechange', () => {
                  if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    // Nova versão instalada, mas ainda não ativa
                    console.log('📦 PWA: Update ready to install')
                  }
                })
              }
            })

          }, 1000)
        } catch (error) {
          console.error('❌ PWA: Service Worker registration failed:', error)
        }
      }
    }

    registerSW()

    // Listener para mudanças de conectividade
    const handleOnline = () => {
      console.log('🌐 PWA: Network online')
      // Disparar sincronização se disponível
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
          // @ts-ignore - Background Sync API
          if ('sync' in registration) {
            (registration as any).sync.register('background-sync')
          }
        }).catch(console.error)
      }
    }

    const handleOffline = () => {
      console.log('📴 PWA: Network offline')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Prevenção de zoom em dispositivos móveis (comportamento nativo de app)
    const preventZoom = (e: TouchEvent) => {
      if (e.touches.length > 1) {
        e.preventDefault()
      }
    }

    document.addEventListener('touchstart', preventZoom, { passive: false })

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      document.removeEventListener('touchstart', preventZoom)
    }
  }, [])

  return (
    <>
      {/* Indicador de status offline/online */}
      <OfflineIndicator />
      
      {/* Prompt de instalação PWA */}
      <PWAPrompt variant="banner" autoShow={true} />
      
      {/* Conteúdo principal */}
      {children}
    </>
  )
}

// Hook para verificar se está rodando como PWA
export function usePWAStatus() {
  const [isPWA, setIsPWA] = React.useState(false)

  React.useEffect(() => {
    const checkPWA = () => {
      // Verificar se está em modo standalone (PWA instalada)
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches
      // Verificar iOS PWA
      const isIOSPWA = (window.navigator as any).standalone === true
      // Verificar Android PWA
      const isAndroidPWA = window.matchMedia('(display-mode: standalone)').matches
      
      const pwaMode = isStandalone || isIOSPWA || isAndroidPWA
      setIsPWA(pwaMode)
      
      // Adicionar classe CSS para PWA
      if (pwaMode) {
        document.body.classList.add('pwa-mode')
        console.log('📱 PWA: Running as installed app')
      } else {
        document.body.classList.remove('pwa-mode')
        console.log('🌐 PWA: Running in browser')
      }
    }

    checkPWA()

    // Listener para mudanças no display mode
    const mediaQuery = window.matchMedia('(display-mode: standalone)')
    mediaQuery.addEventListener('change', checkPWA)

    return () => {
      mediaQuery.removeEventListener('change', checkPWA)
    }
  }, [])

  return isPWA
}

// Component para detectar instalação
export function PWAInstallDetector() {
  React.useEffect(() => {
    // Detectar quando o app é instalado
    window.addEventListener('appinstalled', () => {
      console.log('🎉 PWA: App installed successfully')
      
      // Opcional: Analytics ou feedback
      // gtag('event', 'pwa_installed')
      
      // Mostrar mensagem de sucesso
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
          registration.showNotification('WhatsApp Agent Instalado!', {
            body: 'O app foi instalado e está pronto para uso offline.',
            icon: '/icon-192x192.png',
            badge: '/icon-72x72.png',
            tag: 'pwa-installed',
            requireInteraction: true
          }).catch(console.error)
        })
      }
    })

    // Detectar quando o prompt de instalação é mostrado
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('💫 PWA: Install prompt shown')
      // Opcional: Analytics
      // gtag('event', 'pwa_prompt_shown')
    })
  }, [])

  return null
}
