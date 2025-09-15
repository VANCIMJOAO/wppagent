'use client'

import { useState, useEffect } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function usePWAInstall() {
  const [isInstallable, setIsInstallable] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    // Verificar se já está instalado
    const checkIfInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches
      const isIOSPWA = (window.navigator as any).standalone === true
      const isInstalled = isStandalone || isIOSPWA
      setIsInstalled(isInstalled)
    }

    // Event listener para o prompt de instalação
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      const event = e as BeforeInstallPromptEvent
      setDeferredPrompt(event)
      setIsInstallable(true)
      console.log('🔄 PWA: Install prompt available')
    }

    // Event listener para quando o app é instalado
    const handleAppInstalled = () => {
      setIsInstalled(true)
      setIsInstallable(false)
      setDeferredPrompt(null)
      console.log('✅ PWA: App installed successfully')
    }

    checkIfInstalled()

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const installPWA = async () => {
    if (!deferredPrompt) {
      console.log('❌ PWA: No install prompt available')
      return false
    }

    try {
      await deferredPrompt.prompt()
      const choiceResult = await deferredPrompt.userChoice

      if (choiceResult.outcome === 'accepted') {
        console.log('✅ PWA: User accepted install')
        setIsInstallable(false)
        setDeferredPrompt(null)
        return true
      } else {
        console.log('❌ PWA: User dismissed install')
        return false
      }
    } catch (error) {
      console.error('❌ PWA: Install error:', error)
      return false
    }
  }

  return {
    isInstallable,
    isInstalled,
    installPWA
  }
}

// Hook para gerenciamento do Service Worker
export function useServiceWorker() {
  const [isSupported, setIsSupported] = useState(false)
  const [isRegistered, setIsRegistered] = useState(false)
  const [needsUpdate, setNeedsUpdate] = useState(false)
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null)

  useEffect(() => {
    const checkSupport = () => {
      const supported = 'serviceWorker' in navigator
      setIsSupported(supported)
      return supported
    }

    const registerSW = async () => {
      if (!checkSupport()) return

      try {
        const reg = await navigator.serviceWorker.register('/sw-advanced.js', {
          scope: '/'
        })

        setRegistration(reg)
        setIsRegistered(true)
        console.log('✅ SW: Service Worker registered')

        // Verificar atualizações
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.log('🔄 SW: Update available')
                setNeedsUpdate(true)
              }
            })
          }
        })

        // Verificar se há um novo service worker esperando
        if (reg.waiting) {
          setNeedsUpdate(true)
        }

        // Verificar periodicamente por atualizações
        setInterval(() => {
          reg.update()
        }, 60000) // A cada minuto

      } catch (error) {
        console.error('❌ SW: Registration failed:', error)
      }
    }

    registerSW()
  }, [])

  const updateServiceWorker = () => {
    if (registration?.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
      window.location.reload()
    }
  }

  const clearCache = async () => {
    if (!registration) return

    try {
      // Enviar mensagem para o SW limpar cache
      const messageChannel = new MessageChannel()

      const promise = new Promise<boolean>((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.cleared === true)
        }
      })

      registration.active?.postMessage({ type: 'CLEAR_CACHE' }, [messageChannel.port2])

      const cleared = await promise
      if (cleared) {
        console.log('🧹 SW: Cache cleared')
        window.location.reload()
      }

      return cleared
    } catch (error) {
      console.error('❌ SW: Error clearing cache:', error)
      return false
    }
  }

  return {
    isSupported,
    isRegistered,
    needsUpdate,
    updateServiceWorker,
    clearCache,
    registration
  }
}

// Hook combinado para PWA completo
export function usePWA() {
  const install = usePWAInstall()
  const serviceWorker = useServiceWorker()

  return {
    ...install,
    ...serviceWorker,
    isPWAReady: serviceWorker.isSupported && serviceWorker.isRegistered
  }
}
