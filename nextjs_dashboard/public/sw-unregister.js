// Script para desregistrar todos os service workers
console.log('🗑️ Desregistrando todos os service workers...')

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
      console.log('🗑️ Removendo service worker:', registration.scope)
      registration.unregister().then(function(success) {
        console.log('✅ Service worker removido com sucesso:', success)
      }).catch(function(error) {
        console.error('❌ Erro ao remover service worker:', error)
      })
    }
  }).catch(function(error) {
    console.error('❌ Erro ao buscar service workers:', error)
  })
}

// Limpar todos os caches
if ('caches' in window) {
  caches.keys().then(function(cacheNames) {
    return Promise.all(
      cacheNames.map(function(cacheName) {
        console.log('🗑️ Removendo cache:', cacheName)
        return caches.delete(cacheName)
      })
    )
  }).then(function() {
    console.log('✅ Todos os caches foram removidos')
  }).catch(function(error) {
    console.error('❌ Erro ao limpar caches:', error)
  })
}

console.log('✅ Limpeza concluída. Recarregue a página.')
