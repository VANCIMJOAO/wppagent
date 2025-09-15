// H005: Service Worker PWA com bypass para autenticação
// Versão otimizada que funciona offline mas não interfere com login/auth
const CACHE_NAME = 'whatsapp-agent-h005-v1'
const API_CACHE = 'api-cache-h005-v1'
const STATIC_CACHE = 'static-cache-h005-v1'
const AUTH_CACHE = 'auth-cache-h005-v1'

// URLs que devem sempre passar pela rede (não cachear)
const AUTH_BYPASS_URLS = [
  '/api/auth/',
  '/api/login',
  '/api/logout',
  '/api/session',
  '/api/csrf',
  '/auth/',
  '/login',
  '/logout'
]

// URLs que podem ser cacheadas para funcionamento offline
const CACHEABLE_URLS = [
  '/dashboard',
  '/agendamentos',
  '/conversas',
  '/monitoring',
  '/clientes',
  '/analytics',
  '/configuracoes'
]

// Recursos estáticos essenciais
const STATIC_RESOURCES = [
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png',
  '/offline'
]

// Install event
self.addEventListener('install', event => {
  console.log('🔧 H005 SW: Installing PWA Service Worker...')
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => {
        console.log('📦 H005 SW: Caching static resources')
        return cache.addAll(STATIC_RESOURCES)
      }),
      caches.open(API_CACHE),
      caches.open(AUTH_CACHE)
    ]).then(() => {
      console.log('✅ H005 SW: Installation complete - PWA ready')
    }).catch(error => {
      console.log('❌ H005 SW: Installation failed', error)
    })
  )
  self.skipWaiting()
})

// Activate event
self.addEventListener('activate', event => {
  console.log('🔄 H005 SW: Activating PWA Service Worker...')
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName =>
            !cacheName.includes('h005') // Manter apenas caches da versão H005
          )
          .map(cacheName => {
            console.log('🗑️ H005 SW: Deleting old cache', cacheName)
            return caches.delete(cacheName)
          })
      )
    }).then(() => {
      console.log('✅ H005 SW: Activation complete')
      return self.clients.claim()
    }).catch(error => {
      console.log('❌ H005 SW: Activation failed', error)
    })
  )
})

// Verificar se URL deve usar bypass de autenticação
function shouldBypassAuth(url) {
  return AUTH_BYPASS_URLS.some(authUrl => url.pathname.includes(authUrl))
}

// Verificar se é uma request de navegação (página)
function isNavigationRequest(request) {
  return request.mode === 'navigate' ||
         (request.method === 'GET' && request.headers.get('accept') &&
          request.headers.get('accept').includes('text/html'))
}

// Estratégia: Network First para Auth, Cache First para recursos offline
self.addEventListener('fetch', event => {
  const request = event.request
  const url = new URL(request.url)

  // Ignorar requests externos
  if (!url.origin.includes(self.location.origin)) {
    return
  }

  // BYPASS: Sempre usar rede para autenticação (não cachear)
  if (shouldBypassAuth(url)) {
    console.log('🔐 H005 SW: Auth bypass for', url.pathname)
    event.respondWith(
      fetch(request).catch(error => {
        console.log('❌ H005 SW: Auth request failed - offline', error)
        // Para auth offline, retornar resposta que indica necessidade de login
        if (isNavigationRequest(request)) {
          return new Response(
            '<!DOCTYPE html><html><head><title>Offline</title></head><body><script>window.location.href="/offline?auth=required"</script></body></html>',
            {
              headers: { 'Content-Type': 'text/html' },
              status: 200
            }
          )
        }
        return new Response(JSON.stringify({error: 'Offline - auth required'}), {
          headers: { 'Content-Type': 'application/json' },
          status: 401
        })
      })
    )
    return
  }

  // Para APIs não-auth: tentar rede primeiro, cache como fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE).then(cache => {
        return fetch(request).then(response => {
          // Cachear apenas respostas 200
          if (response.status === 200) {
            cache.put(request, response.clone())
          }
          return response
        }).catch(() => {
          console.log('📱 H005 SW: Using cached API response for', url.pathname)
          return cache.match(request) || new Response(
            JSON.stringify({error: 'Offline', cached: false}),
            { headers: { 'Content-Type': 'application/json' } }
          )
        })
      })
    )
    return
  }

  // Para páginas: estratégia stale-while-revalidate
  if (isNavigationRequest(request)) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(cache => {
        return cache.match(request).then(cachedResponse => {
          const fetchPromise = fetch(request).then(networkResponse => {
            if (networkResponse.status === 200) {
              cache.put(request, networkResponse.clone())
            }
            return networkResponse
          }).catch(() => {
            console.log('📱 H005 SW: Network failed, serving offline page')
            // Se não há versão cacheada, servir página offline
            return cache.match('/offline') || new Response(
              '<!DOCTYPE html><html><head><title>Offline</title></head><body><h1>Aplicação Offline</h1><p>Sem conexão com internet. Algumas funcionalidades podem estar limitadas.</p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            )
          })

          // Retornar cache imediatamente se existir, senão aguardar rede
          return cachedResponse || fetchPromise
        })
      })
    )
    return
  }

  // Para recursos estáticos: cache first
  if (request.destination === 'script' ||
      request.destination === 'style' ||
      request.destination === 'image' ||
      url.pathname.includes('_next/static')) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(cache => {
        return cache.match(request).then(cachedResponse => {
          if (cachedResponse) {
            // Atualizar em background
            fetch(request).then(response => {
              if (response.status === 200) {
                cache.put(request, response.clone())
              }
            }).catch(() => {}) // Ignorar erros de background update
            return cachedResponse
          }

          return fetch(request).then(response => {
            if (response.status === 200) {
              cache.put(request, response.clone())
            }
            return response
          })
        })
      })
    )
    return
  }
})

// Background sync para quando voltar online
self.addEventListener('sync', event => {
  console.log('🔄 H005 SW: Background sync triggered', event.tag)
  // Implementar sync de dados pendentes quando voltar online
})

// Push notifications (futuro)
self.addEventListener('push', event => {
  console.log('🔔 H005 SW: Push notification received', event.data?.text())
  // Implementar notificações push
})

console.log('✅ H005 SW: PWA Service Worker loaded with auth bypass')
