'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bell, BellRing, Send, Settings } from 'lucide-react'

const PushNotificationTest: React.FC = () => {
  const [subscription, setSubscription] = useState<PushSubscription | null>(null)
  const [permission, setPermission] = useState<NotificationPermission>('default')
  const [isSupported, setIsSupported] = useState(false)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')

  useEffect(() => {
    // Check if push notifications are supported
    setIsSupported('serviceWorker' in navigator && 'PushManager' in window)
    setPermission(Notification.permission)

    // Load existing subscription
    loadExistingSubscription()
  }, [])

  const loadExistingSubscription = async () => {
    try {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration()
        if (registration) {
          const sub = await registration.pushManager.getSubscription()
          setSubscription(sub)
        }
      }
    } catch (error) {
      console.error('Error loading subscription:', error)
    }
  }

  const requestPermission = async () => {
    try {
      const permission = await Notification.requestPermission()
      setPermission(permission)
      return permission === 'granted'
    } catch (error) {
      console.error('Error requesting permission:', error)
      return false
    }
  }

  const subscribe = async () => {
    setLoading(true)
    setStatus('Inscrevendo em notificações...')

    try {
      // Request permission if not granted
      if (permission !== 'granted') {
        const granted = await requestPermission()
        if (!granted) {
          setStatus('Permissão negada para notificações')
          return
        }
      }

      // Register service worker
      const registration = await navigator.serviceWorker.register('/sw-push.js')
      await navigator.serviceWorker.ready

      // Get VAPID public key from backend
      const vapidResponse = await fetch('/api/push/vapid-public-key')
      const { publicKey } = await vapidResponse.json()

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: publicKey
      })

      // Send subscription to backend
      const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Required': 'true'
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          p256dh_key: arrayBufferToBase64(subscription.getKey('p256dh')!),
          auth_key: arrayBufferToBase64(subscription.getKey('auth')!)
        })
      })

      if (response.ok) {
        setSubscription(subscription)
        setStatus('Inscrito com sucesso!')
      } else {
        throw new Error('Erro ao salvar subscription no backend')
      }
    } catch (error) {
      console.error('Error subscribing:', error)
      setStatus(`Erro: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const unsubscribe = async () => {
    setLoading(true)
    setStatus('Cancelando inscrição...')

    try {
      if (subscription) {
        // Unsubscribe from push manager
        await subscription.unsubscribe()

        // Remove from backend
        await fetch('/api/push/unsubscribe', {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-Auth-Required': 'true'
          },
          body: JSON.stringify({
            endpoint: subscription.endpoint
          })
        })

        setSubscription(null)
        setStatus('Inscrição cancelada')
      }
    } catch (error) {
      console.error('Error unsubscribing:', error)
      setStatus(`Erro: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const sendTestNotification = async () => {
    setLoading(true)
    setStatus('Enviando notificação de teste...')

    try {
      const response = await fetch('/api/push/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Required': 'true'
        },
        body: JSON.stringify({
          title: 'Teste de Push Notification',
          body: 'Esta é uma notificação de teste do WhatsApp Agent!',
          icon: '/favicon.ico',
          badge: '/favicon.ico'
        })
      })

      if (response.ok) {
        setStatus('Notificação enviada!')
      } else {
        throw new Error('Erro ao enviar notificação')
      }
    } catch (error) {
      console.error('Error sending notification:', error)
      setStatus(`Erro: ${error}`)
    } finally {
      setLoading(false)
    }
  }

  const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
  }

  const getPermissionBadge = () => {
    switch (permission) {
      case 'granted':
        return <Badge className="bg-green-500">Permitido</Badge>
      case 'denied':
        return <Badge variant="destructive">Negado</Badge>
      default:
        return <Badge variant="secondary">Não solicitado</Badge>
    }
  }

  if (!isSupported) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Push Notifications
          </CardTitle>
          <CardDescription>
            Teste do sistema de notificações push
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-500">
              Push notifications não são suportadas neste navegador
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Push Notifications
        </CardTitle>
        <CardDescription>
          Teste do sistema de notificações push
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium">Permissão:</label>
            <div className="mt-1">
              {getPermissionBadge()}
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">Status:</label>
            <div className="mt-1">
              {subscription ? (
                <Badge className="bg-blue-500">Inscrito</Badge>
              ) : (
                <Badge variant="outline">Não inscrito</Badge>
              )}
            </div>
          </div>
        </div>

        {status && (
          <div className="p-3 bg-gray-50 rounded-md">
            <p className="text-sm">{status}</p>
          </div>
        )}

        <div className="flex gap-2 flex-wrap">
          {!subscription ? (
            <Button
              onClick={subscribe}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <BellRing className="h-4 w-4" />
              Inscrever-se
            </Button>
          ) : (
            <>
              <Button
                onClick={unsubscribe}
                disabled={loading}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Bell className="h-4 w-4" />
                Cancelar Inscrição
              </Button>
              <Button
                onClick={sendTestNotification}
                disabled={loading}
                className="flex items-center gap-2"
              >
                <Send className="h-4 w-4" />
                Teste
              </Button>
            </>
          )}
        </div>

        {subscription && (
          <div className="text-xs text-gray-500 mt-4">
            <p>Endpoint: {subscription.endpoint.substring(0, 50)}...</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default PushNotificationTest
