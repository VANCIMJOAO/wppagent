/**
 * 🔔 Service Worker para Push Notifications
 * 
 * Gerencia push notifications do WhatsApp Agent Dashboard.
 * Funcionalidades:
 * - Receber push notifications
 * - Exibir notificações customizadas
 * - Tratar cliques e interações
 * - Offline capabilities
 */

// Configurações do Service Worker
const CACHE_NAME = 'whatsapp-agent-v1';
const NOTIFICATION_TAG = 'whatsapp-agent';
const API_BASE_URL = self.location.origin;

/**
 * 📦 Instalação do Service Worker
 */
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Installing...');
    
    // Força a ativação imediata
    event.waitUntil(self.skipWaiting());
});

/**
 * 🚀 Ativação do Service Worker
 */
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker: Activated');
    
    // Assume controle de todas as abas
    event.waitUntil(self.clients.claim());
});

/**
 * 🔔 Recebimento de Push Notifications
 */
self.addEventListener('push', (event) => {
    console.log('📬 Push notification received:', event);
    
    if (!event.data) {
        console.warn('Push notification without data');
        return;
    }
    
    try {
        const data = event.data.json();
        
        // Configurações padrão
        const options = {
            title: data.title || 'WhatsApp Agent',
            body: data.body || 'Nova notificação disponível',
            icon: data.icon || '/icons/notification-icon-192.png',
            badge: data.badge || '/icons/badge-icon-96.png',
            tag: data.tag || NOTIFICATION_TAG,
            data: data.data || {},
            
            // Configurações avançadas
            requireInteraction: data.requireInteraction || false,
            silent: false,
            timestamp: data.timestamp || Date.now(),
            
            // Ações da notificação
            actions: getNotificationActions(data),
            
            // Visual
            image: data.image,
            vibrate: data.vibrate || [200, 100, 200]
        };
        
        // Log da notificação
        console.log('📤 Displaying notification:', options);
        
        // Exibir notificação
        event.waitUntil(
            self.registration.showNotification(options.title, options)
        );
        
    } catch (error) {
        console.error('❌ Error processing push notification:', error);
        
        // Fallback notification
        event.waitUntil(
            self.registration.showNotification('WhatsApp Agent', {
                body: 'Nova notificação disponível',
                icon: '/icons/notification-icon-192.png',
                tag: NOTIFICATION_TAG
            })
        );
    }
});

/**
 * 👆 Clique em Notificação
 */
self.addEventListener('notificationclick', (event) => {
    console.log('👆 Notification clicked:', event);
    
    const notification = event.notification;
    const action = event.action;
    const data = notification.data || {};
    
    // Fechar notificação
    notification.close();
    
    // URLs para diferentes ações
    const urls = {
        default: '/dashboard',
        conversation: data.conversation_id ? `/dashboard/conversas/${data.conversation_id}` : '/dashboard/conversas',
        appointment: data.appointment_id ? `/dashboard/agendamentos/${data.appointment_id}` : '/dashboard/agendamentos',
        alert: '/dashboard/alertas',
        test: '/dashboard',
        settings: '/dashboard/configuracoes'
    };
    
    // Determinar URL de destino
    let targetUrl = urls.default;
    
    if (action) {
        targetUrl = urls[action] || urls.default;
    } else if (data.url) {
        targetUrl = data.url;
    } else if (data.conversation_id) {
        targetUrl = urls.conversation;
    } else if (data.appointment_id) {
        targetUrl = urls.appointment;
    } else if (data.alert_type) {
        targetUrl = urls.alert;
    }
    
    // Abrir ou focar na aba
    event.waitUntil(
        openOrFocusTab(targetUrl, data)
    );
    
    // Analytics/tracking (opcional)
    trackNotificationClick(action, data);
});

/**
 * ❌ Fechamento de Notificação
 */
self.addEventListener('notificationclose', (event) => {
    console.log('❌ Notification closed:', event);
    
    const data = event.notification.data || {};
    
    // Analytics/tracking opcional
    trackNotificationClose(data);
});

/**
 * 📧 Mensagem do Cliente
 */
self.addEventListener('message', (event) => {
    console.log('📧 Message received:', event.data);
    
    const { type, payload } = event.data;
    
    switch (type) {
        case 'UPDATE_SUBSCRIPTION':
            // Atualizar dados da subscription
            updateSubscriptionData(payload);
            break;
            
        case 'CLEAR_NOTIFICATIONS':
            // Limpar todas as notificações
            clearAllNotifications();
            break;
            
        case 'TEST_NOTIFICATION':
            // Exibir notificação de teste
            showTestNotification();
            break;
            
        default:
            console.warn('Unknown message type:', type);
    }
});

// ========================================
// FUNÇÕES AUXILIARES
// ========================================

/**
 * 🎯 Obter ações da notificação baseado no tipo
 */
function getNotificationActions(data) {
    const baseActions = [
        {
            action: 'default',
            title: '👀 Ver Dashboard',
            icon: '/icons/action-view.png'
        }
    ];
    
    // Ações específicas por tipo
    if (data.data?.conversation_id) {
        return [
            {
                action: 'conversation',
                title: '💬 Ver Conversa',
                icon: '/icons/action-chat.png'
            },
            {
                action: 'default',
                title: '📊 Dashboard',
                icon: '/icons/action-dashboard.png'
            }
        ];
    }
    
    if (data.data?.appointment_id) {
        return [
            {
                action: 'appointment',
                title: '📅 Ver Agendamento',
                icon: '/icons/action-calendar.png'
            },
            {
                action: 'default',
                title: '📊 Dashboard',
                icon: '/icons/action-dashboard.png'
            }
        ];
    }
    
    if (data.data?.alert_type) {
        return [
            {
                action: 'alert',
                title: '🚨 Ver Alerta',
                icon: '/icons/action-alert.png'
            },
            {
                action: 'settings',
                title: '⚙️ Configurações',
                icon: '/icons/action-settings.png'
            }
        ];
    }
    
    return baseActions;
}

/**
 * 🪟 Abrir ou focar em aba existente
 */
async function openOrFocusTab(url, data) {
    try {
        const fullUrl = new URL(url, self.location.origin).href;
        
        // Procurar por aba existente
        const clients = await self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        });
        
        // Verificar se já existe uma aba com a URL
        for (const client of clients) {
            if (client.url === fullUrl && 'focus' in client) {
                console.log('🎯 Focusing existing tab:', fullUrl);
                await client.focus();
                
                // Enviar dados adicionais para a aba
                if (data && Object.keys(data).length > 0) {
                    client.postMessage({
                        type: 'NOTIFICATION_DATA',
                        payload: data
                    });
                }
                
                return;
            }
        }
        
        // Abrir nova aba se não encontrou existente
        console.log('🆕 Opening new tab:', fullUrl);
        await self.clients.openWindow(fullUrl);
        
    } catch (error) {
        console.error('❌ Error opening/focusing tab:', error);
    }
}

/**
 * 📊 Atualizar dados da subscription
 */
function updateSubscriptionData(data) {
    // Armazenar dados localmente se necessário
    console.log('📊 Updating subscription data:', data);
}

/**
 * 🧹 Limpar todas as notificações
 */
async function clearAllNotifications() {
    try {
        const notifications = await self.registration.getNotifications();
        notifications.forEach(notification => notification.close());
        console.log(`🧹 Cleared ${notifications.length} notifications`);
    } catch (error) {
        console.error('❌ Error clearing notifications:', error);
    }
}

/**
 * 🧪 Exibir notificação de teste
 */
async function showTestNotification() {
    try {
        await self.registration.showNotification('🧪 Teste de Notificação', {
            body: 'As notificações push estão funcionando perfeitamente!',
            icon: '/icons/notification-icon-192.png',
            badge: '/icons/badge-icon-96.png',
            tag: 'test-notification',
            data: { test: true },
            actions: [
                {
                    action: 'default',
                    title: '✅ Perfeito!',
                    icon: '/icons/action-check.png'
                }
            ]
        });
        
        console.log('🧪 Test notification shown');
        
    } catch (error) {
        console.error('❌ Error showing test notification:', error);
    }
}

/**
 * 📈 Tracking de clique em notificação
 */
function trackNotificationClick(action, data) {
    // Implementar analytics se necessário
    console.log('📈 Notification click tracked:', { action, data });
}

/**
 * 📈 Tracking de fechamento de notificação
 */
function trackNotificationClose(data) {
    // Implementar analytics se necessário
    console.log('📈 Notification close tracked:', data);
}

// ========================================
// BACKGROUND SYNC (Futuro)
// ========================================

/**
 * 🔄 Background Sync
 * Para funcionalidades offline futuras
 */
self.addEventListener('sync', (event) => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    switch (event.tag) {
        case 'sync-notifications':
            event.waitUntil(syncNotifications());
            break;
            
        default:
            console.log('Unknown sync tag:', event.tag);
    }
});

async function syncNotifications() {
    // Implementar sincronização offline no futuro
    console.log('🔄 Syncing notifications...');
}

// ========================================
// ERROR HANDLING
// ========================================

self.addEventListener('error', (event) => {
    console.error('❌ Service Worker error:', event);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Service Worker unhandled rejection:', event);
});

// Log de inicialização
console.log('🔔 Push Notifications Service Worker loaded successfully');
console.log('🌐 Service Worker scope:', self.registration.scope);
console.log('🔧 API Base URL:', API_BASE_URL);
