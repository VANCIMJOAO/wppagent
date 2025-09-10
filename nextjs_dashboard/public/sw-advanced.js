const CACHE_NAME = 'whatsapp-agent-v1'
const API_CACHE = 'api-cache-v1'
const STATIC_CACHE = 'static-cache-v1'

// Recursos para cache estático
const STATIC_RESOURCES = [
  '/dashboard',
  '/agendamentos',
  '/conversas',
  '/monitoring',
  '/offline',
  '/icon-192x192.png',
  '/manifest.json',
  '/_next/static/css/app.css',
  '/_next/static/chunks/webpack.js',
  '/_next/static/chunks/main.js',
  '/_next/static/chunks/pages/_app.js'
]

// Recursos de API para cache
const API_ENDPOINTS = [
  '/api/dashboard/stats',
  '/api/appointments/',
  '/api/conversations/',
  '/api/health/alerts',
  '/api/auth/verify'
]

// Install event
self.addEventListener('install', event => {
  console.log('🔧 SW: Installing...')
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => {
        console.log('📦 SW: Caching static resources')
        return cache.addAll(STATIC_RESOURCES.filter(url => !url.includes('_next')))
      }),
      caches.open(API_CACHE) // Preparar cache de API
    ]).then(() => {
      console.log('✅ SW: Installation complete')
    }).catch(error => {
      console.log('❌ SW: Installation failed', error)
    })
  )
  self.skipWaiting()
})

// Activate event
self.addEventListener('activate', event => {
  console.log('🔄 SW: Activating...')
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => 
            cacheName !== CACHE_NAME && 
            cacheName !== API_CACHE && 
            cacheName !== STATIC_CACHE
          )
          .map(cacheName => {
            console.log('🗑️ SW: Deleting old cache', cacheName)
            return caches.delete(cacheName)
          })
      )
    }).then(() => {
      console.log('✅ SW: Activation complete')
    })
  )
  self.clients.claim()
})

// Fetch event com estratégias diferentes
self.addEventListener('fetch', event => {
  const request = event.request
  const url = new URL(request.url)
  
  // Ignorar requests externos ou chrome-extension
  if (!url.origin.includes('localhost') && !url.origin.includes('127.0.0.1') && !url.origin.includes(self.location.origin)) {
    return
  }
  
  // Estratégia para APIs
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request))
  }
  // Estratégia para recursos estáticos
  else if (request.destination === 'script' || 
           request.destination === 'style' ||
           request.destination === 'image' ||
           url.pathname.includes('_next/static')) {
    event.respondWith(cacheFirstStrategy(request))
  }
  // Estratégia para páginas
  else if (request.mode === 'navigate') {
    event.respondWith(staleWhileRevalidateStrategy(request))
  }
})

// Network First - para APIs críticas
async function networkFirstStrategy(request) {
  try {
    console.log('🌐 SW: Network first for', request.url)
    const response = await fetch(request)
    
    // Se sucesso, atualizar cache
    if (response.status === 200) {
      const cache = await caches.open(API_CACHE)
      cache.put(request, response.clone())
      console.log('💾 SW: API cached', request.url)
    }
    
    return response
  } catch (error) {
    console.log('📴 SW: Network failed, trying cache for', request.url)
    // Fallback para cache
    const cachedResponse = await caches.match(request)
    if (cachedResponse) {
      // Adicionar header indicando que é cache
      const headers = new Headers(cachedResponse.headers)
      headers.set('X-Served-From', 'cache')
      headers.set('X-Cache-Date', new Date().toISOString())
      
      console.log('📋 SW: Serving from cache', request.url)
      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: headers
      })
    }
    
    // Se não tem cache, retornar resposta de erro ou página offline
    if (request.mode === 'navigate') {
      return caches.match('/offline') || new Response('Offline', { status: 503 })
    }
    
    // Para APIs, retornar dados offline padrão
    if (request.url.includes('/api/')) {
      return new Response(JSON.stringify({ 
        error: 'offline', 
        message: 'Dados não disponíveis offline',
        cached: false 
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      })
    }
    
    throw error
  }
}

// Cache First - para recursos estáticos
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request)
  if (cachedResponse) {
    console.log('⚡ SW: Cache hit for', request.url)
    return cachedResponse
  }
  
  try {
    console.log('🌐 SW: Fetching and caching', request.url)
    const response = await fetch(request)
    const cache = await caches.open(STATIC_CACHE)
    cache.put(request, response.clone())
    return response
  } catch (error) {
    console.log('❌ SW: Failed to fetch', request.url)
    // Fallback básico para imagens
    if (request.destination === 'image') {
      return new Response(`<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#f3f4f6"/>
        <text x="50" y="50" text-anchor="middle" dy="0.3em" font-family="Arial" font-size="12" fill="#6b7280">Offline</text>
      </svg>`, { 
        headers: { 'Content-Type': 'image/svg+xml' }
      })
    }
    throw error
  }
}

// Stale While Revalidate - para páginas
async function staleWhileRevalidateStrategy(request) {
  const cachedResponse = await caches.match(request)
  
  // Retornar cache imediatamente se disponível
  if (cachedResponse) {
    console.log('📋 SW: Serving stale content for', request.url)
    
    // Atualizar cache em background (sem waitUntil - execução assíncrona)
    fetch(request).then(response => {
      if (response.status === 200) {
        return caches.open(STATIC_CACHE).then(cache => {
          cache.put(request, response)
          console.log('🔄 SW: Background update completed for', request.url)
        })
      }
    }).catch(() => {
      // Ignorar erros de rede em background
      console.log('📴 SW: Background update failed for', request.url)
    })
    
    return cachedResponse
  }
  
  // Se não tem cache, buscar da rede
  try {
    console.log('🌐 SW: Fresh fetch for', request.url)
    const response = await fetch(request)
    if (response.status === 200) {
      const cache = await caches.open(STATIC_CACHE)
      cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    console.log('📴 SW: Network failed, serving offline page')
    return caches.match('/offline') || new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Offline - WhatsApp Agent</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f3f4f6; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .icon { font-size: 48px; margin-bottom: 20px; }
            h1 { color: #374151; margin-bottom: 10px; }
            p { color: #6b7280; margin-bottom: 20px; }
            button { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="icon">📴</div>
            <h1>Você está offline</h1>
            <p>Verifique sua conexão com a internet</p>
            <button onclick="window.location.reload()">Tentar Novamente</button>
          </div>
        </body>
      </html>
    `, { 
      headers: { 'Content-Type': 'text/html' },
      status: 503
    })
  }
}

// Background sync para ações offline
self.addEventListener('sync', event => {
  console.log('🔄 SW: Background sync triggered', event.tag)
  if (event.tag === 'background-sync') {
    event.waitUntil(syncOfflineActions())
  }
})

async function syncOfflineActions() {
  console.log('🔄 SW: Starting background sync...')
  try {
    // Buscar ações pendentes do IndexedDB
    const pendingActions = await getStoredActions()
    console.log(`📊 SW: Found ${pendingActions.length} pending actions`)
    
    for (const action of pendingActions) {
      try {
        console.log('🔄 SW: Syncing action', action.id, action.url)
        const response = await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        })
        
        if (response.ok) {
          // Remover ação sincronizada
          await removeStoredAction(action.id)
          console.log('✅ SW: Action synced successfully', action.id)
        } else {
          console.log('❌ SW: Sync failed for action', action.id, response.status)
        }
      } catch (error) {
        console.log('❌ SW: Sync error for action', action.id, error)
      }
    }
  } catch (error) {
    console.log('❌ SW: Background sync failed', error)
  }
}

// Funções para IndexedDB (simplified)
async function getStoredActions() {
  return new Promise((resolve) => {
    const request = indexedDB.open('WhatsAppAgentDB', 1)
    request.onsuccess = () => {
      const db = request.result
      if (!db.objectStoreNames.contains('pending_actions')) {
        resolve([])
        return
      }
      
      const transaction = db.transaction(['pending_actions'], 'readonly')
      const store = transaction.objectStore('pending_actions')
      const getRequest = store.getAll()
      
      getRequest.onsuccess = () => resolve(getRequest.result || [])
      getRequest.onerror = () => resolve([])
    }
    request.onerror = () => resolve([])
  })
}

async function removeStoredAction(id) {
  return new Promise((resolve) => {
    const request = indexedDB.open('WhatsAppAgentDB', 1)
    request.onsuccess = () => {
      const db = request.result
      if (!db.objectStoreNames.contains('pending_actions')) {
        resolve()
        return
      }
      
      const transaction = db.transaction(['pending_actions'], 'readwrite')
      const store = transaction.objectStore('pending_actions')
      const deleteRequest = store.delete(id)
      
      deleteRequest.onsuccess = () => resolve()
      deleteRequest.onerror = () => resolve()
    }
    request.onerror = () => resolve()
  })
}

// Message handling para comunicação com o app
self.addEventListener('message', event => {
  console.log('💬 SW: Message received', event.data)
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
  
  if (event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME })
  }
  
  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(cacheNames.map(cacheName => caches.delete(cacheName)))
      }).then(() => {
        event.ports[0].postMessage({ cleared: true })
      })
    )
  }
})

console.log('🚀 SW: Advanced Service Worker loaded')
