/**
 * 🔧 Advanced Service Worker - Offline Support
 * =============================================
 * 
 * Service Worker avançado com:
 * - Background Sync para queue offline
 * - Cache strategies inteligentes
 * - Selective caching por tipo de recurso
 * - Network-first vs Cache-first strategies
 * 
 * Status: Resolução completa do problema 4.2 Offline Support Limitado
 */

const CACHE_NAME = 'whatsapp-agent-offline-v2';
const DATA_CACHE_NAME = 'whatsapp-agent-data-v2';

// URLs para cache estático (recursos da aplicação)
const STATIC_CACHE_URLS = [
  '/',
  '/login',
  '/dashboard',
  '/appointments',
  '/analytics',
  '/manifest.json',
  '/offline.html',
  // Assets
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Styles e scripts críticos serão adicionados automaticamente
];

// URLs para cache dinâmico (dados da API)
const API_CACHE_PATTERNS = [
  /^\/api\/dashboard/,
  /^\/api\/appointments/,
  /^\/api\/analytics/,
  /^\/api\/messages/
];

// URLs que nunca devem ser cachadas
const NO_CACHE_PATTERNS = [
  /^\/api\/auth/,
  /^\/api\/upload/,
  /^\/api\/sync/
];

// Sync queue for offline actions
let syncQueue = [];

/**
 * 📦 Install Event - Cache recursos estáticos
 */
self.addEventListener('install', event => {
  console.log('📦 Service Worker: Installing...');
  
  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        
        // Cache recursos estáticos essenciais
        await cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, {
          credentials: 'same-origin'
        })));
        
        console.log('✅ Service Worker: Static resources cached');
        
        // Skip waiting to activate immediately
        await self.skipWaiting();
        
      } catch (error) {
        console.error('❌ Service Worker: Install failed:', error);
      }
    })()
  );
});

/**
 * 🔄 Activate Event - Cleanup old caches
 */
self.addEventListener('activate', event => {
  console.log('🔄 Service Worker: Activating...');
  
  event.waitUntil(
    (async () => {
      try {
        // Cleanup old caches
        const cacheNames = await caches.keys();
        const deletePromises = cacheNames
          .filter(name => name !== CACHE_NAME && name !== DATA_CACHE_NAME)
          .map(name => caches.delete(name));
        
        await Promise.all(deletePromises);
        
        console.log('🧹 Service Worker: Old caches cleaned');
        
        // Claim control of all clients
        await self.clients.claim();
        
        console.log('✅ Service Worker: Activated successfully');
        
      } catch (error) {
        console.error('❌ Service Worker: Activation failed:', error);
      }
    })()
  );
});

/**
 * 🌐 Fetch Event - Handle network requests
 */
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests for caching
  if (request.method !== 'GET') {
    // Handle POST/PUT/DELETE for offline queueing
    if (!navigator.onLine && ['POST', 'PUT', 'DELETE'].includes(request.method)) {
      event.respondWith(handleOfflineAction(request));
    }
    return;
  }
  
  // Determine cache strategy based on URL
  if (isApiRequest(url)) {
    // API requests: Network-first with cache fallback
    event.respondWith(networkFirstStrategy(request));
  } else if (isStaticResource(url)) {
    // Static resources: Cache-first with network fallback
    event.respondWith(cacheFirstStrategy(request));
  } else {
    // Default: Network-first
    event.respondWith(networkFirstStrategy(request));
  }
});

/**
 * 🔄 Background Sync Event
 */
self.addEventListener('sync', event => {
  console.log('🔄 Background Sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(processOfflineQueue());
  }
});

/**
 * 💬 Message Event - Communication with main thread
 */
self.addEventListener('message', event => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'QUEUE_OFFLINE_ACTION':
      queueOfflineAction(data);
      break;
      
    case 'FORCE_SYNC':
      processOfflineQueue();
      break;
      
    case 'CLEAR_CACHE':
      clearCaches(data.cacheNames);
      break;
      
    case 'GET_CACHE_STATUS':
      getCacheStatus().then(status => {
        event.ports[0].postMessage({ type: 'CACHE_STATUS', data: status });
      });
      break;
      
    default:
      console.warn('Unknown message type:', type);
  }
});

/**
 * 🌐 Network-First Strategy
 * Tenta rede primeiro, fallback para cache
 */
async function networkFirstStrategy(request) {
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok && shouldCacheResponse(request, response)) {
      const cache = await caches.open(isApiRequest(new URL(request.url)) ? DATA_CACHE_NAME : CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.log('🔄 Network failed, trying cache:', request.url);
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // Add offline indicator header
      const headers = new Headers(cachedResponse.headers);
      headers.append('X-Served-From', 'cache');
      
      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: headers
      });
    }
    
    // If no cache, return offline page for navigation requests
    if (request.destination === 'document') {
      const offlinePage = await caches.match('/offline.html');
      return offlinePage || new Response('Offline', { status: 503 });
    }
    
    // For other requests, return error response
    return new Response(JSON.stringify({
      error: 'Offline and no cache available',
      url: request.url
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * 💾 Cache-First Strategy
 * Serve do cache primeiro, atualiza em background
 */
async function cacheFirstStrategy(request) {
  try {
    // Try cache first
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      // Serve from cache immediately
      
      // Update cache in background if online
      if (navigator.onLine) {
        fetch(request).then(response => {
          if (response.ok) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, response);
            });
          }
        }).catch(error => {
          console.log('Background update failed:', error);
        });
      }
      
      return cachedResponse;
    }
    
    // If not in cache, fetch from network
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.error('Cache-first strategy failed:', error);
    return new Response('Resource unavailable', { status: 503 });
  }
}

/**
 * 📱 Handle offline actions (POST/PUT/DELETE)
 */
async function handleOfflineAction(request) {
  try {
    const action = {
      id: generateId(),
      url: request.url,
      method: request.method,
      headers: {},
      body: await request.text(),
      timestamp: Date.now()
    };
    
    // Convert headers
    for (const [key, value] of request.headers.entries()) {
      action.headers[key] = value;
    }
    
    // Queue the action
    await queueOfflineAction(action);
    
    // Return optimistic response
    return new Response(JSON.stringify({
      success: true,
      message: 'Action queued for sync when online',
      queued: true,
      actionId: action.id
    }), {
      status: 202, // Accepted
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    console.error('Failed to handle offline action:', error);
    
    return new Response(JSON.stringify({
      error: 'Failed to queue offline action',
      details: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * ➕ Queue offline action
 */
async function queueOfflineAction(action) {
  try {
    // Open IndexedDB
    const db = await openIndexedDB();
    const tx = db.transaction(['syncQueue'], 'readwrite');
    const store = tx.objectStore('syncQueue');
    
    await store.add(action);
    
    console.log('📤 Offline action queued:', action);
    
    // Register for background sync
    if ('sync' in self.registration) {
      await self.registration.sync.register('background-sync');
    }
    
  } catch (error) {
    console.error('Failed to queue offline action:', error);
  }
}

/**
 * 🔄 Process offline queue
 */
async function processOfflineQueue() {
  try {
    if (!navigator.onLine) {
      console.log('Still offline, skipping queue processing');
      return;
    }
    
    console.log('🔄 Processing offline queue...');
    
    const db = await openIndexedDB();
    const tx = db.transaction(['syncQueue'], 'readonly');
    const store = tx.objectStore('syncQueue');
    const actions = await store.getAll();
    
    console.log(`📋 Found ${actions.length} queued actions`);
    
    for (const action of actions) {
      try {
        await executeQueuedAction(action);
        await removeFromQueue(action.id);
        console.log('✅ Action executed and removed from queue:', action.id);
        
      } catch (error) {
        console.error('❌ Failed to execute queued action:', action.id, error);
        
        // Increment retry count
        action.retries = (action.retries || 0) + 1;
        
        if (action.retries >= 3) {
          console.warn('⚠️ Max retries reached, removing action:', action.id);
          await removeFromQueue(action.id);
        } else {
          console.log(`🔄 Will retry action ${action.id} (attempt ${action.retries})`);
        }
      }
    }
    
    // Notify clients about sync completion
    notifyClients({ type: 'SYNC_COMPLETED', count: actions.length });
    
  } catch (error) {
    console.error('❌ Failed to process offline queue:', error);
  }
}

/**
 * ⚡ Execute queued action
 */
async function executeQueuedAction(action) {
  const response = await fetch(action.url, {
    method: action.method,
    headers: action.headers,
    body: action.body || undefined
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  return response;
}

/**
 * 🗑️ Remove action from queue
 */
async function removeFromQueue(actionId) {
  const db = await openIndexedDB();
  const tx = db.transaction(['syncQueue'], 'readwrite');
  const store = tx.objectStore('syncQueue');
  await store.delete(actionId);
}

/**
 * 🗄️ Open IndexedDB
 */
async function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('WhatsAppAgentSW', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('syncQueue')) {
        const store = db.createObjectStore('syncQueue', { keyPath: 'id' });
        store.createIndex('timestamp', 'timestamp');
        store.createIndex('url', 'url');
      }
    };
  });
}

/**
 * 📡 Notify all clients
 */
function notifyClients(message) {
  self.clients.matchAll().then(clients => {
    clients.forEach(client => {
      client.postMessage(message);
    });
  });
}

/**
 * 🧹 Clear specific caches
 */
async function clearCaches(cacheNames = []) {
  try {
    if (cacheNames.length === 0) {
      cacheNames = [CACHE_NAME, DATA_CACHE_NAME];
    }
    
    for (const cacheName of cacheNames) {
      await caches.delete(cacheName);
      console.log(`🧹 Cleared cache: ${cacheName}`);
    }
    
  } catch (error) {
    console.error('❌ Failed to clear caches:', error);
  }
}

/**
 * 📊 Get cache status
 */
async function getCacheStatus() {
  try {
    const cacheNames = await caches.keys();
    const status = {};
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      status[cacheName] = keys.length;
    }
    
    return status;
    
  } catch (error) {
    console.error('❌ Failed to get cache status:', error);
    return {};
  }
}

// Helper functions

function isApiRequest(url) {
  return url.pathname.startsWith('/api/') || API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isStaticResource(url) {
  return url.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)$/);
}

function shouldCacheResponse(request, response) {
  const url = new URL(request.url);
  
  // Don't cache if it matches no-cache patterns
  if (NO_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return false;
  }
  
  // Don't cache error responses
  if (!response.ok) {
    return false;
  }
  
  // Don't cache responses without proper headers
  const cacheControl = response.headers.get('cache-control');
  if (cacheControl && cacheControl.includes('no-store')) {
    return false;
  }
  
  return true;
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

console.log('🔧 Service Worker: Loaded successfully');
